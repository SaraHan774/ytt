class Ytt < Formula
  include Language::Python::Virtualenv

  desc "YouTube Transcript Tool - AI-powered video transcription and summarization"
  homepage "https://github.com/SaraHan774/ytt"
  url "https://github.com/SaraHan774/ytt/archive/refs/tags/v1.0.0.tar.gz"
  sha256 "de7cc83d80fe05b36df0935106728c639b0d05b7b79c3be79abda2e994ad317e"
  license "MIT"
  head "https://github.com/SaraHan774/ytt.git", branch: "main"

  depends_on "ffmpeg"
  depends_on "python@3.11"

  resource "faster-whisper" do
    url "https://files.pythonhosted.org/packages/source/f/faster-whisper/faster-whisper-1.2.1.tar.gz"
    sha256 "RESOURCE_SHA256_HERE"
  end

  resource "anthropic" do
    url "https://files.pythonhosted.org/packages/source/a/anthropic/anthropic-0.76.0.tar.gz"
    sha256 "RESOURCE_SHA256_HERE"
  end

  resource "yt-dlp" do
    url "https://files.pythonhosted.org/packages/source/y/yt-dlp/yt_dlp-2024.12.23.tar.gz"
    sha256 "RESOURCE_SHA256_HERE"
  end

  resource "librosa" do
    url "https://files.pythonhosted.org/packages/source/l/librosa/librosa-0.10.2.tar.gz"
    sha256 "RESOURCE_SHA256_HERE"
  end

  resource "soundfile" do
    url "https://files.pythonhosted.org/packages/source/s/soundfile/soundfile-0.12.1.tar.gz"
    sha256 "RESOURCE_SHA256_HERE"
  end

  resource "click" do
    url "https://files.pythonhosted.org/packages/source/c/click/click-8.1.7.tar.gz"
    sha256 "RESOURCE_SHA256_HERE"
  end

  resource "rich" do
    url "https://files.pythonhosted.org/packages/source/r/rich/rich-13.9.4.tar.gz"
    sha256 "RESOURCE_SHA256_HERE"
  end

  resource "python-dotenv" do
    url "https://files.pythonhosted.org/packages/source/p/python-dotenv/python-dotenv-1.0.1.tar.gz"
    sha256 "RESOURCE_SHA256_HERE"
  end

  def install
    virtualenv_install_with_resources

    # Generate shell completions
    generate_completions_from_executable(bin/"ytt", shells: [:bash, :zsh, :fish], shell_parameter_format: :click)
  end

  def post_install
    # Create config directory
    (var/"ytt").mkpath
  end

  def caveats
    <<~EOS
      🎬 YouTube Transcript Tool (ytt) has been installed!

      To get started:
        1. Run the setup wizard:
           $ ytt-init

        2. Or set your API key manually:
           $ ytt-config set-api-key "your-anthropic-api-key"

        3. Transcribe a YouTube video:
           $ ytt "https://youtube.com/watch?v=xxx" ./output

        4. With summary:
           $ ytt "https://youtube.com/watch?v=xxx" ./output --summarize

      For help:
        $ ytt --help
        $ ytt-init --help
        $ ytt-config --help

      Documentation: https://github.com/SaraHan774/ytt
    EOS
  end

  test do
    # Test that commands are available
    assert_match "YouTube Transcript Tool", shell_output("#{bin}/ytt --version")
    assert_match "설정 마법사", shell_output("#{bin}/ytt-init --help")
    assert_match "설정 관리", shell_output("#{bin}/ytt-config --help")

    # Test config directory creation
    system bin/"ytt-config", "show-config"
  end
end
