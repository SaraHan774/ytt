"""
i18n (Internationalization) module for ytt

Provides simple JSON-based translation support for Korean, English, and Chinese.
"""

import json
import os
from pathlib import Path
from typing import Dict, Optional

# 현재 설정된 언어 (기본값: 한국어)
_current_language = "ko"

# 번역 캐시
_translations: Dict[str, Dict[str, str]] = {}

# 지원하는 언어 목록
SUPPORTED_LANGUAGES = {
    "ko": "한국어",
    "en": "English",
    "zh": "中文"
}


def get_locale_dir() -> Path:
    """locale 파일이 저장된 디렉토리 경로 반환"""
    return Path(__file__).parent / "locales"


def load_language(lang: str) -> Dict[str, str]:
    """
    특정 언어의 번역 파일 로드

    Args:
        lang: 언어 코드 (ko, en, zh)

    Returns:
        번역 딕셔너리
    """
    if lang in _translations:
        return _translations[lang]

    locale_file = get_locale_dir() / f"{lang}.json"

    if not locale_file.exists():
        # 파일이 없으면 한국어로 폴백
        if lang != "ko":
            return load_language("ko")
        return {}

    try:
        with open(locale_file, 'r', encoding='utf-8') as f:
            translations = json.load(f)
            _translations[lang] = translations
            return translations
    except Exception as e:
        print(f"Warning: Failed to load language file {locale_file}: {e}")
        if lang != "ko":
            return load_language("ko")
        return {}


def set_language(lang: str):
    """
    현재 언어 설정

    Args:
        lang: 언어 코드 (ko, en, zh)
    """
    global _current_language

    if lang not in SUPPORTED_LANGUAGES:
        print(f"Warning: Unsupported language '{lang}', falling back to Korean")
        lang = "ko"

    _current_language = lang
    # 미리 로드
    load_language(lang)


def get_language() -> str:
    """현재 설정된 언어 코드 반환"""
    return _current_language


def t(key: str, **kwargs) -> str:
    """
    번역 함수 (translate의 약자)

    Args:
        key: 번역 키 (예: "setup.welcome", "cli.help")
        **kwargs: 포맷 문자열 인자

    Returns:
        번역된 문자열

    Examples:
        >>> t("setup.welcome")
        "YouTube Transcript Tool 설정"

        >>> t("setup.processing", file="video.mp4")
        "video.mp4 처리 중..."
    """
    translations = load_language(_current_language)

    # 키를 찾되, 없으면 키 자체를 반환
    text = translations.get(key, f"[{key}]")

    # 포맷 문자열 처리
    if kwargs:
        try:
            text = text.format(**kwargs)
        except KeyError as e:
            print(f"Warning: Missing format key {e} in translation '{key}'")

    return text


def init_i18n_from_config():
    """
    사용자 설정에서 언어를 읽어와서 초기화
    """
    try:
        from . import config
        user_config = config.get_config()
        lang = user_config.get('language', 'ko')
        set_language(lang)
    except Exception:
        # 설정 파일이 없거나 읽기 실패 시 기본값 사용
        set_language('ko')


def get_language_name(lang_code: str) -> str:
    """
    언어 코드를 언어 이름으로 변환

    Args:
        lang_code: 언어 코드 (ko, en, zh)

    Returns:
        언어 이름
    """
    return SUPPORTED_LANGUAGES.get(lang_code, lang_code)


def list_languages() -> Dict[str, str]:
    """
    지원하는 언어 목록 반환

    Returns:
        {언어코드: 언어이름} 딕셔너리
    """
    return SUPPORTED_LANGUAGES.copy()


# 자동 초기화 (모듈 import 시)
try:
    init_i18n_from_config()
except Exception:
    # 초기화 실패해도 기본값으로 진행
    pass
