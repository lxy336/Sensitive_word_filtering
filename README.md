# 语音敏感词过滤系统

基于OpenAI Whisper的语音识别与敏感词过滤集成方案，支持语音转文字、敏感词检测与过滤，并提供性能测试与结果可视化功能。


## 核心功能
- 语音识别：基于Whisper模型实现多语言语音转文字（支持英语、中文等）
- 敏感词过滤：提供多种过滤算法，支持文本净化处理
- 结果展示：包含原始文本、简体转换、过滤结果的分段对比
- 性能测试：支持不同算法、词库规模、音频长度的性能对比
- 数据可视化：生成测试结果图表，直观展示各指标差异


## 依赖安装
1. 安装Whisper核心依赖：
   ```bash
   # 安装最新版Whisper
   pip install -U openai-whisper
   # 或从源码安装
   pip install git+https://github.com/openai/whisper.git
   ```

2. 安装系统工具：
   - 需安装`ffmpeg`（参考Whisper官方文档的系统安装命令）
   - 可选：`rust`环境（用于优化tokenizer）
     ```bash
     pip install setuptools-rust
     ```

3. 其他依赖：根据项目脚本需求安装Python数据处理库（如`pandas`、`matplotlib`等）


## 使用说明
1. **Web界面**：通过`templates/index.html`启动前端界面，支持音频上传或现场录音
2. **敏感词过滤**：系统自动处理语音识别结果，提供多种过滤算法选择
3. **性能测试**：运行性能测试脚本：
   ```bash
   python performance_test.py
   ```
4. **结果可视化**：生成测试图表：
   ```bash
   python create_final_charts.py
   ```


## 许可证
- Whisper核心代码遵循MIT许可证（详见`whisper/LICENSE`）
- 本项目扩展部分遵循相同许可证条款