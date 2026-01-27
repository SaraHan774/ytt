"""
Integration tests for YouTube Summarizer
실제 API를 호출하지 않고 전체 워크플로우를 테스트
"""
import os
import sys
import pytest
from unittest.mock import Mock, patch, MagicMock
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app


@pytest.mark.integration
class TestAudioProcessingPipeline:
    """오디오 처리 파이프라인 통합 테스트"""

    def test_audio_download_to_chunks(self, mock_youtube_url, mock_audio_file, temp_dir):
        """YouTube 다운로드 → 청킹 파이프라인"""
        with patch('app.yt_dlp.YoutubeDL') as mock_ydl:
            # YouTube 다운로드 mock
            mock_ydl_instance = Mock()
            mock_ydl.return_value.__enter__.return_value = mock_ydl_instance

            # 실제 오디오 파일을 다운로드 디렉토리에 복사
            download_dir = os.path.join(temp_dir, "downloads")
            os.makedirs(download_dir, exist_ok=True)
            downloaded_file = os.path.join(download_dir, "video.mp3")
            shutil.copy(mock_audio_file, downloaded_file)

            with patch('app.find_audio_files', return_value=[downloaded_file]):
                # 다운로드
                audio_path = app.youtube_to_mp3(mock_youtube_url, download_dir)

                # 청킹
                chunks_dir = os.path.join(temp_dir, "chunks")
                chunked_files = app.chunk_audio(
                    audio_path,
                    segment_length=1,
                    output_dir=chunks_dir
                )

                # 검증
                assert os.path.exists(audio_path)
                assert len(chunked_files) > 0
                assert all(os.path.exists(f) for f in chunked_files)
                assert all(f.endswith(".mp3") for f in chunked_files)

    @patch('app.load_whisper_model')
    def test_chunks_to_transcription(self, mock_load_whisper, mock_audio_files, mock_whisper_segments, temp_dir):
        """청킹된 오디오 → 전사 파이프라인"""
        # Whisper 모델 mock
        mock_whisper = Mock()
        mock_whisper.transcribe.return_value = (mock_whisper_segments, {"language": "ko"})
        mock_load_whisper.return_value = mock_whisper

        # 전사
        output_file = os.path.join(temp_dir, "transcripts.txt")
        transcripts = app.transcribe_audio(
            mock_audio_files,
            output_file=output_file,
            model_size="base"
        )

        # 검증
        assert len(transcripts) == len(mock_audio_files)
        assert os.path.exists(output_file)
        assert all(isinstance(t, str) and len(t) > 0 for t in transcripts)

    @patch('app.anthropic')
    def test_transcription_to_summary(self, mock_anthropic, mock_transcripts, mock_claude_response, temp_dir):
        """전사 → 요약 파이프라인"""
        mock_anthropic.messages.create.return_value = mock_claude_response

        # 요약
        output_file = os.path.join(temp_dir, "summary.txt")
        summaries = app.summarize_claude(
            mock_transcripts,
            system_prompt="요약해주세요",
            output_file=output_file
        )

        # 검증
        assert len(summaries) == len(mock_transcripts)
        assert os.path.exists(output_file)
        assert all(isinstance(s, str) and len(s) > 0 for s in summaries)


@pytest.mark.integration
class TestCompleteWorkflow:
    """전체 워크플로우 통합 테스트"""

    @patch('app.anthropic')
    @patch('app.load_whisper_model')
    @patch('app.yt_dlp.YoutubeDL')
    def test_youtube_url_to_summary_complete(
        self,
        mock_ydl,
        mock_load_whisper,
        mock_anthropic,
        mock_youtube_url,
        mock_audio_file,
        mock_whisper_segments,
        mock_claude_response,
        temp_dir
    ):
        """YouTube URL → 최종 요약 전체 플로우"""
        # Setup: YouTube 다운로드
        mock_ydl_instance = Mock()
        mock_ydl.return_value.__enter__.return_value = mock_ydl_instance

        download_dir = os.path.join(temp_dir, "outputs", "raw_audio")
        os.makedirs(download_dir, exist_ok=True)
        downloaded_file = os.path.join(download_dir, "video.mp3")
        shutil.copy(mock_audio_file, downloaded_file)

        # Setup: Whisper
        mock_whisper = Mock()
        mock_whisper.transcribe.return_value = (mock_whisper_segments, {"language": "ko"})
        mock_load_whisper.return_value = mock_whisper

        # Setup: Claude
        mock_anthropic.messages.create.return_value = mock_claude_response

        with patch('app.find_audio_files', return_value=[downloaded_file]):
            # Mock progress components
            mock_progress_bar = Mock()
            mock_progress_text = Mock()

            # 전체 워크플로우 실행
            outputs_dir = os.path.join(temp_dir, "outputs")
            long_summary, short_summary = app.summarize_youtube_video(
                mock_youtube_url,
                outputs_dir,
                mock_progress_bar,
                mock_progress_text,
                app.summarize_claude,
                model_size="base"
            )

            # 검증
            assert isinstance(long_summary, str)
            assert isinstance(short_summary, str)
            assert len(long_summary) > 0
            assert len(short_summary) > 0

            # 디렉토리 구조 확인
            assert os.path.exists(outputs_dir)
            assert os.path.exists(os.path.join(outputs_dir, "chunks"))

            # 함수 호출 확인
            assert mock_ydl_instance.download.called
            assert mock_whisper.transcribe.called
            assert mock_anthropic.messages.create.called

            # Progress bar 업데이트 확인
            assert mock_progress_bar.progress.called
            assert mock_progress_text.text.called


@pytest.mark.integration
class TestErrorRecovery:
    """에러 복구 및 예외 처리 통합 테스트"""

    @patch('app.load_whisper_model')
    def test_partial_transcription_failure(self, mock_load_whisper, mock_audio_files):
        """일부 전사 실패 시 나머지 처리 계속"""
        mock_whisper = Mock()

        # 첫 번째는 성공, 두 번째는 실패, 세 번째는 성공
        class MockSegment:
            def __init__(self, text):
                self.text = text

        mock_whisper.transcribe.side_effect = [
            ([MockSegment("성공 1")], {"language": "ko"}),
            Exception("전사 실패"),
            ([MockSegment("성공 2")], {"language": "ko"}),
        ]
        mock_load_whisper.return_value = mock_whisper

        with patch('streamlit.error'):
            transcripts = app.transcribe_audio(mock_audio_files, model_size="base")

            # 성공한 것들만 결과에 포함
            assert len(transcripts) == 2
            assert "성공" in transcripts[0]
            assert "성공" in transcripts[1]

    @patch('app.anthropic')
    def test_partial_summarization_failure(self, mock_anthropic, mock_transcripts):
        """일부 요약 실패 시 나머지 처리 계속"""
        # 첫 번째는 성공, 두 번째는 실패, 세 번째는 성공
        class MockContent:
            def __init__(self, text):
                self.text = text

        class MockMessage:
            def __init__(self, text):
                self.content = [MockContent(text)]

        mock_anthropic.messages.create.side_effect = [
            MockMessage("요약 1"),
            Exception("API 에러"),
            MockMessage("요약 2"),
        ]

        with patch('streamlit.error'):
            summaries = app.summarize_claude(mock_transcripts, system_prompt="요약")

            # 모든 청크에 대한 결과가 있어야 함 (실패한 것은 에러 메시지)
            assert len(summaries) == len(mock_transcripts)
            assert "요약 1" in summaries[0]
            assert "[요약 실패" in summaries[1]
            assert "요약 2" in summaries[2]

    @patch('app.yt_dlp.YoutubeDL')
    def test_youtube_download_failure_handling(self, mock_ydl, mock_youtube_url, temp_dir):
        """YouTube 다운로드 실패 처리"""
        from yt_dlp.utils import DownloadError

        mock_ydl_instance = Mock()
        mock_ydl_instance.download.side_effect = DownloadError("다운로드 실패")
        mock_ydl.return_value.__enter__.return_value = mock_ydl_instance

        # DownloadError는 pass로 처리되므로 예외가 발생하지 않아야 함
        # 하지만 find_audio_files에서 IndexError 발생 가능
        with patch('app.find_audio_files', return_value=[]):
            try:
                app.youtube_to_mp3(mock_youtube_url, temp_dir)
            except IndexError:
                pass  # 예상된 동작


@pytest.mark.integration
class TestOutputFiles:
    """출력 파일 생성 및 형식 테스트"""

    @patch('app.load_whisper_model')
    def test_transcript_file_format(self, mock_load_whisper, mock_audio_files, mock_whisper_segments, temp_dir):
        """전사 파일 형식 검증"""
        mock_whisper = Mock()
        mock_whisper.transcribe.return_value = (mock_whisper_segments, {"language": "ko"})
        mock_load_whisper.return_value = mock_whisper

        output_file = os.path.join(temp_dir, "transcripts.txt")
        app.transcribe_audio(mock_audio_files, output_file=output_file, model_size="base")

        # 파일 내용 검증
        with open(output_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            assert len(lines) == len(mock_audio_files)
            assert all(line.strip() for line in lines)  # 모든 라인에 내용이 있어야 함

    @patch('app.anthropic')
    def test_summary_file_format(self, mock_anthropic, mock_transcripts, mock_claude_response, temp_dir):
        """요약 파일 형식 검증"""
        mock_anthropic.messages.create.return_value = mock_claude_response

        output_file = os.path.join(temp_dir, "summary.txt")
        app.summarize_claude(mock_transcripts, system_prompt="요약", output_file=output_file)

        # 파일 내용 검증
        with open(output_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            assert len(lines) == len(mock_transcripts)
            assert all(line.strip() for line in lines)

    @patch('app.anthropic')
    @patch('app.load_whisper_model')
    @patch('app.yt_dlp.YoutubeDL')
    def test_complete_output_structure(
        self,
        mock_ydl,
        mock_load_whisper,
        mock_anthropic,
        mock_youtube_url,
        mock_audio_file,
        mock_whisper_segments,
        mock_claude_response,
        temp_dir
    ):
        """완전한 출력 디렉토리 구조 검증"""
        # Setup mocks
        mock_ydl_instance = Mock()
        mock_ydl.return_value.__enter__.return_value = mock_ydl_instance

        download_dir = os.path.join(temp_dir, "outputs", "raw_audio")
        os.makedirs(download_dir, exist_ok=True)
        downloaded_file = os.path.join(download_dir, "video.mp3")
        shutil.copy(mock_audio_file, downloaded_file)

        mock_whisper = Mock()
        mock_whisper.transcribe.return_value = (mock_whisper_segments, {"language": "ko"})
        mock_load_whisper.return_value = mock_whisper

        mock_anthropic.messages.create.return_value = mock_claude_response

        with patch('app.find_audio_files', return_value=[downloaded_file]):
            mock_progress_bar = Mock()
            mock_progress_text = Mock()

            outputs_dir = os.path.join(temp_dir, "outputs")
            app.summarize_youtube_video(
                mock_youtube_url,
                outputs_dir,
                mock_progress_bar,
                mock_progress_text,
                app.summarize_claude,
                model_size="base"
            )

            # 디렉토리 구조 검증
            assert os.path.exists(outputs_dir)
            assert os.path.exists(os.path.join(outputs_dir, "raw_audio"))
            assert os.path.exists(os.path.join(outputs_dir, "chunks"))

            # 파일 존재 확인
            assert os.path.exists(os.path.join(outputs_dir, "transcripts.txt"))
            assert os.path.exists(os.path.join(outputs_dir, "summary.txt"))


@pytest.mark.integration
@pytest.mark.slow
class TestPerformance:
    """성능 테스트"""

    @patch('app.load_whisper_model')
    def test_large_audio_chunking(self, mock_load_whisper, temp_dir):
        """큰 오디오 파일 청킹 성능"""
        import soundfile as sf
        import numpy as np

        # 10초짜리 오디오 생성
        sample_rate = 44100
        duration = 10
        samples = np.random.randn(sample_rate * duration).astype(np.float32)
        audio_path = os.path.join(temp_dir, "large_audio.mp3")
        sf.write(audio_path, samples, sample_rate)

        # 2초 단위로 청킹
        chunks_dir = os.path.join(temp_dir, "chunks")
        chunked_files = app.chunk_audio(audio_path, segment_length=2, output_dir=chunks_dir)

        # 약 5개의 청크가 생성되어야 함
        assert len(chunked_files) >= 5
        assert all(os.path.exists(f) for f in chunked_files)

    @patch('app.anthropic')
    def test_multiple_chunks_summarization(self, mock_anthropic, mock_claude_response):
        """여러 청크 요약 성능"""
        # 10개의 청크
        many_transcripts = [f"전사 내용 {i}" for i in range(10)]
        mock_anthropic.messages.create.return_value = mock_claude_response

        summaries = app.summarize_claude(many_transcripts, system_prompt="요약")

        assert len(summaries) == 10
        # API가 10번 호출되었는지 확인
        assert mock_anthropic.messages.create.call_count == 10
