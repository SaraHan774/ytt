"""
Unit tests for ytt.core module
"""
import os
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open
import pytest
import numpy as np
import soundfile as sf

# ytt.core 모듈 import
from ytt import core


class TestFindAudioFiles:
    """find_audio_files 함수 테스트"""

    def test_find_audio_files_empty_directory(self, temp_dir):
        """빈 디렉토리에서 오디오 파일 찾기"""
        result = core.find_audio_files(temp_dir)
        assert result == []

    def test_find_audio_files_with_mp3_files(self, temp_dir):
        """MP3 파일이 있는 디렉토리에서 찾기"""
        test_files = ["test1.mp3", "test2.mp3", "test3.txt"]
        for filename in test_files:
            filepath = os.path.join(temp_dir, filename)
            with open(filepath, "w") as f:
                f.write("test")

        result = core.find_audio_files(temp_dir)
        assert len(result) == 2
        assert all(f.endswith(".mp3") for f in result)

    def test_find_audio_files_with_custom_extension(self, temp_dir):
        """커스텀 확장자로 오디오 파일 찾기"""
        test_files = ["test1.wav", "test2.wav", "test3.mp3"]
        for filename in test_files:
            filepath = os.path.join(temp_dir, filename)
            with open(filepath, "w") as f:
                f.write("test")

        result = core.find_audio_files(temp_dir, extension=".wav")
        assert len(result) == 2
        assert all(f.endswith(".wav") for f in result)

    def test_find_audio_files_nested_directories(self, temp_dir):
        """중첩된 디렉토리에서 오디오 파일 찾기"""
        nested_dir = os.path.join(temp_dir, "nested")
        os.makedirs(nested_dir)

        with open(os.path.join(temp_dir, "top.mp3"), "w") as f:
            f.write("test")
        with open(os.path.join(nested_dir, "nested.mp3"), "w") as f:
            f.write("test")

        result = core.find_audio_files(temp_dir)
        assert len(result) == 2


class TestFormatTime:
    """format_time 함수 테스트"""

    def test_format_time_zero(self):
        """0초 포맷팅"""
        result = core.format_time(0)
        assert result == "00:00:00"

    def test_format_time_seconds_only(self):
        """초만 있는 경우"""
        result = core.format_time(45)
        assert result == "00:00:45"

    def test_format_time_minutes_and_seconds(self):
        """분과 초가 있는 경우"""
        result = core.format_time(125)  # 2분 5초
        assert result == "00:02:05"

    def test_format_time_hours_minutes_seconds(self):
        """시, 분, 초 모두 있는 경우"""
        result = core.format_time(3661)  # 1시간 1분 1초
        assert result == "01:01:01"

    def test_format_time_with_decimals(self):
        """소수점이 있는 초"""
        result = core.format_time(125.7)
        assert result == "00:02:05"


class TestGetWhisperModel:
    """get_whisper_model 함수 테스트"""

    @patch('ytt.core.WhisperModel')
    def test_get_whisper_model_gpu_success(self, mock_whisper_model):
        """GPU로 모델 로드 성공"""
        mock_model = Mock()
        mock_whisper_model.return_value = mock_model

        # 캐시 클리어
        core.get_whisper_model.cache_clear()

        result = core.get_whisper_model("base")

        # GPU 설정으로 호출되었는지 확인
        mock_whisper_model.assert_called_once_with(
            "base",
            device="cuda",
            compute_type="float16"
        )
        assert result == mock_model

    @patch('ytt.core.WhisperModel')
    def test_get_whisper_model_gpu_fallback_to_cpu(self, mock_whisper_model):
        """GPU 실패 시 CPU로 fallback"""
        # GPU 시도 시 실패, CPU는 성공
        mock_cpu_model = Mock()
        mock_whisper_model.side_effect = [
            Exception("CUDA not available"),
            mock_cpu_model
        ]

        # 캐시 클리어
        core.get_whisper_model.cache_clear()

        result = core.get_whisper_model("large")

        # GPU 시도 후 CPU로 fallback 확인
        assert mock_whisper_model.call_count == 2
        # 두 번째 호출이 CPU 설정인지 확인
        assert mock_whisper_model.call_args_list[1][0][0] == "large"
        assert mock_whisper_model.call_args_list[1][1]["device"] == "cpu"
        assert mock_whisper_model.call_args_list[1][1]["compute_type"] == "int8"
        assert result == mock_cpu_model


class TestChunkAudio:
    """chunk_audio 함수 테스트"""

    def test_chunk_audio_creates_directory(self, mock_audio_file, temp_dir):
        """청킹 시 디렉토리가 생성되는지 확인"""
        output_dir = Path(temp_dir) / "output"
        result = core.chunk_audio(Path(mock_audio_file), output_dir, segment_length=1)

        chunks_dir = output_dir / "chunks"
        assert chunks_dir.exists()
        assert len(result) > 0

    def test_chunk_audio_returns_sorted_paths(self, mock_audio_file, temp_dir):
        """청크 파일들이 Path 객체이고 정렬되어 있는지 확인"""
        output_dir = Path(temp_dir) / "output"
        result = core.chunk_audio(Path(mock_audio_file), output_dir, segment_length=1)

        assert all(isinstance(p, Path) for p in result)
        assert result == sorted(result)

    def test_chunk_audio_files_exist(self, mock_audio_file, temp_dir):
        """생성된 청크 파일들이 실제로 존재하는지 확인"""
        output_dir = Path(temp_dir) / "output"
        result = core.chunk_audio(Path(mock_audio_file), output_dir, segment_length=1)

        assert all(chunk_path.exists() for chunk_path in result)
        assert all(chunk_path.suffix == ".mp3" for chunk_path in result)


class TestDownloadYoutube:
    """download_youtube 함수 테스트"""

    @patch('ytt.core.yt_dlp.YoutubeDL')
    @patch('ytt.core.find_audio_files')
    def test_download_youtube_success(self, mock_find_audio, mock_yt_dlp, temp_dir):
        """YouTube 다운로드 성공 케이스"""
        output_dir = Path(temp_dir)
        test_url = "https://www.youtube.com/watch?v=test123"

        # Mock yt-dlp
        mock_info = {
            'title': 'Test Video',
            'duration': 300,
            'uploader': 'Test Channel'
        }
        mock_ydl_instance = MagicMock()
        mock_ydl_instance.extract_info.return_value = mock_info
        mock_yt_dlp.return_value.__enter__.return_value = mock_ydl_instance

        # Mock find_audio_files
        mock_audio_path = str(output_dir / "raw_audio" / "test.mp3")
        mock_find_audio.return_value = [mock_audio_path]

        result = core.download_youtube(test_url, output_dir)

        # 검증
        assert result['title'] == 'Test Video'
        assert result['duration'] == 300
        assert result['url'] == test_url
        assert result['uploader'] == 'Test Channel'
        assert isinstance(result['audio_path'], Path)

    @patch('ytt.core.yt_dlp.YoutubeDL')
    @patch('ytt.core.find_audio_files')
    def test_download_youtube_no_audio_file(self, mock_find_audio, mock_yt_dlp, temp_dir):
        """다운로드 후 오디오 파일을 찾을 수 없는 경우"""
        output_dir = Path(temp_dir)
        test_url = "https://www.youtube.com/watch?v=test123"

        mock_ydl_instance = MagicMock()
        mock_ydl_instance.extract_info.return_value = {'title': 'Test'}
        mock_yt_dlp.return_value.__enter__.return_value = mock_ydl_instance

        # 오디오 파일을 찾지 못함
        mock_find_audio.return_value = []

        with pytest.raises(ValueError, match="No audio file found after download"):
            core.download_youtube(test_url, output_dir)

    @patch('ytt.core.yt_dlp.YoutubeDL')
    def test_download_youtube_download_error(self, mock_yt_dlp, temp_dir):
        """다운로드 에러 처리"""
        from yt_dlp.utils import DownloadError

        output_dir = Path(temp_dir)
        test_url = "https://www.youtube.com/watch?v=invalid"

        mock_ydl_instance = MagicMock()
        mock_ydl_instance.extract_info.side_effect = DownloadError("Download failed")
        mock_yt_dlp.return_value.__enter__.return_value = mock_ydl_instance

        with pytest.raises(DownloadError):
            core.download_youtube(test_url, output_dir)


class TestTranscribeAudio:
    """transcribe_audio 함수 테스트"""

    @patch('ytt.core.get_whisper_model')
    def test_transcribe_audio_single_file(self, mock_get_model, mock_audio_file):
        """단일 오디오 파일 전사"""
        # Mock Whisper 모델
        mock_segment = Mock()
        mock_segment.start = 0.0
        mock_segment.end = 1.0
        mock_segment.text = "테스트 전사 결과"

        mock_model = Mock()
        mock_info = Mock()
        mock_info.language = "ko"
        mock_model.transcribe.return_value = ([mock_segment], mock_info)
        mock_get_model.return_value = mock_model

        result = core.transcribe_audio([Path(mock_audio_file)], model_size="base")

        assert len(result) == 1
        assert result[0]['chunk_id'] == 0
        assert result[0]['language'] == "ko"
        assert len(result[0]['segments']) == 1
        assert result[0]['segments'][0]['text'] == "테스트 전사 결과"

    @patch('ytt.core.get_whisper_model')
    def test_transcribe_audio_multiple_files(self, mock_get_model, mock_audio_files):
        """여러 오디오 파일 전사"""
        mock_segment = Mock()
        mock_segment.start = 0.0
        mock_segment.end = 1.0
        mock_segment.text = "테스트"

        mock_model = Mock()
        mock_info = Mock()
        mock_info.language = "ko"
        mock_model.transcribe.return_value = ([mock_segment], mock_info)
        mock_get_model.return_value = mock_model

        audio_paths = [Path(f) for f in mock_audio_files]
        result = core.transcribe_audio(audio_paths, model_size="base", language="ko")

        assert len(result) == len(mock_audio_files)
        # chunk_id가 순서대로인지 확인
        for i, chunk in enumerate(result):
            assert chunk['chunk_id'] == i

    @patch('ytt.core._transcribe_single_chunk')
    def test_transcribe_audio_with_exception_handling(self, mock_transcribe_chunk, mock_audio_files):
        """전사 중 일부 청크에서 예외 발생 시 처리"""
        # 첫 번째와 세 번째는 성공, 두 번째는 None (실패)
        mock_transcribe_chunk.side_effect = [
            {'chunk_id': 0, 'segments': [{'text': 'first'}]},
            None,  # 실패한 청크
            {'chunk_id': 2, 'segments': [{'text': 'third'}]}
        ]

        audio_paths = [Path(f) for f in mock_audio_files]
        result = core.transcribe_audio(audio_paths, model_size="base")

        # None이 아닌 결과만 포함되어야 함
        assert len(result) == 2
        assert result[0]['chunk_id'] == 0
        assert result[1]['chunk_id'] == 2


class TestSaveTranscripts:
    """save_transcripts 함수 테스트"""

    def test_save_transcripts_creates_files(self, temp_dir):
        """전사 결과 파일들이 생성되는지 확인"""
        output_dir = Path(temp_dir)
        transcripts = [
            {
                'chunk_id': 0,
                'segments': [
                    {'start': 0.0, 'end': 1.0, 'text': '첫 번째 세그먼트'},
                    {'start': 1.0, 'end': 2.0, 'text': '두 번째 세그먼트'}
                ]
            }
        ]

        core.save_transcripts(transcripts, output_dir, video_title="테스트 비디오")

        # 파일들이 생성되었는지 확인
        assert (output_dir / "transcript.txt").exists()
        assert (output_dir / "transcript_with_timestamps.txt").exists()
        assert (output_dir / "transcript.json").exists()

    def test_save_transcripts_content(self, temp_dir):
        """저장된 내용이 올바른지 확인"""
        output_dir = Path(temp_dir)
        transcripts = [
            {
                'chunk_id': 0,
                'segments': [
                    {'start': 0.0, 'end': 1.5, 'text': '테스트 텍스트'}
                ]
            }
        ]

        core.save_transcripts(transcripts, output_dir, video_title="Test")

        # 평문 텍스트 확인
        with open(output_dir / "transcript.txt", "r", encoding="utf-8") as f:
            content = f.read()
            assert "Test" in content
            assert "테스트 텍스트" in content

        # JSON 확인
        with open(output_dir / "transcript.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            assert data['title'] == "Test"
            assert len(data['chunks']) == 1


class TestSummarizeWithClaude:
    """summarize_with_claude 함수 테스트"""

    @patch('ytt.core.Anthropic')
    def test_summarize_with_claude_success(self, mock_anthropic_class, mock_env_vars):
        """Claude 요약 성공 케이스"""
        # Mock Anthropic client
        mock_content = Mock()
        mock_content.text = "요약된 텍스트"
        mock_message = Mock()
        mock_message.content = [mock_content]

        mock_client = Mock()
        mock_client.messages.create.return_value = mock_message
        mock_anthropic_class.return_value = mock_client

        transcripts = [
            {
                'segments': [
                    {'text': '첫 번째 텍스트'},
                    {'text': '두 번째 텍스트'}
                ]
            }
        ]

        result = core.summarize_with_claude(
            transcripts,
            api_key="test-key",
            language="ko"
        )

        assert 'long_summary' in result
        assert 'short_summary' in result
        assert isinstance(result['long_summary'], str)
        assert isinstance(result['short_summary'], str)

    @patch('ytt.core.Anthropic')
    @patch.dict(os.environ, {}, clear=True)
    def test_summarize_with_claude_no_api_key(self, mock_anthropic_class):
        """API 키가 없는 경우 (환경 변수도 없음)"""
        transcripts = [{'segments': [{'text': 'test'}]}]

        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY not found"):
            core.summarize_with_claude(transcripts, api_key=None)

    @patch('ytt.core.Anthropic')
    def test_summarize_with_claude_different_languages(self, mock_anthropic_class, mock_env_vars):
        """다양한 언어로 요약"""
        mock_content = Mock()
        mock_content.text = "Summary"
        mock_message = Mock()
        mock_message.content = [mock_content]

        mock_client = Mock()
        mock_client.messages.create.return_value = mock_message
        mock_anthropic_class.return_value = mock_client

        transcripts = [{'segments': [{'text': 'test'}]}]

        for lang in ['ko', 'en', 'zh']:
            result = core.summarize_with_claude(
                transcripts,
                api_key="test-key",
                language=lang
            )
            assert 'long_summary' in result
            assert 'short_summary' in result

    @patch('ytt.core.Anthropic')
    def test_summarize_with_claude_unsupported_language(self, mock_anthropic_class, mock_env_vars):
        """지원하지 않는 언어는 한국어로 fallback"""
        mock_content = Mock()
        mock_content.text = "요약"
        mock_message = Mock()
        mock_message.content = [mock_content]

        mock_client = Mock()
        mock_client.messages.create.return_value = mock_message
        mock_anthropic_class.return_value = mock_client

        transcripts = [{'segments': [{'text': 'test'}]}]

        # 지원하지 않는 언어 코드
        result = core.summarize_with_claude(
            transcripts,
            api_key="test-key",
            language="fr"  # 프랑스어는 지원하지 않음
        )

        assert 'long_summary' in result
        assert 'short_summary' in result

    @patch('ytt.core.Anthropic')
    def test_summarize_with_claude_chunk_error(self, mock_anthropic_class, mock_env_vars):
        """청크 요약 중 에러 발생"""
        mock_client = Mock()
        # 첫 번째 호출은 에러, 두 번째는 성공
        mock_client.messages.create.side_effect = [
            Exception("API Error"),
            Mock(content=[Mock(text="최종 요약")])
        ]
        mock_anthropic_class.return_value = mock_client

        transcripts = [{'segments': [{'text': 'test'}]}]

        result = core.summarize_with_claude(
            transcripts,
            api_key="test-key"
        )

        # 에러가 발생해도 결과는 반환되어야 함
        assert 'long_summary' in result
        assert '[요약 실패' in result['long_summary']

    @patch('ytt.core.Anthropic')
    def test_summarize_with_claude_final_summary_error(self, mock_anthropic_class, mock_env_vars):
        """최종 요약 중 에러 발생"""
        mock_content = Mock()
        mock_content.text = "청크 요약"
        mock_message = Mock()
        mock_message.content = [mock_content]

        mock_client = Mock()
        # 청크 요약은 성공, 최종 요약은 실패
        mock_client.messages.create.side_effect = [
            mock_message,  # 청크 요약 성공
            Exception("Final summary error")  # 최종 요약 실패
        ]
        mock_anthropic_class.return_value = mock_client

        transcripts = [{'segments': [{'text': 'test'}]}]

        result = core.summarize_with_claude(
            transcripts,
            api_key="test-key"
        )

        assert 'long_summary' in result
        assert 'short_summary' in result
        assert result['short_summary'] == "[최종 요약 실패]"


class TestSaveSummary:
    """save_summary 함수 테스트"""

    def test_save_summary_creates_file(self, temp_dir):
        """요약 파일이 생성되는지 확인"""
        output_dir = Path(temp_dir)
        summary = {
            'long_summary': '상세한 요약입니다.',
            'short_summary': '짧은 요약입니다.'
        }

        core.save_summary(summary, output_dir)

        summary_file = output_dir / "summary.txt"
        assert summary_file.exists()

        with open(summary_file, "r", encoding="utf-8") as f:
            content = f.read()
            assert '상세한 요약입니다.' in content
            assert '짧은 요약입니다.' in content


class TestSaveMetadata:
    """save_metadata 함수 테스트"""

    def test_save_metadata_creates_json(self, temp_dir):
        """메타데이터 JSON 파일이 생성되는지 확인"""
        output_dir = Path(temp_dir)
        metadata = {
            'title': 'Test Video',
            'duration': 300,
            'url': 'https://youtube.com/watch?v=test',
            'audio_path': Path('/test/path.mp3')
        }

        core.save_metadata(metadata, output_dir)

        metadata_file = output_dir / "metadata.json"
        assert metadata_file.exists()

        with open(metadata_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert data['title'] == 'Test Video'
            assert data['duration'] == 300
            # Path가 문자열로 변환되었는지 확인
            assert isinstance(data['audio_path'], str)


class TestCleanupTempFiles:
    """cleanup_temp_files 함수 테스트"""

    def test_cleanup_temp_files_removes_directories(self, temp_dir):
        """임시 디렉토리들이 삭제되는지 확인"""
        output_dir = Path(temp_dir)
        chunks_dir = output_dir / "chunks"
        raw_audio_dir = output_dir / "raw_audio"

        # 디렉토리 생성
        chunks_dir.mkdir(parents=True)
        raw_audio_dir.mkdir(parents=True)

        # 더미 파일 생성
        (chunks_dir / "test.mp3").touch()
        (raw_audio_dir / "test.mp3").touch()

        assert chunks_dir.exists()
        assert raw_audio_dir.exists()

        core.cleanup_temp_files(output_dir)

        assert not chunks_dir.exists()
        assert not raw_audio_dir.exists()

    def test_cleanup_temp_files_nonexistent_directories(self, temp_dir):
        """존재하지 않는 디렉토리 정리 시 에러 없음"""
        output_dir = Path(temp_dir)

        # 에러 없이 실행되어야 함
        core.cleanup_temp_files(output_dir)


class TestTranscribeSingleChunk:
    """_transcribe_single_chunk 함수 테스트"""

    @patch('ytt.core.get_whisper_model')
    def test_transcribe_single_chunk_success(self, mock_get_model, mock_audio_file):
        """단일 청크 전사 성공"""
        mock_segment = Mock()
        mock_segment.start = 0.0
        mock_segment.end = 1.0
        mock_segment.text = " 테스트 "

        mock_info = Mock()
        mock_info.language = "ko"

        mock_model = Mock()
        mock_model.transcribe.return_value = ([mock_segment], mock_info)
        mock_get_model.return_value = mock_model

        args = (0, Path(mock_audio_file), "base", "ko")
        result = core._transcribe_single_chunk(args)

        assert result is not None
        assert result['chunk_id'] == 0
        assert result['language'] == "ko"
        assert len(result['segments']) == 1
        assert result['segments'][0]['text'] == "테스트"  # strip 적용됨

    @patch('ytt.core.get_whisper_model')
    def test_transcribe_single_chunk_exception(self, mock_get_model, mock_audio_file):
        """전사 중 예외 발생"""
        mock_model = Mock()
        mock_model.transcribe.side_effect = Exception("Transcription error")
        mock_get_model.return_value = mock_model

        args = (0, Path(mock_audio_file), "base", "ko")
        result = core._transcribe_single_chunk(args)

        assert result is None
