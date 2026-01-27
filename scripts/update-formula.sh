#!/bin/bash
set -e

# YouTube Transcript Tool - Formula 업데이트 스크립트

VERSION=$1
GITHUB_USER="${2:-yourusername}"
REPO="ytt"
TAP_REPO="homebrew-${REPO}"

if [ -z "$VERSION" ]; then
  echo "Usage: $0 <version> [github_user]"
  echo "Example: $0 1.0.1 yourusername"
  exit 1
fi

echo "🔄 Updating formula for version v${VERSION}..."
echo ""

# 1. tarball 다운로드 및 SHA256 계산
TARBALL_URL="https://github.com/${GITHUB_USER}/${REPO}/archive/refs/tags/v${VERSION}.tar.gz"
echo "📥 Downloading tarball: ${TARBALL_URL}"

TMP_FILE=$(mktemp)
curl -sL "${TARBALL_URL}" -o "${TMP_FILE}"

SHA256=$(shasum -a 256 "${TMP_FILE}" | awk '{print $1}')
rm "${TMP_FILE}"

echo "✓ SHA256: ${SHA256}"
echo ""

# 2. Tap 저장소 확인
if [ ! -d "../${TAP_REPO}" ]; then
  echo "❌ Tap repository not found: ../${TAP_REPO}"
  echo "Run create-homebrew-tap.sh first"
  exit 1
fi

# 3. Formula 업데이트
echo "📝 Updating Formula..."
cd "../${TAP_REPO}"

# 백업 생성
cp Formula/ytt.rb Formula/ytt.rb.bak

# URL 업데이트
sed -i.tmp "s|url \".*\"|url \"${TARBALL_URL}\"|g" Formula/ytt.rb
# SHA256 업데이트
sed -i.tmp "s|sha256 \".*\"|sha256 \"${SHA256}\"|g" Formula/ytt.rb

rm Formula/ytt.rb.tmp

echo "✓ Formula updated"
echo ""

# 변경사항 표시
echo "📋 Changes:"
git diff Formula/ytt.rb
echo ""

# 4. 커밋 여부 확인
read -p "Commit and push changes? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
  git add Formula/ytt.rb
  git commit -m "Update to v${VERSION}"
  git push origin main

  echo ""
  echo "✅ Formula updated and pushed!"
  echo ""
  echo "Users can update with:"
  echo "  brew update"
  echo "  brew upgrade ytt"
else
  echo "⚠️  Changes not committed. Restoring backup..."
  mv Formula/ytt.rb.bak Formula/ytt.rb
fi
