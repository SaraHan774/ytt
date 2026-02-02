"""
YouTube Transcript Tool - Configuration Management
"""
import os
from pathlib import Path
from typing import Optional


def get_config_dir() -> Path:
    """
    설정 디렉토리 반환

    - macOS/Linux: ~/.config/ytt
    - Windows: %APPDATA%/ytt
    """
    if os.name == 'nt':  # Windows
        config_dir = Path(os.getenv('APPDATA', Path.home() / 'AppData' / 'Roaming')) / 'ytt'
    else:  # Unix-like (macOS, Linux)
        config_dir = Path.home() / '.config' / 'ytt'

    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_api_key() -> Optional[str]:
    """
    Claude API 키 반환

    우선순위:
    1. 환경 변수 ANTHROPIC_API_KEY
    2. 설정 파일 ~/.config/ytt/api_key.txt
    """
    # 1. 환경 변수 확인
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        return api_key

    # 2. 설정 파일 확인
    config_file = get_config_dir() / "api_key.txt"
    if config_file.exists():
        with open(config_file, 'r') as f:
            key = f.read().strip()
            if key:
                return key

    return None


def set_api_key(api_key: str):
    """
    Claude API 키 저장

    ~/.config/ytt/api_key.txt에 저장
    """
    config_file = get_config_dir() / "api_key.txt"
    with open(config_file, 'w') as f:
        f.write(api_key.strip())

    # 파일 권한 설정 (Unix-like 시스템에서)
    if os.name != 'nt':
        config_file.chmod(0o600)  # rw-------


def delete_api_key():
    """저장된 API 키 삭제"""
    config_file = get_config_dir() / "api_key.txt"
    if config_file.exists():
        config_file.unlink()


def get_config() -> dict:
    """
    설정 파일 로드

    Returns:
        dict: 설정값 딕셔너리
    """
    config_file = get_config_dir() / "config.json"

    if not config_file.exists():
        return get_default_config()

    try:
        import json
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
            # 기본값과 병합
            default = get_default_config()
            default.update(config_data)
            return default
    except Exception:
        return get_default_config()


def get_default_config() -> dict:
    """기본 설정 반환"""
    return {
        'language': 'ko',  # CLI 언어 (ko, en, zh)
        'default_language': 'ko',  # 요약 언어
        'default_model_size': 'base',
        'auto_summarize': False,
        # 성능 최적화 설정
        'performance': {
            'use_ffmpeg_chunking': True,    # ffmpeg 자동 감지 및 사용
            'enable_prompt_caching': True,   # 프롬프트 캐싱 활성화
            'vad_config': {
                'min_silence_duration_ms': 300,  # aggressive (더 빠른 전사)
                'speech_pad_ms': 200,            # speech 세그먼트 패딩
                'threshold': 0.5                 # 음성 감지 임계값
            }
        }
    }


def save_config(config_data: dict):
    """
    설정 파일 저장

    Args:
        config_data: 저장할 설정 딕셔너리
    """
    import json
    config_file = get_config_dir() / "config.json"

    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=2, ensure_ascii=False)
