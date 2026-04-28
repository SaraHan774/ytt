# YouTube Transcript Tool (ytt)

[한국어](README.md) | **English** | [中文](README.zh.md)

A CLI tool for automatically transcribing and summarizing YouTube videos.

## Key Features

- 🆓 **Completely Free Transcription**: Uses local Whisper models (no API costs)
- 🍎 **Apple Silicon GPU Acceleration**: `mlx-whisper` on Metal — **6.3x faster** than faster-whisper on long videos (measured: 82-min audio, base model, M1 Max)
- ⚡ **Layered Optimization**: Zero-copy ffmpeg chunking + raw audio stream + per-worker model load
- 🤖 **Claude Sonnet 4.6 Summarization**: Prompt Caching reduces token cost on repeat invocations
- 🌍 **Summary Languages**: Korean / English / Chinese (other languages fall back to Korean)
- 💻 **CLI Interface**: Simple command-line usage
- 🎯 **Summary-only Mode**: Quickly regenerate summaries from existing transcripts

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

# Transcription + Summary (does NOT auto-save transcript.json since v1.4.0)
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

To regenerate summaries from an existing run, you need `transcript.json`. **`--summarize` alone no longer creates it** (since v1.4.0), so you must combine `--summarize --json` on the first run.

```bash
# First run — keep transcript.json for later reuse
ytt "URL" ./output --summarize --json

# Later, regenerate summary only (e.g., different language)
ytt ./output --summarize-only -l en
```

### Options

The most accurate option list is always `ytt --help`. The table below reflects v1.4.1.

| Option | Description | Default |
|---|---|---|
| `--summarize`, `-s` | Generate Claude summary (`summary.txt`) | off |
| `--summarize-only` | Re-run summary from existing `transcript.json` (no URL needed) | off |
| `--timestamps` | Save transcript with timestamps | off |
| `--json` | Save structured JSON. Required for `--summarize-only` reuse | off |
| `--metadata` | Save video metadata (`metadata.json`) | off |
| `--model-size`, `-m` | Whisper model (`tiny`/`base`/`small`/`medium`/`large`) | `base` |
| `--language`, `-l` | Language code (`ko`/`en`/`zh`/`auto` etc). Summary supports ko/en/zh only | `auto` |
| `--backend` | Transcription backend (`auto`/`mlx`/`faster-whisper`). `auto` picks mlx on Apple Silicon | `auto` |
| `--fast` | Fast mode (`beam_size=1`, 300s chunks, condition off). ~1.6x faster on CPU | off |
| `--vad-aggressive` | Shorter silence threshold (300ms) for faster transcription | off |
| `--force-librosa` | Disable ffmpeg, use librosa for chunking (debug) | off |
| `--no-cache` | Disable Prompt Caching for summaries | off |
| `--no-cleanup` | Keep `raw_audio/` and `chunks/` directories | off |
| `--verbose`, `-v` | DEBUG log output | off |
| `--version` | Print version and exit | — |

`--backend` semantics:
- `auto` (default): MLX on Apple Silicon if `mlx-whisper` is installed, otherwise faster-whisper
- `mlx`: force MLX (auto-falls back to faster-whisper with a warning if unsupported)
- `faster-whisper`: force CPU/CUDA path

---

## Output Files

By default, only `transcript.txt` is created. All other files are optional.

```
output/
├── transcript.txt                    # Video info + plain transcript (always created)
├── transcript_with_timestamps.txt    # Transcript with timestamps (--timestamps)
├── transcript.json                   # JSON format data (--json)
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
