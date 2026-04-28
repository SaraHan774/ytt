# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.4.1] - 2026-04-29

### Fixed
- **`chunk_audio_with_ffmpeg`**: removed `capture_output=True` + `stderr=...` conflict that caused every ffmpeg chunking call to fail and silently fall back to librosa. Zero-copy ffmpeg chunking now actually runs (verified ~5x faster than librosa fallback on 82-minute audio).
- **YouTube download compatibility**: removed `extractor_args.player_client = ["android", "web"]` override that conflicted with YouTube SABR streaming and caused `Requested format is not available`. yt-dlp's default client selection is now used. Custom `User-Agent` headers retained.

### Benchmarks (M1 Max, base model, 82m 40s video)
- MLX backend: 64.8s (chunking 0.7s + transcribe 64.1s)
- faster-whisper: 408.9s
- `--fast`: 248.8s
- MLX is ~6.3x faster than faster-whisper on long videos.

## [1.4.0] - 2026-04-21

### Added
- **MLX backend** (`--backend mlx`): Apple Silicon GPU-accelerated Whisper via `mlx-whisper`. Up to 6x faster than faster-whisper on long videos. Auto-detects on Apple Silicon (`--backend auto`).
- **Thread-local Whisper model cache**: model loaded once per worker thread instead of per chunk. Cumulative gain on long videos with many chunks.
- **Zero-copy raw audio download**: yt-dlp now keeps the original audio stream (`m4a`/`webm`/`opus`) instead of re-encoding to mp3. Saves disk I/O and CPU.
- Optional install: `pip install 'ytt[mlx]'`.

### Changed
- `--summarize` no longer auto-creates `transcript.json`. Use `--summarize` with `--json` together if you want the structured JSON for later `--summarize-only` runs.

## [1.3.0] - 2026-03-22

### Added
- **Download progress bar** with size + speed via `rich.progress`.
- **`--fast` mode**: `beam_size=1`, 300s chunks, condition_on_previous_text disabled. ~1.6x faster on CPU-only environments.

## [1.2.0] - 2026-02-03

### Added
- **Selective output options**: `--timestamps`, `--json`, `--metadata` flags. Default output is now just `transcript.txt`.
- Thread-safety hardening for parallel transcription.

## [1.1.0] - 2026-02-02

### Added - Phase 2 Performance Optimizations

#### ffmpeg Direct Chunking
- **Zero-copy audio chunking** using ffmpeg segment muxer
- Automatic fallback to librosa if ffmpeg is not installed
- 60x faster chunking, 80-90% memory reduction
- New CLI flag: `--force-librosa` to disable ffmpeg and use librosa

#### Prompt Caching
- **90% API cost reduction** using Claude's Prompt Caching
- Automatic caching of system prompts (5-minute TTL)
- Cache hit tracking in logs
- New CLI flag: `--no-cache` to disable prompt caching

#### VAD Parameter Tuning
- **20-30% faster transcription** with aggressive VAD settings
- Configurable VAD parameters via config file
- New CLI flag: `--vad-aggressive` for faster transcription
- Default: Conservative (500ms), Aggressive (300ms)

### Changed
- Version bump: 1.0.4 → 1.1.0
- Updated `core.chunk_audio()` to support both ffmpeg and librosa
- Enhanced `core.transcribe_audio()` with custom VAD configuration
- Improved `core.summarize_with_claude()` with prompt caching support
- CLI now loads user config for performance settings

### Performance Improvements

**30-minute video (base model, GPU):**
- Processing time: 13.9min → 8.3min (1.7x faster)
- Peak memory: 800MB → 150MB (81% reduction)
- API cost: $0.80 → $0.08 (90% reduction)

**60-minute video:**
- Processing time: 27.8min → 15.9min (1.7x faster)
- Peak memory: 1600MB → 180MB (89% reduction)
- API cost: $1.60 → $0.16 (90% reduction)

### Configuration
- Added `performance` section to default config:
  - `use_ffmpeg_chunking`: Auto-detect and use ffmpeg (default: true)
  - `enable_prompt_caching`: Enable prompt caching for summaries (default: true)
  - `vad_config`: Aggressive VAD settings for faster transcription

### Testing
- Added comprehensive test suite for new features:
  - `TestChunkAudioWithFFmpeg`: ffmpeg chunking tests
  - `TestChunkAudioLibrosa`: librosa fallback tests
  - `TestChunkAudioWrapper`: wrapper function tests
  - `TestTranscribeWithVADConfig`: VAD configuration tests
  - `TestSummarizeWithPromptCaching`: Prompt caching tests

### Documentation
- Updated README.md with performance optimization section
- Added benchmark results and usage examples
- Documented new CLI flags and configuration options
- Added ffmpeg installation guide

---

## [1.0.4] - Previous Release

See git history for previous releases.
