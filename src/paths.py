"""
HWAE (Hostile Waters Antaeus Eternal)

paths.py

Handles path resolution for both development and PyInstaller environments
"""

import os
import sys
from pathlib import Path


def get_base_path() -> Path:
    """
    Returns the base path for the application, handling both development and PyInstaller environments.
    
    Returns:
        Path: The base path where application resources are located
    """
    if getattr(sys, 'frozen', False):
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        if hasattr(sys, '_MEIPASS'):
            return Path(sys._MEIPASS)
        else:
            # Fallback to executable directory if _MEIPASS is not available
            return Path(sys.executable).parent
    else:
        # Development mode - use the src parent directory
        return Path(__file__).resolve().parent.parent


def get_assets_path() -> Path:
    """
    Returns the path to the assets directory
    
    Returns:
        Path: Path to the assets directory
    """
    if getattr(sys, 'frozen', False):
        # In PyInstaller bundle, assets are in a dedicated folder next to the executable
        return get_base_path() / "assets"
    else:
        # In development mode, assets are in the src directory
        return Path(__file__).resolve().parent / "assets"


def get_templates_path() -> Path:
    """
    Returns the path to the templates directory
    
    Returns:
        Path: Path to the templates directory
    """
    return get_assets_path() / "templates"


def get_textures_path() -> Path:
    """
    Returns the path to the textures directory
    
    Returns:
        Path: Path to the textures directory
    """
    return get_assets_path() / "textures"
