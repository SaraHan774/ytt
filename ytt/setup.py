"""
Interactive Setup Tool for YouTube Transcript Tool
"""
import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table

from . import config

console = Console()


def check_ffmpeg() -> bool:
    """ffmpeg 설치 확인"""
    return shutil.which("ffmpeg") is not None


def check_gpu() -> Optional[str]:
    """GPU 사용 가능 여부 확인"""
    try:
        import torch
        if torch.cuda.is_available():
            return f"CUDA (GPU: {torch.cuda.get_device_name(0)})"
        else:
            return "CPU only"
    except ImportError:
        return "CPU only (PyTorch not found)"


def get_system_info() -> dict:
    """시스템 정보 수집"""
    return {
        'ffmpeg': check_ffmpeg(),
        'gpu': check_gpu(),
        'python': f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
        'platform': os.sys.platform,
    }


def display_welcome():
    """환영 메시지 출력"""
    console.print()
    console.print(Panel.fit(
        "[bold cyan]🎬 YouTube Transcript Tool (ytt) - 설치 마법사[/bold cyan]\n\n"
        "[dim]YouTube 영상을 전사하고 요약하는 CLI 도구입니다.[/dim]",
        border_style="cyan",
        padding=(1, 2)
    ))
    console.print()


def display_system_check(info: dict):
    """시스템 환경 확인 결과 출력"""
    console.print("[bold]📋 시스템 환경 확인[/bold]\n")

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("항목", style="cyan")
    table.add_column("상태")

    # Python
    table.add_row("Python", f"✓ {info['python']}")

    # ffmpeg
    if info['ffmpeg']:
        table.add_row("ffmpeg", "✓ 설치됨")
    else:
        table.add_row("ffmpeg", "[red]✗ 설치 필요[/red]")

    # GPU
    table.add_row("GPU", f"ℹ  {info['gpu']}")

    # Platform
    platform_name = {
        'darwin': 'macOS',
        'linux': 'Linux',
        'win32': 'Windows'
    }.get(info['platform'], info['platform'])
    table.add_row("OS", f"ℹ  {platform_name}")

    console.print(table)
    console.print()


def setup_api_key() -> Optional[str]:
    """API 키 설정"""
    console.print("[bold]🔑 Anthropic API 키 설정[/bold]\n")

    # 기존 API 키 확인
    existing_key = config.get_api_key()
    if existing_key:
        console.print(f"[dim]현재 API 키: {existing_key[:20]}...[/dim]")
        if not Confirm.ask("API 키를 변경하시겠습니까?", default=False):
            return existing_key

    console.print("[dim]Anthropic API 키는 요약 기능에 필요합니다.[/dim]")
    console.print("[dim]나중에 설정하려면 Enter를 누르세요.[/dim]\n")

    api_key = Prompt.ask(
        "Anthropic API 키",
        default="",
        password=True
    )

    if api_key:
        # 간단한 형식 검증
        if not api_key.startswith("sk-ant-"):
            console.print("[yellow]⚠ 경고: API 키 형식이 올바르지 않을 수 있습니다.[/yellow]")
            if not Confirm.ask("계속 진행하시겠습니까?", default=True):
                return None

        # 설정 파일에 저장
        config.set_api_key(api_key)
        console.print("[green]✓ API 키가 저장되었습니다.[/green]\n")
        return api_key
    else:
        console.print("[yellow]ℹ  API 키를 나중에 설정할 수 있습니다:[/yellow]")
        console.print("[dim]  export ANTHROPIC_API_KEY='your-key'[/dim]")
        console.print("[dim]  또는: ytt config set-api-key 'your-key'[/dim]\n")
        return None


def setup_defaults() -> dict:
    """기본 설정값 지정"""
    console.print("[bold]⚙️  기본 설정[/bold]\n")

    # 기본 언어
    console.print("[dim]요약 및 출력에 사용할 기본 언어를 선택하세요.[/dim]")
    language = Prompt.ask(
        "기본 언어",
        choices=["ko", "en", "ja"],
        default="ko"
    )

    # 기본 모델 크기
    console.print("\n[dim]Whisper 모델 크기 (작을수록 빠르지만 정확도 낮음)[/dim]")
    model_size = Prompt.ask(
        "기본 모델 크기",
        choices=["tiny", "base", "small", "medium", "large"],
        default="base"
    )

    # 자동 요약 여부
    console.print()
    auto_summarize = Confirm.ask(
        "전사 후 항상 자동으로 요약하시겠습니까?",
        default=False
    )

    settings = {
        'default_language': language,
        'default_model_size': model_size,
        'auto_summarize': auto_summarize,
    }

    console.print()
    return settings


def save_user_config(settings: dict):
    """설정 저장"""
    config.save_config(settings)
    config_path = config.get_config_dir() / "config.json"
    console.print(f"[green]✓ 설정이 저장되었습니다: {config_path}[/green]\n")


def display_ffmpeg_install_instructions(platform: str):
    """ffmpeg 설치 방법 안내"""
    console.print("\n[bold red]⚠️  ffmpeg가 설치되지 않았습니다![/bold red]\n")
    console.print("ffmpeg는 필수 의존성입니다. 다음 명령어로 설치하세요:\n")

    if platform == 'darwin':  # macOS
        console.print("  [cyan]brew install ffmpeg[/cyan]\n")
    elif platform == 'linux':
        console.print("  [cyan]sudo apt-get install ffmpeg[/cyan]  # Ubuntu/Debian")
        console.print("  [cyan]sudo yum install ffmpeg[/cyan]      # CentOS/RHEL\n")
    elif platform == 'win32':
        console.print("  [cyan]choco install ffmpeg[/cyan]  # Chocolatey")
        console.print("  또는 https://ffmpeg.org/download.html 에서 다운로드\n")


def display_quickstart():
    """빠른 시작 가이드"""
    console.print("[bold]🚀 빠른 시작[/bold]\n")

    console.print("기본 사용법:")
    console.print("  [cyan]ytt \"https://youtube.com/watch?v=xxx\" ./output[/cyan]")
    console.print()

    console.print("요약 포함:")
    console.print("  [cyan]ytt \"https://youtube.com/watch?v=xxx\" ./output --summarize[/cyan]")
    console.print()

    console.print("자세한 도움말:")
    console.print("  [cyan]ytt --help[/cyan]")
    console.print()

    console.print("[dim]문서: https://github.com/yourusername/ytt[/dim]")
    console.print()


def run_setup(skip_checks: bool = False) -> bool:
    """
    대화형 설치 실행

    Args:
        skip_checks: 시스템 체크 건너뛰기

    Returns:
        bool: 설치 성공 여부
    """
    display_welcome()

    # 시스템 환경 확인
    if not skip_checks:
        info = get_system_info()
        display_system_check(info)

        # ffmpeg 미설치 시 경고
        if not info['ffmpeg']:
            display_ffmpeg_install_instructions(info['platform'])
            if not Confirm.ask("계속 진행하시겠습니까?", default=True):
                console.print("[yellow]설치가 취소되었습니다.[/yellow]")
                return False
            console.print()

    # API 키 설정
    api_key = setup_api_key()

    # 기본 설정
    settings = setup_defaults()

    # 설정 저장
    save_user_config(settings)

    # 완료 메시지
    console.print(Panel.fit(
        "[bold green]✓ 설치가 완료되었습니다![/bold green]\n\n"
        "[dim]이제 ytt를 사용할 준비가 되었습니다.[/dim]",
        border_style="green"
    ))
    console.print()

    # 빠른 시작 가이드
    display_quickstart()

    return True


def check_first_run() -> bool:
    """첫 실행 여부 확인"""
    config_file = config.get_config_dir() / "config.json"
    return not config_file.exists()
