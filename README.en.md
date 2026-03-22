# YouTube Transcript Tool (ytt)

[한국어](README.md) | **English** | [中文](README.zh.md)

A CLI tool for automatically transcribing and summarizing YouTube videos.

## Key Features

- 🆓 **Completely Free Transcription**: Uses local Whisper models (no API costs)
- 🚀 **GPU Acceleration**: 5-10x faster processing with faster-whisper
- 🤖 **Latest Claude Sonnet 4.6**: High-quality summarization
- 🌍 **Multi-language Support**: Korean, English, and Chinese summaries
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
- 🌍 Default language selection (Korean/English/Chinese)
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
# Transcription only (video info + plain text)
ytt "https://youtube.com/watch?v=xxx" ./output

# Transcription + Summary (auto-saves transcript.json)
ytt "https://youtube.com/watch?v=xxx" ./output --summarize

# Also save timestamps file
ytt "https://youtube.com/watch?v=xxx" ./output --timestamps

# Also save JSON + metadata files
ytt "https://youtube.com/watch?v=xxx" ./output --json --metadata

# Specify language + summary
ytt "https://youtube.com/watch?v=xxx" ./output -l ko --summarize

# English video + English summary
ytt "https://youtube.com/watch?v=xxx" ./output -l en --summarize
```

### Summary-only Mode

Generate summaries only from already transcribed directories:

```bash
# First, transcribe with --json (required for --summarize-only)
ytt "URL" ./output -m tiny --json

# Or run with --summarize first (transcript.json auto-created)
ytt "URL" ./output --summarize

# Later, regenerate summary only
ytt ./output --summarize-only -l ko
```

### Detailed Options

```bash
ytt --help
```

**Key Options:**
- `--summarize, -s`: Generate summary along with transcription (auto-saves transcript.json)
- `--summarize-only`: Generate summary only from existing transcript.json
- `--timestamps`: Also save transcript with timestamps (transcript_with_timestamps.txt)
- `--json`: Also save structured JSON (transcript.json)
- `--metadata`: Also save video metadata (metadata.json)
- `--model-size, -m`: Whisper model size (default: base)
- `--language, -l`: Language specification (default: auto - auto-detect)
- `--no-cleanup`: Don't delete temporary files
- `--no-cache`: Disable prompt caching (when summarizing)
- `--vad-aggressive`: Use aggressive VAD (faster transcription)
- `--force-librosa`: Force librosa chunking (disable ffmpeg)
- `--verbose, -v`: Verbose logging output

---

## Output Files

By default, only `transcript.txt` is created. All other files are optional.

```
output/
├── transcript.txt                    # Video info + plain transcript (always created)
├── transcript_with_timestamps.txt    # Transcript with timestamps (--timestamps)
├── transcript.json                   # JSON format data (--json or --summarize)
├── metadata.json                     # Video metadata (--metadata)
└── summary.txt                       # AI summary (--summarize)
```

`transcript.txt` includes a header with the video title, URL, uploader, and duration.

---

## Examples

### 1. Korean Lecture Transcription and Summary

```bash
ytt "https://youtube.com/watch?v=lecture123" ./lectures/ai-basics \
    --summarize \
    --model-size medium \
    --language ko
```

### 2. Quick English Podcast Transcription (save all files)

```bash
ytt "https://youtube.com/watch?v=podcast456" ./podcasts/ep01 \
    -m tiny \
    -l en \
    --timestamps --json --metadata
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

Apache License 2.0

---

## Contributing

Issues and PRs are always welcome!

---

## Repository

- **GitHub**: https://github.com/SaraHan774/ytt
- **Issues**: https://github.com/SaraHan774/ytt/issues
- **Releases**: https://github.com/SaraHan774/ytt/releases
