"""
CLI 테스트
"""
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest
from click.testing import CliRunner

# ytt 패키지 import
sys.path.insert(0, str(Path(__file__).parent.parent))
from ytt import cli, core, config


class TestCLI:
    """CLI 인터페이스 테스트"""

    def test_cli_help(self):
        """--help 옵션 테스트"""
        runner = CliRunner()
        result = runner.invoke(cli.main, ['--help'])

        assert result.exit_code == 0
        assert 'YouTube Transcript Tool' in result.output
        assert 'youtube_url' in result.output.lower()
        assert 'output_dir' in result.output.lower()

    def test_cli_version(self):
        """--version 옵션 테스트"""
        runner = CliRunner()
        result = runner.invoke(cli.main, ['--version'])

        assert result.exit_code == 0
        assert '1.0.0' in result.output

    @patch('ytt.core.download_youtube')
    @patch('ytt.core.chunk_audio')
    @patch('ytt.core.transcribe_audio')
    @patch('ytt.core.save_transcripts')
    @patch('ytt.core.cleanup_temp_files')
    def test_cli_basic_flow(
        self,
        mock_cleanup,
        mock_save,
        mock_transcribe,
        mock_chunk,
        mock_download,
        temp_dir
    ):
        """기본 CLI 플로우 테스트"""
        runner = CliRunner()

        # Mock 설정
        mock_download.return_value = {
            'audio_path': Path(temp_dir) / 'audio.mp3',
            'title': 'Test Video',
            'duration': 120,
            'url': 'https://youtube.com/watch?v=test'
        }

        mock_chunk.return_value = [
            Path(temp_dir) / 'chunk1.mp3',
            Path(temp_dir) / 'chunk2.mp3'
        ]

        mock_transcribe.return_value = [
            {'chunk_id': 0, 'segments': [{'text': 'Test 1', 'start': 0, 'end': 1}]},
            {'chunk_id': 1, 'segments': [{'text': 'Test 2', 'start': 1, 'end': 2}]}
        ]

        # CLI 실행
        output_dir = Path(temp_dir) / 'output'
        result = runner.invoke(cli.main, [
            'https://youtube.com/watch?v=test',
            str(output_dir),
            '-m', 'tiny',  # 빠른 모델
        ])

        # 검증
        assert result.exit_code == 0
        assert '다운로드 완료' in result.output
        assert '전사 완료' in result.output

        # 함수 호출 확인
        assert mock_download.called
        assert mock_chunk.called
        assert mock_transcribe.called
        assert mock_save.called

    @patch('ytt.core.download_youtube')
    @patch('ytt.core.chunk_audio')
    @patch('ytt.core.transcribe_audio')
    @patch('ytt.core.save_transcripts')
    @patch('ytt.core.summarize_with_claude')
    @patch('ytt.core.save_summary')
    @patch('ytt.config.get_api_key')
    def test_cli_with_summarize(
        self,
        mock_get_api_key,
        mock_save_summary,
        mock_summarize,
        mock_save_transcripts,
        mock_transcribe,
        mock_chunk,
        mock_download,
        temp_dir
    ):
        """--summarize 옵션 테스트"""
        runner = CliRunner()

        # Mock 설정
        mock_get_api_key.return_value = "test-api-key"

        mock_download.return_value = {
            'audio_path': Path(temp_dir) / 'audio.mp3',
            'title': 'Test Video',
            'duration': 120,
            'url': 'https://youtube.com/watch?v=test'
        }

        mock_chunk.return_value = [Path(temp_dir) / 'chunk1.mp3']

        mock_transcribe.return_value = [{
            'chunk_id': 0,
            'segments': [{'text': 'Test', 'start': 0, 'end': 1}]
        }]

        mock_summarize.return_value = {
            'long_summary': 'Long summary',
            'short_summary': 'Short summary'
        }

        # CLI 실행
        output_dir = Path(temp_dir) / 'output'
        result = runner.invoke(cli.main, [
            'https://youtube.com/watch?v=test',
            str(output_dir),
            '--summarize'
        ])

        # 검증
        assert result.exit_code == 0
        assert '요약 완료' in result.output
        assert mock_summarize.called
        assert mock_save_summary.called

    def test_cli_missing_arguments(self):
        """필수 인자 누락 시 에러"""
        runner = CliRunner()

        # URL만 제공
        result = runner.invoke(cli.main, ['https://youtube.com/watch?v=test'])
        assert result.exit_code != 0

        # 인자 없음
        result = runner.invoke(cli.main, [])
        assert result.exit_code != 0

    def test_cli_invalid_model_size(self):
        """유효하지 않은 모델 크기"""
        runner = CliRunner()

        result = runner.invoke(cli.main, [
            'https://youtube.com/watch?v=test',
            './output',
            '-m', 'invalid'
        ])

        assert result.exit_code != 0
        assert 'Invalid value' in result.output or 'invalid' in result.output.lower()


class TestConfig:
    """설정 관리 테스트"""

    def test_get_config_dir(self):
        """설정 디렉토리 생성 확인"""
        config_dir = config.get_config_dir()

        assert config_dir.exists()
        assert config_dir.is_dir()

    def test_set_and_get_api_key(self):
        """API 키 저장 및 읽기"""
        test_key = "test-api-key-123"

        # 저장
        config.set_api_key(test_key)

        # 읽기
        retrieved_key = config.get_api_key()
        assert retrieved_key == test_key

        # 정리
        config.delete_api_key()

    def test_api_key_from_env(self, monkeypatch):
        """환경 변수에서 API 키 읽기"""
        test_key = "env-api-key"
        monkeypatch.setenv("ANTHROPIC_API_KEY", test_key)

        key = config.get_api_key()
        assert key == test_key

    def test_api_key_priority(self, monkeypatch):
        """API 키 우선순위 (환경 변수 > 파일)"""
        # 파일에 저장
        file_key = "file-key"
        config.set_api_key(file_key)

        # 환경 변수 설정
        env_key = "env-key"
        monkeypatch.setenv("ANTHROPIC_API_KEY", env_key)

        # 환경 변수가 우선
        key = config.get_api_key()
        assert key == env_key

        # 정리
        config.delete_api_key()


class TestCore:
    """Core 함수 테스트"""

    def test_format_time(self):
        """시간 포맷 변환 테스트"""
        assert core.format_time(0) == "00:00:00"
        assert core.format_time(61) == "00:01:01"
        assert core.format_time(3661) == "01:01:01"
        assert core.format_time(3723.5) == "01:02:03"

    @patch('ytt.core.get_whisper_model')
    def test_transcribe_audio_empty_list(self, mock_get_model):
        """빈 오디오 리스트 전사"""
        result = core.transcribe_audio([])
        assert result == []

    def test_find_audio_files_empty(self, temp_dir):
        """빈 디렉토리에서 오디오 파일 찾기"""
        result = core.find_audio_files(temp_dir)
        assert result == []

    def test_find_audio_files_with_files(self, temp_dir):
        """오디오 파일이 있는 디렉토리"""
        # 테스트 파일 생성
        (Path(temp_dir) / "test1.mp3").touch()
        (Path(temp_dir) / "test2.mp3").touch()
        (Path(temp_dir) / "test3.txt").touch()

        result = core.find_audio_files(temp_dir)
        assert len(result) == 2
        assert all(f.endswith('.mp3') for f in result)


@pytest.mark.integration
class TestCLIIntegration:
    """CLI 통합 테스트"""

    @patch('ytt.core.download_youtube')
    @patch('ytt.core.chunk_audio')
    @patch('ytt.core.transcribe_audio')
    def test_full_pipeline_without_network(
        self,
        mock_transcribe,
        mock_chunk,
        mock_download,
        temp_dir
    ):
        """전체 파이프라인 (네트워크 호출 없이)"""
        runner = CliRunner()

        # Mock 설정
        audio_file = Path(temp_dir) / 'test.mp3'
        audio_file.touch()

        mock_download.return_value = {
            'audio_path': audio_file,
            'title': 'Integration Test Video',
            'duration': 60,
            'url': 'https://youtube.com/watch?v=test'
        }

        chunk1 = Path(temp_dir) / 'chunk_001.mp3'
        chunk1.touch()
        mock_chunk.return_value = [chunk1]

        mock_transcribe.return_value = [{
            'chunk_id': 0,
            'file': 'chunk_001.mp3',
            'language': 'ko',
            'segments': [
                {'start': 0.0, 'end': 1.0, 'text': '안녕하세요'},
                {'start': 1.0, 'end': 2.0, 'text': '테스트입니다'}
            ]
        }]

        # CLI 실행
        output_dir = Path(temp_dir) / 'output'
        result = runner.invoke(cli.main, [
            'https://youtube.com/watch?v=test',
            str(output_dir),
            '-m', 'tiny',
            '--verbose'
        ])

        # 검증
        assert result.exit_code == 0

        # 출력 파일 확인
        assert (output_dir / 'transcript.txt').exists()
        assert (output_dir / 'transcript_with_timestamps.txt').exists()
        assert (output_dir / 'transcript.json').exists()
        assert (output_dir / 'metadata.json').exists()
