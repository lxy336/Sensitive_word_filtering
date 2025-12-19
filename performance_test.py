#!/usr/bin/env python3
"""
五种过滤算法性能测试脚本
测试用例1-4：基础性能对比、词库规模影响、音频长度影响、语言差异对比
"""

import os
import sys
import time
import random
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from datetime import datetime
from pathlib import Path
import psutil
import gc

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 设置 FFmpeg 路径
ffmpeg_path = r"C:\Users\30687\.conda\envs\MachineLearningHomework\Library\bin"
current_path = os.environ.get('PATH', '')
if ffmpeg_path not in current_path:
    os.environ['PATH'] = ffmpeg_path + os.pathsep + current_path

# 添加本地 whisper 目录到 Python 路径
whisper_path = os.path.join(os.path.dirname(__file__), 'whisper')
if whisper_path not in sys.path:
    sys.path.insert(0, whisper_path)

import whisper

class PerformanceTester:
    def __init__(self):
        self.results = []
        self.model = None
        self.file_selection_counter = 0  # 用于确保不同测试选择不同文件
        
        # 敏感词配置 - 使用常见日常词汇
        self.chinese_words_small = ['我', '是', '今天']
        self.chinese_words_medium = ['我', '是', '今天', '学校', '朋友', '工作', '时间', '地方', '问题', '方法']
        self.chinese_words_large = ['我', '是', '今天',  '朋友', '家庭', '工作', '时间', '地方', '问题', '方法',
                                   '孩子', '父母', '同学', '班级', '课程', '作业', '考试', '成绩', '书本', '知识',
                                   '生活', '学习', '思考', '理解', '记忆', '经验', '故事', '事情', '情况', '结果',
                                   '开始', '结束', '过程', '发展', '变化', '进步', '努力', '坚持', '成功', '失败',
                                   '希望', '梦想', '目标', '计划', '决定', '选择', '机会', '挑战', '困难', '解决']
        
        self.english_words_small = ['school', 'today', 'I']
        self.english_words_medium = ['school', 'is', 'you', 'friend', 'family', 'work', 'time', 'place', 'problem', 'method']
        self.english_words_large = ['school', 'was', 'He', 'friend', 'family', 'work', 'time', 'place', 'problem', 'method',
                                   'child', 'parent', 'class', 'lesson', 'homework', 'test', 'grade', 'book', 'knowledge', 'story',
                                   'life', 'study', 'think', 'understand', 'remember', 'experience', 'situation', 'result', 'process', 'change',
                                   'start', 'finish', 'develop', 'progress', 'effort', 'success', 'failure', 'hope', 'dream', 'goal',
                                   'plan', 'decision', 'choice', 'opportunity', 'challenge', 'difficulty', 'solution', 'important', 'different', 'special']
        
        # 过滤方法列表
        self.filter_methods = ['DFA', 'aho_corasick', 'trie_tree', 'replace', 'regular_expression']
        
    def load_model(self):
        """加载Whisper模型"""
        print("加载 Whisper base 模型...")
        try:
            self.model = whisper.load_model("base")
            print("模型加载完成")
            return True
        except Exception as e:
            print(f"模型加载失败: {e}")
            return False
    
    def get_audio_files(self, data_dir, count=3):
        """获取指定数量的音频文件"""
        data_path = Path(data_dir)

        if not data_path.exists():
            print(f"数据目录不存在: {data_dir}")
            return []

        # 获取所有mp3文件并排序（确保顺序一致）
        all_files = sorted(list(data_path.glob("*.mp3")))

        if len(all_files) < count:
            print(f"{data_dir} 中只有 {len(all_files)} 个文件，少于请求的 {count} 个")
            return all_files

        # 使用计数器确保不同测试选择不同文件
        start_idx = (self.file_selection_counter * count) % len(all_files)
        selected_files = []

        for i in range(count):
            file_idx = (start_idx + i) % len(all_files)
            selected_files.append(all_files[file_idx])

        self.file_selection_counter += 1
        return selected_files
    
    def get_audio_duration(self, audio_file):
        """获取音频时长（简单估算）"""
        try:
            # 使用文件大小估算时长（粗略估算）
            file_size = os.path.getsize(audio_file)
            # 假设平均比特率为128kbps
            estimated_duration = file_size / (128 * 1024 / 8)  # 秒
            return max(1.0, estimated_duration)  # 至少1秒
        except:
            return 60.0  # 默认60秒
    
    def test_single_audio(self, audio_file, sensitive_words, filter_method, language="zh"):
        """测试单个音频文件"""
        print(f"  测试文件: {os.path.basename(audio_file)}")
        print(f"  过滤方法: {filter_method}")
        print(f"  敏感词数量: {len(sensitive_words) if sensitive_words else 0}")
        
        # 记录内存使用
        process = psutil.Process()
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        
        start_time = time.time()
        
        try:
            # 转录参数
            transcribe_params = {
                "language": language,
                "verbose": False,
                "word_timestamps": True,
                "sensitive_words": sensitive_words
            }
            
            if sensitive_words and filter_method:
                transcribe_params["filter_method"] = filter_method
            
            # 执行转录
            result = self.model.transcribe(str(audio_file), **transcribe_params)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # 计算音频时长
            if result['segments']:
                audio_duration = result['segments'][-1]['end']
            else:
                audio_duration = self.get_audio_duration(audio_file)
            
            # 计算实时倍数
            real_time_factor = total_time / audio_duration if audio_duration > 0 else 0
            
            # 记录内存使用
            memory_after = process.memory_info().rss / 1024 / 1024  # MB
            memory_used = memory_after - memory_before
            
            # 统计敏感词过滤效果
            filtered_count = 0
            if sensitive_words:
                original_text = result.get('simplified_text', result['text'])
                filtered_text = result['text']
                for word in sensitive_words:
                    filtered_count += original_text.count(word) - filtered_text.count(word)
            
            test_result = {
                'audio_file': os.path.basename(audio_file),
                'language': language,
                'filter_method': filter_method,
                'sensitive_words_count': len(sensitive_words) if sensitive_words else 0,
                'audio_duration': audio_duration,
                'total_time': total_time,
                'real_time_factor': real_time_factor,
                'memory_used': memory_used,
                'segments_count': len(result['segments']),
                'filtered_words_count': filtered_count,
                'success': True
            }
            
            print(f"  完成 - 时长: {audio_duration:.1f}s, 处理: {total_time:.1f}s, 倍数: {real_time_factor:.2f}x")
            
        except Exception as e:
            print(f"  失败: {e}")
            test_result = {
                'audio_file': os.path.basename(audio_file),
                'language': language,
                'filter_method': filter_method,
                'sensitive_words_count': len(sensitive_words) if sensitive_words else 0,
                'audio_duration': 0,
                'total_time': 0,
                'real_time_factor': 0,
                'memory_used': 0,
                'segments_count': 0,
                'filtered_words_count': 0,
                'success': False,
                'error': str(e)
            }
        
        # 清理内存
        gc.collect()
        
        return test_result

    def test_case_1_basic_performance(self):
        """测试用例1：基础性能对比"""
        print("\n测试用例1：基础性能对比")
        print("="*60)

        # 获取测试文件（每种语言3个文件）
        chinese_files = self.get_audio_files("中文数据", 3)
        english_files = self.get_audio_files("英语数据", 3)

        if not chinese_files or not english_files:
            print("无法获取足够的测试文件")
            return

        # 测试中文文件
        print(f"\n测试中文音频（{len(chinese_files)}个文件）...")
        for audio_file in chinese_files:
            for method in self.filter_methods:
                result = self.test_single_audio(
                    audio_file,
                    self.chinese_words_small,
                    method,
                    "zh"
                )
                result['test_case'] = 'basic_performance'
                result['word_set'] = 'small'
                self.results.append(result)

        # 测试英文文件
        print(f"\n测试英文音频（{len(english_files)}个文件）...")
        for audio_file in english_files:
            for method in self.filter_methods:
                result = self.test_single_audio(
                    audio_file,
                    self.english_words_small,
                    method,
                    "en"
                )
                result['test_case'] = 'basic_performance'
                result['word_set'] = 'small'
                self.results.append(result)

    def test_case_2_word_set_size(self):
        """测试用例2：词库规模影响"""
        print("\n测试用例2：词库规模影响")
        print("="*60)

        # 获取测试文件（3个文件）
        chinese_files = self.get_audio_files("中文数据", 3)

        if not chinese_files:
            print("无法获取中文测试文件")
            return

        word_sets = {
            'small': self.chinese_words_small,
            'medium': self.chinese_words_medium,
            'large': self.chinese_words_large
        }

        print(f"\n测试不同词库规模（{len(chinese_files)}个文件）...")
        for audio_file in chinese_files:
            for word_set_name, words in word_sets.items():
                for method in self.filter_methods:
                    result = self.test_single_audio(
                        audio_file,
                        words,
                        method,
                        "zh"
                    )
                    result['test_case'] = 'word_set_size'
                    result['word_set'] = word_set_name
                    self.results.append(result)

    def test_case_3_audio_length(self):
        """测试用例3：音频长度影响"""
        print("\n测试用例3：音频长度影响")
        print("="*60)

        # 获取测试文件并按长度分类（9个文件，每类3个）
        chinese_files = self.get_audio_files("中文数据", 9)

        if not chinese_files:
            print("无法获取中文测试文件")
            return

        # 简单按文件大小分类（作为长度的代理）
        file_sizes = [(f, os.path.getsize(f)) for f in chinese_files]
        file_sizes.sort(key=lambda x: x[1])

        short_files = [f[0] for f in file_sizes[:3]]    # 最小的3个
        medium_files = [f[0] for f in file_sizes[3:6]]  # 中间的3个
        long_files = [f[0] for f in file_sizes[6:9]]    # 最大的3个

        length_categories = {
            'short': short_files,
            'medium': medium_files,
            'long': long_files
        }

        print(f"\n测试不同音频长度（每类3个文件）...")
        for length_cat, files in length_categories.items():
            print(f"  测试 {length_cat} 类别...")
            for audio_file in files:
                for method in self.filter_methods:
                    result = self.test_single_audio(
                        audio_file,
                        self.chinese_words_medium,
                        method,
                        "zh"
                    )
                    result['test_case'] = 'audio_length'
                    result['word_set'] = 'medium'
                    result['length_category'] = length_cat
                    self.results.append(result)

    def test_case_4_language_comparison(self):
        """测试用例4：语言差异对比"""
        print("\n测试用例4：语言差异对比")
        print("="*60)

        # 获取测试文件（每种语言3个文件）
        chinese_files = self.get_audio_files("中文数据", 3)
        english_files = self.get_audio_files("英语数据", 3)

        if not chinese_files or not english_files:
            print("无法获取足够的测试文件")
            return

        print(f"\n测试中文音频（{len(chinese_files)}个文件）...")
        for audio_file in chinese_files:
            for method in self.filter_methods:
                result = self.test_single_audio(
                    audio_file,
                    self.chinese_words_medium,
                    method,
                    "zh"
                )
                result['test_case'] = 'language_comparison'
                result['word_set'] = 'medium'
                self.results.append(result)

        print(f"\n测试英文音频（{len(english_files)}个文件）...")
        for audio_file in english_files:
            for method in self.filter_methods:
                result = self.test_single_audio(
                    audio_file,
                    self.english_words_medium,
                    method,
                    "en"
                )
                result['test_case'] = 'language_comparison'
                result['word_set'] = 'medium'
                self.results.append(result)

    def save_results(self):
        """保存测试结果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 保存为JSON
        json_file = f"performance_results_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)

        # 保存为CSV
        csv_file = f"performance_results_{timestamp}.csv"
        df = pd.DataFrame(self.results)
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')

        print(f"\n结果已保存:")
        print(f"   JSON: {json_file}")
        print(f"   CSV: {csv_file}")

        return df, timestamp

    def run_all_tests(self):
        """运行所有测试用例"""
        print("开始五种过滤算法性能测试")
        print("="*80)

        # 加载模型
        if not self.load_model():
            return

        start_time = time.time()

        try:
            # 运行测试用例
            self.test_case_1_basic_performance()
            self.test_case_2_word_set_size()
            self.test_case_3_audio_length()
            self.test_case_4_language_comparison()

            total_time = time.time() - start_time

            print(f"\n所有测试完成！总耗时: {total_time:.1f} 秒")
            print(f"共完成 {len(self.results)} 个测试")

            # 保存结果和生成可视化
            df, timestamp = self.save_results()
            #elf.create_visualizations(df, timestamp)

            # 显示测试统计
            success_count = sum(1 for r in self.results if r['success'])
            failure_count = len(self.results) - success_count

            print(f"\n测试统计:")
            print(f"   成功: {success_count}")
            print(f"   失败: {failure_count}")
            print(f"   成功率: {success_count/len(self.results)*100:.1f}%")

        except KeyboardInterrupt:
            print("\n测试被用户中断")
        except Exception as e:
            print(f"\n测试过程中出现错误: {e}")
            import traceback
            traceback.print_exc()


def main():
    """主函数"""
    print("五种过滤算法性能测试系统")
    print("="*80)
    print("测试用例:")
    print("  1. 基础性能对比 - 五种算法在小词库下的表现")
    print("  2. 词库规模影响 - 不同词库大小对性能的影响")
    print("  3. 音频长度影响 - 不同音频长度对处理效率的影响")
    print("  4. 语言差异对比 - 中英文识别和过滤效果对比")
    print()
    print("性能指标:")
    print("  • 总处理时间 - 端到端处理时间")
    print("  • 实时倍数 - 处理时间/音频时长")
    print("  • 内存使用 - 处理过程中的内存消耗")
    print("  • 过滤效果 - 敏感词检测和替换数量")
    print()

    # 检查数据目录
    if not os.path.exists("中文数据"):
        print("中文数据目录不存在")
        return

    if not os.path.exists("英语数据"):
        print("英语数据目录不存在")
        return

    # 确认开始测试
    response = input("是否开始测试？(y/n): ").strip().lower()
    if response != 'y':
        print("测试已取消")
        return

    # 创建测试器并运行
    tester = PerformanceTester()
    tester.run_all_tests()

    print("\n 性能测试完成！")
    print("查看生成的图表和数据文件了解详细结果")


if __name__ == "__main__":
    main()
