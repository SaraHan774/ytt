"""
Unit tests for YouTube Summarizer app
"""
import os
import sys
import pytest
from unittest.mock import Mock, patch, MagicMock
import numpy as np

# app.py를 import하기 위한 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app


class TestFindAudioFiles:
    """find_audio_files 함수 테스트"""

    def test_find_audio_files_empty_directory(self, temp_dir):
        """빈 디렉토리에서 오디오 파일 찾기"""
        result = app.find_audio_files(temp_dir)
        assert result == []

    def test_find_audio_files_with_mp3_files(self, temp_dir):
        """MP3 파일이 있는 디렉토리에서 찾기"""
        # 테스트 파일 생성
        test_files = ["test1.mp3", "test2.mp3", "test3.txt"]
        for filename in test_files:
            filepath = os.path.join(temp_dir, filename)
            with open(filepath, "w") as f:
                f.write("test")

        result = app.find_audio_files(temp_dir)
        assert len(result) == 2
        assert all(f.endswith(".mp3") for f in result)

    def test_find_audio_files_with_custom_extension(self, temp_dir):
        """커스텀 확장자로 오디오 파일 찾기"""
        test_files = ["test1.wav", "test2.wav", "test3.mp3"]
        for filename in test_files:
            filepath = os.path.join(temp_dir, filename)
            with open(filepath, "w") as f:
                f.write("test")

        result = app.find_audio_files(temp_dir, extension=".wav")
        assert len(result) == 2
        assert all(f.endswith(".wav") for f in result)

    def test_find_audio_files_nested_directories(self, temp_dir):
        """중첩된 디렉토리에서 오디오 파일 찾기"""
        nested_dir = os.path.join(temp_dir, "nested")
        os.makedirs(nested_dir)

        # 상위 디렉토리에 파일
        with open(os.path.join(temp_dir, "top.mp3"), "w") as f:
            f.write("test")

        # 하위 디렉토리에 파일
        with open(os.path.join(nested_dir, "nested.mp3"), "w") as f:
            f.write("test")

        result = app.find_audio_files(temp_dir)
        assert len(result) == 2


class TestChunkAudio:
    """chunk_audio 함수 테스트"""

    def test_chunk_audio_creates_output_directory(self, mock_audio_file, temp_dir):
        """청킹 시 출력 디렉토리가 생성되는지 확인"""
        output_dir = os.path.join(temp_dir, "chunks")
        result = app.chunk_audio(mock_audio_file, segment_length=1, output_dir=output_dir)

        assert os.path.exists(output_dir)
        assert len(result) > 0

    def test_chunk_audio_returns_sorted_files(self, mock_audio_file, temp_dir):
        """청킹된 파일들이 정렬되어 반환되는지 확인"""
        output_dir = os.path.join(temp_dir, "chunks")
        result = app.chunk_audio(mock_audio_file, segment_length=1, output_dir=output_dir)

        # 파일명이 정렬되어 있는지 확인
        assert result == sorted(result)

    def test_chunk_audio_segment_length(self, mock_audio_file, temp_dir):
        """지정된 길이로 오디오가 청킹되는지 확인"""
        output_dir = os.path.join(temp_dir, "chunks")
        segment_length = 1  # 1초

        result = app.chunk_audio(mock_audio_file, segment_length=segment_length, output_dir=output_dir)

        # 최소 1개 이상의 청크가 생성되어야 함
        assert len(result) >= 1
        # 모든 청크 파일이 존재해야 함
        assert all(os.path.exists(f) for f in result)


class TestTranscribeAudio:
    """transcribe_audio 함수 테스트"""

    @patch('app.load_whisper_model')
    def test_transcribe_audio_success(self, mock_load_model, mock_audio_files, mock_whisper_segments, temp_dir):
        """오디오 전사 성공 케이스"""
        # Mock Whisper 모델
        mock_model = Mock()
        mock_model.transcribe.return_value = (mock_whisper_segments, {"language": "ko"})
        mock_load_model.return_value = mock_model

        result = app.transcribe_audio(mock_audio_files, model_size="base")

        assert len(result) == len(mock_audio_files)
        assert all(isinstance(transcript, str) for transcript in result)
        assert mock_model.transcribe.call_count == len(mock_audio_files)

    @patch('app.load_whisper_model')
    def test_transcribe_audio_with_output_file(self, mock_load_model, mock_audio_files, mock_whisper_segments, temp_dir):
        """전사 결과를 파일로 저장"""
        mock_model = Mock()
        mock_model.transcribe.return_value = (mock_whisper_segments, {"language": "ko"})
        mock_load_model.return_value = mock_model

        output_file = os.path.join(temp_dir, "transcripts.txt")
        result = app.transcribe_audio(mock_audio_files, output_file=output_file, model_size="base")

        assert os.path.exists(output_file)
        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()
            assert len(content) > 0

    @patch('app.load_whisper_model')
    @patch('streamlit.error')
    def test_transcribe_audio_handles_exception(self, mock_st_error, mock_load_model, mock_audio_files):
        """전사 중 예외 발생 시 처리"""
        mock_model = Mock()
        mock_model.transcribe.side_effect = Exception("Transcription failed")
        mock_load_model.return_value = mock_model

        result = app.transcribe_audio(mock_audio_files, model_size="base")

        # 예외 발생 시 빈 리스트 또는 continue로 스킵
        assert isinstance(result, list)
        assert mock_st_error.called


class TestSummarizeClaude:
    """summarize_claude 함수 테스트"""

    @patch('app.anthropic')
    def test_summarize_claude_success(self, mock_anthropic, mock_transcripts, mock_claude_response):
        """Claude 요약 성공 케이스"""
        mock_anthropic.messages.create.return_value = mock_claude_response

        result = app.summarize_claude(
            mock_transcripts,
            system_prompt="요약해주세요",
            model="claude-3-5-sonnet-20241022"
        )

        assert len(result) == len(mock_transcripts)
        assert all(isinstance(summary, str) for summary in result)
        assert mock_anthropic.messages.create.call_count == len(mock_transcripts)

    @patch('app.anthropic')
    def test_summarize_claude_with_output_file(self, mock_anthropic, mock_transcripts, mock_claude_response, temp_dir):
        """요약 결과를 파일로 저장"""
        mock_anthropic.messages.create.return_value = mock_claude_response

        output_file = os.path.join(temp_dir, "summary.txt")
        result = app.summarize_claude(
            mock_transcripts,
            system_prompt="요약해주세요",
            output_file=output_file
        )

        assert os.path.exists(output_file)
        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()
            assert len(content) > 0

    @patch('app.anthropic')
    @patch('streamlit.error')
    def test_summarize_claude_handles_api_error(self, mock_st_error, mock_anthropic, mock_transcripts):
        """Claude API 에러 처리"""
        mock_anthropic.messages.create.side_effect = Exception("API Error")

        result = app.summarize_claude(
            mock_transcripts,
            system_prompt="요약해주세요"
        )

        assert isinstance(result, list)
        assert len(result) == len(mock_transcripts)
        # 에러 메시지가 포함되어 있어야 함
        assert any("[요약 실패" in summary for summary in result)
        assert mock_st_error.called

    @patch('app.anthropic')
    def test_summarize_claude_custom_parameters(self, mock_anthropic, mock_transcripts, mock_claude_response):
        """커스텀 파라미터로 Claude 호출"""
        mock_anthropic.messages.create.return_value = mock_claude_response

        custom_model = "claude-3-opus-20240229"
        result = app.summarize_claude(
            mock_transcripts,
            system_prompt="상세히 요약해주세요",
            model=custom_model
        )

        # 올바른 모델로 호출되었는지 확인
        call_args = mock_anthropic.messages.create.call_args
        assert call_args[1]["model"] == custom_model
        assert call_args[1]["max_tokens"] == 2048
        assert call_args[1]["temperature"] == 0.3


class TestYoutubeToMp3:
    """youtube_to_mp3 함수 테스트"""

    @patch('app.yt_dlp.YoutubeDL')
    @patch('app.find_audio_files')
    def test_youtube_to_mp3_success(self, mock_find_audio, mock_yt_dlp, mock_youtube_url, temp_dir):
        """YouTube 다운로드 성공 케이스"""
        mock_audio_path = os.path.join(temp_dir, "video.mp3")
        mock_find_audio.return_value = [mock_audio_path]

        mock_ydl_instance = Mock()
        mock_yt_dlp.return_value.__enter__.return_value = mock_ydl_instance

        result = app.youtube_to_mp3(mock_youtube_url, temp_dir)

        assert result == mock_audio_path
        assert mock_ydl_instance.download.called

    @patch('app.yt_dlp.YoutubeDL')
    def test_youtube_to_mp3_creates_output_dir(self, mock_yt_dlp, mock_youtube_url, temp_dir):
        """출력 디렉토리가 자동 생성되는지 확인"""
        output_dir = os.path.join(temp_dir, "new_dir")

        mock_ydl_instance = Mock()
        mock_yt_dlp.return_value.__enter__.return_value = mock_ydl_instance

        # find_audio_files가 빈 리스트를 반환하도록 mock (IndexError 발생)
        with patch('app.find_audio_files', return_value=[]):
            try:
                app.youtube_to_mp3(mock_youtube_url, output_dir)
            except IndexError:
                pass  # 예상된 에러

        assert os.path.exists(output_dir)


class TestLoadWhisperModel:
    """load_whisper_model 함수 테스트"""

    @patch('app.WhisperModel')
    @patch('streamlit.cache_resource', lambda func: func)
    def test_load_whisper_model_default(self, mock_whisper_model):
        """기본 설정으로 Whisper 모델 로드"""
        mock_model = Mock()
        mock_whisper_model.return_value = mock_model

        result = app.load_whisper_model()

        mock_whisper_model.assert_called_once_with(
            "base",
            device="cuda",
            compute_type="float16"
        )
        assert result == mock_model

    @patch('app.WhisperModel')
    @patch('streamlit.cache_resource', lambda func: func)
    def test_load_whisper_model_custom_size(self, mock_whisper_model):
        """커스텀 모델 크기로 로드"""
        mock_model = Mock()
        mock_whisper_model.return_value = mock_model

        result = app.load_whisper_model(model_size="medium")

        mock_whisper_model.assert_called_once_with(
            "medium",
            device="cuda",
            compute_type="float16"
        )


class TestSummarizeYoutubeVideo:
    """summarize_youtube_video 통합 함수 테스트"""

    @patch('app.youtube_to_mp3')
    @patch('app.chunk_audio')
    @patch('app.transcribe_audio')
    def test_summarize_youtube_video_flow(
        self,
        mock_transcribe,
        mock_chunk,
        mock_youtube_dl,
        mock_youtube_url,
        mock_transcripts,
        sample_output_dir
    ):
        """YouTube 요약 전체 플로우 테스트"""
        # Mock 설정
        mock_audio_path = os.path.join(sample_output_dir["raw_audio_dir"], "video.mp3")
        mock_youtube_dl.return_value = mock_audio_path

        mock_chunk_files = [
            os.path.join(sample_output_dir["chunks_dir"], f"chunk_{i}.mp3")
            for i in range(3)
        ]
        mock_chunk.return_value = mock_chunk_files
        mock_transcribe.return_value = mock_transcripts

        # Mock progress bar와 text
        mock_progress_bar = Mock()
        mock_progress_text = Mock()

        # Mock summarization function
        def mock_summarizer(chunks, system_prompt, output_file=None):
            return ["요약 1", "요약 2", "요약 3"] if len(chunks) > 1 else ["최종 요약"]

        # 테스트 실행
        long_summary, short_summary = app.summarize_youtube_video(
            mock_youtube_url,
            sample_output_dir["output_dir"],
            mock_progress_bar,
            mock_progress_text,
            mock_summarizer,
            model_size="base"
        )

        # 검증
        assert mock_youtube_dl.called
        assert mock_chunk.called
        assert mock_transcribe.called
        assert isinstance(long_summary, str)
        assert isinstance(short_summary, str)
        assert len(short_summary) > 0


# 통합 테스트를 위한 마커
@pytest.mark.integration
class TestEndToEnd:
    """End-to-End 통합 테스트 (실제 API 호출 없이)"""

    @patch('app.anthropic')
    @patch('app.load_whisper_model')
    @patch('app.youtube_to_mp3')
    def test_full_pipeline_mock(
        self,
        mock_youtube_dl,
        mock_load_whisper,
        mock_anthropic,
        mock_youtube_url,
        mock_audio_file,
        mock_whisper_segments,
        mock_claude_response,
        temp_dir
    ):
        """전체 파이프라인 mock 테스트"""
        # Setup mocks
        mock_youtube_dl.return_value = mock_audio_file

        mock_whisper = Mock()
        mock_whisper.transcribe.return_value = (mock_whisper_segments, {"language": "ko"})
        mock_load_whisper.return_value = mock_whisper

        mock_anthropic.messages.create.return_value = mock_claude_response

        # Create mock progress components
        mock_progress_bar = Mock()
        mock_progress_text = Mock()

        # Run pipeline
        outputs_dir = os.path.join(temp_dir, "outputs")
        long_summary, short_summary = app.summarize_youtube_video(
            mock_youtube_url,
            outputs_dir,
            mock_progress_bar,
            mock_progress_text,
            app.summarize_claude,
            model_size="base"
        )

        # Verify
        assert long_summary is not None
        assert short_summary is not None
        assert mock_youtube_dl.called
        assert mock_whisper.transcribe.called
        assert mock_anthropic.messages.create.called
