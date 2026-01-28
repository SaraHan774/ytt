# YTT MCP Server Design

## 개요

YouTube Transcript Tool (ytt)을 Claude Desktop에서 MCP (Model Context Protocol)를 통해 사용할 수 있도록 하는 MCP 서버 설계 문서입니다.

## 목표

- Claude가 YouTube 영상 URL을 받아 자동으로 전사 및 요약 수행
- 기존 ytt CLI의 모든 기능을 MCP 도구로 제공
- 사용자 친화적인 설치 및 설정 프로세스

## 아키텍처

### 구조 선택: Option A (ytt 패키지 내부에 MCP 모듈 추가)

```
ytt/
├── ytt/
│   ├── __init__.py
│   ├── core.py           # 기존 핵심 로직
│   ├── cli.py            # 기존 CLI
│   ├── config.py         # 기존 설정
│   ├── setup.py          # 기존 설정 마법사
│   └── mcp/              # 🆕 MCP 서버 모듈
│       ├── __init__.py
│       ├── server.py     # MCP 서버 메인
│       ├── tools.py      # MCP 도구 구현
│       └── utils.py      # 헬퍼 함수
├── setup.py              # ytt-mcp-server 엔트리포인트 추가
└── docs/
    └── MCP_SETUP.md      # MCP 설정 가이드
```

**선택 이유:**
- ytt 내부 함수 직접 호출 가능 (import ytt.core)
- 단일 패키지 설치로 CLI + MCP 모두 사용 가능
- 버전 관리 및 유지보수 단순화
- 의존성 공유

## MCP Tools 명세

### 1. `ytt_transcribe`

YouTube 영상을 전사합니다.

**Input Schema:**
```json
{
  "youtube_url": {
    "type": "string",
    "description": "YouTube video URL",
    "required": true
  },
  "model_size": {
    "type": "string",
    "enum": ["tiny", "base", "small", "medium", "large"],
    "description": "Whisper model size",
    "default": "base"
  },
  "language": {
    "type": "string",
    "description": "Language code (ko/en/zh/auto)",
    "default": "auto"
  }
}
```

**Output:**
```json
{
  "success": true,
  "transcript": "Full transcript text...",
  "transcript_with_timestamps": "...",
  "metadata": {
    "title": "Video title",
    "duration": 960,
    "language_detected": "ko"
  },
  "output_path": "/path/to/output"
}
```

### 2. `ytt_summarize`

전사된 텍스트를 요약합니다.

**Input Schema:**
```json
{
  "transcript_path": {
    "type": "string",
    "description": "Path to transcript directory or file",
    "required": true
  },
  "language": {
    "type": "string",
    "description": "Summary language (ko/en/zh)",
    "default": "ko"
  }
}
```

**Output:**
```json
{
  "success": true,
  "long_summary": "Detailed summary...",
  "short_summary": "TL;DR...",
  "summary_path": "/path/to/summary.txt"
}
```

### 3. `ytt_transcribe_and_summarize`

전사와 요약을 한 번에 수행합니다 (가장 자주 사용될 도구).

**Input Schema:**
```json
{
  "youtube_url": {
    "type": "string",
    "description": "YouTube video URL",
    "required": true
  },
  "model_size": {
    "type": "string",
    "enum": ["tiny", "base", "small", "medium", "large"],
    "default": "base"
  },
  "language": {
    "type": "string",
    "description": "Language for summary (ko/en/zh/auto)",
    "default": "auto"
  }
}
```

**Output:**
```json
{
  "success": true,
  "transcript": "Full transcript...",
  "metadata": {
    "title": "Video title",
    "duration": 960,
    "language_detected": "ko"
  },
  "summary": {
    "long": "Detailed summary...",
    "short": "TL;DR..."
  },
  "output_path": "/path/to/output"
}
```

### 4. `ytt_read_transcript`

이미 생성된 전사 파일을 읽습니다.

**Input Schema:**
```json
{
  "path": {
    "type": "string",
    "description": "Path to transcript file or directory",
    "required": true
  },
  "include_timestamps": {
    "type": "boolean",
    "description": "Include timestamps in output",
    "default": false
  }
}
```

**Output:**
```json
{
  "success": true,
  "transcript": "Full transcript text...",
  "metadata": {
    "title": "Video title",
    "duration": 960
  }
}
```

### 5. `ytt_get_config`

현재 ytt 설정을 조회합니다.

**Input Schema:**
```json
{}
```

**Output:**
```json
{
  "success": true,
  "config": {
    "default_language": "ko",
    "default_model_size": "base",
    "auto_summarize": false,
    "api_key_set": true
  },
  "config_path": "/path/to/config.json"
}
```

## 구현 상세

### server.py

```python
"""
YTT MCP Server
Claude Desktop에서 ytt를 사용할 수 있게 하는 MCP 서버
"""
import asyncio
import logging
from mcp.server import Server
from mcp.server.stdio import stdio_server
from .tools import (
    transcribe_tool,
    summarize_tool,
    transcribe_and_summarize_tool,
    read_transcript_tool,
    get_config_tool
)

logger = logging.getLogger(__name__)

async def main():
    """MCP 서버 메인 함수"""
    server = Server("ytt-mcp-server")

    # 도구 등록
    server.add_tool(transcribe_tool)
    server.add_tool(summarize_tool)
    server.add_tool(transcribe_and_summarize_tool)
    server.add_tool(read_transcript_tool)
    server.add_tool(get_config_tool)

    logger.info("YTT MCP Server starting...")

    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream)

def run():
    """엔트리포인트"""
    asyncio.run(main())
```

### tools.py

```python
"""
YTT MCP Tools
각 도구의 구현
"""
import tempfile
import json
from pathlib import Path
from mcp.server import Tool
from mcp.types import TextContent

from .. import core, config

# 임시 디렉토리 관리
TEMP_DIR = Path(tempfile.gettempdir()) / "ytt-mcp"
TEMP_DIR.mkdir(exist_ok=True)

async def transcribe_tool(youtube_url: str, model_size: str = "base", language: str = "auto"):
    """YouTube 영상 전사"""
    try:
        # 출력 디렉토리 생성
        output_dir = TEMP_DIR / f"video_{hash(youtube_url)}"
        output_dir.mkdir(exist_ok=True)

        # 다운로드
        metadata = core.download_youtube(youtube_url, output_dir)

        # 청킹
        chunks = core.chunk_audio(metadata['audio_path'], output_dir)

        # 전사
        lang = None if language == "auto" else language
        transcripts = core.transcribe_audio(chunks, model_size, lang)

        # 저장
        core.save_transcripts(transcripts, output_dir, metadata['title'])
        core.save_metadata(metadata, output_dir)

        # 결과 읽기
        with open(output_dir / "transcript.txt", "r") as f:
            transcript_text = f.read()

        return {
            "success": True,
            "transcript": transcript_text,
            "metadata": {
                "title": metadata['title'],
                "duration": metadata['duration'],
                "language_detected": transcripts[0]['language'] if transcripts else "unknown"
            },
            "output_path": str(output_dir)
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

async def transcribe_and_summarize_tool(
    youtube_url: str,
    model_size: str = "base",
    language: str = "auto"
):
    """전사 + 요약 (원스톱)"""
    try:
        # 1. 전사
        transcribe_result = await transcribe_tool(youtube_url, model_size, language)

        if not transcribe_result["success"]:
            return transcribe_result

        # 2. 요약
        output_path = transcribe_result["output_path"]

        # transcript.json 읽기
        with open(Path(output_path) / "transcript.json", "r") as f:
            transcript_data = json.load(f)

        # 요약 생성
        cfg = config.load_config()
        summary_lang = language if language != "auto" else cfg.get('default_language', 'ko')

        summary = core.summarize_with_claude(
            transcript_data['chunks'],
            language=summary_lang
        )

        # 요약 저장
        core.save_summary(summary, Path(output_path))

        return {
            "success": True,
            "transcript": transcribe_result["transcript"],
            "metadata": transcribe_result["metadata"],
            "summary": {
                "long": summary['long_summary'],
                "short": summary['short_summary']
            },
            "output_path": output_path
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# 나머지 도구들도 유사하게 구현...
```

## 설정 파일

### Claude Desktop Config

사용자는 `~/Library/Application Support/Claude/claude_desktop_config.json`에 추가:

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

또는 환경 변수를 통해:

```json
{
  "mcpServers": {
    "ytt": {
      "command": "ytt-mcp-server"
    }
  }
}
```

## 에러 핸들링

### 에러 타입

1. **설정 관련**
   - API 키 미설정
   - ytt 설정 파일 없음

2. **입력 관련**
   - 잘못된 YouTube URL
   - 지원하지 않는 언어 코드
   - 존재하지 않는 파일 경로

3. **실행 관련**
   - ffmpeg 미설치
   - 네트워크 오류
   - 디스크 공간 부족
   - Whisper 모델 로드 실패

### 에러 응답 형식

```json
{
  "success": false,
  "error": "Error message",
  "error_type": "ConfigurationError",
  "suggestion": "Run 'ytt-init' to configure ytt first"
}
```

## 사용 시나리오

### 시나리오 1: 기본 요약
```
User: "https://youtube.com/watch?v=xxx 이 영상 요약해줘"

Claude:
1. ytt_transcribe_and_summarize 도구 호출
2. 결과에서 요약 추출
3. 사용자에게 요약 제시
```

### 시나리오 2: 전사만
```
User: "이 영상 전사만 해줘 (URL)"

Claude:
1. ytt_transcribe 도구 호출
2. 전사 결과 제시
```

### 시나리오 3: 기존 전사 재요약
```
User: "/path/to/output 이 전사 파일을 영어로 다시 요약해줘"

Claude:
1. ytt_summarize 도구 호출 (language="en")
2. 영어 요약 제시
```

## 성능 고려사항

### 비동기 처리
- MCP는 비동기이지만 ytt core는 동기 함수
- `asyncio.to_thread()` 사용하여 블로킹 방지

### 타임아웃
- 긴 영상의 경우 처리 시간이 오래 걸림
- 진행 상황 업데이트 필요 (MCP progress notifications)

### 임시 파일 관리
- `/tmp/ytt-mcp/` 에 임시 파일 저장
- 주기적 정리 필요 (또는 사용자가 수동 정리)

## 다음 단계

1. **Phase 1: 기본 구현**
   - MCP 서버 스켈레톤
   - `ytt_transcribe_and_summarize` 도구 구현
   - 기본 테스트

2. **Phase 2: 전체 도구**
   - 나머지 4개 도구 구현
   - 에러 핸들링 강화
   - 진행 상황 알림

3. **Phase 3: 문서화 및 배포**
   - 설치 가이드 작성
   - Homebrew formula 업데이트
   - 예시 및 트러블슈팅

## 보안 고려사항

1. **API 키 보호**
   - 환경 변수로 관리
   - MCP 응답에 API 키 노출 금지

2. **파일 접근**
   - ytt 출력 디렉토리만 접근
   - 경로 traversal 방지

3. **입력 검증**
   - YouTube URL 형식 검증
   - 파일 경로 검증

## 참고 자료

- [MCP Python SDK](https://github.com/anthropics/anthropic-mcp-python)
- [MCP Specification](https://spec.modelcontextprotocol.io/)
- [Claude Desktop MCP Guide](https://docs.anthropic.com/claude/docs/mcp)
