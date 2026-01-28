# YTT MCP Server 구현 로드맵

## 개요

이 문서는 ytt MCP 서버를 구현하기 위한 단계별 로드맵입니다.

## Phase 1: 기본 인프라 (1-2일)

### 목표
- MCP 서버 기본 구조 구축
- 하나의 도구만 작동하는 프로토타입

### 작업 항목

1. **의존성 추가**
   - [ ] `requirements.txt`에 `anthropic-mcp` 추가
   - [ ] `setup.py`에 `ytt-mcp-server` 엔트리포인트 추가

2. **디렉토리 구조 생성**
   ```bash
   mkdir -p ytt/mcp
   touch ytt/mcp/__init__.py
   touch ytt/mcp/server.py
   touch ytt/mcp/tools.py
   touch ytt/mcp/utils.py
   ```

3. **기본 서버 구현**
   - [ ] `server.py`: MCP 서버 스켈레톤
   - [ ] stdio 연결 설정
   - [ ] 로깅 설정

4. **첫 번째 도구 구현**
   - [ ] `ytt_transcribe_and_summarize` 구현
   - [ ] 입력 스키마 정의
   - [ ] 출력 포맷 정의
   - [ ] 에러 핸들링

5. **로컬 테스트**
   - [ ] 수동으로 MCP 서버 실행
   - [ ] JSON-RPC 요청/응답 테스트
   - [ ] 기본 동작 확인

### 산출물
- 작동하는 MCP 서버 프로토타입
- `ytt-mcp-server` 명령어 실행 가능

## Phase 2: 전체 도구 구현 (2-3일)

### 목표
- 5개 도구 모두 구현
- 에러 핸들링 강화

### 작업 항목

1. **나머지 도구 구현**
   - [ ] `ytt_transcribe`
   - [ ] `ytt_summarize`
   - [ ] `ytt_read_transcript`
   - [ ] `ytt_get_config`

2. **비동기 처리**
   - [ ] `asyncio.to_thread()` 적용
   - [ ] 블로킹 방지
   - [ ] 타임아웃 설정

3. **진행 상황 알림**
   - [ ] MCP progress notifications 구현
   - [ ] 긴 작업에 대한 피드백

4. **임시 파일 관리**
   - [ ] `/tmp/ytt-mcp/` 디렉토리 관리
   - [ ] 파일 정리 로직
   - [ ] 디스크 공간 체크

5. **에러 핸들링**
   - [ ] 모든 도구에 try-catch
   - [ ] 구체적인 에러 메시지
   - [ ] 해결 방법 제안

### 산출물
- 완전한 기능의 MCP 서버
- 모든 도구 작동 확인

## Phase 3: 테스트 및 안정화 (2-3일)

### 목표
- 실제 사용 시나리오 테스트
- 버그 수정 및 안정화

### 작업 항목

1. **단위 테스트**
   ```bash
   mkdir -p tests/mcp
   touch tests/mcp/test_tools.py
   touch tests/mcp/test_server.py
   ```
   - [ ] 각 도구별 테스트 케이스
   - [ ] 에러 케이스 테스트
   - [ ] Mock을 사용한 격리 테스트

2. **통합 테스트**
   - [ ] Claude Desktop과 실제 통합
   - [ ] 다양한 YouTube 영상 테스트
   - [ ] 다국어 테스트 (ko/en/zh)

3. **성능 테스트**
   - [ ] 긴 영상 (1시간+) 테스트
   - [ ] 동시 요청 처리
   - [ ] 메모리 사용량 모니터링

4. **에지 케이스**
   - [ ] 잘못된 URL
   - [ ] 네트워크 끊김
   - [ ] API 키 없음
   - [ ] 디스크 공간 부족

### 산출물
- 테스트 커버리지 80%+
- 안정적인 MCP 서버

## Phase 4: 문서화 (1-2일)

### 목표
- 사용자 친화적인 문서 작성
- 설치 및 설정 가이드

### 작업 항목

1. **사용자 문서**
   - [x] `MCP_DESIGN.md` - 설계 문서
   - [x] `MCP_SETUP.md` - 설정 가이드
   - [ ] README 업데이트 (MCP 섹션 추가)

2. **개발자 문서**
   - [ ] API 레퍼런스
   - [ ] 아키텍처 다이어그램
   - [ ] 기여 가이드

3. **예시 및 튜토리얼**
   - [ ] 기본 사용 예시
   - [ ] 고급 사용 시나리오
   - [ ] 트러블슈팅 가이드

4. **비디오 데모** (옵션)
   - [ ] 설치 및 설정 데모
   - [ ] 실제 사용 데모

### 산출물
- 완전한 문서 세트
- 사용자가 쉽게 따라할 수 있는 가이드

## Phase 5: 배포 및 릴리스 (1일)

### 목표
- 버전 1.1.0 릴리스
- Homebrew 업데이트

### 작업 항목

1. **버전 업데이트**
   - [ ] `__init__.py`: 1.0.4 → 1.1.0
   - [ ] CHANGELOG 작성

2. **Homebrew Formula 업데이트**
   - [ ] 의존성 추가 (`anthropic-mcp`)
   - [ ] 엔트리포인트 추가
   - [ ] 테스트 추가

3. **GitHub Release**
   - [ ] 릴리스 노트 작성
   - [ ] 바이너리 빌드 (필요시)
   - [ ] v1.1.0 태그

4. **배포**
   - [ ] PyPI 업로드 (pip 사용자용)
   - [ ] Homebrew tap 업데이트
   - [ ] 문서 사이트 업데이트

### 산출물
- v1.1.0 공식 릴리스
- 사용자가 설치 가능

## Phase 6: 피드백 및 개선 (지속적)

### 목표
- 사용자 피드백 수집
- 지속적 개선

### 작업 항목

1. **피드백 수집**
   - [ ] GitHub Issues 모니터링
   - [ ] 사용자 리뷰 확인
   - [ ] 개선 사항 우선순위 설정

2. **개선 항목** (Phase 1 이후)
   - [ ] 더 많은 출력 포맷 (SRT, VTT 자막)
   - [ ] 영상 메타데이터 추출 강화
   - [ ] 캐싱 메커니즘
   - [ ] 배치 처리 최적화

3. **추가 기능** (Phase 2 이후)
   - [ ] 플레이리스트 지원
   - [ ] 실시간 전사 (라이브 스트림)
   - [ ] 화자 구분 (diarization)
   - [ ] 키워드 추출

## 현재 상태

```
[ ] Phase 1: 기본 인프라
[ ] Phase 2: 전체 도구 구현
[ ] Phase 3: 테스트 및 안정화
[x] Phase 4: 문서화 (설계 문서 완료)
[ ] Phase 5: 배포 및 릴리스
[ ] Phase 6: 피드백 및 개선
```

## 예상 일정

- **Week 1**: Phase 1-2 (기본 구현)
- **Week 2**: Phase 3-4 (테스트 및 문서)
- **Week 3**: Phase 5-6 (배포 및 초기 피드백)

## 우선순위

### P0 (필수)
- Phase 1-3: 기본 동작하는 MCP 서버
- `ytt_transcribe_and_summarize` 도구

### P1 (중요)
- Phase 4: 문서화
- 나머지 4개 도구
- 에러 핸들링

### P2 (선택)
- 진행 상황 알림
- 고급 기능
- 성능 최적화

## 기술 스택

### 필수 의존성
```
anthropic-mcp>=1.0.0
asyncio
typing
```

### 개발 의존성
```
pytest
pytest-asyncio
pytest-cov
```

## 참고 자료

- [MCP Python SDK](https://github.com/anthropics/anthropic-mcp-python)
- [MCP Specification](https://spec.modelcontextprotocol.io/)
- [Existing MCP Servers](https://github.com/modelcontextprotocol/servers)

## 팀 역할 (1인 개발 기준)

- **설계**: 완료 ✅
- **구현**: 진행 예정
- **테스트**: 진행 예정
- **문서화**: 진행 중 🚧
- **배포**: 대기 중

## 성공 지표

- [ ] Claude Desktop에서 ytt 도구 사용 가능
- [ ] 5개 도구 모두 정상 작동
- [ ] 테스트 커버리지 80% 이상
- [ ] 사용자가 10분 내에 설정 완료 가능
- [ ] GitHub Stars 증가

## 다음 액션

**지금 바로 시작하려면:**
1. Phase 1의 첫 번째 작업 항목부터 시작
2. `requirements.txt`에 `anthropic-mcp` 추가
3. `ytt/mcp/` 디렉토리 생성
4. `server.py` 스켈레톤 작성

**질문이 있다면:**
- GitHub Issues에 올리기
- 설계 문서 다시 검토
- 기존 MCP 서버 예시 참고
