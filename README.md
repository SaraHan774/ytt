# YouTube Transcript Tool (ytt)

**한국어** | [English](README.en.md) | [中文](README.zh.md)

YouTube 영상을 자동으로 전사하고 요약하는 CLI 도구입니다.

## 주요 특징

- 🆓 **완전 무료 전사**: 로컬 Whisper 모델 사용 (API 비용 없음)
- 🚀 **GPU 가속**: faster-whisper로 5-10배 빠른 처리
- 🍎 **Apple Silicon 최적화**: MLX Whisper 백엔드로 Metal GPU 가속 (faster-whisper CPU 대비 8-15배)
- ⚡ **극한 최적화**: ffmpeg 청킹 + 원본 스트림 저장 + 워커별 모델 1회 로드
- 🤖 **최신 Claude Sonnet 4.6**: 고품질 요약, Prompt Caching으로 API 비용 90% 절감
- 🌍 **다국어 지원**: 한국어, 영어, 중국어 요약 지원
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

이미 전사가 완료된 디렉토리에서 요약만 생성:

```bash
# 먼저 전사 + JSON 저장 (--summarize-only 재사용을 위해 --json 필요)
ytt "URL" ./output -m tiny --json

# 또는 --summarize로 처음 실행하면 transcript.json 자동 생성됨
ytt "URL" ./output --summarize

# 나중에 요약만 추가
ytt ./output --summarize-only -l ko
```

### 상세 옵션

```bash
ytt --help
```

**주요 옵션:**
- `--summarize, -s`: 요약도 함께 생성 (transcript.json 자동 저장)
- `--summarize-only`: 기존 transcript.json으로 요약만 생성
- `--timestamps`: 타임스탬프 포함 전사 파일도 저장 (transcript_with_timestamps.txt)
- `--json`: 구조화된 JSON 파일도 저장 (transcript.json)
- `--metadata`: 영상 메타데이터 파일도 저장 (metadata.json)
- `--model-size, -m`: Whisper 모델 크기 (기본값: base)
- `--language, -l`: 언어 지정 (기본값: auto - 자동 감지)
- `--no-cleanup`: 임시 파일 삭제하지 않음
- `--no-cache`: 프롬프트 캐싱 비활성화 (요약 시)
- `--vad-aggressive`: Aggressive VAD 사용 (빠른 전사, 짧은 무음 포함 가능)
- `--force-librosa`: librosa 청킹 강제 사용 (ffmpeg 비활성화)
- `--verbose, -v`: 상세 로그 출력

---

## 출력 파일

기본 실행 시 `transcript.txt` 하나만 생성됩니다. 나머지는 옵션으로 선택적으로 생성됩니다.

```
output/
├── transcript.txt                    # 영상 정보 + 전사 텍스트 (항상 생성)
├── transcript_with_timestamps.txt    # 타임스탬프 포함 전사 (--timestamps)
├── transcript.json                   # JSON 형식 데이터 (--json 또는 --summarize)
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

## 처리 시간

- **tiny 모델**: 약 실시간의 1/10 속도
- **base 모델**: 약 실시간의 1/5 속도 (권장)
- **medium 모델**: 약 실시간의 1/3 속도
- **large 모델**: 약 실시간과 비슷

예시: 16분 영상 → 약 3-4분 (base 모델, GPU 사용 시)

---

## 🚀 성능 최적화 (v1.1.0+)

ytt는 대용량 영상 처리를 위한 다양한 최적화를 제공합니다:

### 1. ffmpeg 직접 청킹 (자동 활성화)

**효과**: 메모리 사용량 80-90% 감소, 청킹 속도 60배 향상

**작동 방식**:
- ffmpeg가 설치되어 있으면 자동으로 사용
- 재인코딩 없이 복사만 수행 (zero-copy)
- librosa 대비 메모리 효율 극대화

**설치 확인**:
```bash
# ffmpeg 설치 여부 확인
ffmpeg -version

# macOS에서 설치
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg
```

**수동 비활성화** (필요시):
```bash
# librosa 청킹 강제 사용
ytt "URL" ./output --force-librosa
```

### 2. Prompt Caching (자동 활성화)

**효과**: API 비용 90% 절감 (Claude API 사용 시)

**작동 방식**:
- 시스템 프롬프트가 5분간 캐시됨
- 2번째 청크부터 캐시 재사용 (토큰 비용 절감)
- 품질 저하 없음

**수동 비활성화** (필요시):
```bash
# 프롬프트 캐싱 비활성화
ytt "URL" ./output --summarize --no-cache
```

### 3. Aggressive VAD (선택적)

**효과**: 전사 속도 20-30% 향상

**작동 방식**:
- 더 짧은 무음 구간에서 스킵 (500ms → 300ms)
- 빠른 전사, 품질 저하 최소화

**사용 방법**:
```bash
# Aggressive VAD 활성화
ytt "URL" ./output --vad-aggressive
```

### 성능 벤치마크

**30분 영상 처리 (base 모델, GPU)**

| 최적화 | 처리 시간 | 메모리 | API 비용 |
|--------|----------|--------|----------|
| v1.0.x (최적화 전) | 13.9분 | 800MB | $0.80 |
| v1.1.0 (최적화 후) | 8.3분 | 150MB | $0.08 |
| **개선율** | **1.7배** | **81%↓** | **90%↓** |

**60분 영상 처리**

| 최적화 | 처리 시간 | 메모리 | API 비용 |
|--------|----------|--------|----------|
| v1.0.x | 27.8분 | 1600MB | $1.60 |
| v1.1.0 | 15.9분 | 180MB | $0.16 |
| **개선율** | **1.7배** | **89%↓** | **90%↓** |

### 최적 사용 예시

```bash
# 최대 성능으로 긴 영상 처리
ytt "https://youtube.com/watch?v=xxx" ./output \
    --summarize \
    --vad-aggressive \
    --model-size base

# 메모리 제한 환경 (ffmpeg 자동 사용)
ytt "https://youtube.com/watch?v=xxx" ./output

# 비용 절약 (캐싱 자동 활성화)
ytt "https://youtube.com/watch?v=xxx" ./output --summarize
```

---

## 문제 해결

### GPU가 감지되지 않음

```bash
# CUDA 확인
python -c "import torch; print('CUDA:', torch.cuda.is_available())"

# CPU 강제 실행
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

- [CLI 사용 가이드](USAGE_CLI.md) - 상세한 사용법과 예시
- [CLI 디자인](CLI_DESIGN.md) - 아키텍처 및 설계 문서

---

## 라이선스

Apache License 2.0

---

## 기여

이슈와 PR은 언제나 환영합니다!
