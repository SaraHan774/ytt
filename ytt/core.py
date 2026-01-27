"""
YouTube Transcript Tool - Core Logic
Streamlit 의존성 없이 핵심 기능만 제공
"""
import os
import shutil
import logging
from pathlib import Path
from typing import List, Optional, Dict
from functools import lru_cache
import json

import librosa
import soundfile as sf
import yt_dlp
from yt_dlp.utils import DownloadError
from faster_whisper import WhisperModel
from anthropic import Anthropic
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

logger = logging.getLogger(__name__)


# Whisper 모델 캐싱 (Streamlit 대신 lru_cache 사용)
@lru_cache(maxsize=1)
def get_whisper_model(model_size: str = "base"):
    """
    Whisper 모델 로드 (캐싱)
    GPU가 없으면 자동으로 CPU로 fallback
    """
    logger.info(f"Loading Whisper model: {model_size}")

    try:
        # GPU 시도
        model = WhisperModel(
            model_size,
            device="cuda",
            compute_type="float16"
        )
        logger.info("Using GPU acceleration")
        return model
    except Exception as e:
        # GPU 실패 시 CPU로 fallback
        logger.warning(f"GPU not available ({e}), falling back to CPU")
        return WhisperModel(
            model_size,
            device="cpu",
            compute_type="int8"
        )


def find_audio_files(path: str, extension: str = ".mp3") -> List[str]:
    """지정된 경로에서 오디오 파일 찾기"""
    audio_files = []
    for root, dirs, files in os.walk(path):
        for f in files:
            if f.endswith(extension):
                audio_files.append(os.path.join(root, f))
    return audio_files


def download_youtube(youtube_url: str, output_dir: Path) -> Dict[str, any]:
    """
    YouTube 영상 다운로드

    Returns:
        dict: {
            'audio_path': Path,
            'title': str,
            'duration': float,
            'url': str
        }
    """
    logger.info(f"Downloading: {youtube_url}")

    raw_audio_dir = output_dir / "raw_audio"
    raw_audio_dir.mkdir(parents=True, exist_ok=True)

    ydl_config = {
        "format": "bestaudio/best",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "outtmpl": str(raw_audio_dir / "%(title)s.%(ext)s"),
        "quiet": not logger.isEnabledFor(logging.DEBUG),
        "no_warnings": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_config) as ydl:
            info = ydl.extract_info(youtube_url, download=True)

            # 메타데이터 추출
            metadata = {
                'title': info.get('title', 'Unknown'),
                'duration': info.get('duration', 0),
                'url': youtube_url,
                'uploader': info.get('uploader', 'Unknown'),
            }

            # 다운로드된 파일 찾기
            audio_files = find_audio_files(str(raw_audio_dir))
            if not audio_files:
                raise ValueError("No audio file found after download")

            audio_path = Path(audio_files[0])

            logger.info(f"Downloaded: {metadata['title']}")

            return {
                'audio_path': audio_path,
                **metadata
            }

    except DownloadError as e:
        logger.error(f"Download failed: {e}")
        raise


def chunk_audio(audio_path: Path, output_dir: Path, segment_length: int = 600) -> List[Path]:
    """
    오디오를 세그먼트로 분할

    Args:
        audio_path: 원본 오디오 파일 경로
        output_dir: 청크 저장 디렉토리
        segment_length: 세그먼트 길이 (초)

    Returns:
        List[Path]: 청크 파일 경로 리스트
    """
    logger.info(f"Chunking audio: {audio_path.name}")

    chunks_dir = output_dir / "chunks"
    chunks_dir.mkdir(parents=True, exist_ok=True)

    # 오디오 로드
    audio, sr = librosa.load(audio_path, sr=44100)
    duration = librosa.get_duration(y=audio, sr=sr)
    num_segments = int(duration / segment_length) + 1

    logger.info(f"Duration: {duration:.1f}s, creating {num_segments} chunks")

    chunk_files = []
    for i in range(num_segments):
        start = i * segment_length * sr
        end = (i + 1) * segment_length * sr
        segment = audio[start:end]

        chunk_path = chunks_dir / f"segment_{i:03d}.mp3"
        sf.write(chunk_path, segment, sr)
        chunk_files.append(chunk_path)

    logger.info(f"Created {len(chunk_files)} chunks")
    return sorted(chunk_files)


def transcribe_audio(
    audio_files: List[Path],
    model_size: str = "base",
    language: Optional[str] = "ko"
) -> List[Dict]:
    """
    오디오 파일들을 전사

    Args:
        audio_files: 오디오 파일 경로 리스트
        model_size: Whisper 모델 크기
        language: 언어 코드 (None이면 자동 감지)

    Returns:
        List[Dict]: 전사 결과 (세그먼트 정보 포함)
    """
    logger.info(f"Transcribing {len(audio_files)} files with model: {model_size}")

    model = get_whisper_model(model_size)
    transcripts = []

    for i, audio_file in enumerate(audio_files):
        logger.info(f"Transcribing chunk {i+1}/{len(audio_files)}: {audio_file.name}")

        try:
            segments, info = model.transcribe(
                str(audio_file),
                language=language,
                beam_size=5,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500)
            )

            chunk_data = {
                'chunk_id': i,
                'file': audio_file.name,
                'language': info.language,
                'segments': []
            }

            for seg in segments:
                chunk_data['segments'].append({
                    'start': seg.start,
                    'end': seg.end,
                    'text': seg.text.strip()
                })

            transcripts.append(chunk_data)
            logger.debug(f"Chunk {i+1}: {len(chunk_data['segments'])} segments")

        except Exception as e:
            logger.error(f"Transcription failed for {audio_file}: {e}")
            # 실패해도 계속 진행
            continue

    logger.info(f"Transcription complete: {len(transcripts)} chunks")
    return transcripts


def format_time(seconds: float) -> str:
    """초를 HH:MM:SS 형식으로 변환"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def save_transcripts(transcripts: List[Dict], output_dir: Path, video_title: str = "video"):
    """
    전사 결과를 파일로 저장

    저장 파일:
    - transcript.txt: 평문 텍스트
    - transcript_with_timestamps.txt: 타임스탬프 포함
    - transcript.json: 구조화된 데이터
    """
    logger.info(f"Saving transcripts to {output_dir}")

    # 1. 평문 텍스트
    with open(output_dir / "transcript.txt", "w", encoding="utf-8") as f:
        f.write(f"# {video_title}\n\n")
        for chunk in transcripts:
            for seg in chunk['segments']:
                f.write(seg['text'] + " ")
            f.write("\n\n")

    # 2. 타임스탬프 포함
    with open(output_dir / "transcript_with_timestamps.txt", "w", encoding="utf-8") as f:
        f.write(f"# {video_title}\n\n")
        for chunk in transcripts:
            for seg in chunk['segments']:
                timestamp = f"[{format_time(seg['start'])} -> {format_time(seg['end'])}]"
                f.write(f"{timestamp} {seg['text']}\n")
            f.write("\n")

    # 3. JSON 형식
    with open(output_dir / "transcript.json", "w", encoding="utf-8") as f:
        json.dump({
            'title': video_title,
            'chunks': transcripts
        }, f, ensure_ascii=False, indent=2)

    logger.info("Transcripts saved")


def summarize_with_claude(
    transcripts: List[Dict],
    api_key: Optional[str] = None,
    model: str = "claude-sonnet-4-5-20250929",
    language: str = "ko"
) -> Dict[str, str]:
    """
    전사 결과를 Claude로 요약

    Args:
        transcripts: 전사 결과 리스트
        api_key: Anthropic API 키
        model: Claude 모델명
        language: 요약 언어 ('ko', 'en', 'ja' 등)

    Returns:
        dict: {
            'long_summary': str,
            'short_summary': str
        }
    """
    logger.info(f"Generating summary with Claude (language: {language})")

    # API 키 확인
    if not api_key:
        api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not found. Set it via environment variable or config.")

    anthropic = Anthropic(api_key=api_key)

    # 언어별 프롬프트 설정
    prompts = {
        'ko': {
            'chunk': "당신은 YouTube 영상을 요약하는 도움이 되는 어시스턴트입니다. 제공된 오디오 전사 내용을 명확한 bullet point로 요약해주세요. 반드시 한국어로 답변하세요.",
            'final': "핵심 포인트를 1-2문장으로 요약해주세요. 반드시 한국어로 답변하세요."
        },
        'en': {
            'chunk': "You are a helpful assistant that summarizes YouTube videos. Summarize the provided audio transcript chunk into clear bullet points.",
            'final': "Summarize the key points into 1-2 sentences that capture the essence."
        },
        'ja': {
            'chunk': "あなたはYouTube動画を要約する役立つアシスタントです。提供された音声トランスクリプトを明確な箇条書きで要約してください。必ず日本語で回答してください。",
            'final': "重要なポイントを1〜2文で要約してください。必ず日本語で回答してください。"
        }
    }

    # 언어가 지정되지 않았거나 지원하지 않는 경우 한국어 사용
    if language not in prompts:
        language = 'ko'
        logger.warning(f"Unsupported language, defaulting to Korean")

    chunk_prompt = prompts[language]['chunk']
    final_prompt = prompts[language]['final']

    # 전체 텍스트 결합
    full_text = ""
    for chunk in transcripts:
        for seg in chunk['segments']:
            full_text += seg['text'] + " "

    logger.info(f"Text length: {len(full_text)} characters")

    # 청크별 요약
    chunk_summaries = []
    for i, chunk in enumerate(transcripts):
        chunk_text = " ".join([seg['text'] for seg in chunk['segments']])

        logger.info(f"Summarizing chunk {i+1}/{len(transcripts)}")

        try:
            message = anthropic.messages.create(
                model=model,
                max_tokens=2048,
                temperature=0.3,
                system=chunk_prompt,
                messages=[{
                    "role": "user",
                    "content": chunk_text
                }]
            )

            summary = message.content[0].text
            chunk_summaries.append(summary)

        except Exception as e:
            logger.error(f"Summary failed for chunk {i+1}: {e}")
            chunk_summaries.append(f"[요약 실패: {str(e)}]")

    # 전체 요약 (long summary)
    long_summary = "\n\n".join(chunk_summaries)

    # 최종 요약 (TL;DR)
    logger.info("Generating final summary")
    try:
        message = anthropic.messages.create(
            model=model,
            max_tokens=512,
            temperature=0.3,
            system=final_prompt,
            messages=[{
                "role": "user",
                "content": long_summary
            }]
        )

        short_summary = message.content[0].text

    except Exception as e:
        logger.error(f"Final summary failed: {e}")
        short_summary = "[최종 요약 실패]"

    logger.info("Summary complete")

    return {
        'long_summary': long_summary,
        'short_summary': short_summary
    }


def save_summary(summary: Dict[str, str], output_dir: Path):
    """요약 결과 저장"""
    logger.info(f"Saving summary to {output_dir}")

    with open(output_dir / "summary.txt", "w", encoding="utf-8") as f:
        f.write("=== 상세 요약 ===\n\n")
        f.write(summary['long_summary'])
        f.write("\n\n=== TL;DR ===\n\n")
        f.write(summary['short_summary'])

    logger.info("Summary saved")


def save_metadata(metadata: Dict, output_dir: Path):
    """메타데이터 저장"""
    # Path 객체를 문자열로 변환
    serializable_metadata = {}
    for key, value in metadata.items():
        if isinstance(value, Path):
            serializable_metadata[key] = str(value)
        else:
            serializable_metadata[key] = value

    with open(output_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(serializable_metadata, f, ensure_ascii=False, indent=2)


def cleanup_temp_files(output_dir: Path):
    """임시 파일 정리"""
    logger.info("Cleaning up temporary files")

    # chunks 디렉토리 삭제
    chunks_dir = output_dir / "chunks"
    if chunks_dir.exists():
        shutil.rmtree(chunks_dir)

    # raw_audio 디렉토리 삭제
    raw_audio_dir = output_dir / "raw_audio"
    if raw_audio_dir.exists():
        shutil.rmtree(raw_audio_dir)

    logger.info("Cleanup complete")
