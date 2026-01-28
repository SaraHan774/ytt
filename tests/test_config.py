"""
Unit tests for ytt.config module
"""
import os
from pathlib import Path
from unittest.mock import patch, mock_open
import pytest

from ytt import config


class TestGetConfigDir:
    """get_config_dir 함수 테스트"""

    @patch('os.name', 'posix')
    @patch('pathlib.Path.home')
    def test_get_config_dir_unix(self, mock_home, temp_dir):
        """Unix-like 시스템에서 설정 디렉토리"""
        mock_home.return_value = Path(temp_dir)
        result = config.get_config_dir()
        expected = Path(temp_dir) / '.config' / 'ytt'
        assert result == expected

    @pytest.mark.skipif(os.name != 'nt', reason="Windows 전용 테스트")
    @patch('os.name', 'nt')
    @patch('os.getenv')
    def test_get_config_dir_windows(self, mock_getenv, temp_dir):
        """Windows 시스템에서 설정 디렉토리"""
        mock_getenv.return_value = temp_dir
        result = config.get_config_dir()
        expected = Path(temp_dir) / 'ytt'
        assert result == expected


class TestGetApiKey:
    """get_api_key 함수 테스트"""

    @patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'env-key-123'})
    def test_get_api_key_from_env(self):
        """환경 변수에서 API 키 가져오기"""
        result = config.get_api_key()
        assert result == 'env-key-123'

    @patch.dict(os.environ, {}, clear=True)
    @patch('ytt.config.get_config_dir')
    def test_get_api_key_from_file(self, mock_get_config_dir, temp_dir):
        """파일에서 API 키 가져오기"""
        config_dir = Path(temp_dir)
        mock_get_config_dir.return_value = config_dir

        # API 키 파일 생성
        api_key_file = config_dir / "api_key.txt"
        config_dir.mkdir(parents=True, exist_ok=True)
        with open(api_key_file, 'w') as f:
            f.write('file-key-456')

        result = config.get_api_key()
        assert result == 'file-key-456'

    @patch.dict(os.environ, {}, clear=True)
    @patch('ytt.config.get_config_dir')
    def test_get_api_key_not_found(self, mock_get_config_dir, temp_dir):
        """API 키가 없는 경우"""
        config_dir = Path(temp_dir)
        mock_get_config_dir.return_value = config_dir
        config_dir.mkdir(parents=True, exist_ok=True)

        result = config.get_api_key()
        assert result is None


class TestSetApiKey:
    """set_api_key 함수 테스트"""

    @patch('ytt.config.get_config_dir')
    def test_set_api_key(self, mock_get_config_dir, temp_dir):
        """API 키 저장"""
        config_dir = Path(temp_dir)
        mock_get_config_dir.return_value = config_dir
        config_dir.mkdir(parents=True, exist_ok=True)

        config.set_api_key('new-key-789')

        api_key_file = config_dir / "api_key.txt"
        assert api_key_file.exists()
        with open(api_key_file, 'r') as f:
            assert f.read() == 'new-key-789'

    @patch('ytt.config.get_config_dir')
    def test_set_api_key_strips_whitespace(self, mock_get_config_dir, temp_dir):
        """API 키 저장 시 공백 제거"""
        config_dir = Path(temp_dir)
        mock_get_config_dir.return_value = config_dir
        config_dir.mkdir(parents=True, exist_ok=True)

        config.set_api_key('  key-with-spaces  ')

        api_key_file = config_dir / "api_key.txt"
        with open(api_key_file, 'r') as f:
            assert f.read() == 'key-with-spaces'


class TestDeleteApiKey:
    """delete_api_key 함수 테스트"""

    @patch('ytt.config.get_config_dir')
    def test_delete_api_key(self, mock_get_config_dir, temp_dir):
        """API 키 삭제"""
        config_dir = Path(temp_dir)
        mock_get_config_dir.return_value = config_dir
        config_dir.mkdir(parents=True, exist_ok=True)

        # 먼저 API 키 생성
        api_key_file = config_dir / "api_key.txt"
        with open(api_key_file, 'w') as f:
            f.write('key-to-delete')

        assert api_key_file.exists()

        # 삭제
        config.delete_api_key()
        assert not api_key_file.exists()

    @patch('ytt.config.get_config_dir')
    def test_delete_api_key_not_exists(self, mock_get_config_dir, temp_dir):
        """존재하지 않는 API 키 삭제 (에러 없이 처리)"""
        config_dir = Path(temp_dir)
        mock_get_config_dir.return_value = config_dir
        config_dir.mkdir(parents=True, exist_ok=True)

        # 에러 없이 실행되어야 함
        config.delete_api_key()


class TestGetDefaultConfig:
    """get_default_config 함수 테스트"""

    def test_get_default_config(self):
        """기본 설정 반환"""
        result = config.get_default_config()

        assert isinstance(result, dict)
        assert 'language' in result
        assert 'default_language' in result
        assert 'default_model_size' in result
        assert 'auto_summarize' in result


class TestGetConfig:
    """get_config 함수 테스트"""

    @patch('ytt.config.get_config_dir')
    def test_get_config_file_not_exists(self, mock_get_config_dir, temp_dir):
        """설정 파일이 없을 때 기본값 반환"""
        config_dir = Path(temp_dir)
        mock_get_config_dir.return_value = config_dir
        config_dir.mkdir(parents=True, exist_ok=True)

        result = config.get_config()
        default = config.get_default_config()
        assert result == default

    @patch('ytt.config.get_config_dir')
    def test_get_config_from_file(self, mock_get_config_dir, temp_dir):
        """설정 파일에서 설정 로드"""
        import json

        config_dir = Path(temp_dir)
        mock_get_config_dir.return_value = config_dir
        config_dir.mkdir(parents=True, exist_ok=True)

        # 설정 파일 생성
        config_file = config_dir / "config.json"
        test_config = {
            'language': 'en',
            'custom_option': 'value'
        }
        with open(config_file, 'w') as f:
            json.dump(test_config, f)

        result = config.get_config()
        assert result['language'] == 'en'
        assert result['custom_option'] == 'value'
        # 기본값도 포함되어야 함
        assert 'default_model_size' in result


class TestSaveConfig:
    """save_config 함수 테스트"""

    @patch('ytt.config.get_config_dir')
    def test_save_config(self, mock_get_config_dir, temp_dir):
        """설정 저장"""
        import json

        config_dir = Path(temp_dir)
        mock_get_config_dir.return_value = config_dir
        config_dir.mkdir(parents=True, exist_ok=True)

        test_config = {
            'language': 'zh',
            'auto_summarize': True
        }

        config.save_config(test_config)

        config_file = config_dir / "config.json"
        assert config_file.exists()

        with open(config_file, 'r') as f:
            saved_config = json.load(f)
            assert saved_config == test_config
