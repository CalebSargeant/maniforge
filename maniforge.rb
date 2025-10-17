class Maniforge < Formula
  desc "Terraform-like tool for managing Kubernetes applications"
  homepage "https://github.com/calebsargeant/maniforge"
  license "MIT"

  on_macos do
    if Hardware::CPU.arm?
      url "https://github.com/calebsargeant/maniforge/releases/download/v1.0.0/maniforge-macos-arm64"
      sha256 "" # Will be calculated from release binary
    else
      url "https://github.com/calebsargeant/maniforge/releases/download/v1.0.0/maniforge-macos-x86_64"
      sha256 "" # Will be calculated from release binary
    end
  end

  on_linux do
    if Hardware::CPU.arm?
      url "https://github.com/calebsargeant/maniforge/releases/download/v1.0.0/maniforge-linux-arm64"
      sha256 "" # Will be calculated from release binary
    else
      url "https://github.com/calebsargeant/maniforge/releases/download/v1.0.0/maniforge-linux-x86_64"
      sha256 "" # Will be calculated from release binary
    end
  end

  def install
    # The downloaded file is already the executable
    bin.install Dir["maniforge-*"].first => "maniforge"
  end

  test do
    system "#{bin}/maniforge", "--help"
  end
end
