#!/bin/bash
set -e

# README 동기화 확인 스크립트
# Checks if all README versions are synchronized

echo "🔍 Checking README synchronization..."
echo ""

# 파일 존재 확인
if [ ! -f "README.md" ]; then
    echo "❌ README.md not found"
    exit 1
fi

if [ ! -f "README.en.md" ]; then
    echo "⚠️  README.en.md not found"
    exit 1
fi

if [ ! -f "README.zh.md" ]; then
    echo "⚠️  README.zh.md not found"
    exit 1
fi

echo "✓ All README files exist"
echo ""

# 파일 크기 비교 (대략적인 동기화 체크)
SIZE_KO=$(wc -l < README.md | tr -d ' ')
SIZE_EN=$(wc -l < README.en.md | tr -d ' ')
SIZE_ZH=$(wc -l < README.zh.md | tr -d ' ')

echo "📊 File sizes (lines):"
echo "  Korean:  $SIZE_KO"
echo "  English: $SIZE_EN"
echo "  Chinese: $SIZE_ZH"
echo ""

# 크기 차이가 너무 크면 경고
SIZE_DIFF_EN=$((SIZE_KO - SIZE_EN))
SIZE_DIFF_ZH=$((SIZE_KO - SIZE_ZH))

# 절대값으로 변환
SIZE_DIFF_EN=${SIZE_DIFF_EN#-}
SIZE_DIFF_ZH=${SIZE_DIFF_ZH#-}

THRESHOLD=50  # 50줄 이상 차이나면 경고

if [ $SIZE_DIFF_EN -gt $THRESHOLD ]; then
    echo "⚠️  Korean and English README have significant size difference ($SIZE_DIFF_EN lines)"
fi

if [ $SIZE_DIFF_ZH -gt $THRESHOLD ]; then
    echo "⚠️  Korean and Chinese README have significant size difference ($SIZE_DIFF_ZH lines)"
fi

# 언어 선택 배지 확인
echo "🔗 Checking language selector badges..."

if ! grep -q "English.*README.en.md" README.md; then
    echo "❌ Korean README missing English link"
    exit 1
fi

if ! grep -q "中文.*README.zh.md" README.md; then
    echo "❌ Korean README missing Chinese link"
    exit 1
fi

if ! grep -q "한국어.*README.md" README.en.md; then
    echo "❌ English README missing Korean link"
    exit 1
fi

if ! grep -q "한국어.*README.md" README.zh.md; then
    echo "❌ Chinese README missing Korean link"
    exit 1
fi

echo "✓ Language selector badges present in all files"
echo ""

# 주요 섹션 확인
echo "📋 Checking major sections..."

SECTIONS=("## 설치" "## 사용" "## 라이선스")
EN_SECTIONS=("## Installation" "## Usage" "## License")
ZH_SECTIONS=("## 安装" "## 使用" "## 许可证")

for section in "${SECTIONS[@]}"; do
    if ! grep -q "$section" README.md; then
        echo "⚠️  Korean README missing section: $section"
    fi
done

for section in "${EN_SECTIONS[@]}"; do
    if ! grep -q "$section" README.en.md; then
        echo "⚠️  English README missing section: $section"
    fi
done

for section in "${ZH_SECTIONS[@]}"; do
    if ! grep -q "$section" README.zh.md; then
        echo "⚠️  Chinese README missing section: $section"
    fi
done

echo "✓ Major sections present"
echo ""

# GitHub 링크 확인
echo "🔗 Checking GitHub links..."

GITHUB_URL="https://github.com/SaraHan774/ytt"

for file in README.md README.en.md README.zh.md; do
    if ! grep -q "$GITHUB_URL" "$file"; then
        echo "⚠️  $file missing GitHub repository link"
    fi
done

echo "✓ GitHub links present"
echo ""

echo "✅ README synchronization check complete!"
echo ""
echo "💡 Tips:"
echo "  - Keep all README files updated together"
echo "  - Use translation tools for consistency"
echo "  - Review translations by native speakers"
