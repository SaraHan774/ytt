# YouTube Transcript Tool (ytt)

[한국어](README.md) | **English** | [中文](README.zh.md)

A CLI tool for automatically transcribing and summarizing YouTube videos.

## Key Features

- 🆓 **Completely Free Transcription**: Uses local Whisper models (no API costs)
- 🚀 **GPU Acceleration**: 5-10x faster processing with faster-whisper
- 🤖 **Latest Claude Sonnet 4.5**: High-quality summarization
- 🌍 **Multi-language Support**: Korean, English, and Japanese summaries
- 💻 **CLI Interface**: Simple command-line usage
- ⚡ **Summary-only Mode**: Quickly regenerate summaries from existing transcripts

---

## Installation

### Method 1: Homebrew (Recommended - macOS/Linux)

```bash
# Add tap
brew tap SaraHan774/ytt

# Install (ffmpeg auto-installed)
brew install ytt

# Run interactive setup
ytt-init
```

### Method 2: pip (Manual Installation)

#### 1. Install ffmpeg (Required)

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# Windows (Chocolatey)
choco install ffmpeg
```

#### 2. Install Python Package

```bash
# Clone repository
git clone https://github.com/SaraHan774/ytt.git
cd ytt

# Install package
pip install -r requirements.txt
pip install -e .
```

#### 3. Interactive Setup (Recommended)

The interactive setup wizard runs automatically on first `ytt` execution:

```bash
# First run automatically triggers setup
ytt

# Or manually run setup
ytt-init

# Reset and reconfigure
ytt-init --reset
```

**Setup wizard configures:**
- ✅ System environment check (ffmpeg, GPU, etc.)
- 🔑 Anthropic API key setup
- 🌍 Default language selection (Korean/English/Japanese)
- 🎤 Default Whisper model size
- ⚙️ Auto-summarize activation

#### 4. Manual API Key Setup (Optional)

```bash
# Set as environment variable
export ANTHROPIC_API_KEY="your-api-key"

# Or use CLI command
ytt-config set-api-key "your-api-key"

# Check configuration
ytt-config show-config

# Or create .env file
echo "ANTHROPIC_API_KEY=your-api-key" > .env
```

---

## Usage

### Basic Usage

```bash
# Transcription only
ytt "https://youtube.com/watch?v=xxx" ./output

# Transcription + Summary
ytt "https://youtube.com/watch?v=xxx" ./output --summarize

# Specify model size (tiny/base/small/medium/large)
ytt "https://youtube.com/watch?v=xxx" ./output -m medium

# Specify language (Korean)
ytt "https://youtube.com/watch?v=xxx" ./output -l ko --summarize

# English summary
ytt "https://youtube.com/watch?v=xxx" ./output -l en --summarize
```

### Summary-only Mode

Generate summaries only from already transcribed directories:

```bash
# First, quickly transcribe with tiny model
ytt "URL" ./output -m tiny

# Later, add summary only
ytt ./output --summarize-only -l ko
```

### Detailed Options

```bash
ytt --help
```

**Key Options:**
- `--summarize, -s`: Generate summary along with transcription
- `--summarize-only`: Generate summary only from existing transcript
- `--model-size, -m`: Whisper model size (default: base)
- `--language, -l`: Language specification (default: ko)
- `--no-cleanup`: Don't delete temporary files
- `--verbose, -v`: Verbose logging output

---

## Output Files

```
output/
├── transcript.txt                    # Plain text transcript
├── transcript_with_timestamps.txt    # Transcript with timestamps
├── transcript.json                   # JSON format data
├── metadata.json                     # Video metadata
└── summary.txt                       # AI summary (with --summarize option)
```

---

## Examples

### 1. Korean Lecture Transcription and Summary

```bash
ytt "https://youtube.com/watch?v=lecture123" ./lectures/ai-basics \
    --summarize \
    --model-size medium \
    --language ko
```

### 2. Quick English Podcast Transcription

```bash
ytt "https://youtube.com/watch?v=podcast456" ./podcasts/ep01 \
    -m tiny \
    -l en
```

### 3. Batch Processing Script

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

## Testing

```bash
# Full test suite
pytest

# With coverage
pytest --cov=ytt

# Unit tests only
pytest -m "not integration"

# Integration tests only
pytest -m integration
```

---

## Cost

- **Speech Transcription**: Free (local processing)
- **Summarization**: Based on Claude API usage (~0.5-2 tokens per character)

---

## Processing Time

- **tiny model**: ~1/10 of real-time
- **base model**: ~1/5 of real-time (recommended)
- **medium model**: ~1/3 of real-time
- **large model**: ~real-time

Example: 16-minute video → ~3-4 minutes (base model with GPU)

---

## Troubleshooting

### GPU Not Detected

```bash
# Check CUDA
python -c "import torch; print('CUDA:', torch.cuda.is_available())"

# Force CPU execution
CUDA_VISIBLE_DEVICES="" ytt "URL" ./output
```

### API Key Error

```bash
# Check API key
echo $ANTHROPIC_API_KEY

# Test
python -c "import os; print(os.getenv('ANTHROPIC_API_KEY'))"
```

### Out of Memory

```bash
# Use smaller model
ytt "URL" ./output -m tiny
```

---

## Documentation

- [CLI Usage Guide](USAGE_CLI.md) - Detailed usage and examples
- [CLI Design](CLI_DESIGN.md) - Architecture and design documentation

---

## License

MIT License

---

## Contributing

Issues and PRs are always welcome!

---

## Repository

- **GitHub**: https://github.com/SaraHan774/ytt
- **Issues**: https://github.com/SaraHan774/ytt/issues
- **Releases**: https://github.com/SaraHan774/ytt/releases
