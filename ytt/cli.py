"""
YouTube Transcript Tool - CLI Interface
"""
import click
import logging
from pathlib import Path
from rich.console import Console
from rich.progress import (
    Progress, SpinnerColumn, TextColumn, BarColumn,
    TaskProgressColumn, TimeRemainingColumn, DownloadColumn, TransferSpeedColumn,
)
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Confirm

from . import core
from . import config
from . import setup

console = Console()


def setup_logging(verbose: bool):
    """로깅 설정"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(levelname)s: %(message)s' if not verbose else '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


@click.command()
@click.argument('youtube_url_or_dir')
@click.argument('output_dir', type=click.Path(), required=False)
@click.option(
    '--summarize', '-s',
    is_flag=True,
    help='요약도 함께 생성 (Claude API 필요)'
)
@click.option(
    '--summarize-only',
    is_flag=True,
    help='기존 transcript로 요약만 생성 (youtube_url 불필요)'
)
@click.option(
    '--timestamps',
    is_flag=True,
    help='타임스탬프 포함 전사 파일도 저장 (transcript_with_timestamps.txt)'
)
@click.option(
    '--json',
    'save_json',
    is_flag=True,
    help='구조화된 JSON 파일도 저장 (transcript.json)'
)
@click.option(
    '--metadata',
    'save_metadata',
    is_flag=True,
    help='영상 메타데이터 파일도 저장 (metadata.json)'
)
@click.option(
    '--model-size', '-m',
    type=click.Choice(['tiny', 'base', 'small', 'medium', 'large']),
    default='base',
    help='Whisper 모델 크기 (default: base)'
)
@click.option(
    '--language', '-l',
    default='auto',
    help='언어 지정 (ko/en/zh/auto 등, default: auto)'
)
@click.option(
    '--no-cleanup',
    is_flag=True,
    help='임시 파일 삭제하지 않음'
)
@click.option(
    '--no-cache',
    is_flag=True,
    help='프롬프트 캐싱 비활성화 (요약 시)'
)
@click.option(
    '--vad-aggressive',
    is_flag=True,
    help='Aggressive VAD 사용 (빠른 전사, 짧은 무음 포함 가능)'
)
@click.option(
    '--force-librosa',
    is_flag=True,
    help='librosa 청킹 강제 사용 (ffmpeg 비활성화)'
)
@click.option(
    '--fast',
    is_flag=True,
    help='빠른 전사 모드: beam_size=1, 청크 300초, CPU 풀 활용 (속도 우선, 품질 소폭 저하)'
)
@click.option(
    '--backend',
    type=click.Choice(['auto', 'mlx', 'faster-whisper']),
    default='auto',
    help='전사 백엔드 선택. auto: Apple Silicon에서 mlx-whisper 자동 사용, 나머지는 faster-whisper'
)
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='상세 로그 출력'
)
@click.version_option(version='1.4.0', prog_name='ytt')
def main(youtube_url_or_dir, output_dir, summarize, summarize_only, timestamps, save_json, save_metadata, model_size, language, no_cleanup, no_cache, vad_aggressive, force_librosa, fast, backend, verbose):
    """
    YouTube Transcript Tool (ytt)

    YouTube 영상을 다운로드하고 전사(transcript)를 생성합니다.
    기본 출력: 영상 정보 + 전체 전사 텍스트 (transcript.txt)

    \b
    예시:
        ytt "https://youtube.com/watch?v=xxx" ./output
        ytt "https://youtube.com/watch?v=xxx" ./output --timestamps --json
        ytt "https://youtube.com/watch?v=xxx" ./output --summarize
        ytt "https://youtube.com/watch?v=xxx" ./output -m medium -s
        ytt ./output --summarize-only  # 기존 transcript 요약만
    """
    setup_logging(verbose)

    # 설정 로드
    user_config = config.get_config()

    # 첫 실행 체크
    if setup.check_first_run():
        console.print("\n[yellow]👋 ytt를 처음 실행하시는 것 같습니다![/yellow]\n")
        if Confirm.ask("대화형 설정을 진행하시겠습니까?", default=True):
            if not setup.run_setup():
                return
            console.print("[dim]계속해서 작업을 진행합니다...[/dim]\n")
        else:
            console.print("[dim]설정을 건너뜁니다. 나중에 'ytt init' 명령어로 설정할 수 있습니다.[/dim]\n")
            # 기본 설정 파일 생성
            config.save_config(config.get_default_config())

    # --summarize를 주더라도 transcript.json은 --json이 명시된 경우에만 생성.
    # (재실행을 원한다면 처음 실행 시 --json을 함께 지정)

    # 인자 파싱
    if summarize_only:
        # summarize-only 모드: 첫 번째 인자가 output_dir
        youtube_url = None
        output_path = Path(youtube_url_or_dir).absolute()
        if not summarize:
            summarize = True  # summarize-only는 자동으로 summarize 활성화
    else:
        # 일반 모드: 첫 번째 인자가 youtube_url
        youtube_url = youtube_url_or_dir
        if not output_dir:
            console.print("[bold red]✗ 오류:[/bold red] OUTPUT_DIR이 필요합니다.")
            console.print("\n사용법:")
            console.print("  ytt <youtube_url> <output_dir> [OPTIONS]")
            console.print("  ytt <output_dir> --summarize-only")
            exit(1)
        output_path = Path(output_dir).absolute()

    if summarize_only:
        # summarize-only: 디렉토리가 존재하고 transcript.json 또는 transcript.txt가 있어야 함
        if not output_path.exists():
            console.print(f"[bold red]✗ 오류:[/bold red] 출력 디렉토리가 존재하지 않습니다: {output_path}")
            exit(1)

        transcript_file = output_path / "transcript.json"
        if not transcript_file.exists():
            console.print(f"[bold red]✗ 오류:[/bold red] transcript.json 파일을 찾을 수 없습니다: {transcript_file}")
            console.print("[dim]--summarize-only를 사용하려면 처음 실행 시 --json 플래그로 전사를 저장해야 합니다.[/dim]")
            console.print("[dim]예: ytt <url> <dir> --summarize --json[/dim]")
            exit(1)
    else:
        output_path.mkdir(parents=True, exist_ok=True)

    # 헤더 출력
    console.print(Panel.fit(
        "[bold cyan]YouTube Transcript Tool (ytt)[/bold cyan]\n"
        "[dim]AI-powered video transcription[/dim]",
        border_style="cyan"
    ))

    if not summarize_only:
        console.print(f"\n[bold]URL:[/bold] {youtube_url}")
    console.print(f"[bold]Output:[/bold] {output_path}")

    if summarize_only:
        console.print("[bold yellow]📝 요약 전용 모드[/bold yellow]")
    else:
        resolved_backend = core.resolve_backend(backend)
        console.print(f"[bold]Model:[/bold] {model_size}")
        console.print(f"[bold]Language:[/bold] {language if language != 'auto' else 'auto-detect'}")
        backend_label = {
            'mlx': '⚡ MLX (Apple Silicon GPU)',
            'faster-whisper': 'faster-whisper (CPU/CUDA)',
        }.get(resolved_backend, resolved_backend)
        console.print(f"[bold]Backend:[/bold] {backend_label}")
        if fast:
            console.print("[bold magenta]⚡ 빠른 전사 모드 (beam_size=1, 300초 청크)[/bold magenta]")
        if summarize:
            console.print("[bold yellow]📝 요약 모드 활성화[/bold yellow]")
    console.print()

    try:
        import json

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            console=console,
        ) as progress:

            if summarize_only:
                # 기존 transcript 로드
                console.print("[bold cyan]📂 기존 transcript 로딩 중...[/bold cyan]")
                with open(output_path / "transcript.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                    transcripts = data.get('chunks', [])
                    video_title = data.get('title', 'Unknown')
                console.print(f"[bold green]✓[/bold green] Transcript 로드 완료 ({len(transcripts)} chunks)")
                console.print(f"  [dim]제목: {video_title}[/dim]")
            else:
                # 1. YouTube 다운로드
                task1 = progress.add_task("🎬 영상 다운로드 중...", total=100)

                def _dl_hook(d):
                    if d['status'] == 'downloading':
                        total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                        downloaded = d.get('downloaded_bytes', 0)
                        speed = d.get('speed', 0) or 0
                        speed_str = f"{speed/1024/1024:.1f} MB/s" if speed > 0 else ""
                        if total > 0:
                            pct = (downloaded / total) * 100
                            size_str = f"{downloaded/1024/1024:.1f}/{total/1024/1024:.1f} MB"
                            desc = f"🎬 영상 다운로드 중... [{size_str}] {speed_str}"
                            progress.update(task1, completed=pct, description=desc)
                    elif d['status'] == 'finished':
                        progress.update(task1, completed=100, description="🎬 다운로드 완료, 오디오 변환 중...")

                download_result = core.download_youtube(youtube_url, output_path, progress_hook=_dl_hook)
                progress.remove_task(task1)
                console.print("[bold green]✓[/bold green] 다운로드 완료")

                video_title = download_result['title']
                console.print(f"  [dim]제목: {video_title}[/dim]")

                # 메타데이터 저장 (선택)
                if save_metadata:
                    core.save_metadata(download_result, output_path)

                # 2. 오디오 청킹
                task2 = progress.add_task("🎵 오디오 처리 중...", total=None)
                segment_length = 300 if fast else 600
                chunks = core.chunk_audio(
                    download_result['audio_path'],
                    output_path,
                    segment_length=segment_length,
                    force_librosa=force_librosa
                )
                progress.remove_task(task2)
                console.print(f"[bold green]✓[/bold green] 오디오 처리 완료 ({len(chunks)} chunks)")

                # 3. VAD 설정 준비
                vad_config = None
                if vad_aggressive:
                    # CLI 플래그로 aggressive 지정
                    vad_config = user_config.get('performance', {}).get('vad_config', {
                        'min_silence_duration_ms': 300,
                        'speech_pad_ms': 200,
                        'threshold': 0.5
                    })
                elif 'performance' in user_config and 'vad_config' in user_config['performance']:
                    # 설정 파일에서 VAD 설정 로드
                    vad_config = user_config['performance']['vad_config']

                # 4. 전사
                beam_size = 1 if fast else 5
                task3_desc = f"🎤 음성 전사 중... (모델: {model_size}" + (" ⚡빠름" if fast else "") + ")"
                task3 = progress.add_task(task3_desc, total=len(chunks))

                def _on_chunk_done(idx):
                    progress.advance(task3)

                transcripts = core.transcribe_audio(
                    chunks,
                    model_size=model_size,
                    language=language if language != 'auto' else None,
                    vad_config=vad_config,
                    on_chunk_done=_on_chunk_done,
                    beam_size=beam_size,
                    condition_on_previous_text=not fast,
                    backend=backend,
                )

                progress.remove_task(task3)
                console.print(f"[bold green]✓[/bold green] 전사 완료 ({len(transcripts)} chunks)")

                # 5. 파일 저장
                core.save_transcripts(
                    transcripts,
                    output_path,
                    video_title,
                    metadata=download_result,
                    save_timestamps=timestamps,
                    save_json=save_json,
                )
                console.print(f"[bold green]✓[/bold green] 전사 파일 저장 완료")

            # 6. 요약 (옵션)
            if summarize:
                # API 키 확인
                api_key = config.get_api_key()
                if not api_key:
                    console.print(
                        "\n[bold red]✗ 오류:[/bold red] ANTHROPIC_API_KEY가 설정되지 않았습니다.\n"
                        "환경 변수로 설정하거나 `ytt-config set-api-key <key>`를 실행하세요."
                    )
                else:
                    # Prompt Caching 설정 (기본: 활성화, --no-cache로 비활성화)
                    enable_caching = not no_cache
                    if 'performance' in user_config:
                        enable_caching = user_config['performance'].get('enable_prompt_caching', True) and not no_cache

                    task4 = progress.add_task("🤖 Claude로 요약 생성 중...", total=None)
                    summary = core.summarize_with_claude(
                        transcripts,
                        api_key,
                        language=language,
                        enable_caching=enable_caching
                    )
                    core.save_summary(summary, output_path)
                    progress.remove_task(task4)
                    console.print("[bold green]✓[/bold green] 요약 완료")

            # 7. 정리
            if not no_cleanup:
                core.cleanup_temp_files(output_path)
                console.print("[bold green]✓[/bold green] 임시 파일 정리 완료")

        # 결과 요약 테이블
        console.print()
        table = Table(title="생성된 파일", show_header=True, header_style="bold cyan")
        table.add_column("파일명", style="cyan")
        table.add_column("설명")

        table.add_row("transcript.txt", "영상 정보 + 전사 텍스트")
        if timestamps:
            table.add_row("transcript_with_timestamps.txt", "타임스탬프 포함 전사")
        if save_json:
            table.add_row("transcript.json", "구조화된 JSON 데이터")
        if save_metadata:
            table.add_row("metadata.json", "영상 메타데이터")
        if summarize and api_key:
            table.add_row("summary.txt", "AI 요약 (상세 + TL;DR)")

        console.print(table)

        console.print(f"\n[bold green]✓ 모든 작업 완료![/bold green]")
        console.print(f"[dim]결과물 위치: {output_path}[/dim]")

    except KeyboardInterrupt:
        console.print("\n[yellow]작업이 사용자에 의해 중단되었습니다.[/yellow]")
        exit(130)

    except Exception as e:
        console.print(f"\n[bold red]✗ 오류 발생:[/bold red] {str(e)}")
        if verbose:
            console.print_exception()
        exit(1)


@click.group()
def config_cli():
    """설정 관리"""
    pass


@config_cli.command('set-api-key')
@click.argument('api_key')
def set_api_key(api_key):
    """Claude API 키 설정"""
    config.set_api_key(api_key)
    console.print("[green]✓ API 키가 저장되었습니다.[/green]")


@config_cli.command('show-config')
def show_config():
    """현재 설정 표시"""
    config_dir = config.get_config_dir()
    api_key = config.get_api_key()
    user_config = config.get_config()

    console.print(f"\n[bold]설정 디렉토리:[/bold] {config_dir}")
    console.print(f"[bold]API 키 설정 여부:[/bold] {'✓ 설정됨' if api_key else '✗ 없음'}\n")

    console.print("[bold]기본 설정:[/bold]")
    console.print(f"  언어: {user_config.get('default_language', 'ko')}")
    console.print(f"  모델 크기: {user_config.get('default_model_size', 'base')}")
    console.print(f"  자동 요약: {'예' if user_config.get('auto_summarize', False) else '아니오'}\n")


@click.command()
@click.option('--reset', is_flag=True, help='기존 설정을 초기화하고 다시 설정')
def init(reset):
    """대화형 설정 마법사"""
    if reset:
        console.print("[yellow]⚠️  기존 설정을 초기화합니다.[/yellow]\n")

    success = setup.run_setup(skip_checks=False)

    if not success:
        exit(1)


if __name__ == '__main__':
    main()
