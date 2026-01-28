"""
Unit tests for ytt.i18n module
"""
from pathlib import Path
from unittest.mock import patch, mock_open
import pytest
import json

from ytt import i18n


class TestGetLocaleDir:
    """get_locale_dir 함수 테스트"""

    def test_get_locale_dir(self):
        """locale 디렉토리 경로 반환"""
        result = i18n.get_locale_dir()
        assert isinstance(result, Path)
        assert result.name == "locales"


class TestSupportedLanguages:
    """SUPPORTED_LANGUAGES 상수 테스트"""

    def test_supported_languages(self):
        """지원하는 언어 목록 확인"""
        assert "ko" in i18n.SUPPORTED_LANGUAGES
        assert "en" in i18n.SUPPORTED_LANGUAGES
        assert "zh" in i18n.SUPPORTED_LANGUAGES


class TestLoadLanguage:
    """load_language 함수 테스트"""

    def test_load_language_from_cache(self):
        """캐시에서 언어 로드"""
        # 캐시에 미리 저장
        test_translations = {"key": "value"}
        i18n._translations["test_lang"] = test_translations

        result = i18n.load_language("test_lang")
        assert result == test_translations

        # 캐시 정리
        del i18n._translations["test_lang"]

    @patch('ytt.i18n.get_locale_dir')
    @patch('builtins.open', new_callable=mock_open, read_data='{"hello": "안녕하세요"}')
    def test_load_language_from_file(self, mock_file, mock_get_locale_dir, temp_dir):
        """파일에서 언어 로드"""
        locale_dir = Path(temp_dir) / "locales"
        locale_dir.mkdir(parents=True, exist_ok=True)
        mock_get_locale_dir.return_value = locale_dir

        # 실제 파일 생성
        ko_file = locale_dir / "ko.json"
        with open(ko_file, 'w', encoding='utf-8') as f:
            json.dump({"hello": "안녕하세요"}, f)

        # 캐시 클리어
        i18n._translations.clear()

        result = i18n.load_language("ko")
        assert "hello" in result


class TestSetLanguage:
    """set_language 함수 테스트"""

    def test_set_language(self):
        """언어 설정"""
        original_lang = i18n._current_language

        i18n.set_language("en")
        assert i18n._current_language == "en"

        # 원래 언어로 복원
        i18n._current_language = original_lang


class TestGetText:
    """get_text 함수 테스트"""

    def test_get_text_with_existing_key(self):
        """존재하는 키로 텍스트 가져오기"""
        # 테스트용 번역 설정
        i18n._translations["test"] = {"greeting": "Hello"}
        i18n._current_language = "test"

        result = i18n.get_text("greeting")
        assert result == "Hello"

        # 정리
        del i18n._translations["test"]

    def test_get_text_with_missing_key(self):
        """존재하지 않는 키는 키 자체를 반환"""
        i18n._translations["test"] = {}
        i18n._current_language = "test"

        result = i18n.get_text("missing_key")
        assert result == "missing_key"

        # 정리
        del i18n._translations["test"]
