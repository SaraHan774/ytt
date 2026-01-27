# YouTube Transcript Tool (ytt)

YouTube 영상을 자동으로 전사하고 요약하는 CLI 도구입니다.

## 주요 특징

- 🆓 **완전 무료 전사**: 로컬 Whisper 모델 사용 (API 비용 없음)
- 🚀 **GPU 가속**: faster-whisper로 5-10배 빠른 처리
- 🤖 **최신 Claude Sonnet 4.5**: 고품질 요약
- 🌍 **다국어 지원**: 한국어, 영어, 일본어 요약 지원
- 💻 **CLI 인터페이스**: 명령줄에서 간단하게 사용
- ⚡ **요약 전용 모드**: 이미 전사된 파일에서 요약만 빠르게 생성

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
- 🌍 기본 언어 선택 (한국어/영어/일본어)
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
# 전사만 생성
ytt "https://youtube.com/watch?v=xxx" ./output

# 전사 + 요약
ytt "https://youtube.com/watch?v=xxx" ./output --summarize

# 모델 크기 지정 (tiny/base/small/medium/large)
ytt "https://youtube.com/watch?v=xxx" ./output -m medium

# 언어 지정 (한국어)
ytt "https://youtube.com/watch?v=xxx" ./output -l ko --summarize

# 영어 요약
ytt "https://youtube.com/watch?v=xxx" ./output -l en --summarize
```

### 요약 전용 모드

이미 전사가 완료된 디렉토리에서 요약만 생성:

```bash
# 먼저 전사만 빠르게 생성 (tiny 모델)
ytt "URL" ./output -m tiny

# 나중에 요약만 추가
ytt ./output --summarize-only -l ko
```

### 상세 옵션

```bash
ytt --help
```

**주요 옵션:**
- `--summarize, -s`: 요약도 함께 생성
- `--summarize-only`: 기존 transcript로 요약만 생성
- `--model-size, -m`: Whisper 모델 크기 (기본값: base)
- `--language, -l`: 언어 지정 (기본값: ko)
- `--no-cleanup`: 임시 파일 삭제하지 않음
- `--verbose, -v`: 상세 로그 출력

---

## 출력 파일

```
output/
├── transcript.txt                    # 평문 전사
├── transcript_with_timestamps.txt    # 타임스탬프 포함 전사
├── transcript.json                   # JSON 형식 데이터
├── metadata.json                     # 영상 메타데이터
└── summary.txt                       # AI 요약 (--summarize 옵션 시)
```

---

## 예시

### 1. 한국어 강의 전사 및 요약

```bash
ytt "https://youtube.com/watch?v=lecture123" ./lectures/ai-basics \
    --summarize \
    --model-size medium \
    --language ko
```

### 2. 영어 팟캐스트 빠른 전사

```bash
ytt "https://youtube.com/watch?v=podcast456" ./podcasts/ep01 \
    -m tiny \
    -l en
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

MIT License

---

## 기여

이슈와 PR은 언제나 환영합니다!
