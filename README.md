# YouTube Transcript Tool (ytt)

**한국어** | [English](README.en.md) | [中文](README.zh.md)

YouTube 영상을 자동으로 전사하고 요약하는 CLI 도구입니다.

## 주요 특징

- 🆓 **완전 무료 전사**: 로컬 Whisper 모델 사용 (API 비용 없음)
- 🍎 **Apple Silicon GPU 가속**: `mlx-whisper`로 Metal GPU 활용 — 82분 영상 기준 faster-whisper 대비 **6.3배** 빠름 (실측, base 모델 / M1 Max)
- ⚡ **다층 최적화**: zero-copy ffmpeg 청킹 + 원본 오디오 스트림 저장 + 워커별 모델 1회 로드
- 🤖 **Claude Sonnet 4.6 요약**: Prompt Caching으로 반복 호출 시 토큰 비용 절감
- 🌍 **요약 다국어**: 한국어 / 영어 / 중국어 (그 외 언어는 한국어로 폴백)
- 💻 **CLI 인터페이스**: 명령줄에서 간단하게 사용
- 🎯 **요약 전용 모드**: 이미 전사된 파일에서 요약만 빠르게 생성

---

## 설치

### 방법 1: Homebrew (권장 - macOS/Linux)

```bash
# Tap 추가
brew tap SaraHan774/ytt

# 설치 (ffmpeg 자동 설치됨)
brew install ytt

# 대화형 설정 실행
ytt-init
```

### 방법 2: pip (수동 설치)

#### 1. ffmpeg 설치 (필수)

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# Windows (Chocolatey)
choco install ffmpeg
```

#### 2. Python 패키지 설치

```bash
# 저장소 클론
git clone <repository-url>
cd ytt

# 패키지 설치
pip install -r requirements.txt
pip install -e .

# (선택) Apple Silicon에서 Metal GPU 가속 전사 활성화
pip install -e '.[mlx]'
```

#### 3. 대화형 설정 (권장)

설치 후 처음 `ytt`를 실행하면 자동으로 대화형 설정 마법사가 실행됩니다:

```bash
# 첫 실행 시 자동으로 설정 진행
ytt

# 또는 수동으로 설정 실행
ytt-init

# 설정 초기화 및 재설정
ytt-init --reset
```

**대화형 설정에서 구성하는 항목:**
- ✅ 시스템 환경 확인 (ffmpeg, GPU 등)
- 🔑 Anthropic API 키 설정
- 🌍 기본 언어 선택 (한국어/영어/중국어)
- 🎤 기본 Whisper 모델 크기
- ⚙️ 자동 요약 활성화 여부

#### 4. 수동 API 키 설정 (선택)

```bash
# 환경 변수로 설정
export ANTHROPIC_API_KEY="your-api-key"

# 또는 CLI 명령어로 설정
ytt-config set-api-key "your-api-key"

# 설정 확인
ytt-config show-config

# 또는 .env 파일 생성
echo "ANTHROPIC_API_KEY=your-api-key" > .env
```

---

## 사용 방법

### 기본 사용법

```bash
# 전사만 생성 (transcript.txt 하나만 생성)
ytt "https://youtube.com/watch?v=xxx" ./output

# 전사 + 요약 (transcript.txt + summary.txt)
ytt "https://youtube.com/watch?v=xxx" ./output --summarize

# 타임스탬프 파일도 함께 저장
ytt "https://youtube.com/watch?v=xxx" ./output --timestamps

# JSON + 메타데이터 파일도 함께 저장
ytt "https://youtube.com/watch?v=xxx" ./output --json --metadata

# 언어 수동 지정 + 요약
ytt "https://youtube.com/watch?v=xxx" ./output -l ko --summarize

# 영어 영상 + 영어 요약
ytt "https://youtube.com/watch?v=xxx" ./output -l en --summarize

# Apple Silicon에서 MLX 백엔드 명시 (mlx-whisper 설치 필요)
ytt "https://youtube.com/watch?v=xxx" ./output --backend mlx
```

### 요약 전용 모드

이미 전사가 완료된 디렉토리에서 요약만 다시 생성하려면 `transcript.json`이 필요합니다. **`--summarize`만으로는 JSON이 저장되지 않으므로** (v1.4.0 이후), 처음 실행 시 `--json`을 함께 지정해야 재사용 가능합니다.

```bash
# 처음 실행 시 transcript.json까지 저장 (재사용 의도)
ytt "URL" ./output --summarize --json

# 나중에 요약만 다시 (다른 언어, 모델 변경 등)
ytt ./output --summarize-only -l en
```

### 옵션 일람

가장 정확한 최신 옵션 목록은 항상 `ytt --help`에서 확인하세요. 아래는 v1.4.1 기준.

| 옵션 | 설명 | 기본값 |
|---|---|---|
| `--summarize`, `-s` | Claude로 요약 생성 (`summary.txt` 저장) | off |
| `--summarize-only` | 기존 `transcript.json`으로 요약만 생성 (URL 불필요) | off |
| `--timestamps` | 타임스탬프 포함 전사 추가 저장 | off |
| `--json` | 구조화된 JSON(`transcript.json`) 추가 저장. `--summarize-only` 재실행에 필요 | off |
| `--metadata` | 영상 메타데이터(`metadata.json`) 추가 저장 | off |
| `--model-size`, `-m` | Whisper 모델 (`tiny`/`base`/`small`/`medium`/`large`) | `base` |
| `--language`, `-l` | 언어 코드 (`ko`/`en`/`zh`/`auto` 등). 요약은 ko/en/zh만 지원 | `auto` |
| `--backend` | 전사 백엔드 (`auto`/`mlx`/`faster-whisper`). `auto`는 Apple Silicon에서 mlx 자동 선택 | `auto` |
| `--fast` | 빠른 모드 (`beam_size=1`, 청크 300초, condition off). MLX 미사용 시 ~1.6배 빠름 | off |
| `--vad-aggressive` | 더 짧은 무음 임계값(300ms)로 전사 가속. 품질 소폭 영향 | off |
| `--force-librosa` | ffmpeg 비활성화하고 librosa로 청킹 (디버그용) | off |
| `--no-cache` | 요약 Prompt Caching 비활성화 | off |
| `--no-cleanup` | `raw_audio/`, `chunks/` 임시 디렉토리 유지 | off |
| `--verbose`, `-v` | DEBUG 로그 출력 | off |
| `--version` | 버전 출력 후 종료 | — |

`--backend` 동작:
- `auto` (기본): Apple Silicon + `mlx-whisper` 설치 시 → MLX, 그 외 → faster-whisper
- `mlx`: 강제 MLX (조건 미충족 시 faster-whisper로 자동 폴백, warning 로그)
- `faster-whisper`: 강제 CPU/CUDA

---

## 출력 파일

기본 실행 시 `transcript.txt` 하나만 생성됩니다. 나머지는 옵션으로 선택적으로 생성됩니다.

```
output/
├── transcript.txt                    # 영상 정보 + 전사 텍스트 (항상 생성)
├── transcript_with_timestamps.txt    # 타임스탬프 포함 전사 (--timestamps)
├── transcript.json                   # JSON 형식 데이터 (--json)
├── metadata.json                     # 영상 메타데이터 (--metadata)
└── summary.txt                       # AI 요약 (--summarize)
```

`transcript.txt`에는 영상 제목, URL, 업로더, 재생 시간이 헤더로 포함됩니다.

---

## 예시

### 1. 한국어 강의 전사 및 요약

```bash
ytt "https://youtube.com/watch?v=lecture123" ./lectures/ai-basics \
    --summarize \
    --model-size medium \
    --language ko
```

### 2. 영어 팟캐스트 전사 (모든 파일 저장)

```bash
ytt "https://youtube.com/watch?v=podcast456" ./podcasts/ep01 \
    -m tiny \
    -l en \
    --timestamps --json --metadata
```

### 3. 배치 처리 스크립트

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

## 테스트

```bash
# 전체 테스트
pytest

# 커버리지 포함
pytest --cov=ytt

# 단위 테스트만
pytest -m "not integration"

# 통합 테스트만
pytest -m integration
```

---

## 비용

- **음성 전사**: 무료 (로컬 처리)
- **요약**: Claude API 사용량에 따름 (약 0.5-2 tokens per character)

---

## 처리 시간 / 성능

### 실측 벤치마크 (M1 Max, base 모델, 82분 40초 영상, v1.4.1)

| Backend | 청킹 | 전사 | 합계 | vs faster-whisper |
|---|---:|---:|---:|---:|
| MLX (`--backend mlx`) | 0.7s | 64.1s | **64.8s** | **6.3배 빠름** |
| faster-whisper (default) | 0.7s | 408.1s | 408.9s | 1.0x |
| faster-whisper + `--fast` | 0.8s | 248.0s | 248.8s | 1.6배 빠름 |

> 참고: MLX 백엔드의 가속 폭은 영상 길이와 모델 크기에 따라 변동합니다. 짧은 영상(10분 이하)에서는 ~2배, 긴 영상(60분 이상)에서는 6~7배 정도가 일반적입니다. 상위 mlx-whisper 프로젝트의 8–15배 카피는 large 모델 또는 다른 하드웨어 기준입니다.

### 핵심 최적화 동작

| 최적화 | 효과 | 활성화 |
|---|---|---|
| **MLX 백엔드** (Apple Silicon) | Metal GPU 가속, 6배+ 빠름 | `--backend auto` 또는 `--backend mlx` (`pip install 'ytt[mlx]'` 필요) |
| **Zero-copy ffmpeg 청킹** | 청킹 시간 ~5배 단축, 메모리 80%↓ | ffmpeg 설치 시 자동 |
| **Thread-local 모델 캐시** | 워커당 Whisper 모델 1회만 로드 | 자동 |
| **원본 오디오 스트림** | mp3 재인코딩 생략 (m4a/webm/opus 직접 사용) | 자동 |
| **Prompt Caching** | Claude 시스템 프롬프트 캐싱 (5분 TTL) | `--summarize` 사용 시 자동, `--no-cache`로 끔 |
| **`--fast` 모드** | beam=1, 청크 300s, condition off | `--fast` |
| **Aggressive VAD** | 무음 임계값 500ms → 300ms | `--vad-aggressive` |

긴 영상 처리 권장 조합:
```bash
# Apple Silicon: MLX 자동 선택, 추가 옵션 거의 불필요
ytt "URL" ./output --summarize

# Linux/Intel Mac/CUDA 없는 환경: --fast로 가속
ytt "URL" ./output --fast --summarize
```

---

## 문제 해결

### MLX 백엔드를 쓰고 싶은데 faster-whisper로 폴백됨

```bash
# 설치 확인
python -c "import mlx_whisper; print('mlx-whisper OK')"

# 미설치면
pip install 'ytt[mlx]'

# 강제 지정 (Apple Silicon만 가능)
ytt "URL" ./output --backend mlx
```

조건: Apple Silicon (M1/M2/M3/M4) + macOS + `mlx-whisper` 설치. 비-Apple Silicon에서 `--backend mlx`를 지정하면 자동으로 faster-whisper로 폴백되며 warning 로그가 남습니다.

### CUDA가 감지되지 않음 (Linux/Windows)

```bash
# CUDA 확인
python -c "import torch; print('CUDA:', torch.cuda.is_available())"

# CPU 강제 실행 (CUDA 환경에서)
CUDA_VISIBLE_DEVICES="" ytt "URL" ./output
```

### API 키 오류

```bash
# API 키 확인
echo $ANTHROPIC_API_KEY

# 테스트
python -c "import os; print(os.getenv('ANTHROPIC_API_KEY'))"
```

### 메모리 부족

```bash
# 더 작은 모델 사용
ytt "URL" ./output -m tiny
```

---

## 상세 문서

- [CHANGELOG.md](CHANGELOG.md) — 버전별 변경사항
- [CLAUDE.md](CLAUDE.md) — AI 코딩 에이전트용 진입 가이드 (코드 구조, 동작 정확한 설명)
- [HOMEBREW.md](HOMEBREW.md) — Homebrew 배포 절차
- [USAGE_CLI.md](USAGE_CLI.md) — 추가 사용 예시 (간소화됨, 옵션 일람은 본 README가 정본)
- [CLI_DESIGN.md](CLI_DESIGN.md) — 초기 설계 제안서 (역사적 자료, 현 코드와 다를 수 있음)

---

## 라이선스

Apache License 2.0

---

## 기여

이슈와 PR은 언제나 환영합니다!
