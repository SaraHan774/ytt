"""
YouTube Transcript Tool (ytt) - Setup Script
"""
from setuptools import setup, find_packages
from pathlib import Path

# README 읽기
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="ytt",
    version="1.0.1",
    description="YouTube Transcript Tool - AI-powered video transcription",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/SaraHan774/ytt",
    packages=find_packages(),
    install_requires=[
        "faster-whisper>=0.10.0",
        "anthropic>=0.18.0",
        "yt-dlp>=2023.0.0",
        "librosa>=0.10.0",
        "soundfile>=0.12.0",
        "click>=8.1.0",
        "rich>=13.0.0",
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.12.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "ytt=ytt.cli:main",
            "ytt-init=ytt.cli:init",
            "ytt-config=ytt.cli:config_cli",
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Multimedia :: Sound/Audio :: Speech",
        "Topic :: Multimedia :: Video",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    keywords="youtube transcript transcription whisper claude ai video audio",
    project_urls={
        "Bug Reports": "https://github.com/SaraHan774/ytt/issues",
        "Source": "https://github.com/SaraHan774/ytt",
    },
)
