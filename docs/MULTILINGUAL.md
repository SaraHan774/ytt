# Multilingual Repository Management Guide

[한국어](#한국어-가이드) | [English](#english-guide) | [中文](#中文指南)

---

## 한국어 가이드

### 현재 지원 언어

- 🇰🇷 한국어 (Korean) - 기본 언어
- 🇺🇸 영어 (English)
- 🇨🇳 중국어 간체 (Simplified Chinese)

### 파일 구조

```
ytt/
├── README.md          # 한국어 (기본)
├── README.en.md       # 영어
├── README.zh.md       # 중국어 간체
└── docs/
    ├── MULTILINGUAL.md    # 이 파일
    └── [기타 문서]
```

### README 파일 관리 규칙

1. **언어 선택 배지**
   - 모든 README 파일 상단에 언어 선택 링크 포함
   - 현재 언어는 굵은 텍스트로 표시
   - 형식: `**한국어** | [English](README.en.md) | [中文](README.zh.md)`

2. **내용 동기화**
   - 기본 README (한국어) 업데이트 시 다른 언어 버전도 함께 업데이트
   - 버전 번호, 링크, 코드 예제는 모든 언어에서 동일하게 유지
   - 주요 기능 추가/변경 시 모든 언어 버전에 반영

3. **번역 우선순위**
   - 필수: README, Release Notes
   - 권장: USAGE_CLI.md, HOMEBREW.md
   - 선택: CLI_DESIGN.md, CONTRIBUTING.md

### Release Notes 관리

GitHub Release 작성 시 다음 형식 사용:

```markdown
# YouTube Transcript Tool v1.0.0

---

## 🇰🇷 한국어
[한국어 내용]

---

## 🇺🇸 English
[English content]

---

## 🇨🇳 中文
[中文内容]

---

## 📋 Requirements / 요구사항 / 系统要求
[공통 요구사항]

## 📚 Documentation / 문서 / 文档
[문서 링크]
```

### 코드 내 다국어 지원

#### CLI 메시지
현재 `ytt/setup.py`에서 한국어 메시지 사용. 향후 i18n 도입 고려:

```python
# 현재
console.print("✓ 설치가 완료되었습니다!")

# 개선 방향 (향후)
console.print(t("setup.complete"))
```

#### 요약 프롬프트
`ytt/core.py`의 `summarize_with_claude()` 함수에서 언어별 프롬프트 지원:

```python
prompts = {
    'ko': {'chunk': "...", 'final': "..."},
    'en': {'chunk': "...", 'final': "..."},
    'ja': {'chunk': "...", 'final': "..."}
}
```

### 새 언어 추가 프로세스

1. **README 번역**
   ```bash
   cp README.md README.[lang].md
   # README.[lang].md 번역
   ```

2. **언어 선택 배지 업데이트**
   - 모든 README 파일의 상단 링크에 새 언어 추가

3. **요약 프롬프트 추가** (선택)
   ```python
   # ytt/core.py
   prompts = {
       # ...
       'lang': {
           'chunk': "...",
           'final': "..."
       }
   }
   ```

4. **CLI 언어 옵션 추가**
   ```python
   # ytt/cli.py
   @click.option('--language', '-l',
       type=click.Choice(['ko', 'en', 'ja', 'lang']),
       # ...
   )
   ```

### 자동화 도구

#### README 번역 체크 스크립트

```bash
#!/bin/bash
# scripts/check-readme-sync.sh

# README 버전 체크
VERSION_KO=$(grep "version=\"" README.md)
VERSION_EN=$(grep "version=\"" README.en.md)
VERSION_ZH=$(grep "version=\"" README.zh.md)

if [ "$VERSION_KO" != "$VERSION_EN" ] || [ "$VERSION_KO" != "$VERSION_ZH" ]; then
    echo "⚠️  README versions are not synchronized!"
    exit 1
fi

echo "✓ All README files are synchronized"
```

#### 자동 번역 워크플로우 (향후)

```yaml
# .github/workflows/translate.yml
name: Auto-translate README

on:
  push:
    paths:
      - 'README.md'

jobs:
  translate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Translate to English
        # AI 번역 도구 사용
      - name: Translate to Chinese
        # AI 번역 도구 사용
      - name: Create PR
        # PR 생성
```

### 커뮤니티 기여

다른 언어로 번역을 기여하고 싶다면:

1. 이슈 생성: "Translation: [언어명]"
2. README.[lang].md 파일 작성
3. PR 제출
4. 리뷰 및 병합

---

## English Guide

### Supported Languages

- 🇰🇷 Korean - Default language
- 🇺🇸 English
- 🇨🇳 Simplified Chinese

### File Structure

```
ytt/
├── README.md          # Korean (default)
├── README.en.md       # English
├── README.zh.md       # Simplified Chinese
└── docs/
    ├── MULTILINGUAL.md    # This file
    └── [other docs]
```

### README File Management Rules

1. **Language Selector Badges**
   - Include language selection links at the top of all README files
   - Current language shown in bold text
   - Format: `**한국어** | [English](README.en.md) | [中文](README.zh.md)`

2. **Content Synchronization**
   - Update all language versions when the default README (Korean) is updated
   - Keep version numbers, links, and code examples identical across all languages
   - Reflect major feature additions/changes in all language versions

3. **Translation Priority**
   - Essential: README, Release Notes
   - Recommended: USAGE_CLI.md, HOMEBREW.md
   - Optional: CLI_DESIGN.md, CONTRIBUTING.md

### Release Notes Management

Use this format when writing GitHub Releases:

```markdown
# YouTube Transcript Tool v1.0.0

---

## 🇰🇷 한국어
[Korean content]

---

## 🇺🇸 English
[English content]

---

## 🇨🇳 中文
[Chinese content]

---

## 📋 Requirements / 요구사항 / 系统要求
[Common requirements]

## 📚 Documentation / 문서 / 文档
[Documentation links]
```

### Multilingual Support in Code

#### CLI Messages
Currently uses Korean messages in `ytt/setup.py`. Consider i18n in the future:

```python
# Current
console.print("✓ 설치가 완료되었습니다!")

# Future improvement
console.print(t("setup.complete"))
```

#### Summary Prompts
Language-specific prompts in `ytt/core.py`'s `summarize_with_claude()`:

```python
prompts = {
    'ko': {'chunk': "...", 'final': "..."},
    'en': {'chunk': "...", 'final': "..."},
    'ja': {'chunk': "...", 'final': "..."}
}
```

### Adding a New Language

1. **Translate README**
   ```bash
   cp README.md README.[lang].md
   # Translate README.[lang].md
   ```

2. **Update Language Selector Badges**
   - Add new language to top links in all README files

3. **Add Summary Prompts** (Optional)
   ```python
   # ytt/core.py
   prompts = {
       # ...
       'lang': {
           'chunk': "...",
           'final': "..."
       }
   }
   ```

4. **Add CLI Language Option**
   ```python
   # ytt/cli.py
   @click.option('--language', '-l',
       type=click.Choice(['ko', 'en', 'ja', 'lang']),
       # ...
   )
   ```

### Automation Tools

#### README Sync Check Script

```bash
#!/bin/bash
# scripts/check-readme-sync.sh

# Check README versions
VERSION_KO=$(grep "version=\"" README.md)
VERSION_EN=$(grep "version=\"" README.en.md)
VERSION_ZH=$(grep "version=\"" README.zh.md)

if [ "$VERSION_KO" != "$VERSION_EN" ] || [ "$VERSION_KO" != "$VERSION_ZH" ]; then
    echo "⚠️  README versions are not synchronized!"
    exit 1
fi

echo "✓ All README files are synchronized"
```

#### Auto-translation Workflow (Future)

```yaml
# .github/workflows/translate.yml
name: Auto-translate README

on:
  push:
    paths:
      - 'README.md'

jobs:
  translate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Translate to English
        # Use AI translation tool
      - name: Translate to Chinese
        # Use AI translation tool
      - name: Create PR
        # Create PR
```

### Community Contributions

To contribute translations in other languages:

1. Create issue: "Translation: [Language Name]"
2. Create README.[lang].md file
3. Submit PR
4. Review and merge

---

## 中文指南

### 支持的语言

- 🇰🇷 韩语 - 默认语言
- 🇺🇸 英语
- 🇨🇳 简体中文

### 文件结构

```
ytt/
├── README.md          # 韩语（默认）
├── README.en.md       # 英语
├── README.zh.md       # 简体中文
└── docs/
    ├── MULTILINGUAL.md    # 本文件
    └── [其他文档]
```

### README 文件管理规则

1. **语言选择徽章**
   - 在所有 README 文件顶部包含语言选择链接
   - 当前语言以粗体文本显示
   - 格式：`**한국어** | [English](README.en.md) | [中文](README.zh.md)`

2. **内容同步**
   - 更新默认 README（韩语）时同时更新所有语言版本
   - 保持版本号、链接和代码示例在所有语言中一致
   - 在所有语言版本中反映主要功能添加/更改

3. **翻译优先级**
   - 必须：README、Release Notes
   - 推荐：USAGE_CLI.md、HOMEBREW.md
   - 可选：CLI_DESIGN.md、CONTRIBUTING.md

### Release Notes 管理

编写 GitHub Release 时使用此格式：

```markdown
# YouTube Transcript Tool v1.0.0

---

## 🇰🇷 한국어
[韩语内容]

---

## 🇺🇸 English
[英语内容]

---

## 🇨🇳 中文
[中文内容]

---

## 📋 Requirements / 요구사항 / 系统要求
[通用要求]

## 📚 Documentation / 문서 / 文档
[文档链接]
```

### 代码中的多语言支持

#### CLI 消息
目前在 `ytt/setup.py` 中使用韩语消息。未来考虑 i18n：

```python
# 当前
console.print("✓ 설치가 완료되었습니다!")

# 未来改进
console.print(t("setup.complete"))
```

#### 摘要提示
在 `ytt/core.py` 的 `summarize_with_claude()` 中支持特定语言提示：

```python
prompts = {
    'ko': {'chunk': "...", 'final': "..."},
    'en': {'chunk': "...", 'final': "..."},
    'ja': {'chunk': "...", 'final': "..."}
}
```

### 添加新语言的流程

1. **翻译 README**
   ```bash
   cp README.md README.[lang].md
   # 翻译 README.[lang].md
   ```

2. **更新语言选择徽章**
   - 在所有 README 文件的顶部链接中添加新语言

3. **添加摘要提示**（可选）
   ```python
   # ytt/core.py
   prompts = {
       # ...
       'lang': {
           'chunk': "...",
           'final': "..."
       }
   }
   ```

4. **添加 CLI 语言选项**
   ```python
   # ytt/cli.py
   @click.option('--language', '-l',
       type=click.Choice(['ko', 'en', 'ja', 'lang']),
       # ...
   )
   ```

### 自动化工具

#### README 同步检查脚本

```bash
#!/bin/bash
# scripts/check-readme-sync.sh

# 检查 README 版本
VERSION_KO=$(grep "version=\"" README.md)
VERSION_EN=$(grep "version=\"" README.en.md)
VERSION_ZH=$(grep "version=\"" README.zh.md)

if [ "$VERSION_KO" != "$VERSION_EN" ] || [ "$VERSION_KO" != "$VERSION_ZH" ]; then
    echo "⚠️  README 版本不同步！"
    exit 1
fi

echo "✓ 所有 README 文件已同步"
```

#### 自动翻译工作流程（未来）

```yaml
# .github/workflows/translate.yml
name: Auto-translate README

on:
  push:
    paths:
      - 'README.md'

jobs:
  translate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Translate to English
        # 使用 AI 翻译工具
      - name: Translate to Chinese
        # 使用 AI 翻译工具
      - name: Create PR
        # 创建 PR
```

### 社区贡献

要贡献其他语言的翻译：

1. 创建 issue："Translation: [语言名称]"
2. 创建 README.[lang].md 文件
3. 提交 PR
4. 审查和合并

---

## Best Practices for Multilingual Repositories

### 1. File Naming Convention
- Use ISO 639-1 language codes: `README.[lang].md`
- Examples: `README.en.md`, `README.zh.md`, `README.ja.md`

### 2. Language Selector Placement
- Always at the top of the file, before the title
- Use consistent format across all files
- Link to other language versions

### 3. Content Synchronization
- Keep version numbers consistent
- Update all language versions together
- Use version control to track translation status

### 4. Translation Quality
- Use native speakers when possible
- Maintain technical term consistency
- Preserve code examples and commands identically

### 5. Community Engagement
- Welcome translation contributions
- Provide clear guidelines for translators
- Review translations for accuracy

### 6. Automation
- Use GitHub Actions for translation workflows
- Implement checks for synchronization
- Consider using translation management tools

### 7. Documentation
- Maintain this multilingual guide
- Document translation processes
- Track translation status in issues

---

## Translation Contribution Template

When submitting a translation PR, use this template:

```markdown
## Translation PR: [Language Name]

### Language Information
- Language: [Language Name]
- Language Code: [ISO 639-1 code]
- Translator: @[your-username]

### Files Translated
- [ ] README.[lang].md
- [ ] Release Notes (v1.0.0)
- [ ] Other: [specify]

### Translation Notes
[Any notes about terminology choices, cultural adaptations, etc.]

### Checklist
- [ ] Language selector badges added to all README files
- [ ] Links verified and working
- [ ] Code examples preserved exactly
- [ ] Version numbers consistent
- [ ] Native speaker review completed (if applicable)
```

---

## Resources

### Translation Tools
- DeepL: https://www.deepl.com/
- Google Translate: https://translate.google.com/
- Claude AI: For context-aware technical translations

### i18n Libraries (Future)
- Python: `gettext`, `babel`
- JavaScript: `i18next`, `vue-i18n`

### GitHub Features
- Issue templates for translations
- PR templates for review
- GitHub Actions for automation

---

## Maintenance Schedule

- **Weekly**: Check for README synchronization
- **On Release**: Update all language versions
- **Monthly**: Review and update translation guidelines
- **Quarterly**: Audit translation quality

---

## Contact

For questions about multilingual support:
- Open an issue with label `translation`
- Discuss in Discussions section
- Contact maintainers

---

**Last Updated**: 2026-01-27
**Version**: 1.0.0
