#!/bin/bash
set -e

# YouTube Transcript Tool - Homebrew Tap 생성 스크립트

GITHUB_USER="${1:-SaraHan774}"
REPO_NAME="ytt"
TAP_REPO="homebrew-${REPO_NAME}"

echo "🍺 Creating Homebrew Tap for ${GITHUB_USER}/${REPO_NAME}..."
echo ""

# GitHub CLI 확인
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) not found. Install it first:"
    echo "   brew install gh"
    exit 1
fi

# 인증 확인
if ! gh auth status &> /dev/null; then
    echo "🔐 Please authenticate with GitHub:"
    gh auth login
fi

echo "📦 Step 1: Creating GitHub repository ${TAP_REPO}..."
if gh repo view "${GITHUB_USER}/${TAP_REPO}" &> /dev/null; then
    echo "⚠️  Repository already exists. Skipping creation."
else
    gh repo create "${TAP_REPO}" \
        --public \
        --description "Homebrew tap for ${REPO_NAME}" \
        --clone=false
    echo "✓ Repository created"
fi

echo ""
echo "📥 Step 2: Cloning tap repository..."
if [ -d "${TAP_REPO}" ]; then
    echo "⚠️  Directory already exists. Pulling latest changes..."
    cd "${TAP_REPO}"
    git pull origin main
    cd ..
else
    git clone "https://github.com/${GITHUB_USER}/${TAP_REPO}.git"
    echo "✓ Repository cloned"
fi

echo ""
echo "📝 Step 3: Setting up Formula..."
mkdir -p "${TAP_REPO}/Formula"

# Formula 복사
if [ -f "Formula/ytt.rb" ]; then
    cp "Formula/ytt.rb" "${TAP_REPO}/Formula/"

    # GitHub 사용자명 업데이트
    sed -i.bak "s/SaraHan774/${GITHUB_USER}/g" "${TAP_REPO}/Formula/ytt.rb"
    rm "${TAP_REPO}/Formula/ytt.rb.bak"

    echo "✓ Formula copied and updated"
else
    echo "❌ Formula/ytt.rb not found!"
    exit 1
fi

echo ""
echo "📤 Step 4: Committing and pushing..."
cd "${TAP_REPO}"

git add Formula/ytt.rb
git commit -m "Add ${REPO_NAME} formula" || echo "No changes to commit"
git push origin main

cd ..

echo ""
echo "✅ Homebrew Tap created successfully!"
echo ""
echo "📋 Next steps:"
echo ""
echo "1. Create a release on GitHub:"
echo "   gh release create v1.0.0 --title 'v1.0.0' --notes 'Initial release'"
echo ""
echo "2. Calculate SHA256 of the release tarball:"
echo "   curl -sL https://github.com/${GITHUB_USER}/${REPO_NAME}/archive/refs/tags/v1.0.0.tar.gz | shasum -a 256"
echo ""
echo "3. Update Formula with SHA256:"
echo "   cd ${TAP_REPO}"
echo "   # Edit Formula/ytt.rb and add the SHA256"
echo "   git add Formula/ytt.rb"
echo "   git commit -m 'Add SHA256 checksum'"
echo "   git push"
echo ""
echo "4. Users can install with:"
echo "   brew tap ${GITHUB_USER}/${REPO_NAME}"
echo "   brew install ytt"
echo ""
echo "🎉 Done!"
