"""
Pytest fixtures for testing YouTube Summarizer
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest
import numpy as np
import soundfile as sf


@pytest.fixture
def temp_dir():
    """임시 디렉토리 fixture"""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    # 테스트 후 정리
    if os.path.exists(temp_path):
        shutil.rmtree(temp_path)


@pytest.fixture
def mock_audio_file(temp_dir):
    """테스트용 가짜 오디오 파일 생성"""
    audio_path = os.path.join(temp_dir, "test_audio.mp3")
    # 1초짜리 가짜 오디오 생성 (44.1kHz, 모노)
    sample_rate = 44100
    duration = 1  # 1초
    samples = np.random.randn(sample_rate * duration).astype(np.float32)
    sf.write(audio_path, samples, sample_rate)
    return audio_path


@pytest.fixture
def mock_audio_files(temp_dir):
    """여러 개의 테스트용 오디오 파일 생성"""
    audio_files = []
    for i in range(3):
        audio_path = os.path.join(temp_dir, f"test_audio_{i}.mp3")
        sample_rate = 44100
        duration = 1
        samples = np.random.randn(sample_rate * duration).astype(np.float32)
        sf.write(audio_path, samples, sample_rate)
        audio_files.append(audio_path)
    return audio_files


@pytest.fixture
def mock_transcripts():
    """테스트용 전사 텍스트"""
    return [
        "안녕하세요. 이것은 첫 번째 테스트 세그먼트입니다.",
        "두 번째 세그먼트에서는 중요한 내용을 다룹니다.",
        "마지막 세그먼트에서 결론을 내립니다."
    ]


@pytest.fixture
def mock_youtube_url():
    """테스트용 YouTube URL"""
    return "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


@pytest.fixture
def mock_env_vars(monkeypatch):
    """환경 변수 mock"""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key-123")


@pytest.fixture
def mock_whisper_segments():
    """Whisper 세그먼트 mock 데이터"""
    class MockSegment:
        def __init__(self, text):
            self.text = text
            self.start = 0.0
            self.end = 1.0

    return [
        MockSegment("안녕하세요."),
        MockSegment("테스트 중입니다."),
        MockSegment("감사합니다.")
    ]


@pytest.fixture
def mock_claude_response():
    """Claude API 응답 mock"""
    class MockContent:
        def __init__(self, text):
            self.text = text

    class MockMessage:
        def __init__(self, text):
            self.content = [MockContent(text)]

    return MockMessage("이것은 요약된 텍스트입니다.")


@pytest.fixture
def sample_output_dir(temp_dir):
    """테스트용 출력 디렉토리 구조"""
    output_dir = os.path.join(temp_dir, "outputs")
    raw_audio_dir = os.path.join(output_dir, "raw_audio")
    chunks_dir = os.path.join(output_dir, "chunks")

    os.makedirs(raw_audio_dir, exist_ok=True)
    os.makedirs(chunks_dir, exist_ok=True)

    return {
        "output_dir": output_dir,
        "raw_audio_dir": raw_audio_dir,
        "chunks_dir": chunks_dir
    }


@pytest.fixture
def mock_streamlit(mocker):
    """Streamlit 함수들 mock"""
    mocker.patch('streamlit.progress')
    mocker.patch('streamlit.text')
    mocker.patch('streamlit.error')
    mocker.patch('streamlit.cache_resource', lambda func: func)
