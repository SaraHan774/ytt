# YouTube 转录工具 (ytt)

[한국어](README.md) | [English](README.en.md) | **中文**

一个用于自动转录和总结 YouTube 视频的 CLI 工具。

## 主要特性

- 🆓 **完全免费转录**: 使用本地 Whisper 模型（无 API 费用）
- 🍎 **Apple Silicon GPU 加速**: 使用 `mlx-whisper` 通过 Metal — 长视频实测比 faster-whisper 快 **6.3 倍**（base 模型 / M1 Max / 82 分钟视频）
- ⚡ **多层优化**: zero-copy ffmpeg 切片 + 原始音频流 + 每 worker 仅加载一次模型
- 🤖 **Claude Sonnet 4.6 摘要**: Prompt Caching 降低重复调用的 token 成本
- 🌍 **摘要语言**: 韩语 / 英语 / 中文（其他语言自动回退到韩语）
- 💻 **CLI 界面**: 简单的命令行使用
- 🎯 **仅摘要模式**: 从现有转录快速重新生成摘要

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
- 🌍 默认语言选择（韩语/英语/中文）
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
# 仅转录（视频信息 + 纯文本）
ytt "https://youtube.com/watch?v=xxx" ./output

# 转录 + 摘要（自 v1.4.0 起不再自动保存 transcript.json）
ytt "https://youtube.com/watch?v=xxx" ./output --summarize

# 同时保存时间戳文件
ytt "https://youtube.com/watch?v=xxx" ./output --timestamps

# 同时保存 JSON + 元数据文件
ytt "https://youtube.com/watch?v=xxx" ./output --json --metadata

# 指定语言 + 摘要
ytt "https://youtube.com/watch?v=xxx" ./output -l ko --summarize

# 英语视频 + 英语摘要
ytt "https://youtube.com/watch?v=xxx" ./output -l en --summarize
```

### 仅摘要模式

要从已有运行中重新生成摘要，需要 `transcript.json` 文件。**自 v1.4.0 起 `--summarize` 不再自动生成它**，因此首次运行时必须同时使用 `--summarize --json`。

```bash
# 首次运行 — 保留 transcript.json 以便后续复用
ytt "URL" ./output --summarize --json

# 稍后仅重新生成摘要（例如换语言）
ytt ./output --summarize-only -l en
```

### 选项一览

最准确的最新选项列表请运行 `ytt --help`。下表对应 v1.4.1。

| 选项 | 说明 | 默认值 |
|---|---|---|
| `--summarize`, `-s` | 使用 Claude 生成摘要（`summary.txt`） | off |
| `--summarize-only` | 仅基于现有 `transcript.json` 重新生成摘要（无需 URL） | off |
| `--timestamps` | 额外保存带时间戳的转录 | off |
| `--json` | 额外保存结构化 JSON（`transcript.json`）。`--summarize-only` 复用所需 | off |
| `--metadata` | 额外保存视频元数据（`metadata.json`） | off |
| `--model-size`, `-m` | Whisper 模型（`tiny`/`base`/`small`/`medium`/`large`） | `base` |
| `--language`, `-l` | 语言代码（`ko`/`en`/`zh`/`auto` 等）。摘要仅支持 ko/en/zh | `auto` |
| `--backend` | 转录后端（`auto`/`mlx`/`faster-whisper`）。`auto` 在 Apple Silicon 上选择 mlx | `auto` |
| `--fast` | 快速模式（`beam_size=1`、300 秒分块、condition off）。CPU 上约快 1.6 倍 | off |
| `--vad-aggressive` | 更短的静音阈值（300ms），提高转录速度 | off |
| `--force-librosa` | 禁用 ffmpeg，使用 librosa 分块（调试用） | off |
| `--no-cache` | 禁用摘要的 Prompt Caching | off |
| `--no-cleanup` | 保留 `raw_audio/` 与 `chunks/` 临时目录 | off |
| `--verbose`, `-v` | 输出 DEBUG 日志 | off |
| `--version` | 打印版本后退出 | — |

`--backend` 行为：
- `auto`（默认）: 安装了 `mlx-whisper` 的 Apple Silicon 上选 MLX，否则选 faster-whisper
- `mlx`: 强制 MLX（不满足条件时自动回退到 faster-whisper 并输出 warning）
- `faster-whisper`: 强制 CPU/CUDA 路径

---

## 输出文件

默认只创建 `transcript.txt`，其他文件均为可选。

```
output/
├── transcript.txt                    # 视频信息 + 纯文本转录（始终创建）
├── transcript_with_timestamps.txt    # 带时间戳的转录（--timestamps）
├── transcript.json                   # JSON 格式数据（--json）
├── metadata.json                     # 视频元数据（--metadata）
└── summary.txt                       # AI 摘要（--summarize）
```

`transcript.txt` 的标题中包含视频标题、URL、上传者和时长。

---

## 示例

### 1. 韩语讲座转录和摘要

```bash
ytt "https://youtube.com/watch?v=lecture123" ./lectures/ai-basics \
    --summarize \
    --model-size medium \
    --language ko
```

### 2. 快速英语播客转录（保存所有文件）

```bash
ytt "https://youtube.com/watch?v=podcast456" ./podcasts/ep01 \
    -m tiny \
    -l en \
    --timestamps --json --metadata
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

Apache License 2.0

---

## 贡献

随时欢迎 Issues 和 PRs！

---

## 仓库

- **GitHub**: https://github.com/SaraHan774/ytt
- **Issues**: https://github.com/SaraHan774/ytt/issues
- **Releases**: https://github.com/SaraHan774/ytt/releases
