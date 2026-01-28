# YTT MCP Server 설정 가이드

Claude Desktop에서 YouTube Transcript Tool (ytt)을 MCP를 통해 사용하기 위한 설정 가이드입니다.

## 전제 조건

1. **ytt 설치 완료**
   ```bash
   brew install ytt
   # 또는
   pip install -e .
   ```

2. **ytt 초기 설정 완료**
   ```bash
   ytt-init
   ```

3. **Claude Desktop 설치**
   - [Claude Desktop 다운로드](https://claude.ai/download)

## 설치 순서

### 1. ytt MCP 서버 활성화

ytt 1.1.0 버전부터 MCP 서버가 내장되어 있습니다.

```bash
# 버전 확인
ytt --version  # 1.1.0 이상이어야 함

# MCP 서버 테스트
ytt-mcp-server --version
```

### 2. Claude Desktop 설정

#### macOS

1. Claude Desktop 설정 파일 열기:
   ```bash
   code ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```

2. 다음 내용 추가:
   ```json
   {
     "mcpServers": {
       "ytt": {
         "command": "ytt-mcp-server"
       }
     }
   }
   ```

#### Linux

1. 설정 파일 경로: `~/.config/Claude/claude_desktop_config.json`

2. 동일한 내용 추가

#### Windows

1. 설정 파일 경로: `%APPDATA%\Claude\claude_desktop_config.json`

2. 동일한 내용 추가

### 3. Claude Desktop 재시작

설정 후 Claude Desktop을 완전히 종료하고 다시 시작합니다.

## 사용 방법

### 기본 사용 예시

Claude Desktop에서 다음과 같이 요청하세요:

```
User: "https://youtube.com/watch?v=dQw4w9WgXcQ 이 영상 요약해줘"

Claude: [ytt_transcribe_and_summarize 도구 자동 실행]
이 영상은 다음과 같은 내용을 담고 있습니다:

• 첫 번째 주요 포인트...
• 두 번째 주요 포인트...
• 세 번째 주요 포인트...

TL;DR: 핵심 요약...
```

### 고급 사용 예시

```
# 특정 모델 크기 지정
"이 영상을 medium 모델로 전사해줘: [URL]"

# 다른 언어로 요약
"이 한국어 영상을 영어로 요약해줘: [URL]"

# 전사만 수행
"이 영상 전사만 해줘 (요약은 필요없어): [URL]"

# 기존 전사 파일 재요약
"/Users/gahee/output 이 경로의 전사를 중국어로 다시 요약해줘"
```

## 사용 가능한 도구

Claude가 자동으로 선택하지만, 다음 도구들을 사용할 수 있습니다:

### 1. ytt_transcribe_and_summarize (가장 자주 사용)
- YouTube URL → 전사 + 요약
- 옵션: model_size, language

### 2. ytt_transcribe
- YouTube URL → 전사만
- 옵션: model_size, language

### 3. ytt_summarize
- 기존 전사 → 요약
- 옵션: language

### 4. ytt_read_transcript
- 전사 파일 읽기
- 옵션: include_timestamps

### 5. ytt_get_config
- 현재 ytt 설정 확인

## 문제 해결

### MCP 서버가 연결되지 않음

**증상:** Claude Desktop에서 ytt 도구를 사용할 수 없음

**해결:**
1. 설정 파일 확인
   ```bash
   cat ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```

2. ytt-mcp-server 실행 가능 여부 확인
   ```bash
   which ytt-mcp-server
   ytt-mcp-server --help
   ```

3. Claude Desktop 로그 확인
   ```bash
   tail -f ~/Library/Logs/Claude/mcp*.log
   ```

### API 키 오류

**증상:** "ANTHROPIC_API_KEY not found" 오류

**해결:**
1. ytt 설정 확인
   ```bash
   ytt-config show-config
   ```

2. API 키 재설정
   ```bash
   ytt-config set-api-key "your-key"
   ```

3. 환경 변수 설정 (옵션)
   ```json
   {
     "mcpServers": {
       "ytt": {
         "command": "ytt-mcp-server",
         "env": {
           "ANTHROPIC_API_KEY": "sk-ant-..."
         }
       }
     }
   }
   ```

### 전사가 너무 느림

**해결:**
1. 더 작은 모델 사용 요청
   ```
   "이 영상을 tiny 모델로 빠르게 전사해줘"
   ```

2. GPU 사용 확인
   ```bash
   python -c "import torch; print(torch.cuda.is_available())"
   ```

### ffmpeg 오류

**증상:** "ffmpeg not found" 오류

**해결:**
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# Windows
choco install ffmpeg
```

## 환경 변수 설정 (옵션)

MCP 서버에 추가 환경 변수를 전달할 수 있습니다:

```json
{
  "mcpServers": {
    "ytt": {
      "command": "ytt-mcp-server",
      "env": {
        "YTT_DEFAULT_MODEL": "medium",
        "YTT_DEFAULT_LANGUAGE": "ko",
        "YTT_OUTPUT_DIR": "/Users/gahee/ytt-outputs"
      }
    }
  }
}
```

## 출력 파일 위치

MCP를 통해 처리된 파일들은 다음 위치에 저장됩니다:

- **macOS/Linux:** `/tmp/ytt-mcp/video_[hash]/`
- **Windows:** `%TEMP%\ytt-mcp\video_[hash]\`

각 디렉토리에는:
```
video_123456/
├── transcript.txt                    # 평문 전사
├── transcript_with_timestamps.txt    # 타임스탬프 포함
├── transcript.json                   # JSON 데이터
├── metadata.json                     # 영상 메타데이터
└── summary.txt                       # 요약 (생성된 경우)
```

## 성능 팁

### 빠른 전사를 위해
- `tiny` 모델 사용 (정확도는 낮지만 매우 빠름)
- GPU 활성화 확인

### 고품질 전사를 위해
- `medium` 또는 `large` 모델 사용
- 충분한 시간 확보 (긴 영상의 경우)

### 요약 품질 향상
- 전사 시 올바른 언어 지정
- 요약 언어를 명확히 지정

## 보안 주의사항

1. **API 키 보호**
   - 설정 파일에 API 키 직접 저장 시 권한 확인
   - 환경 변수 사용 권장

2. **임시 파일**
   - 민감한 영상의 경우 처리 후 수동 삭제
   ```bash
   rm -rf /tmp/ytt-mcp/
   ```

## 업데이트

ytt 업데이트 시 MCP 서버도 자동으로 업데이트됩니다:

```bash
# Homebrew
brew upgrade ytt

# pip
pip install -e . --upgrade
```

업데이트 후 Claude Desktop 재시작 필요.

## 예시 워크플로우

### 연구용 영상 분석
```
1. "이 강의 영상 전사해줘: [URL]"
2. Claude가 전사 완료
3. "방금 전사한 내용에서 핵심 개념 5가지 추출해줘"
4. "이걸 마크다운 표로 정리해줘"
```

### 다국어 콘텐츠
```
1. "이 영어 영상을 전사하고 한국어로 요약해줘: [URL]"
2. 또는: "이 한국어 영상을 전사하고 영어와 중국어로 각각 요약해줘"
```

### 배치 처리
```
1. "다음 3개 영상을 모두 전사하고 요약해줘"
2. Claude가 순차적으로 처리
3. "세 영상의 공통점과 차이점을 분석해줘"
```

## 피드백 및 지원

- GitHub Issues: https://github.com/SaraHan774/ytt/issues
- 문서: https://github.com/SaraHan774/ytt

## 다음 단계

MCP 설정이 완료되었다면:
1. 간단한 짧은 영상으로 테스트
2. 다양한 언어와 모델 크기 실험
3. 워크플로우에 통합
