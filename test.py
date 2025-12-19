#!/usr/bin/env python3
"""
测试 Whisper 集成敏感词过滤功能
音频文件: storym.mp3
敏感词: 小狼, 开心, 快乐
"""

import os
import sys
import time
import wave
import pyaudio
from datetime import datetime

# 设置 FFmpeg 路径
ffmpeg_path = r"C:\Users\30687\.conda\envs\MachineLearningHomework\Library\bin"
current_path = os.environ.get('PATH', '')
if ffmpeg_path not in current_path:
    os.environ['PATH'] = ffmpeg_path + os.pathsep + current_path

# 添加本地 whisper 目录到 Python 路径，确保使用本地代码
whisper_path = os.path.join(os.path.dirname(__file__), 'whisper')
if whisper_path not in sys.path:
    sys.path.insert(0, whisper_path)
    print(f"已添加本地 Whisper 路径: {whisper_path}")

# 导入本地的 whisper
import whisper
print(f"使用 Whisper 路径: {whisper.__file__}")


def record_audio(record_time):
    """录音程序"""
    # 定义录音参数
    CHUNK = 1024  # 音频帧率
    FORMAT = pyaudio.paInt16  # 采样格式
    CHANNELS = 1  # 单声道
    RATE = 16000  # 采样率
    RECORD_SECONDS = record_time  # 录音时间
    # 使用时间戳命名录音文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    WAVE_OUTPUT_FILENAME = f"./recording_{timestamp}.wav"  # 保存音频路径

    try:
        p = pyaudio.PyAudio()  # 创建PyAudio对象

        # 检查是否有可用的音频输入设备
        input_device_count = 0
        for i in range(p.get_device_count()):
            device_info = p.get_device_info_by_index(i)
            if device_info['maxInputChannels'] > 0:
                input_device_count += 1

        if input_device_count == 0:
            print("未检测到音频输入设备")
            p.terminate()
            return None

        stream = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK)

        print(f"开始录音 {record_time} 秒...")
        print("请开始说话...")

        frames = []
        for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
            data = stream.read(CHUNK)
            frames.append(data)

            # 显示录音进度
            progress = (i + 1) / int(RATE / CHUNK * RECORD_SECONDS)
            if int(progress * 10) != int((progress - 1/int(RATE / CHUNK * RECORD_SECONDS)) * 10):
                print(f"录音进度: {progress*100:.0f}%")

        print("录音完成")

        stream.stop_stream()
        stream.close()
        p.terminate()

        # 保存录音文件
        wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()

        print(f"录音已保存到: {WAVE_OUTPUT_FILENAME}")
        return WAVE_OUTPUT_FILENAME

    except Exception as e:
        print(f"录音失败: {e}")
        return None


def get_audio_file():
    """交互式选择音频文件"""
    print("\n音频文件选择")
    print("-" * 50)
    print("请选择音频输入方式:")
    print("1. 使用默认音频文件 (storym.mp3)")
    print("2. 指定其他音频文件")
    print("3. 现场录音")

    while True:
        choice = input("\n请输入选择 (1/2/3): ").strip()

        if choice == "1":
            default_file = "storym.mp3"
            if os.path.exists(default_file):
                print(f"使用默认音频文件: {default_file}")
                return default_file
            else:
                print(f"默认音频文件不存在: {default_file}")
                print("请选择其他选项")
                continue

        elif choice == "2":
            print("\n请输入音频文件路径:")
            file_path = input("文件路径: ").strip().strip('"').strip("'")

            if not file_path:
                print("未输入文件路径")
                continue

            if os.path.exists(file_path):
                print(f"使用指定音频文件: {file_path}")
                return file_path
            else:
                print(f"文件不存在: {file_path}")
                continue

        elif choice == "3":
            print("\n现场录音模式")
            print("请选择录音时长:")
            print("1. 5秒")
            print("2. 10秒")
            print("3. 15秒")
            print("4. 自定义时长")

            while True:
                time_choice = input("\n请选择录音时长 (1/2/3/4): ").strip()

                if time_choice == "1":
                    record_time = 5
                    break
                elif time_choice == "2":
                    record_time = 10
                    break
                elif time_choice == "3":
                    record_time = 15
                    break
                elif time_choice == "4":
                    try:
                        record_time = int(input("请输入录音时长（秒）: ").strip())
                        if record_time <= 0:
                            print("录音时长必须大于0")
                            continue
                        if record_time > 60:
                            print("录音时长较长，建议不超过60秒")
                            confirm = input("是否继续？(y/n): ").strip().lower()
                            if confirm != 'y':
                                continue
                        break
                    except ValueError:
                        print("请输入有效的数字")
                        continue
                else:
                    print("无效选择，请输入 1、2、3 或 4")
                    continue

            print(f"\n准备录音 {record_time} 秒")
            input("按回车键开始录音...")

            audio_file = record_audio(record_time)
            if audio_file:
                return audio_file
            else:
                print("录音失败，请选择其他选项")
                continue

        else:
            print("无效选择，请输入 1、2 或 3")

def get_sensitive_words():
    """交互式获取敏感词列表"""
    print("\n敏感词配置")
    print("-" * 50)
    print("请选择敏感词输入方式:")
    print("1. 交互式输入敏感词")
    print("2. 使用默认敏感词 ['小狼', '开心', '快乐']")
    print("3. 不进行敏感词过滤")

    while True:
        choice = input("\n请输入选择 (1/2/3): ").strip()

        if choice == "1":
            print("\n请输入敏感词 (多个词用空格或逗号分隔，回车结束):")
            user_input = input("敏感词: ").strip()

            if not user_input:
                print("未输入任何敏感词，将不进行过滤")
                return None

            # 支持空格或逗号分隔
            if ',' in user_input:
                words = [word.strip() for word in user_input.split(',') if word.strip()]
            else:
                words = [word.strip() for word in user_input.split() if word.strip()]

            if words:
                print(f"已设置敏感词: {words}")
                return words
            else:
                print("未识别到有效敏感词，将不进行过滤")
                return None

        elif choice == "2":
            default_words = ["小狼", "开心", "快乐"]
            print(f"使用默认敏感词: {default_words}")
            return default_words

        elif choice == "3":
            print("不进行敏感词过滤")
            return None

        else:
            print("无效选择，请输入 1、2 或 3")

def get_filter_method():
    """交互式选择过滤方法"""
    print("\n过滤方法选择")
    print("-" * 50)
    print("请选择敏感词过滤方法:")
    print("1. DFA (确定有限自动机) - 推荐，高效且稳定")
    print("2. Aho-Corasick (AC自动机) - 适合大量敏感词")
    print("3. Trie Tree (字典树) - 结构清晰，易于理解")
    print("4. Replace (字符串替换) - 简单直观")
    print("5. Regular Expression (正则表达式) - 灵活强大")

    method_map = {
        "1": "DFA",
        "2": "aho_corasick",
        "3": "trie_tree",
        "4": "replace",
        "5": "regular_expression"
    }

    while True:
        choice = input("\n请输入选择 (1/2/3/4/5): ").strip()

        if choice in method_map:
            method = method_map[choice]
            method_names = {
                "DFA": "DFA (确定有限自动机)",
                "aho_corasick": "Aho-Corasick (AC自动机)",
                "trie_tree": "Trie Tree (字典树)",
                "replace": "Replace (字符串替换)",
                "regular_expression": "Regular Expression (正则表达式)"
            }
            print(f"已选择过滤方法: {method_names[method]}")
            return method
        else:
            print("无效选择，请输入 1、2、3、4 或 5")

def main():
    """主函数 - 测试集成的敏感词过滤功能"""
    print("Whisper 敏感词过滤功能测试")
    print("="*80)

    # 基本配置
    model_name = "base"

    # 交互式选择音频文件
    audio_file = get_audio_file()
    if not audio_file:
        print("未选择有效的音频文件，程序退出")
        return

    # 交互式获取敏感词
    sensitive_words = get_sensitive_words()

    # 交互式选择过滤方法
    filter_method = None
    if sensitive_words:  # 只有在有敏感词时才选择过滤方法
        filter_method = get_filter_method()

    print(f"\n配置信息:")
    print(f"音频文件: {audio_file}")
    print(f"敏感词: {sensitive_words if sensitive_words else '无（不进行过滤）'}")
    print(f"过滤方法: {filter_method if filter_method else '无（不进行过滤）'}")
    print(f"模型: {model_name}")
    print(f"简体字转换: 启用")
    print(f"过滤模块: 使用外部过滤方法")

    # 检查文件
    if not os.path.exists(audio_file):
        print(f"\n文件不存在: {audio_file}")
        print("\n当前目录音频文件:")
        for file in os.listdir('.'):
            if file.endswith(('.mp3', '.wav', '.flac', '.m4a')):
                print(f"   - {file}")
        return

    file_size = os.path.getsize(audio_file) / (1024 * 1024)
    print(f"文件大小: {file_size:.2f} MB")

    # 加载模型
    print(f"\n加载 Whisper {model_name} 模型...")
    try:
        model = whisper.load_model(model_name)
        print("模型加载完成")
    except Exception as e:
        print(f"模型加载失败: {e}")
        return

    # 转录音频（现在会自动进行敏感词过滤）
    print(f"\n开始转录音频（集成敏感词过滤）...")
    start_time = time.time()

    try:
        # 传入敏感词和过滤方法进行转录和过滤
        transcribe_params = {
            "language": "zh",
            "verbose": True,
            "word_timestamps": True,
            "sensitive_words": sensitive_words
        }

        # 只有在有敏感词时才传入过滤方法参数
        if sensitive_words and filter_method:
            transcribe_params["filter_method"] = filter_method

        result = model.transcribe(audio_file, **transcribe_params)

        transcribe_time = time.time() - start_time
        print(f"\n转录完成，耗时: {transcribe_time:.2f} 秒")
        print(f"识别语言: {result['language']}")

    except Exception as e:
        print(f"转录失败: {e}")
        import traceback
        traceback.print_exc()
        return

    # 显示最终结果
    print("\n" + "="*80)
    print("转录结果汇总")
    print("="*80)

    # 显示简体字转换结果
    print(f"\n简体字转换结果:")
    print("-" * 50)
    print(result.get('simplified_text', '未获取到简体字文本'))

    # 显示敏感词过滤结果
    print(f"\n敏感词过滤结果:")
    print("-" * 50)
    print(result['text'])

    # 显示分段详情
    print(f"\n分段详情对比:")
    print("-" * 50)
    for i, segment in enumerate(result['segments'], 1):
        print(f"分段 {i}: [{segment['start']:.2f}s - {segment['end']:.2f}s]")

        # 显示原始文本（如果有）
        if 'original_text' in segment:
            print(f"  原始文本: {segment['original_text']}")

        # 显示简体字文本（如果有）
        if 'simplified_text' in segment:
            print(f"  简体转换: {segment['simplified_text']}")

        # 显示过滤后文本
        print(f"  过滤结果: {segment['text']}")
        print()

    # 统计信息
    audio_duration = result['segments'][-1]['end'] if result['segments'] else 0
    real_time_factor = transcribe_time / audio_duration if audio_duration > 0 else 0

    print(f"处理统计:")
    print(f"   音频时长: {audio_duration:.2f} 秒")
    print(f"   处理时间: {transcribe_time:.2f} 秒")
    print(f"   实时倍数: {real_time_factor:.2f}x")
    print(f"   分段数量: {len(result['segments'])}")
    if filter_method:
        # 显示过滤方法的友好名称
        method_names = {
            "DFA": "DFA (确定有限自动机)",
            "aho_corasick": "Aho-Corasick (AC自动机)",
            "trie_tree": "Trie Tree (字典树)",
            "replace": "Replace (字符串替换)",
            "regular_expression": "Regular Expression (正则表达式)"
        }
        method_display = method_names.get(filter_method, filter_method)
        print(f"   过滤方法: {method_display}")
    else:
        print(f"   过滤方法: 无（未进行过滤）")

    # 保存结果（使用时间戳命名避免覆盖）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"test_result_{timestamp}.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("Whisper 集成敏感词过滤测试结果\n")
        f.write("="*50 + "\n\n")
        f.write(f"处理时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"音频文件: {audio_file}\n")
        f.write(f"敏感词: {sensitive_words if sensitive_words else '无'}\n")
        f.write(f"识别语言: {result['language']}\n")
        f.write(f"简体字转换: 启用\n")

        # 添加过滤方法信息
        if filter_method:
            method_names = {
                "DFA": "DFA (确定有限自动机)",
                "aho_corasick": "Aho-Corasick (AC自动机)",
                "trie_tree": "Trie Tree (字典树)",
                "replace": "Replace (字符串替换)",
                "regular_expression": "Regular Expression (正则表达式)"
            }
            method_display = method_names.get(filter_method, filter_method)
            f.write(f"过滤方法: {method_display}\n")
        else:
            f.write(f"过滤方法: 无（未进行过滤）\n")

        f.write("\n")

        f.write("简体字转换结果:\n")
        f.write("-" * 30 + "\n")
        f.write(result.get('simplified_text', '未获取到简体字文本') + "\n\n")

        f.write("敏感词过滤结果:\n")
        f.write("-" * 30 + "\n")
        f.write(result['text'] + "\n\n")

        f.write("分段详情对比:\n")
        f.write("-" * 30 + "\n")
        for i, segment in enumerate(result['segments'], 1):
            f.write(f"分段 {i}: [{segment['start']:.2f}s - {segment['end']:.2f}s]\n")

            if 'original_text' in segment:
                f.write(f"  原始文本: {segment['original_text']}\n")

            if 'simplified_text' in segment:
                f.write(f"  简体转换: {segment['simplified_text']}\n")

            f.write(f"  过滤结果: {segment['text']}\n\n")

        f.write("统计信息:\n")
        f.write("-" * 30 + "\n")
        f.write(f"音频时长: {audio_duration:.2f} 秒\n")
        f.write(f"处理时间: {transcribe_time:.2f} 秒\n")
        f.write(f"实时倍数: {real_time_factor:.2f}x\n")
        f.write(f"分段数量: {len(result['segments'])}\n")

        # 添加过滤方法信息到统计
        if filter_method:
            method_names = {
                "DFA": "DFA (确定有限自动机)",
                "aho_corasick": "Aho-Corasick (AC自动机)",
                "trie_tree": "Trie Tree (字典树)",
                "replace": "Replace (字符串替换)",
                "regular_expression": "Regular Expression (正则表达式)"
            }
            method_display = method_names.get(filter_method, filter_method)
            f.write(f"过滤方法: {method_display}\n")
        else:
            f.write(f"过滤方法: 无（未进行过滤）\n")

    print(f"\n结果已保存到: {output_file}")

    print(f"\n测试完成！")
    print(f"\n功能验证:")
    print(f"   Whisper 转录正常")
    print(f"   敏感词过滤已集成到 transcribe 函数")
    print(f"   简体字转换已启用")
    print(f"   实时分段过滤工作正常")

if __name__ == "__main__":
    main()