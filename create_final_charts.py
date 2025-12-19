#!/usr/bin/env python3
"""
创建最终版本的测试用例双图表
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import warnings

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 禁用字体警告
warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib')

def load_data():
    """加载测试数据"""
    try:
        df = pd.read_csv('performance_results_20250821_034937.csv', encoding='utf-8-sig')
        print(f"成功加载 {len(df)} 条测试记录")
        return df
    except Exception as e:
        print(f"数据加载失败: {e}")
        return None

def get_chart_config():
    """获取图表配置"""
    colors = {
        'DFA': '#FF6B6B',           # 红色
        'aho_corasick': '#4ECDC4',  # 青色
        'trie_tree': '#45B7D1',     # 蓝色
        'replace': '#96CEB4',       # 绿色
        'regular_expression': '#FECA57'  # 黄色
    }
    
    method_mapping = {
        'DFA': 'DFA',
        'aho_corasick': 'Aho-Corasick',
        'trie_tree': 'Trie Tree',
        'replace': 'Replace',
        'regular_expression': 'Regular Expression'
    }
    
    return colors, method_mapping

def optimize_y_axis(values, margin_ratio=0.1):
    """优化Y轴范围，突出差异"""
    min_val = min(values)
    max_val = max(values)
    range_val = max_val - min_val
    
    # 如果差异很小，从最小值的80%开始显示
    if range_val / max_val < 0.2:  # 差异小于20%
        y_min = min_val * 0.8
    else:
        y_min = max(0, min_val - range_val * margin_ratio)
    
    y_max = max_val + range_val * margin_ratio
    return y_min, y_max

def add_value_labels(ax, bars, y_min, y_max, precision=2, fontsize=7):
    """添加数值标签，避免重叠"""
    for bar in bars:
        height = bar.get_height()
        if height > 0:
            # 计算标签位置，避免重叠
            label_y = height + (y_max - y_min) * 0.02
            if precision == 2:
                label_text = f'{height:.2f}'
            elif precision == 3:
                label_text = f'{height:.3f}'
            else:
                label_text = f'{height:.1f}'
            
            ax.text(bar.get_x() + bar.get_width()/2., label_y,
                   label_text, ha='center', va='bottom', 
                   fontsize=fontsize, fontweight='bold')

def create_basic_performance_chart(df):
    """创建基础性能对比图表"""
    print("生成基础性能对比图表...")
    
    # 过滤基础性能测试数据
    basic_data = df[df['test_case'] == 'basic_performance'].copy()
    
    if basic_data.empty:
        print("没有基础性能测试数据")
        return
    
    # 计算平均值
    avg_data = basic_data.groupby('filter_method').agg({
        'total_time': 'mean',
        'real_time_factor': 'mean'
    }).reset_index()
    
    colors, method_mapping = get_chart_config()
    
    # 创建子图
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    methods = ['DFA', 'aho_corasick', 'trie_tree', 'replace', 'regular_expression']
    
    # 左图：平均处理时间
    time_values = []
    for method in methods:
        method_data = avg_data[avg_data['filter_method'] == method]
        if not method_data.empty:
            time_values.append(method_data['total_time'].iloc[0])
        else:
            time_values.append(0)
    
    # 设置固定Y轴范围
    y_min1, y_max1 = 42, 53

    bars1 = ax1.bar(range(len(methods)), time_values,
                   color=[colors[m] for m in methods], alpha=0.8)

    ax1.set_ylim(y_min1, y_max1)
    add_value_labels(ax1, bars1, y_min1, y_max1, precision=2, fontsize=8)
    
    ax1.set_title('平均处理时间对比', fontsize=14, fontweight='bold')
    ax1.set_xlabel('算法', fontsize=12)
    ax1.set_ylabel('平均处理时间(秒)', fontsize=12)
    ax1.set_xticks(range(len(methods)))
    ax1.set_xticklabels([method_mapping[m] for m in methods], rotation=45)
    ax1.grid(True, alpha=0.3)
    
    # 右图：实时倍数
    rtf_values = []
    for method in methods:
        method_data = avg_data[avg_data['filter_method'] == method]
        if not method_data.empty:
            rtf_values.append(method_data['real_time_factor'].iloc[0])
        else:
            rtf_values.append(0)
    
    # 设置固定Y轴范围
    y_min2, y_max2 = 0.095, 0.120

    bars2 = ax2.bar(range(len(methods)), rtf_values,
                   color=[colors[m] for m in methods], alpha=0.8)

    ax2.set_ylim(y_min2, y_max2)
    add_value_labels(ax2, bars2, y_min2, y_max2, precision=3, fontsize=8)
    
    ax2.set_title('实时倍数对比', fontsize=14, fontweight='bold')
    ax2.set_xlabel('算法', fontsize=12)
    ax2.set_ylabel('实时倍数', fontsize=12)
    ax2.set_xticks(range(len(methods)))
    ax2.set_xticklabels([method_mapping[m] for m in methods], rotation=45)
    ax2.grid(True, alpha=0.3)
    
    plt.suptitle('基础性能对比分析', fontsize=16, fontweight='bold')
    plt.tight_layout()
    
    # 保存图表
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"basic_performance_final_{timestamp}.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"基础性能对比图表已保存: {filename}")
    plt.show()

def create_word_set_impact_chart(df):
    """创建词库规模影响图表"""
    print("生成词库规模影响图表...")
    
    # 过滤词库规模测试数据
    word_set_data = df[df['test_case'] == 'word_set_size'].copy()
    
    if word_set_data.empty:
        print("没有词库规模测试数据")
        return
    
    # 计算平均值
    avg_data = word_set_data.groupby(['word_set', 'filter_method']).agg({
        'total_time': 'mean',
        'real_time_factor': 'mean'
    }).reset_index()
    
    colors, method_mapping = get_chart_config()
    
    # 创建子图
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # 词库规模映射
    word_set_mapping = {
        'small': '小(3词)',
        'medium': '中(10词)',
        'large': '大(50词)'
    }
    
    word_sets = ['small', 'medium', 'large']
    x_pos = np.arange(len(word_sets))
    width = 0.15
    
    methods = ['DFA', 'aho_corasick', 'trie_tree', 'replace', 'regular_expression']
    
    # 收集所有数值用于优化Y轴
    all_time_values = []
    all_rtf_values = []
    
    for method in methods:
        for ws in word_sets:
            method_data = avg_data[(avg_data['word_set'] == ws) & (avg_data['filter_method'] == method)]
            if not method_data.empty:
                all_time_values.append(method_data['total_time'].iloc[0])
                all_rtf_values.append(method_data['real_time_factor'].iloc[0])
    
    # 设置固定Y轴范围
    y_min1, y_max1 = 36, 45
    y_min2, y_max2 = 0.110, 0.140
    
    # 左图：平均处理时间
    all_bars1 = []
    for i, method in enumerate(methods):
        time_values = []
        for ws in word_sets:
            method_data = avg_data[(avg_data['word_set'] == ws) & (avg_data['filter_method'] == method)]
            if not method_data.empty:
                time_values.append(method_data['total_time'].iloc[0])
            else:
                time_values.append(0)
        
        bars = ax1.bar(x_pos + i * width, time_values, width, 
                      label=method_mapping[method], color=colors[method], alpha=0.8)
        all_bars1.extend(bars)
    
    ax1.set_ylim(y_min1, y_max1)
    add_value_labels(ax1, all_bars1, y_min1, y_max1, precision=1, fontsize=6)
    
    ax1.set_title('词库规模对处理时间的影响', fontsize=14, fontweight='bold')
    ax1.set_xlabel('词库规模', fontsize=12)
    ax1.set_ylabel('平均处理时间(秒)', fontsize=12)
    ax1.set_xticks(x_pos + width * 2)
    ax1.set_xticklabels([word_set_mapping[ws] for ws in word_sets])
    ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)
    ax1.grid(True, alpha=0.3)
    
    # 右图：实时倍数
    all_bars2 = []
    for i, method in enumerate(methods):
        rtf_values = []
        for ws in word_sets:
            method_data = avg_data[(avg_data['word_set'] == ws) & (avg_data['filter_method'] == method)]
            if not method_data.empty:
                rtf_values.append(method_data['real_time_factor'].iloc[0])
            else:
                rtf_values.append(0)
        
        bars = ax2.bar(x_pos + i * width, rtf_values, width, 
                      label=method_mapping[method], color=colors[method], alpha=0.8)
        all_bars2.extend(bars)
    
    ax2.set_ylim(y_min2, y_max2)
    add_value_labels(ax2, all_bars2, y_min2, y_max2, precision=3, fontsize=6)
    
    ax2.set_title('词库规模对实时倍数的影响', fontsize=14, fontweight='bold')
    ax2.set_xlabel('词库规模', fontsize=12)
    ax2.set_ylabel('实时倍数', fontsize=12)
    ax2.set_xticks(x_pos + width * 2)
    ax2.set_xticklabels([word_set_mapping[ws] for ws in word_sets])
    ax2.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)
    ax2.grid(True, alpha=0.3)
    
    plt.suptitle('词库规模影响分析', fontsize=16, fontweight='bold')
    plt.tight_layout()
    
    # 保存图表
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"word_set_impact_final_{timestamp}.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"词库规模影响图表已保存: {filename}")
    plt.show()

def create_audio_length_impact_chart(df):
    """创建音频长度影响图表"""
    print("生成音频长度影响图表...")

    # 过滤音频长度测试数据
    length_data = df[df['test_case'] == 'audio_length'].copy()

    if length_data.empty:
        print("没有音频长度测试数据")
        return

    # 计算平均值
    avg_data = length_data.groupby(['length_category', 'filter_method']).agg({
        'total_time': 'mean',
        'real_time_factor': 'mean'
    }).reset_index()

    colors, method_mapping = get_chart_config()

    # 创建子图
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

    # 长度类别映射
    length_mapping = {
        'short': '短(21字)',
        'medium': '中(68字)',
        'long': '长(680字)'
    }

    length_cats = ['short', 'medium', 'long']
    x_pos = np.arange(len(length_cats))
    width = 0.15

    methods = ['DFA', 'aho_corasick', 'trie_tree', 'replace', 'regular_expression']

    # 收集所有数值用于优化Y轴
    all_time_values = []
    all_rtf_values = []

    for method in methods:
        for lc in length_cats:
            method_data = avg_data[(avg_data['length_category'] == lc) & (avg_data['filter_method'] == method)]
            if not method_data.empty:
                all_time_values.append(method_data['total_time'].iloc[0])
                all_rtf_values.append(method_data['real_time_factor'].iloc[0])

    # 优化Y轴范围
    y_min1, y_max1 = optimize_y_axis(all_time_values)
    y_min2, y_max2 = optimize_y_axis(all_rtf_values)

    # 左图：平均处理时间
    all_bars1 = []
    for i, method in enumerate(methods):
        time_values = []
        for lc in length_cats:
            method_data = avg_data[(avg_data['length_category'] == lc) & (avg_data['filter_method'] == method)]
            if not method_data.empty:
                time_values.append(method_data['total_time'].iloc[0])
            else:
                time_values.append(0)

        bars = ax1.bar(x_pos + i * width, time_values, width,
                      label=method_mapping[method], color=colors[method], alpha=0.8)
        all_bars1.extend(bars)

    ax1.set_ylim(y_min1, y_max1)
    add_value_labels(ax1, all_bars1, y_min1, y_max1, precision=1, fontsize=6)

    ax1.set_title('音频长度对处理时间的影响', fontsize=14, fontweight='bold')
    ax1.set_xlabel('音频长度', fontsize=12)
    ax1.set_ylabel('平均处理时间(秒)', fontsize=12)
    ax1.set_xticks(x_pos + width * 2)
    ax1.set_xticklabels([length_mapping[lc] for lc in length_cats])
    ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)
    ax1.grid(True, alpha=0.3)

    # 右图：实时倍数
    all_bars2 = []
    for i, method in enumerate(methods):
        rtf_values = []
        for lc in length_cats:
            method_data = avg_data[(avg_data['length_category'] == lc) & (avg_data['filter_method'] == method)]
            if not method_data.empty:
                rtf_values.append(method_data['real_time_factor'].iloc[0])
            else:
                rtf_values.append(0)

        bars = ax2.bar(x_pos + i * width, rtf_values, width,
                      label=method_mapping[method], color=colors[method], alpha=0.8)
        all_bars2.extend(bars)

    ax2.set_ylim(y_min2, y_max2)
    add_value_labels(ax2, all_bars2, y_min2, y_max2, precision=3, fontsize=6)

    ax2.set_title('音频长度对实时倍数的影响', fontsize=14, fontweight='bold')
    ax2.set_xlabel('音频长度', fontsize=12)
    ax2.set_ylabel('实时倍数', fontsize=12)
    ax2.set_xticks(x_pos + width * 2)
    ax2.set_xticklabels([length_mapping[lc] for lc in length_cats])
    ax2.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)
    ax2.grid(True, alpha=0.3)

    plt.suptitle('音频长度影响分析', fontsize=16, fontweight='bold')
    plt.tight_layout()

    # 保存图表
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"audio_length_impact_final_{timestamp}.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"音频长度影响图表已保存: {filename}")
    plt.show()

def create_language_comparison_chart(df):
    """创建语言对比图表"""
    print("生成语言对比图表...")

    # 过滤语言对比测试数据
    lang_data = df[df['test_case'] == 'language_comparison'].copy()

    if lang_data.empty:
        print("没有语言对比测试数据")
        return

    # 计算平均值
    avg_data = lang_data.groupby(['language', 'filter_method']).agg({
        'total_time': 'mean',
        'real_time_factor': 'mean'
    }).reset_index()

    colors, method_mapping = get_chart_config()

    # 创建子图
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

    # 语言映射
    lang_mapping = {'zh': '中文', 'en': '英文'}

    languages = ['zh', 'en']
    x_pos = np.arange(len(languages))
    width = 0.15

    methods = ['DFA', 'aho_corasick', 'trie_tree', 'replace', 'regular_expression']

    # 收集所有数值用于优化Y轴
    all_time_values = []
    all_rtf_values = []

    for method in methods:
        for lang in languages:
            method_data = avg_data[(avg_data['language'] == lang) & (avg_data['filter_method'] == method)]
            if not method_data.empty:
                all_time_values.append(method_data['total_time'].iloc[0])
                all_rtf_values.append(method_data['real_time_factor'].iloc[0])

    # 优化Y轴范围
    y_min1, y_max1 = optimize_y_axis(all_time_values)
    y_min2, y_max2 = optimize_y_axis(all_rtf_values)

    # 左图：平均处理时间
    all_bars1 = []
    for i, method in enumerate(methods):
        time_values = []
        for lang in languages:
            method_data = avg_data[(avg_data['language'] == lang) & (avg_data['filter_method'] == method)]
            if not method_data.empty:
                time_values.append(method_data['total_time'].iloc[0])
            else:
                time_values.append(0)

        bars = ax1.bar(x_pos + i * width, time_values, width,
                      label=method_mapping[method], color=colors[method], alpha=0.8)
        all_bars1.extend(bars)

    ax1.set_ylim(y_min1, y_max1)
    add_value_labels(ax1, all_bars1, y_min1, y_max1, precision=2, fontsize=7)

    ax1.set_title('不同语言的平均处理时间', fontsize=14, fontweight='bold')
    ax1.set_xlabel('语言', fontsize=12)
    ax1.set_ylabel('平均处理时间(秒)', fontsize=12)
    ax1.set_xticks(x_pos + width * 2)
    ax1.set_xticklabels([lang_mapping[lang] for lang in languages])
    ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=10)
    ax1.grid(True, alpha=0.3)

    # 右图：实时倍数
    all_bars2 = []
    for i, method in enumerate(methods):
        rtf_values = []
        for lang in languages:
            method_data = avg_data[(avg_data['language'] == lang) & (avg_data['filter_method'] == method)]
            if not method_data.empty:
                rtf_values.append(method_data['real_time_factor'].iloc[0])
            else:
                rtf_values.append(0)

        bars = ax2.bar(x_pos + i * width, rtf_values, width,
                      label=method_mapping[method], color=colors[method], alpha=0.8)
        all_bars2.extend(bars)

    ax2.set_ylim(y_min2, y_max2)
    add_value_labels(ax2, all_bars2, y_min2, y_max2, precision=3, fontsize=7)

    ax2.set_title('不同语言的实时倍数', fontsize=14, fontweight='bold')
    ax2.set_xlabel('语言', fontsize=12)
    ax2.set_ylabel('实时倍数', fontsize=12)
    ax2.set_xticks(x_pos + width * 2)
    ax2.set_xticklabels([lang_mapping[lang] for lang in languages])
    ax2.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=10)
    ax2.grid(True, alpha=0.3)

    plt.suptitle('中英文语言对比', fontsize=16, fontweight='bold')
    plt.tight_layout()

    # 保存图表
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"language_comparison_final_{timestamp}.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"语言对比图表已保存: {filename}")
    plt.show()

def main():
    """主函数"""
    print("创建最终版测试用例双图表")
    print("="*50)
    
    # 加载数据
    df = load_data()
    if df is None:
        return
    
    print(f"\n数据概览:")
    print(f"   总记录数: {len(df)}")
    print(f"   成功记录: {len(df[df['success'] == True])}")
    print(f"   测试方法: {df['filter_method'].unique()}")
    print(f"   测试用例: {df['test_case'].unique()}")
    
    # 生成图表
    create_basic_performance_chart(df)
    create_word_set_impact_chart(df)
    create_audio_length_impact_chart(df)
    create_language_comparison_chart(df)

    print(f"\n最终版图表生成完成！")

if __name__ == "__main__":
    main()
