# Agent Guide for `ytt`

This file is the entry point for AI coding agents (Claude Code, Cursor, etc.) working on this repository. Read this first.

## What this project is

`ytt` is a Python CLI that downloads a YouTube video, transcribes it locally via Whisper (faster-whisper or mlx-whisper), and optionally summarizes the transcript with Claude.

Current version: **1.4.1** (see `setup.py`, `CHANGELOG.md`).

## Trust order for agents

When information conflicts, trust in this order:

1. **`ytt --help`** — generated from `cli.py`, always matches the running code. Use this to discover options and their current names/defaults.
2. **`ytt/cli.py`, `ytt/core.py`** — source of truth for behavior.
3. **`README.md`, `CHANGELOG.md`** — kept up-to-date as of v1.4.1.
4. **`USAGE_CLI.md`, `CLI_DESIGN.md`** — partial / historical. Verify against source before relying on.
5. **Your training data** — likely outdated; do not assume option names from memory.

## Key files

| File | Role |
|---|---|
| `ytt/cli.py` | click entry point (`ytt`, `ytt-init`, `ytt-config` commands) |
| `ytt/core.py` | download, chunking, transcription, summarization (no Streamlit) |
| `ytt/config.py` | config file (`~/.config/ytt/`) and API key storage |
| `ytt/setup.py` | first-run interactive wizard |
| `ytt/i18n.py` | locale strings (ko/en/zh — **not ja**) |
| `Formula/ytt.rb` | Homebrew formula (synced to `homebrew-ytt` tap on release) |
| `.github/workflows/release.yml` | auto-updates Homebrew tap on release publish |
| `tests/` | pytest suite, requires `pytest>=7.4` |

## Pipeline

```
download_youtube  → chunk_audio  → transcribe_audio  → save_transcripts
                                                     ↘ summarize_with_claude (optional)
```

- **Download**: yt-dlp keeps the original audio stream (`m4a` / `webm` / `opus`); no mp3 re-encode.
- **Chunking**: ffmpeg segment muxer if available (zero-copy), librosa fallback. Chunks inherit the input extension (e.g. `segment_000.m4a`, **not** `.mp3`).
- **Transcribe**: faster-whisper (CPU/CUDA) or mlx-whisper (Apple Silicon Metal GPU). Backend chosen by `resolve_backend()` based on `--backend` and platform.
- **Workers**: `ThreadPoolExecutor`, `max_workers = cpu_count // 2` for faster-whisper, `1` for MLX (Metal GPU is single-resource). Whisper model is loaded once per worker thread (`_get_thread_local_model`).

## Non-obvious behaviors

- **`--summarize` does NOT auto-create `transcript.json`** as of v1.4.0. To enable `--summarize-only` reuse, run with `--summarize --json` together.
- **`--language` default is `auto`** (auto-detect), not a specific locale.
- **Summarization languages**: `ko`, `en`, `zh` only. Other values silently fall back to `ko` with a warning. Japanese is **not** supported despite older docs.
- **`--backend auto`** picks `mlx` on Apple Silicon if `mlx-whisper` is installed, else `faster-whisper`.
- **`--fast`** enables `beam_size=1`, `condition_on_previous_text=False`, and 300s chunks. Quality regression possible (more segments, less coherent).
- **MLX needs separate install**: `pip install 'ytt[mlx]'`. Brew formula does not bundle it yet.
- **Tests**: `tests/test_core.py::TestTranscribeAudio::test_transcribe_audio_single_file` fails on machines that have `mlx-whisper` system-installed because `_mlx_available()` is `lru_cached` and routes mock audio to MLX. Pin `backend="faster-whisper"` or mock `_mlx_available` when adding new tests around `transcribe_audio`.

## Where things live

- **Config**: `~/.config/ytt/` (Linux/macOS), `%APPDATA%/ytt/` (Windows)
- **Default output**: only `transcript.txt` is created. Other files are opt-in:
  - `--timestamps` → `transcript_with_timestamps.txt`
  - `--json` → `transcript.json`
  - `--metadata` → `metadata.json`
  - `--summarize` → `summary.txt`
- **Whisper model cache**: `~/.cache/huggingface/hub/` (mlx) or `~/.cache/faster-whisper/`

## Performance reference (M1 Max, base model, 82-min audio, v1.4.1)

| Backend | Total time | vs faster-whisper |
|---|---:|---:|
| MLX (`--backend mlx`) | 64.8s | **6.3x faster** |
| faster-whisper (default) | 408.9s | 1.0x |
| faster-whisper + `--fast` | 248.8s | 1.6x faster |

Earlier README claims of "8–15x" reflect upstream mlx-whisper benchmarks on different hardware/model sizes; on base model + M1 Max it's ~6x for long videos, less for short ones.

## Common tasks

### Adding a new CLI option
1. Add `@click.option(...)` in `ytt/cli.py:main`.
2. Plumb through to `core.transcribe_audio` / etc.
3. Update README.md options table (don't update USAGE_CLI.md — that file is being phased out).
4. Add CHANGELOG.md entry.
5. `ytt --help` will reflect it automatically.

### Bumping version
1. Edit `setup.py` `version=`.
2. Edit `ytt/cli.py` `@click.version_option(version=...)`.
3. Add `CHANGELOG.md` entry.
4. Commit, push, `gh release create vX.Y.Z`.
5. Until `secrets.TAP_GITHUB_TOKEN` is set in GitHub repo settings, manually update `Formula/ytt.rb` in `homebrew-ytt/` (the local clone of the tap repo) — see `HOMEBREW.md`.

### Releasing
- `release.yml` updates the Homebrew tap automatically **only if** `TAP_GITHUB_TOKEN` is configured in repo secrets (currently unset). The workflow's `sed` patterns are also too broad and will rewrite resource URLs incorrectly — this is a known bug; manual tap update is the current practice.

## What NOT to do

- **Do not** add ja (Japanese) to `i18n.py` or summarization prompts unless implementing it; existing references are stale.
- **Do not** assume `transcript.json` always exists — only `transcript.txt` is guaranteed.
- **Do not** call `core._load_whisper_model` directly — use `_get_thread_local_model` for caching.
- **Do not** use `subprocess.run(..., capture_output=True, stderr=...)` together — they conflict and were the cause of v1.4.1's main bug fix.
- **Do not** force `extractor_args.player_client` in yt-dlp config — broken under YouTube SABR streaming as of 2026.

## Repo conventions

- Code comments: only when WHY is non-obvious (constraints, workarounds, surprising behavior). Don't restate WHAT.
- Commit messages: prefix with `feat:`, `fix:`, `change:`, `chore:`. Bug fixes for a release line use the patch version (e.g., `fix: v1.4.1 - …`).
- Tests: live in `tests/`, mock external services (Whisper, Claude, yt-dlp). `pytest.ini` enforces 65% coverage.
