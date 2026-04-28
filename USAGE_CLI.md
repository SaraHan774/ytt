# `ytt` CLI 사용 노트

이 문서는 README 보조용 짧은 사용 팁입니다. 옵션 일람과 정본 동작 설명은 [README.md](README.md)와 `ytt --help`를 참고하세요. AI 코딩 에이전트는 [CLAUDE.md](CLAUDE.md)를 먼저 읽기를 권장합니다.

> 이전 버전의 USAGE_CLI.md(약 420줄)는 v1.0 시대 동작에 맞춰져 있어 v1.4 코드와 어긋나는 부분이 많아 축약했습니다. 가장 정확한 정보는 항상 `ytt --help`입니다.

## 빠른 시작

```bash
# Homebrew (가장 권장, macOS/Linux)
brew tap SaraHan774/ytt
brew install ytt
ytt-init   # 대화형 설정

# pip + 소스
pip install -e .
pip install -e '.[mlx]'   # Apple Silicon GPU 가속 추가

# 첫 실행 (자동 설정 마법사)
ytt "https://youtube.com/watch?v=dQw4w9WgXcQ" ./output
```

## 자주 쓰는 조합

```bash
# 전사만, 가장 단순
ytt "URL" ./output

# 전사 + 요약, 다음에 요약 재생성도 가능하도록 JSON 저장
ytt "URL" ./output --summarize --json

# Apple Silicon 명시 (auto가 보통 알아서 골라줌)
ytt "URL" ./output --backend mlx --summarize

# CPU만 있는 환경에서 속도 우선
ytt "URL" ./output --fast --summarize

# 큰 모델 + 영어 요약
ytt "URL" ./output -m medium -l en --summarize

# 기존 디렉토리에서 요약만 재생성
ytt ./output --summarize-only -l ko
```

## 출력 파일

| 파일 | 생성 조건 |
|---|---|
| `transcript.txt` | 항상 |
| `transcript_with_timestamps.txt` | `--timestamps` |
| `transcript.json` | `--json` (이게 있어야 `--summarize-only` 재실행 가능) |
| `metadata.json` | `--metadata` |
| `summary.txt` | `--summarize` |

## API 키 설정

```bash
# 환경 변수 (가장 흔함)
export ANTHROPIC_API_KEY="sk-ant-..."

# 또는 ytt-config 명령
ytt-config set-api-key "sk-ant-..."
ytt-config show-config

# 또는 .env 파일 (ytt가 자동 로드)
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env
```

## 자동화 예시

### 배치 처리 (urls.txt 한 줄씩)

```bash
while IFS= read -r url; do
  timestamp=$(date +%Y%m%d_%H%M%S)
  ytt "$url" "./batch/$timestamp" --summarize --json -v
done < urls.txt
```

### cron으로 정기 처리

```cron
# 매일 02:00에 정해진 URL 처리
0 2 * * * /opt/homebrew/bin/ytt "PLAYLIST_URL" /path/to/output --summarize --json
```

### 파이프라인

```bash
# 전사 후 특정 단어 검색
ytt "URL" ./output && grep "AI" ./output/transcript.txt

# 요약 결과를 메일로 전송
ytt "URL" ./output --summarize \
  && cat ./output/summary.txt | mail -s "Summary" me@example.com
```

## Python에서 직접 호출

```python
from pathlib import Path
from ytt import core

result = core.download_youtube("URL", Path("./output"))
chunks = core.chunk_audio(result['audio_path'], Path("./output"))
transcripts = core.transcribe_audio(
    chunks,
    model_size="base",
    language="en",        # 또는 None으로 자동 감지
    backend="auto",       # "auto" / "mlx" / "faster-whisper"
)
core.save_transcripts(transcripts, Path("./output"), result['title'], metadata=result)
```

## 디버그 팁

```bash
# 상세 로그 + 임시 파일 보존
ytt "URL" ./output -v --no-cleanup

# librosa 청킹 강제 (ffmpeg 문제 진단)
ytt "URL" ./output --force-librosa -v

# 로그를 파일로 저장
ytt "URL" ./output -v 2>&1 | tee transcript.log
```

## 자주 묻는 것

**Q. `--summarize`만 했더니 `--summarize-only`가 안 돼요.**
A. v1.4.0부터 `--summarize`는 `transcript.json`을 자동 생성하지 않습니다. 처음부터 `--summarize --json` 함께 실행하세요.

**Q. Apple Silicon인데 MLX가 안 쓰여요.**
A. `pip install 'ytt[mlx]'`로 별도 설치가 필요합니다. Brew formula에는 아직 번들되어 있지 않아요. 설치 후 `ytt --backend auto`가 자동 선택합니다.

**Q. 일본어 요약이 한국어로 나와요.**
A. 요약은 `ko`/`en`/`zh`만 지원합니다. 다른 언어는 한국어로 폴백되며 warning 로그가 남습니다.

**Q. 다운로드가 `Requested format is not available`로 실패해요.**
A. v1.4.0 이하 버전 문제. `brew upgrade ytt` 또는 `pip install -U ytt`로 v1.4.1+ 사용하세요.

## 더 보기

- [README.md](README.md) — 전체 옵션 일람, 벤치마크, 문제 해결
- [CHANGELOG.md](CHANGELOG.md) — 버전별 변경 이력
- [CLAUDE.md](CLAUDE.md) — AI 에이전트용 코드 가이드
- [HOMEBREW.md](HOMEBREW.md) — 패키징/배포 절차
