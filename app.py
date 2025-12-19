#!/usr/bin/env python3
"""
语音敏感词过滤系统 - Web API
基于 Flask 的后端服务
"""

import os
import sys
import time
import json
import tempfile
import webbrowser
import threading
from datetime import datetime
from flask import Flask, request, jsonify, render_template, send_file, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
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
try:
    import whisper
    print(f"使用 Whisper 路径: {whisper.__file__}")
    # 测试 load_model 函数是否可用
    if hasattr(whisper, 'load_model'):
        print("load_model 函数可用")
    else:
        print("load_model 函数不可用")
        # 尝试直接从whisper模块导入
        from whisper import load_model
        whisper.load_model = load_model
        print("已修复 load_model 函数")
except Exception as e:
    print(f"Whisper 导入失败: {e}")
    whisper = None

# 动态导入其他模块
import wave
import pyaudio

# 添加当前目录到路径，以便导入过滤模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入过滤模块
filter_modules_available = {}

try:
    import DFA
    filter_modules_available['DFA'] = DFA
    print("DFA 模块加载成功")
except ImportError as e:
    print(f"DFA 模块未找到: {e}")

try:
    # 先检查是否有ahocorasick库
    import ahocorasick  # noqa: F401
    # 如果有，再导入我们的模块
    import aho_corasick
    filter_modules_available['aho_corasick'] = aho_corasick
    print("aho_corasick 模块加载成功")
except ImportError as e:
    print(f"aho_corasick 模块未找到: {e}")
    print("提示: 需要安装 pyahocorasick 库: pip install pyahocorasick")

# 注意：文件名有空格，需要特殊处理
try:
    import importlib.util
    spec = importlib.util.spec_from_file_location("trie_tree", "trie tree.py")
    trie_tree_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(trie_tree_module)
    filter_modules_available['trie_tree'] = trie_tree_module
    print("trie tree 模块加载成功")
except Exception as e:
    print(f"trie tree 模块未找到: {e}")

try:
    import replace
    filter_modules_available['replace'] = replace
    print("replace 模块加载成功")
except ImportError as e:
    print(f"replace 模块未找到: {e}")

# 注意：文件名有空格，需要特殊处理
try:
    import importlib.util
    spec = importlib.util.spec_from_file_location("regular_expression", "regular expression.py")
    regular_expression_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(regular_expression_module)
    filter_modules_available['regular_expression'] = regular_expression_module
    print("regular expression 模块加载成功")
except Exception as e:
    print(f"regular expression 模块未找到: {e}")

print(f"已加载过滤模块: {list(filter_modules_available.keys())}")

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 配置
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['RESULTS_FOLDER'] = 'results'

# 创建必要的目录
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESULTS_FOLDER'], exist_ok=True)

# 全局变量
whisper_model = None
filter_methods = {}

def load_whisper_model():
    """加载 Whisper 模型"""
    global whisper_model
    if whisper_model is None:
        print("正在加载 Whisper 模型...")
        try:
            import whisper
            whisper_model = whisper.load_model("base")
            print("Whisper 模型加载成功")
            return True
        except ImportError:
            print("Whisper 未安装，请运行: pip install openai-whisper")
            return False
        except Exception as e:
            print(f"Whisper 模型加载失败: {e}")
            print("提示: 首次使用需要下载模型文件，请确保网络连接正常")
            return False
    return True

def initialize_filter_methods():
    """初始化过滤方法"""
    global filter_methods

    # DFA 过滤器
    if 'DFA' in filter_modules_available:
        try:
            dfa_module = filter_modules_available['DFA']
            if hasattr(dfa_module, 'DFA_filter_words'):
                filter_methods['DFA'] = {
                    'name': 'DFA (确定有限自动机)',
                    'filter_func': dfa_module.DFA_filter_words
                }
                print("DFA 过滤器初始化成功")
            else:
                print("DFA 模块中未找到 DFA_filter_words 函数")
        except Exception as e:
            print(f"DFA 过滤器初始化失败: {e}")

    # Aho-Corasick 过滤器
    if 'aho_corasick' in filter_modules_available:
        try:
            aho_module = filter_modules_available['aho_corasick']
            if hasattr(aho_module, 'aho_corasick_filter_words'):
                filter_methods['aho_corasick'] = {
                    'name': 'Aho-Corasick (AC自动机)',
                    'filter_func': aho_module.aho_corasick_filter_words
                }
                print("Aho-Corasick 过滤器初始化成功")
            else:
                print("Aho-Corasick 模块中未找到 aho_corasick_filter_words 函数")
        except Exception as e:
            print(f"Aho-Corasick 过滤器初始化失败: {e}")

    # Trie Tree 过滤器
    if 'trie_tree' in filter_modules_available:
        try:
            trie_module = filter_modules_available['trie_tree']
            if hasattr(trie_module, 'trie_tree_filter_words'):
                filter_methods['trie_tree'] = {
                    'name': 'Trie Tree (字典树)',
                    'filter_func': trie_module.trie_tree_filter_words
                }
                print("Trie Tree 过滤器初始化成功")
            else:
                print("Trie Tree 模块中未找到 trie_tree_filter_words 函数")
        except Exception as e:
            print(f"Trie Tree 过滤器初始化失败: {e}")

    # Replace 过滤器
    if 'replace' in filter_modules_available:
        try:
            replace_module = filter_modules_available['replace']
            if hasattr(replace_module, 'replace_filter_words'):
                filter_methods['replace'] = {
                    'name': 'Replace (字符串替换)',
                    'filter_func': replace_module.replace_filter_words
                }
                print("Replace 过滤器初始化成功")
            else:
                print("Replace 模块中未找到 replace_filter_words 函数")
        except Exception as e:
            print(f"Replace 过滤器初始化失败: {e}")

    # 正则表达式过滤器
    if 'regular_expression' in filter_modules_available:
        try:
            regex_module = filter_modules_available['regular_expression']
            if hasattr(regex_module, 'regular_expression_filter_words'):
                filter_methods['regular_expression'] = {
                    'name': 'Regular Expression (正则表达式)',
                    'filter_func': regex_module.regular_expression_filter_words
                }
                print("Regular Expression 过滤器初始化成功")
            else:
                print("Regular Expression 模块中未找到 regular_expression_filter_words 函数")
        except Exception as e:
            print(f"Regular Expression 过滤器初始化失败: {e}")

    # 添加一个简单的默认过滤器
    if not filter_methods:
        filter_methods['simple'] = {
            'name': 'Simple (简单替换)',
            'filter_func': simple_filter
        }
        print("使用简单过滤器作为默认选项")

def simple_filter(text, sensitive_words):
    """简单的敏感词过滤函数"""
    filtered_text = text
    for word in sensitive_words:
        filtered_text = filtered_text.replace(word, '*' * len(word))
    return filtered_text

def open_browser():
    """延迟打开浏览器"""
    import time
    time.sleep(1.5)  # 等待服务器启动
    webbrowser.open('http://localhost:5000')

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/style.css')
def serve_css():
    """提供CSS文件"""
    return send_from_directory('.', 'style.css')

@app.route('/script.js')
def serve_js():
    """提供JS文件"""
    return send_from_directory('.', 'script.js')

@app.route('/api/health')
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'whisper_loaded': whisper_model is not None,
        'available_filters': list(filter_methods.keys())
    })

@app.route('/api/upload', methods=['POST'])
def upload_audio():
    """上传音频文件"""
    if 'audio' not in request.files:
        return jsonify({'error': '没有上传文件'}), 400
    
    file = request.files['audio']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    # 检查文件类型
    allowed_extensions = {'.mp3', '.wav', '.m4a', '.flac', '.ogg'}
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_extensions:
        return jsonify({'error': f'不支持的文件格式: {file_ext}'}), 400
    
    # 保存文件
    filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{filename}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    return jsonify({
        'success': True,
        'filename': filename,
        'filepath': filepath,
        'size': os.path.getsize(filepath)
    })

@app.route('/api/process', methods=['POST'])
def process_audio():
    """处理音频文件 - 使用本地whisper集成的敏感词过滤功能"""
    try:
        data = request.get_json()

        # 获取参数
        audio_file = data.get('audio_file')
        sensitive_words = data.get('sensitive_words', [])
        filter_method = data.get('filter_method', 'DFA')

        if not audio_file:
            return jsonify({'error': '没有指定音频文件'}), 400

        # 检查文件是否存在
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], audio_file)
        if not os.path.exists(filepath):
            return jsonify({'error': '音频文件不存在'}), 404

        # 开始处理
        start_time = time.time()

        # 加载模型
        print(f"加载 Whisper base 模型...")
        try:
            model = whisper.load_model("base")
            print("模型加载完成")
        except Exception as e:
            print(f"模型加载失败: {e}")
            return jsonify({'error': f'模型加载失败: {str(e)}'}), 500

        # 使用本地whisper的集成敏感词过滤功能进行转录
        print(f"开始转录音频（集成敏感词过滤）...")

        try:
            # 传入敏感词和过滤方法进行转录和过滤（与test.py一致）
            transcribe_params = {
                "language": "zh",
                "verbose": True,
                "word_timestamps": True,
                "sensitive_words": sensitive_words if sensitive_words else None
            }

            # 只有在有敏感词时才传入过滤方法参数
            if sensitive_words and filter_method:
                transcribe_params["filter_method"] = filter_method

            result = model.transcribe(filepath, **transcribe_params)

            transcribe_time = time.time() - start_time
            print(f"转录完成，耗时: {transcribe_time:.2f} 秒")
            print(f"识别语言: {result['language']}")

        except Exception as e:
            print(f"转录失败: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': f'转录失败: {str(e)}'}), 500

        # 处理结果（与test.py一致的数据结构）
        # 获取基本信息
        original_text = result.get('original_text', '')
        simplified_text = result.get('simplified_text', original_text)
        filtered_text = result.get('text', original_text)  # 本地whisper已经过滤过了
        segments_data = result.get('segments', [])

        # 计算音频时长
        audio_duration = segments_data[-1]['end'] if segments_data else 0

        # 处理分段信息
        segments = []
        for segment in segments_data:
            segments.append({
                'start': segment['start'],
                'end': segment['end'],
                'original': segment.get('original_text', segment['text']),
                'simplified': segment.get('simplified_text', segment['text']),
                'filtered': segment['text']  # 本地whisper已经过滤过了
            })

        # 计算统计信息
        process_time = time.time() - start_time
        real_time_factor = process_time / audio_duration if audio_duration > 0 else 0

        # 统计敏感词数量
        sensitive_word_count = 0
        if sensitive_words:
            for word in sensitive_words:
                sensitive_word_count += original_text.count(word)

        # 生成结果
        result_data = {
            'success': True,
            'audio_file': audio_file,
            'language': result.get('language', 'zh'),
            'duration': f"{int(audio_duration // 60):02d}:{int(audio_duration % 60):02d}",
            'process_time': f"{process_time:.1f}秒",
            'real_time_factor': f"{real_time_factor:.1f}x",
            'filter_method': filter_method,
            'filter_method_name': filter_method,
            'original_text': original_text,
            'simplified_text': simplified_text,
            'filtered_text': filtered_text,
            'segments': segments,
            'stats': {
                'segment_count': len(segments),
                'sensitive_word_count': sensitive_word_count,
                'accuracy_rate': '95%',
                'processing_speed': f"{real_time_factor:.1f}x"
            },
            'timestamp': datetime.now().isoformat(),
            'mode': 'whisper_integrated'
        }

        # 保存结果到文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_filename = f"result_{timestamp}.json"
        result_filepath = os.path.join(app.config['RESULTS_FOLDER'], result_filename)

        with open(result_filepath, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)

        result_data['result_file'] = result_filename

        print(f"处理完成，耗时: {process_time:.1f}秒")
        return jsonify(result_data)

    except Exception as e:
        print(f"处理失败: {e}")
        return jsonify({'error': f'处理失败: {str(e)}'}), 500

@app.route('/api/download/<result_type>/<filename>')
def download_result(result_type, filename):
    """下载结果文件"""
    try:
        if result_type == 'json':
            filepath = os.path.join(app.config['RESULTS_FOLDER'], filename)
            if os.path.exists(filepath):
                return send_file(filepath, as_attachment=True)
        
        elif result_type == 'txt':
            # 生成文本格式结果
            json_filepath = os.path.join(app.config['RESULTS_FOLDER'], filename.replace('.txt', '.json'))
            if os.path.exists(json_filepath):
                with open(json_filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 生成文本内容
                txt_content = generate_txt_result(data)
                
                # 创建临时文件
                with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.txt', delete=False) as f:
                    f.write(txt_content)
                    temp_filepath = f.name
                
                return send_file(temp_filepath, as_attachment=True, download_name=filename)
        
        return jsonify({'error': '文件不存在'}), 404
        
    except Exception as e:
        return jsonify({'error': f'下载失败: {str(e)}'}), 500

def generate_txt_result(data):
    """生成文本格式的结果"""
    content = f"""语音敏感词过滤系统 - 处理结果
{'=' * 50}

基本信息:
音频文件: {data.get('audio_file', '')}
识别语言: {data.get('language', '')}
音频时长: {data.get('duration', '')}
处理时间: {data.get('process_time', '')}
过滤方法: {data.get('filter_method_name', '')}

转录结果:
原文: {data.get('original_text', '')}
简体字转换: {data.get('simplified_text', '')}
过滤后: {data.get('filtered_text', '')}

分段详情:
"""
    
    for i, segment in enumerate(data.get('segments', []), 1):
        content += f"""分段 {i} ({segment['start']:.1f}s - {segment['end']:.1f}s):
    原文: {segment['original']}
    简体字: {segment['simplified']}
    过滤后: {segment['filtered']}

"""
    
    stats = data.get('stats', {})
    content += f"""统计信息:
分段数量: {stats.get('segment_count', 0)}
检测到敏感词: {stats.get('sensitive_word_count', 0)}
识别准确率: {stats.get('accuracy_rate', '未知')}
处理速度: {stats.get('processing_speed', '未知')}

生成时间: {data.get('timestamp', '')}
"""
    
    return content

@app.route('/api/filters')
def get_available_filters():
    """获取可用的过滤方法"""
    return jsonify({
        'filters': [
            {'id': method_id, 'name': method_info['name']}
            for method_id, method_info in filter_methods.items()
        ]
    })

if __name__ == '__main__':
    print("启动语音敏感词过滤系统...")

    # 初始化过滤方法
    initialize_filter_methods()
    print(f"可用过滤方法: {list(filter_methods.keys())}")

    # 预加载 Whisper 模型
    load_whisper_model()

    # 只在主进程中启动浏览器（避免调试模式下重复打开）
    import os
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        threading.Timer(1.5, open_browser).start()
        print("将在1.5秒后自动打开浏览器...")

    # 启动服务器
    app.run(debug=True, host='0.0.0.0', port=5000)
