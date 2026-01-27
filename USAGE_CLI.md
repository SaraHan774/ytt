# YouTube Transcript Tool (ytt) - CLI 사용 가이드

## 빠른 시작

### 1. 설치

```bash
# 저장소 클론
git clone https://github.com/SaraHan774/ytt.git
cd ytt

# 패키지 설치 (개발 모드)
pip install -e .

# 또는 일반 설치
pip install .
```

### 2. 첫 실행

```bash
# 가장 간단한 사용
ytt "https://youtube.com/watch?v=dQw4w9WgXcQ" ./output
```

이렇게만 하면:
- YouTube 영상 다운로드
- 음성 전사 (Whisper base 모델)
- `./output/` 디렉토리에 전사 파일 저장

---

## 명령어 옵션

### 기본 형식

```bash
ytt <youtube_url> <output_dir> [OPTIONS]
```

### 옵션 상세

#### `--summarize, -s`
요약도 함께 생성 (Claude API 필요)

```bash
ytt "URL" ./output --summarize
ytt "URL" ./output -s
```

#### `--model-size, -m`
Whisper 모델 크기 선택

```bash
ytt "URL" ./output -m tiny      # 가장 빠름, 정확도 낮음
ytt "URL" ./output -m base      # 균형 (기본값)
ytt "URL" ./output -m small     # 더 정확
ytt "URL" ./output -m medium    # 매우 정확
ytt "URL" ./output -m large     # 최고 정확도
```

**권장:**
- 빠른 테스트: `tiny`
- 일반 사용: `base` (기본값)
- 고품질: `medium` 또는 `large`

#### `--language, -l`
언어 지정

```bash
ytt "URL" ./output -l ko    # 한국어 (기본값)
ytt "URL" ./output -l en    # 영어
ytt "URL" ./output -l ja    # 일본어
ytt "URL" ./output -l auto  # 자동 감지
```

#### `--no-cleanup`
임시 파일 유지 (디버깅용)

```bash
ytt "URL" ./output --no-cleanup
```

이렇게 하면 `raw_audio/`와 `chunks/` 디렉토리가 삭제되지 않습니다.

#### `--verbose, -v`
상세 로그 출력

```bash
ytt "URL" ./output -v
ytt "URL" ./output --verbose
```

---

## 실전 예시

### 1. 한국어 강의 전사 (요약 포함)

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

### 3. 여러 영상 배치 처리

```bash
#!/bin/bash
# urls.txt 파일에 YouTube URL 목록

while IFS= read -r url; do
  timestamp=$(date +%Y%m%d_%H%M%S)
  ytt "$url" "./batch/$timestamp" --summarize -v
  echo "✓ Processed: $url"
done < urls.txt
```

### 4. 자동화 스크립트

```bash
#!/bin/bash
# auto-transcribe.sh

URL=$1
OUTPUT_DIR="./transcripts/$(date +%Y-%m-%d)"

mkdir -p "$OUTPUT_DIR"

ytt "$URL" "$OUTPUT_DIR" \
    --summarize \
    --model-size base \
    --verbose

echo "✓ 완료: $OUTPUT_DIR"
open "$OUTPUT_DIR"  # macOS에서 폴더 열기
```

사용:
```bash
chmod +x auto-transcribe.sh
./auto-transcribe.sh "https://youtube.com/watch?v=xxx"
```

---

## API 키 관리

### 방법 1: 환경 변수 (권장)

```bash
# ~/.bashrc 또는 ~/.zshrc에 추가
export ANTHROPIC_API_KEY="sk-ant-..."

# 또는 한 번만 사용
ANTHROPIC_API_KEY="sk-ant-..." ytt "URL" ./output --summarize
```

### 방법 2: .env 파일

```bash
# 프로젝트 루트에 .env 파일 생성
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env

# ytt가 자동으로 .env 파일을 읽음
ytt "URL" ./output --summarize
```

### 방법 3: 설정 파일 (미래 기능)

```bash
# API 키 저장
ytt config set-api-key "sk-ant-..."

# 확인
ytt config show-config
```

---

## 출력 파일 설명

### transcript.txt
평문 전사 텍스트 (타임스탬프 없음)

```
# 영상 제목

안녕하세요. 오늘은 AI에 대해 이야기하겠습니다.
인공지능은 최근 빠르게 발전하고 있습니다.
...
```

### transcript_with_timestamps.txt
타임스탬프 포함 전사

```
# 영상 제목

[00:00:00 -> 00:00:03] 안녕하세요. 오늘은 AI에 대해 이야기하겠습니다.
[00:00:03 -> 00:00:08] 인공지능은 최근 빠르게 발전하고 있습니다.
...
```

### transcript.json
구조화된 JSON 데이터

```json
{
  "title": "영상 제목",
  "chunks": [
    {
      "chunk_id": 0,
      "file": "segment_000.mp3",
      "language": "ko",
      "segments": [
        {
          "start": 0.0,
          "end": 3.2,
          "text": "안녕하세요. 오늘은 AI에 대해 이야기하겠습니다."
        }
      ]
    }
  ]
}
```

### metadata.json
영상 메타데이터

```json
{
  "title": "영상 제목",
  "duration": 1234.56,
  "url": "https://youtube.com/watch?v=xxx",
  "uploader": "채널 이름"
}
```

### summary.txt (--summarize 옵션 시)
AI 요약

```
=== 상세 요약 ===

• 첫 번째 주요 포인트
• 두 번째 주요 포인트
...

=== TL;DR ===

이 영상은 AI의 발전과 미래에 대해 설명합니다.
```

---

## 문제 해결

### GPU가 감지되지 않음

```bash
# CUDA 확인
python -c "import torch; print('CUDA:', torch.cuda.is_available())"

# CPU로 강제 실행 (ytt/core.py 수정 필요)
# 또는 환경 변수
CUDA_VISIBLE_DEVICES="" ytt "URL" ./output
```

### ffmpeg를 찾을 수 없음

```bash
# 설치 확인
ffmpeg -version

# macOS
brew install ffmpeg

# Ubuntu
sudo apt-get install ffmpeg

# Windows (Chocolatey)
choco install ffmpeg
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

# 또는 청킹 크기 조정 (코드 수정 필요)
```

---

## 팁 & 트릭

### 1. 빠른 프리뷰

```bash
# tiny 모델로 빠르게 미리보기
ytt "URL" ./preview -m tiny --no-cleanup
head -20 ./preview/transcript.txt
```

### 2. 로그 저장

```bash
ytt "URL" ./output -v 2>&1 | tee transcript.log
```

### 3. Cron으로 자동화

```bash
# crontab -e
0 2 * * * /path/to/ytt "PLAYLIST_URL" /path/to/output --summarize
```

### 4. 파이프라인

```bash
# transcript만 추출
ytt "URL" ./output && cat ./output/transcript.txt

# 특정 단어 검색
ytt "URL" ./output && grep "AI" ./output/transcript.txt

# 여러 작업 연결
ytt "URL" ./output && \
  cat ./output/summary.txt | mail -s "Summary" user@example.com
```

---

## 고급 사용

### Python 스크립트에서 사용

```python
from ytt import core
from pathlib import Path

# 영상 다운로드
result = core.download_youtube("URL", Path("./output"))

# 전사
chunks = core.chunk_audio(result['audio_path'], Path("./output"))
transcripts = core.transcribe_audio(chunks, model_size="base")

# 저장
core.save_transcripts(transcripts, Path("./output"), result['title'])
```

### 커스텀 전처리

```python
import ytt.core as core

# 전사 결과 수정
transcripts = core.transcribe_audio(...)
for chunk in transcripts:
    for seg in chunk['segments']:
        seg['text'] = seg['text'].upper()  # 대문자 변환

core.save_transcripts(transcripts, output_dir, title)
```

---

## 성능 최적화

### GPU 메모리 최적화

```python
# ytt/core.py 수정
return WhisperModel(
    model_size,
    device="cuda",
    compute_type="float16",  # 또는 "int8_float16"
    num_workers=2  # 병렬 처리
)
```

### 배치 처리 최적화

```bash
# 여러 영상을 순차 처리 (한 번에 하나씩)
for url in $(cat urls.txt); do
    ytt "$url" "./output/$(basename $url)" -m base
done

# 병렬 처리 (주의: GPU 메모리 부족 가능)
cat urls.txt | xargs -P 2 -I {} ytt {} ./output/$(basename {})
```

---

## 라이선스

MIT License
