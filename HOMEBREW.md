# Homebrew 배포 가이드

## 준비 사항

### 1. GitHub 저장소 설정

저장소를 GitHub에 푸시해야 합니다:

```bash
cd /Users/gahee/Desktop/YoutubeGPTClaude-main

# Git 초기화 (아직 안 했다면)
git init
git add .
git commit -m "Initial commit"

# GitHub 저장소 연결
git remote add origin https://github.com/SaraHan774/ytt.git
git push -u origin main
```

### 2. 릴리스 생성

GitHub에서 릴리스를 생성하세요:

1. GitHub 저장소 페이지로 이동
2. "Releases" → "Create a new release"
3. Tag version: `v1.0.0`
4. Release title: `v1.0.0 - Initial Release`
5. 설명 작성 후 "Publish release"

또는 CLI로:

```bash
# GitHub CLI 설치 (Homebrew)
brew install gh

# 인증
gh auth login

# 릴리스 생성
gh release create v1.0.0 \
  --title "v1.0.0 - Initial Release" \
  --notes "첫 공식 릴리스

주요 기능:
- YouTube 영상 전사 (Whisper)
- AI 요약 (Claude)
- 다국어 지원 (한국어/영어/일본어)
- 대화형 설치 마법사
- CLI 인터페이스"
```

### 3. SHA256 체크섬 계산

릴리스 tarball의 SHA256을 계산하세요:

```bash
# 릴리스 tarball 다운로드
curl -L https://github.com/SaraHan774/ytt/archive/refs/tags/v1.0.0.tar.gz -o ytt-1.0.0.tar.gz

# SHA256 계산
shasum -a 256 ytt-1.0.0.tar.gz

# 출력 예시:
# abc123def456... ytt-1.0.0.tar.gz
```

### 4. Formula 업데이트

`Formula/ytt.rb` 파일을 수정하세요:

```ruby
class Ytt < Formula
  desc "YouTube Transcript Tool - AI-powered video transcription"
  homepage "https://github.com/SaraHan774/ytt"
  url "https://github.com/SaraHan774/ytt/archive/refs/tags/v1.0.0.tar.gz"
  sha256 "YOUR_ACTUAL_SHA256_HERE"  # 위에서 계산한 값 입력
  license "MIT"
  # ...
end
```

---

## Homebrew Tap 생성

### 방법 1: 개인 Tap (권장)

개인 Homebrew Tap을 만들어 쉽게 배포할 수 있습니다:

```bash
# 1. Tap 저장소 생성 (GitHub에서)
# 저장소 이름: homebrew-ytt
# URL: https://github.com/SaraHan774/homebrew-ytt

# 2. 로컬에 클론
git clone https://github.com/SaraHan774/homebrew-ytt.git
cd homebrew-ytt

# 3. Formula 디렉토리 생성
mkdir -p Formula

# 4. Formula 파일 복사
cp /Users/gahee/Desktop/YoutubeGPTClaude-main/Formula/ytt.rb Formula/

# 5. 커밋 및 푸시
git add Formula/ytt.rb
git commit -m "Add ytt formula"
git push origin main
```

### 방법 2: 간단한 방법 (스크립트)

```bash
#!/bin/bash
# create-homebrew-tap.sh

GITHUB_USER="SaraHan774"
REPO_NAME="ytt"
TAP_REPO="homebrew-${REPO_NAME}"

echo "🍺 Creating Homebrew Tap..."

# 1. GitHub에 Tap 저장소 생성
gh repo create "${TAP_REPO}" --public --description "Homebrew tap for ${REPO_NAME}"

# 2. 클론
git clone "https://github.com/${GITHUB_USER}/${TAP_REPO}.git"
cd "${TAP_REPO}"

# 3. Formula 추가
mkdir -p Formula
cp "../${REPO_NAME}/Formula/ytt.rb" Formula/

# 4. 커밋 및 푸시
git add .
git commit -m "Add ${REPO_NAME} formula"
git push origin main

echo "✓ Tap 생성 완료: ${GITHUB_USER}/${TAP_REPO}"
```

---

## 사용자 설치 방법

### Tap 추가 후 설치

사용자들이 다음과 같이 설치할 수 있습니다:

```bash
# Tap 추가
brew tap SaraHan774/ytt

# 설치
brew install ytt

# 또는 한 줄로
brew install SaraHan774/ytt/ytt
```

### 설치 후 사용

```bash
# 대화형 설정
ytt-init

# 사용
ytt "https://youtube.com/watch?v=xxx" ./output --summarize
```

---

## Formula 자동 업데이트 스크립트

새 버전 릴리스 시 Formula를 자동으로 업데이트:

```bash
#!/bin/bash
# update-formula.sh

VERSION=$1
GITHUB_USER="SaraHan774"
REPO="ytt"

if [ -z "$VERSION" ]; then
  echo "Usage: $0 <version>"
  echo "Example: $0 1.0.1"
  exit 1
fi

echo "🔄 Updating formula for version v${VERSION}..."

# 1. tarball 다운로드
TARBALL_URL="https://github.com/${GITHUB_USER}/${REPO}/archive/refs/tags/v${VERSION}.tar.gz"
curl -L "${TARBALL_URL}" -o "${REPO}-${VERSION}.tar.gz"

# 2. SHA256 계산
SHA256=$(shasum -a 256 "${REPO}-${VERSION}.tar.gz" | awk '{print $1}')
echo "SHA256: ${SHA256}"

# 3. Formula 업데이트
cd "../homebrew-${REPO}"

sed -i.bak "s|url \".*\"|url \"${TARBALL_URL}\"|g" Formula/ytt.rb
sed -i.bak "s|sha256 \".*\"|sha256 \"${SHA256}\"|g" Formula/ytt.rb

rm Formula/ytt.rb.bak

# 4. 커밋 및 푸시
git add Formula/ytt.rb
git commit -m "Update to v${VERSION}"
git push origin main

echo "✓ Formula 업데이트 완료!"
```

사용:

```bash
chmod +x update-formula.sh
./update-formula.sh 1.0.1
```

---

## Homebrew Core 제출 (선택)

공식 Homebrew Core에 포함시키려면:

### 요구사항

1. ✅ 안정적인 릴리스 (v1.0.0+)
2. ✅ MIT/Apache2 등 OSI 승인 라이선스
3. ✅ 활발한 유지보수
4. ✅ 30+ GitHub 스타
5. ✅ 문서화

### 제출 절차

```bash
# 1. Homebrew 최신화
brew update

# 2. Formula 생성
brew create https://github.com/SaraHan774/ytt/archive/refs/tags/v1.0.0.tar.gz

# 3. Formula 편집
brew edit ytt

# 4. 로컬 테스트
brew install --build-from-source ytt
brew test ytt
brew audit --strict ytt

# 5. PR 생성
cd "$(brew --repository homebrew/core)"
git checkout -b ytt
cp /path/to/Formula/ytt.rb Formula/
git add Formula/ytt.rb
git commit -m "ytt 1.0.0 (new formula)"
git push origin ytt

# 6. GitHub에서 PR 생성
# https://github.com/Homebrew/homebrew-core/compare
```

---

## 테스트

Formula가 제대로 작동하는지 테스트:

```bash
# 1. Tap 제거 (깨끗한 상태에서 테스트)
brew untap SaraHan774/ytt

# 2. 재설치
brew tap SaraHan774/ytt
brew install ytt

# 3. 명령어 테스트
ytt --version
ytt-init --help
ytt-config show-config

# 4. 제거 테스트
brew uninstall ytt
brew untap SaraHan774/ytt
```

---

## GitHub Actions로 자동화

자동화 워크플로는 이미 `.github/workflows/release.yml`에 구성되어 있습니다. release를 publish하면 다음을 자동 수행합니다:

1. tarball SHA256 계산
2. `homebrew-ytt` tap 저장소 clone
3. `Formula/ytt.rb`의 top-level `url` / `sha256` 업데이트 (2-space 인덴트 anchor로 resource 블록은 건드리지 않음)
4. 커밋 후 push

### 사전 요구사항: `TAP_GITHUB_TOKEN` 시크릿

워크플로는 `homebrew-ytt` 저장소에 push할 토큰이 필요합니다. **이 시크릿이 없으면 워크플로의 첫 단계에서 명확한 에러 메시지와 함께 실패합니다.**

설정 절차:

1. fine-grained PAT 생성: https://github.com/settings/personal-access-tokens
   - Repository access: `homebrew-ytt` 선택
   - Repository permissions → Contents: **Read and write**
   - 만료일 설정 (예: 1년)
2. 메인 저장소에 시크릿 등록: `https://github.com/<owner>/ytt/settings/secrets/actions`
   - Name: `TAP_GITHUB_TOKEN`
   - Secret: 위에서 생성한 PAT 값

(classic PAT를 쓴다면 `repo` scope 전체 권한이 필요합니다.)

### 시크릿 미설정 상태 우회

토큰을 등록하기 전에 release를 게시해야 한다면, 수동으로 tap을 업데이트할 수 있습니다:

```bash
# 1. 새 tarball 다운 + sha256
TAG=v1.4.1
URL="https://github.com/SaraHan774/ytt/archive/refs/tags/${TAG}.tar.gz"
SHA=$(curl -sL "$URL" | shasum -a 256 | awk '{print $1}')

# 2. tap 저장소에서 Formula 업데이트
cd /path/to/homebrew-ytt
sed -i '' "s|^  url \".*\"|  url \"${URL}\"|" Formula/ytt.rb
sed -i '' "s|^  sha256 \".*\"|  sha256 \"${SHA}\"|" Formula/ytt.rb

# 3. 커밋 + 푸시
git add Formula/ytt.rb
git commit -m "Update ytt to ${TAG}"
git push
```

(macOS BSD sed는 `-i`에 빈 인자가 필요함. Linux GNU sed는 `sed -i 's|...|'` 그대로 작동.)

---

## README에 추가할 설치 방법

```markdown
## 설치

### Homebrew (macOS/Linux)

```bash
# Tap 추가
brew tap SaraHan774/ytt

# 설치
brew install ytt

# 사용
ytt-init  # 대화형 설정
ytt "https://youtube.com/watch?v=xxx" ./output --summarize
```

### pip (모든 플랫폼)

```bash
pip install -r requirements.txt
pip install -e .
```
```

---

## 문제 해결

### Formula 오류 확인

```bash
brew audit --strict ytt
brew style ytt
```

### 의존성 문제

```bash
# Python 버전 확인
brew info python@3.11

# ffmpeg 확인
brew info ffmpeg
```

### 로그 확인

```bash
# 설치 로그
brew install --verbose ytt

# 디버그 모드
brew install --debug ytt
```
