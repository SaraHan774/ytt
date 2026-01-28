"""
Unit tests for ytt.cli module
"""
import os
import logging
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest
from click.testing import CliRunner

from ytt import cli


class TestSetupLogging:
    """setup_logging 함수 테스트"""

    @patch('logging.basicConfig')
    def test_setup_logging_not_verbose(self, mock_basicConfig):
        """일반 모드 로깅 설정"""
        cli.setup_logging(verbose=False)
        mock_basicConfig.assert_called_once()
        # level이 INFO로 설정되었는지 확인
        call_args = mock_basicConfig.call_args[1]
        assert call_args['level'] == logging.INFO

    @patch('logging.basicConfig')
    def test_setup_logging_verbose(self, mock_basicConfig):
        """상세 모드 로깅 설정"""
        cli.setup_logging(verbose=True)
        mock_basicConfig.assert_called_once()
        # level이 DEBUG로 설정되었는지 확인
        call_args = mock_basicConfig.call_args[1]
        assert call_args['level'] == logging.DEBUG


class TestMainCommand:
    """main CLI 명령어 테스트"""

    @patch('ytt.cli.setup.check_first_run')
    @patch('ytt.cli.core.download_youtube')
    @patch('ytt.cli.core.chunk_audio')
    @patch('ytt.cli.core.transcribe_audio')
    @patch('ytt.cli.core.save_transcripts')
    @patch('ytt.cli.core.cleanup_temp_files')
    @patch('ytt.cli.core.save_metadata')
    def test_main_basic_transcription(
        self,
        mock_save_metadata,
        mock_cleanup,
        mock_save_transcripts,
        mock_transcribe,
        mock_chunk,
        mock_download,
        mock_check_first_run,
        temp_dir
    ):
        """기본 전사 작업 테스트"""
        runner = CliRunner()

        # Mock 설정
        mock_check_first_run.return_value = False

        output_dir = Path(temp_dir) / "output"
        mock_download.return_value = {
            'audio_path': Path(temp_dir) / "audio.mp3",
            'title': 'Test Video',
            'duration': 100,
            'url': 'https://youtube.com/watch?v=test'
        }
        mock_chunk.return_value = [Path(temp_dir) / "chunk1.mp3"]
        mock_transcribe.return_value = [
            {'chunk_id': 0, 'segments': [{'text': 'test', 'start': 0, 'end': 1}]}
        ]

        result = runner.invoke(cli.main, [
            'https://youtube.com/watch?v=test',
            str(output_dir)
        ])

        assert result.exit_code == 0
        assert mock_download.called
        assert mock_chunk.called
        assert mock_transcribe.called
        assert mock_save_transcripts.called

    @patch('ytt.cli.setup.check_first_run')
    def test_main_help(self, mock_check_first_run):
        """도움말 출력 테스트"""
        mock_check_first_run.return_value = False
        runner = CliRunner()
        result = runner.invoke(cli.main, ['--help'])

        assert result.exit_code == 0
        assert 'YouTube Transcript Tool' in result.output

    @patch('ytt.cli.setup.check_first_run')
    def test_main_version(self, mock_check_first_run):
        """버전 출력 테스트"""
        mock_check_first_run.return_value = False
        runner = CliRunner()
        result = runner.invoke(cli.main, ['--version'])

        assert result.exit_code == 0
        assert 'ytt' in result.output
        assert '1.0' in result.output

    @patch('ytt.cli.setup.check_first_run')
    @patch('ytt.cli.core.summarize_with_claude')
    @patch('ytt.cli.core.save_summary')
    @patch('ytt.cli.core.download_youtube')
    @patch('ytt.cli.core.chunk_audio')
    @patch('ytt.cli.core.transcribe_audio')
    @patch('ytt.cli.core.save_transcripts')
    @patch('ytt.cli.core.cleanup_temp_files')
    @patch('ytt.cli.core.save_metadata')
    @patch('ytt.cli.config.get_api_key')
    def test_main_with_summarize(
        self,
        mock_get_api_key,
        mock_save_metadata,
        mock_cleanup,
        mock_save_transcripts,
        mock_transcribe,
        mock_chunk,
        mock_download,
        mock_save_summary,
        mock_summarize,
        mock_check_first_run,
        temp_dir
    ):
        """요약 옵션 포함 테스트"""
        runner = CliRunner()

        mock_check_first_run.return_value = False
        mock_get_api_key.return_value = 'test-key'

        output_dir = Path(temp_dir) / "output"
        mock_download.return_value = {
            'audio_path': Path(temp_dir) / "audio.mp3",
            'title': 'Test Video',
            'duration': 100,
            'url': 'https://youtube.com/watch?v=test'
        }
        mock_chunk.return_value = [Path(temp_dir) / "chunk1.mp3"]
        mock_transcribe.return_value = [
            {'chunk_id': 0, 'segments': [{'text': 'test', 'start': 0, 'end': 1}]}
        ]
        mock_summarize.return_value = {
            'long_summary': 'Long summary',
            'short_summary': 'Short summary'
        }

        result = runner.invoke(cli.main, [
            'https://youtube.com/watch?v=test',
            str(output_dir),
            '--summarize'
        ])

        assert result.exit_code == 0
        assert mock_summarize.called
        assert mock_save_summary.called


class TestCLIOptions:
    """CLI 옵션 테스트"""

    @patch('ytt.cli.setup.check_first_run')
    @patch('ytt.cli.core.download_youtube')
    @patch('ytt.cli.core.chunk_audio')
    @patch('ytt.cli.core.transcribe_audio')
    @patch('ytt.cli.core.save_transcripts')
    @patch('ytt.cli.core.save_metadata')
    def test_model_size_option(
        self,
        mock_save_metadata,
        mock_save_transcripts,
        mock_transcribe,
        mock_chunk,
        mock_download,
        mock_check_first_run,
        temp_dir
    ):
        """모델 크기 옵션 테스트"""
        runner = CliRunner()

        mock_check_first_run.return_value = False
        output_dir = Path(temp_dir) / "output"
        mock_download.return_value = {
            'audio_path': Path(temp_dir) / "audio.mp3",
            'title': 'Test Video',
            'duration': 100,
            'url': 'https://youtube.com/watch?v=test'
        }
        mock_chunk.return_value = [Path(temp_dir) / "chunk1.mp3"]
        mock_transcribe.return_value = [
            {'chunk_id': 0, 'segments': [{'text': 'test', 'start': 0, 'end': 1}]}
        ]

        result = runner.invoke(cli.main, [
            'https://youtube.com/watch?v=test',
            str(output_dir),
            '--model-size', 'medium'
        ])

        assert result.exit_code == 0
        # transcribe_audio가 medium 모델로 호출되었는지 확인
        call_args = mock_transcribe.call_args
        assert call_args[1]['model_size'] == 'medium'

    @patch('ytt.cli.setup.check_first_run')
    @patch('ytt.cli.core.download_youtube')
    @patch('ytt.cli.core.chunk_audio')
    @patch('ytt.cli.core.transcribe_audio')
    @patch('ytt.cli.core.save_transcripts')
    @patch('ytt.cli.core.save_metadata')
    def test_language_option(
        self,
        mock_save_metadata,
        mock_save_transcripts,
        mock_transcribe,
        mock_chunk,
        mock_download,
        mock_check_first_run,
        temp_dir
    ):
        """언어 옵션 테스트"""
        runner = CliRunner()

        mock_check_first_run.return_value = False
        output_dir = Path(temp_dir) / "output"
        mock_download.return_value = {
            'audio_path': Path(temp_dir) / "audio.mp3",
            'title': 'Test Video',
            'duration': 100,
            'url': 'https://youtube.com/watch?v=test'
        }
        mock_chunk.return_value = [Path(temp_dir) / "chunk1.mp3"]
        mock_transcribe.return_value = [
            {'chunk_id': 0, 'segments': [{'text': 'test', 'start': 0, 'end': 1}]}
        ]

        result = runner.invoke(cli.main, [
            'https://youtube.com/watch?v=test',
            str(output_dir),
            '--language', 'en'
        ])

        assert result.exit_code == 0
        # transcribe_audio가 en 언어로 호출되었는지 확인
        call_args = mock_transcribe.call_args
        assert call_args[1]['language'] == 'en'

    @patch('ytt.cli.setup.check_first_run')
    @patch('ytt.cli.core.download_youtube')
    @patch('ytt.cli.core.chunk_audio')
    @patch('ytt.cli.core.transcribe_audio')
    @patch('ytt.cli.core.save_transcripts')
    @patch('ytt.cli.core.cleanup_temp_files')
    @patch('ytt.cli.core.save_metadata')
    def test_no_cleanup_option(
        self,
        mock_save_metadata,
        mock_cleanup,
        mock_save_transcripts,
        mock_transcribe,
        mock_chunk,
        mock_download,
        mock_check_first_run,
        temp_dir
    ):
        """cleanup 비활성화 옵션 테스트"""
        runner = CliRunner()

        mock_check_first_run.return_value = False
        output_dir = Path(temp_dir) / "output"
        mock_download.return_value = {
            'audio_path': Path(temp_dir) / "audio.mp3",
            'title': 'Test Video',
            'duration': 100,
            'url': 'https://youtube.com/watch?v=test'
        }
        mock_chunk.return_value = [Path(temp_dir) / "chunk1.mp3"]
        mock_transcribe.return_value = [
            {'chunk_id': 0, 'segments': [{'text': 'test', 'start': 0, 'end': 1}]}
        ]

        result = runner.invoke(cli.main, [
            'https://youtube.com/watch?v=test',
            str(output_dir),
            '--no-cleanup'
        ])

        assert result.exit_code == 0
        # cleanup이 호출되지 않아야 함
        assert not mock_cleanup.called
