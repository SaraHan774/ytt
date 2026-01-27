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
from .i18n import t, set_language, SUPPORTED_LANGUAGES

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
        f"[bold cyan]{t('setup.welcome.title')}[/bold cyan]\n\n"
        f"[dim]{t('setup.welcome.description')}[/dim]",
        border_style="cyan",
        padding=(1, 2)
    ))
    console.print()


def display_system_check(info: dict):
    """시스템 환경 확인 결과 출력"""
    console.print(f"[bold]{t('setup.system_check.title')}[/bold]\n")

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(t('setup.system_check.item'), style="cyan")
    table.add_column(t('setup.system_check.status'))

    # Python
    table.add_row("Python", f"✓ {info['python']}")

    # ffmpeg
    if info['ffmpeg']:
        table.add_row("ffmpeg", t('setup.system_check.ffmpeg_installed'))
    else:
        table.add_row("ffmpeg", f"[red]{t('setup.system_check.ffmpeg_required')}[/red]")

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


def setup_cli_language() -> str:
    """CLI 언어 설정 (먼저 선택)"""
    console.print("[bold]🌍 CLI Language / CLI 언어 / CLI 语言[/bold]\n")

    # 언어 목록 표시
    for code, name in SUPPORTED_LANGUAGES.items():
        console.print(f"  [{code}] {name}")
    console.print()

    language = Prompt.ask(
        "Select language / 언어 선택 / 选择语言",
        choices=list(SUPPORTED_LANGUAGES.keys()),
        default="ko"
    )

    # 선택한 언어로 즉시 전환
    set_language(language)
    console.print(f"[green]✓ Language set to {SUPPORTED_LANGUAGES[language]}[/green]\n")

    return language


def setup_api_key() -> Optional[str]:
    """API 키 설정"""
    console.print(f"[bold]{t('setup.api_key.title')}[/bold]\n")

    # 기존 API 키 확인
    existing_key = config.get_api_key()
    if existing_key:
        console.print(f"[dim]{t('setup.api_key.current', api_key=existing_key[:20])}[/dim]")
        if not Confirm.ask(t('setup.api_key.change'), default=False):
            return existing_key

    console.print(f"[dim]{t('setup.api_key.description')}[/dim]")
    console.print(f"[dim]{t('setup.api_key.skip')}[/dim]\n")

    api_key = Prompt.ask(
        t('setup.api_key.prompt'),
        default="",
        password=True
    )

    if api_key:
        # 간단한 형식 검증
        if not api_key.startswith("sk-ant-"):
            console.print(f"[yellow]{t('setup.api_key.warning')}[/yellow]")
            if not Confirm.ask(t('setup.api_key.continue'), default=True):
                return None

        # 설정 파일에 저장
        config.set_api_key(api_key)
        console.print(f"[green]{t('setup.api_key.saved')}[/green]\n")
        return api_key
    else:
        console.print(f"[yellow]{t('setup.api_key.later_info')}[/yellow]")
        console.print(f"[dim]{t('setup.api_key.later_export')}[/dim]")
        console.print(f"[dim]{t('setup.api_key.later_command')}[/dim]\n")
        return None


def setup_defaults() -> dict:
    """기본 설정값 지정"""
    console.print(f"[bold]{t('setup.defaults.title')}[/bold]\n")

    # 기본 요약 언어
    console.print(f"[dim]{t('setup.defaults.language_description')}[/dim]")
    default_language = Prompt.ask(
        t('setup.defaults.language_prompt'),
        choices=["ko", "en", "zh"],
        default="ko"
    )

    # 기본 모델 크기
    console.print(f"\n[dim]{t('setup.defaults.model_description')}[/dim]")
    model_size = Prompt.ask(
        t('setup.defaults.model_prompt'),
        choices=["tiny", "base", "small", "medium", "large"],
        default="base"
    )

    # 자동 요약 여부
    console.print()
    auto_summarize = Confirm.ask(
        t('setup.defaults.auto_summarize'),
        default=False
    )

    settings = {
        'default_language': default_language,
        'default_model_size': model_size,
        'auto_summarize': auto_summarize,
    }

    console.print()
    return settings


def save_user_config(settings: dict):
    """설정 저장"""
    config.save_config(settings)
    config_path = config.get_config_dir() / "config.json"
    console.print(f"[green]{t('setup.config_saved', path=config_path)}[/green]\n")


def display_ffmpeg_install_instructions(platform: str):
    """ffmpeg 설치 방법 안내"""
    console.print(f"\n[bold red]{t('setup.ffmpeg.title')}[/bold red]\n")
    console.print(f"{t('setup.ffmpeg.description')}\n")

    if platform == 'darwin':  # macOS
        console.print("  [cyan]brew install ffmpeg[/cyan]\n")
    elif platform == 'linux':
        console.print("  [cyan]sudo apt-get install ffmpeg[/cyan]  # Ubuntu/Debian")
        console.print("  [cyan]sudo yum install ffmpeg[/cyan]      # CentOS/RHEL\n")
    elif platform == 'win32':
        console.print("  [cyan]choco install ffmpeg[/cyan]  # Chocolatey")
        console.print("  or download from https://ffmpeg.org/download.html\n")


def display_quickstart():
    """빠른 시작 가이드"""
    console.print(f"[bold]{t('setup.quickstart.title')}[/bold]\n")

    console.print(f"{t('setup.quickstart.basic')}")
    console.print("  [cyan]ytt \"https://youtube.com/watch?v=xxx\" ./output[/cyan]")
    console.print()

    console.print(f"{t('setup.quickstart.with_summary')}")
    console.print("  [cyan]ytt \"https://youtube.com/watch?v=xxx\" ./output --summarize[/cyan]")
    console.print()

    console.print(f"{t('setup.quickstart.help')}")
    console.print("  [cyan]ytt --help[/cyan]")
    console.print()

    console.print(f"[dim]{t('setup.quickstart.docs')}[/dim]")
    console.print()


def run_setup(skip_checks: bool = False) -> bool:
    """
    대화형 설치 실행

    Args:
        skip_checks: 시스템 체크 건너뛰기

    Returns:
        bool: 설치 성공 여부
    """
    # 먼저 CLI 언어 선택
    cli_language = setup_cli_language()

    display_welcome()

    # 시스템 환경 확인
    if not skip_checks:
        info = get_system_info()
        display_system_check(info)

        # ffmpeg 미설치 시 경고
        if not info['ffmpeg']:
            display_ffmpeg_install_instructions(info['platform'])
            if not Confirm.ask(t('setup.api_key.continue'), default=True):
                console.print(f"[yellow]{t('setup.cancelled')}[/yellow]")
                return False
            console.print()

    # API 키 설정
    api_key = setup_api_key()

    # 기본 설정
    settings = setup_defaults()

    # CLI 언어 추가
    settings['language'] = cli_language

    # 설정 저장
    save_user_config(settings)

    # 완료 메시지
    console.print(Panel.fit(
        f"[bold green]{t('setup.complete.title')}[/bold green]\n\n"
        f"[dim]{t('setup.complete.description')}[/dim]",
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
