# YouTube 转录工具 (ytt)

[한국어](README.md) | [English](README.en.md) | **中文**

一个用于自动转录和总结 YouTube 视频的 CLI 工具。

## 主要特性

- 🆓 **完全免费转录**: 使用本地 Whisper 模型（无 API 费用）
- 🚀 **GPU 加速**: 使用 faster-whisper 处理速度提升 5-10 倍
- 🤖 **最新 Claude Sonnet 4.5**: 高质量摘要生成
- 🌍 **多语言支持**: 支持韩语、英语和日语摘要
- 💻 **CLI 界面**: 简单的命令行使用
- ⚡ **仅摘要模式**: 从现有转录快速重新生成摘要

---

## 安装

### 方法 1: Homebrew（推荐 - macOS/Linux）

```bash
# 添加 tap
brew tap SaraHan774/ytt

# 安装（自动安装 ffmpeg）
brew install ytt

# 运行交互式设置
ytt-init
```

### 方法 2: pip（手动安装）

#### 1. 安装 ffmpeg（必需）

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# Windows (Chocolatey)
choco install ffmpeg
```

#### 2. 安装 Python 包

```bash
# 克隆仓库
git clone https://github.com/SaraHan774/ytt.git
cd ytt

# 安装包
pip install -r requirements.txt
pip install -e .
```

#### 3. 交互式设置（推荐）

首次执行 `ytt` 时会自动运行交互式设置向导：

```bash
# 首次运行自动触发设置
ytt

# 或手动运行设置
ytt-init

# 重置并重新配置
ytt-init --reset
```

**设置向导配置项：**
- ✅ 系统环境检查（ffmpeg、GPU 等）
- 🔑 Anthropic API 密钥设置
- 🌍 默认语言选择（韩语/英语/日语）
- 🎤 默认 Whisper 模型大小
- ⚙️ 自动摘要激活

#### 4. 手动 API 密钥设置（可选）

```bash
# 设置为环境变量
export ANTHROPIC_API_KEY="your-api-key"

# 或使用 CLI 命令
ytt-config set-api-key "your-api-key"

# 检查配置
ytt-config show-config

# 或创建 .env 文件
echo "ANTHROPIC_API_KEY=your-api-key" > .env
```

---

## 使用方法

### 基本使用

```bash
# 仅转录（自动检测语言）
ytt "https://youtube.com/watch?v=xxx" ./output

# 转录 + 摘要
ytt "https://youtube.com/watch?v=xxx" ./output --summarize

# 指定模型大小（tiny/base/small/medium/large）
ytt "https://youtube.com/watch?v=xxx" ./output -m medium

# 手动指定语言（韩语）
ytt "https://youtube.com/watch?v=xxx" ./output -l ko --summarize

# 英语视频 + 英语摘要
ytt "https://youtube.com/watch?v=xxx" ./output -l en --summarize
```

### 仅摘要模式

仅从已转录的目录生成摘要：

```bash
# 首先，使用 tiny 模型快速转录
ytt "URL" ./output -m tiny

# 稍后，仅添加摘要
ytt ./output --summarize-only -l ko
```

### 详细选项

```bash
ytt --help
```

**主要选项：**
- `--summarize, -s`: 转录时一并生成摘要
- `--summarize-only`: 仅从现有转录生成摘要
- `--model-size, -m`: Whisper 模型大小（默认：base）
- `--language, -l`: 语言规范（默认：auto - 自动检测）
- `--no-cleanup`: 不删除临时文件
- `--verbose, -v`: 详细日志输出

---

## 输出文件

```
output/
├── transcript.txt                    # 纯文本转录
├── transcript_with_timestamps.txt    # 带时间戳的转录
├── transcript.json                   # JSON 格式数据
├── metadata.json                     # 视频元数据
└── summary.txt                       # AI 摘要（使用 --summarize 选项）
```

---

## 示例

### 1. 韩语讲座转录和摘要

```bash
ytt "https://youtube.com/watch?v=lecture123" ./lectures/ai-basics \
    --summarize \
    --model-size medium \
    --language ko
```

### 2. 快速英语播客转录

```bash
ytt "https://youtube.com/watch?v=podcast456" ./podcasts/ep01 \
    -m tiny \
    -l en
```

### 3. 批处理脚本

```bash
#!/bin/bash
# process-videos.sh

while IFS= read -r url; do
  timestamp=$(date +%Y%m%d_%H%M%S)
  ytt "$url" "./batch/$timestamp" --summarize -v
  echo "✓ Processed: $url"
done < urls.txt
```

---

## 测试

```bash
# 完整测试套件
pytest

# 包含覆盖率
pytest --cov=ytt

# 仅单元测试
pytest -m "not integration"

# 仅集成测试
pytest -m integration
```

---

## 费用

- **语音转录**: 免费（本地处理）
- **摘要生成**: 基于 Claude API 使用量（每字符约 0.5-2 tokens）

---

## 处理时间

- **tiny 模型**: 约实时的 1/10
- **base 模型**: 约实时的 1/5（推荐）
- **medium 模型**: 约实时的 1/3
- **large 模型**: 约实时

示例：16 分钟视频 → 约 3-4 分钟（base 模型，使用 GPU）

---

## 故障排除

### GPU 未检测到

```bash
# 检查 CUDA
python -c "import torch; print('CUDA:', torch.cuda.is_available())"

# 强制 CPU 执行
CUDA_VISIBLE_DEVICES="" ytt "URL" ./output
```

### API 密钥错误

```bash
# 检查 API 密钥
echo $ANTHROPIC_API_KEY

# 测试
python -c "import os; print(os.getenv('ANTHROPIC_API_KEY'))"
```

### 内存不足

```bash
# 使用较小的模型
ytt "URL" ./output -m tiny
```

---

## 文档

- [CLI 使用指南](USAGE_CLI.md) - 详细使用方法和示例
- [CLI 设计](CLI_DESIGN.md) - 架构和设计文档

---

## 许可证

MIT License

---

## 贡献

随时欢迎 Issues 和 PRs！

---

## 仓库

- **GitHub**: https://github.com/SaraHan774/ytt
- **Issues**: https://github.com/SaraHan774/ytt/issues
- **Releases**: https://github.com/SaraHan774/ytt/releases
