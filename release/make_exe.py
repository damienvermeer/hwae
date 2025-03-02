"""
HWAE (Hostile Waters Antaeus Eternal)

make_exe.py

Script to build a PyInstaller executable and prepare the distribution
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


def main():
    # Get the project root directory
    project_root = Path(__file__).resolve().parent.parent
    src_dir = project_root / "src"
    sys.path.append(str(src_dir))
    build_dir = project_root / "build"
    dist_dir = project_root / "dist"
    assets_dir = src_dir / "assets"

    from constants import VERSION_STR

    # Create build directory if it doesn't exist
    build_dir.mkdir(exist_ok=True)

    # Clean up previous builds
    if dist_dir.exists():
        print(f"Cleaning up previous build in {dist_dir}")
        shutil.rmtree(dist_dir)

    # Install PyInstaller if not already installed
    # try:
    import PyInstaller

    # print("PyInstaller is already installed")
    # except ImportError:
    #     print("Installing PyInstaller...")
    #     subprocess.check_call([sys.executable, "-m", "pip", "install", "PyInstaller"])

    # Build the executable
    print("Building executable with PyInstaller...")
    subprocess.check_call(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--onefile",
            "--hidden-import",
            "ui",
            "--hidden-import",
            "fileio",
            "--hidden-import",
            "tkinter",
            f"--name=HW Antaeus Eternal v{VERSION_STR}.exe",
            "--clean",
            "--distpath",
            str(dist_dir),
            "--workpath",
            str(build_dir / "pyinstaller"),
            "--paths",
            str(src_dir),
            "--add-data",
            f"{src_dir / 'paths.py'};.",
            str(src_dir / "main.py"),
            # set icon
            "--icon",
            str(assets_dir / "icon.ico"),
        ]
    )

    # Create assets directory in the distribution folder
    dist_assets_dir = dist_dir / "assets"
    if dist_assets_dir.exists():
        shutil.rmtree(dist_assets_dir)

    # Copy assets to the distribution folder
    print(f"Copying assets from {assets_dir} to {dist_assets_dir}")
    shutil.copytree(assets_dir, dist_assets_dir)

    print("Build completed successfully!")
    print(f"Executable and assets are available in: {dist_dir}")

    # clean build dir afterwards)
    shutil.rmtree(build_dir)


if __name__ == "__main__":
    main()
