# CLI 앱 전환 설계서

## 1. 프로젝트 구조

```
ytt/
├── ytt/
│   ├── __init__.py
│   ├── cli.py              # CLI 진입점
│   ├── core.py             # 핵심 로직 (기존 app.py에서 추출)
│   ├── utils.py            # 유틸리티 함수
│   ├── config.py           # 설정 관리
│   └── __main__.py         # python -m ytt 지원
├── setup.py                # 패키징 설정
├── pyproject.toml          # 현대적 패키징
├── requirements.txt
├── README.md
└── tests/
```

## 2. CLI 진입점 (ytt/cli.py)

```python
import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from pathlib import Path
import logging
from . import core, config

console = Console()

@click.command()
@click.argument('youtube_url')
@click.argument('output_dir', type=click.Path())
@click.option('--summarize', '-s', is_flag=True, help='요약도 함께 생성')
@click.option('--model-size', '-m',
              type=click.Choice(['tiny', 'base', 'small', 'medium']),
              default='base', help='Whisper 모델 크기')
@click.option('--language', '-l', default='ko', help='언어 지정 (ko/en/ja/auto)')
@click.option('--no-cleanup', is_flag=True, help='임시 파일 삭제하지 않음')
@click.option('--verbose', '-v', is_flag=True, help='상세 로그 출력')
@click.version_option(version='1.0.0')
def main(youtube_url, output_dir, summarize, model_size, language, no_cleanup, verbose):
    """
    YouTube Transcript Tool (ytt)

    YouTube 영상을 다운로드하고 전사(transcript)를 생성합니다.

    예시:
        ytt "https://youtube.com/watch?v=xxx" ./output
        ytt "https://youtube.com/watch?v=xxx" ./output --summarize
    """
    # 로깅 설정
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=log_level)

    # 출력 디렉토리 생성
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    console.print(f"[bold green]YouTube Transcript Tool[/bold green]")
    console.print(f"URL: {youtube_url}")
    console.print(f"Output: {output_path.absolute()}")

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # 1. YouTube 다운로드
            task1 = progress.add_task("영상 다운로드 중...", total=None)
            audio_file = core.download_youtube(youtube_url, output_path)
            progress.remove_task(task1)
            console.print("✓ 다운로드 완료", style="green")

            # 2. 오디오 청킹
            task2 = progress.add_task("오디오 처리 중...", total=None)
            chunks = core.process_audio(audio_file, output_path)
            progress.remove_task(task2)
            console.print("✓ 오디오 처리 완료", style="green")

            # 3. 전사
            task3 = progress.add_task("음성 전사 중...", total=len(chunks))
            transcript = core.transcribe(
                chunks,
                model_size=model_size,
                language=language if language != 'auto' else None
            )
            progress.remove_task(task3)
            console.print("✓ 전사 완료", style="green")

            # 4. 파일 저장
            core.save_transcript(transcript, output_path)
            console.print(f"✓ 저장 완료: {output_path / 'transcript.txt'}", style="green")

            # 5. 요약 (옵션)
            if summarize:
                task4 = progress.add_task("요약 생성 중...", total=None)
                summary = core.summarize(transcript)
                core.save_summary(summary, output_path)
                progress.remove_task(task4)
                console.print(f"✓ 요약 완료: {output_path / 'summary.txt'}", style="green")

            # 6. 정리
            if not no_cleanup:
                core.cleanup_temp_files(output_path)

        console.print("\n[bold green]✓ 모든 작업 완료![/bold green]")
        console.print(f"결과물: {output_path.absolute()}")

    except Exception as e:
        console.print(f"[bold red]✗ 오류 발생:[/bold red] {str(e)}")
        if verbose:
            console.print_exception()
        exit(1)

if __name__ == '__main__':
    main()
```

## 3. 핵심 로직 (ytt/core.py)

```python
"""
기존 app.py의 함수들을 Streamlit 의존성 없이 재작성
"""
import os
import logging
from pathlib import Path
from typing import List, Optional
from functools import lru_cache

from faster_whisper import WhisperModel
import yt_dlp
import librosa
import soundfile as sf
from anthropic import Anthropic

logger = logging.getLogger(__name__)

# Whisper 모델 캐싱
@lru_cache(maxsize=1)
def get_whisper_model(model_size: str = "base"):
    """Whisper 모델 로드 (캐싱)"""
    logger.info(f"Loading Whisper model: {model_size}")
    try:
        return WhisperModel(
            model_size,
            device="cuda",
            compute_type="float16"
        )
    except:
        # GPU 실패 시 CPU로 fallback
        logger.warning("GPU not available, using CPU")
        return WhisperModel(
            model_size,
            device="cpu",
            compute_type="int8"
        )

def download_youtube(url: str, output_dir: Path) -> Path:
    """YouTube 영상 다운로드"""
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': str(output_dir / '%(title)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        title = info['title']

        # 제목 저장
        with open(output_dir / 'video_title.txt', 'w', encoding='utf-8') as f:
            f.write(title)

        # 오디오 파일 찾기
        audio_file = list(output_dir.glob('*.mp3'))[0]
        return audio_file

def process_audio(audio_file: Path, output_dir: Path, segment_length: int = 600) -> List[Path]:
    """오디오를 세그먼트로 분할"""
    chunks_dir = output_dir / "chunks"
    chunks_dir.mkdir(exist_ok=True)

    audio, sr = librosa.load(audio_file, sr=44100)
    duration = librosa.get_duration(y=audio, sr=sr)
    num_segments = int(duration / segment_length) + 1

    chunk_files = []
    for i in range(num_segments):
        start = i * segment_length * sr
        end = (i + 1) * segment_length * sr
        segment = audio[start:end]

        chunk_path = chunks_dir / f"segment_{i:03d}.mp3"
        sf.write(chunk_path, segment, sr)
        chunk_files.append(chunk_path)

    return chunk_files

def transcribe(chunks: List[Path], model_size: str = "base", language: Optional[str] = None) -> List[dict]:
    """오디오 파일들을 전사"""
    model = get_whisper_model(model_size)
    transcripts = []

    for i, chunk in enumerate(chunks):
        logger.info(f"Transcribing chunk {i+1}/{len(chunks)}")

        segments, info = model.transcribe(
            str(chunk),
            language=language,
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500)
        )

        # 세그먼트별로 저장
        chunk_data = {
            'chunk_id': i,
            'segments': []
        }

        for seg in segments:
            chunk_data['segments'].append({
                'start': seg.start,
                'end': seg.end,
                'text': seg.text
            })

        transcripts.append(chunk_data)

    return transcripts

def save_transcript(transcripts: List[dict], output_dir: Path):
    """전사 결과 저장"""
    # 1. 일반 텍스트 (타임스탬프 없음)
    with open(output_dir / 'transcript.txt', 'w', encoding='utf-8') as f:
        for chunk in transcripts:
            for seg in chunk['segments']:
                f.write(seg['text'] + ' ')
            f.write('\n')

    # 2. 타임스탬프 포함
    with open(output_dir / 'transcript_with_timestamps.txt', 'w', encoding='utf-8') as f:
        for chunk in transcripts:
            for seg in chunk['segments']:
                timestamp = f"[{format_time(seg['start'])} -> {format_time(seg['end'])}]"
                f.write(f"{timestamp} {seg['text']}\n")

def format_time(seconds: float) -> str:
    """초를 HH:MM:SS 형식으로 변환"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

def summarize(transcripts: List[dict]) -> str:
    """전사 결과 요약 (Claude)"""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY 환경 변수가 설정되지 않았습니다")

    anthropic = Anthropic(api_key=api_key)

    # 전체 텍스트 결합
    full_text = ""
    for chunk in transcripts:
        for seg in chunk['segments']:
            full_text += seg['text'] + " "

    # Claude로 요약
    message = anthropic.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=2048,
        temperature=0.3,
        messages=[{
            "role": "user",
            "content": f"다음 YouTube 영상 전사 내용을 요약해주세요:\n\n{full_text}"
        }]
    )

    return message.content[0].text

def save_summary(summary: str, output_dir: Path):
    """요약 결과 저장"""
    with open(output_dir / 'summary.txt', 'w', encoding='utf-8') as f:
        f.write(summary)

def cleanup_temp_files(output_dir: Path):
    """임시 파일 정리"""
    import shutil

    # chunks 디렉토리 삭제
    chunks_dir = output_dir / "chunks"
    if chunks_dir.exists():
        shutil.rmtree(chunks_dir)

    # 원본 mp3 파일 삭제 (옵션)
    for mp3_file in output_dir.glob("*.mp3"):
        if mp3_file.name != "audio.mp3":  # 필요시 원본 유지
            mp3_file.unlink()
```

## 4. 설정 관리 (ytt/config.py)

```python
"""
설정 파일 관리
"""
import os
from pathlib import Path
from typing import Optional

def get_config_dir() -> Path:
    """설정 디렉토리 반환"""
    if os.name == 'nt':  # Windows
        config_dir = Path(os.getenv('APPDATA')) / 'ytt'
    else:  # Unix-like
        config_dir = Path.home() / '.config' / 'ytt'

    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir

def get_api_key() -> Optional[str]:
    """Claude API 키 반환"""
    # 1. 환경 변수 확인
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        return api_key

    # 2. 설정 파일 확인
    config_file = get_config_dir() / "config.txt"
    if config_file.exists():
        with open(config_file) as f:
            return f.read().strip()

    return None

def set_api_key(api_key: str):
    """Claude API 키 저장"""
    config_file = get_config_dir() / "config.txt"
    with open(config_file, 'w') as f:
        f.write(api_key)
```

## 5. setup.py (패키징)

```python
from setuptools import setup, find_packages

setup(
    name='ytt',
    version='1.0.0',
    description='YouTube Transcript Tool - AI-powered video transcription',
    author='Your Name',
    author_email='your.email@example.com',
    url='https://github.com/yourusername/ytt',
    packages=find_packages(),
    install_requires=[
        'faster-whisper>=0.10.0',
        'anthropic>=0.18.0',
        'yt-dlp>=2023.0.0',
        'librosa>=0.10.0',
        'soundfile>=0.12.0',
        'click>=8.1.0',
        'tqdm>=4.65.0',
        'rich>=13.0.0',
        'python-dotenv>=1.0.0',
    ],
    entry_points={
        'console_scripts': [
            'ytt=ytt.cli:main',
        ],
    },
    python_requires='>=3.8',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
)
```

## 6. Homebrew Formula (ytt.rb)

```ruby
class Ytt < Formula
  include Language::Python::Virtualenv

  desc "YouTube Transcript Tool - AI-powered video transcription"
  homepage "https://github.com/yourusername/ytt"
  url "https://github.com/yourusername/ytt/archive/v1.0.0.tar.gz"
  sha256 "YOUR_SHA256_HERE"
  license "MIT"

  depends_on "python@3.11"
  depends_on "ffmpeg"

  resource "faster-whisper" do
    url "https://files.pythonhosted.org/packages/.../faster-whisper-0.10.0.tar.gz"
    sha256 "..."
  end

  # ... 다른 의존성들 ...

  def install
    virtualenv_install_with_resources
  end

  test do
    system "#{bin}/ytt", "--version"
  end
end
```

## 7. 사용 예시

```bash
# 설치 (Homebrew)
brew tap yourusername/tap
brew install ytt

# API 키 설정 (최초 1회)
export ANTHROPIC_API_KEY="your-api-key"

# 기본 사용
ytt "https://youtube.com/watch?v=dQw4w9WgXcQ" ./output

# 요약 포함
ytt "https://youtube.com/watch?v=dQw4w9WgXcQ" ./output --summarize

# 작은 모델로 빠르게
ytt "https://youtube.com/watch?v=dQw4w9WgXcQ" ./output -m tiny

# 상세 로그
ytt "https://youtube.com/watch?v=dQw4w9WgXcQ" ./output -v
```

## 8. 장점

1. **단순함**: 웹 서버 불필요, 명령어 한 줄로 실행
2. **Homebrew 배포**: macOS/Linux 사용자 쉽게 설치
3. **스크립트 통합**: 배치 처리, 자동화 가능
4. **가벼움**: Streamlit 의존성 제거로 설치 용량 감소
5. **파이프라인**: 다른 CLI 도구와 조합 가능

```bash
# 예: 여러 영상 배치 처리
cat youtube_urls.txt | while read url; do
  ytt "$url" "./transcripts/$(date +%Y%m%d_%H%M%S)"
done
```

## 9. 다음 단계

1. `ytt/` 디렉토리 구조 생성
2. `cli.py`, `core.py` 구현
3. `setup.py` 작성
4. PyPI에 배포
5. Homebrew Formula 작성
6. GitHub Actions로 CI/CD 구축
