"""
HWAE (Hostile Waters Antaeus Eternal)

src.texture

Handles selecting and copying textures
"""

from dataclasses import dataclass
from src.logger import get_logger

logger = get_logger()
import noise
from fileio.cfg import CfgFile
from fileio.ob3 import MAP_SCALER
from noisegen import NoiseGenerator
import numpy as np
import os
from PIL import Image
import shutil
from pathlib import Path


def select_map_texture_group(
    path_to_textures: Path,
    cfg: CfgFile,
    noise_gen: NoiseGenerator,
    paste_textures_path: str,
) -> None:
    """
    Selects a random group of textures from the pre-grouped textures, loads the
    texture info into the CFG file and then copies them to the paste_textures_path

    Args:
        path_to_textures (Path): Location of the pre-grouped textures
        cfg (CfgFile): CFG file interface
        noise_gen (NoiseGenerator): Noise generator
        paste_textures_path (str): Location to copy the textures to
    """
    # count how many folders there are
    folders = os.listdir(path_to_textures)

    # select a random folder using noise_gen
    if len(folders) == 1:
        folder_idx = 0
    else:
        folder_idx = noise_gen.randint(0, len(folders) - 1)

    # Load the texture_description from the folder
    with open(
        path_to_textures / f"{folders[folder_idx]}" / "texture_description.txt", "r"
    ) as f:
        cfg["Land Textures"] = f.read()

    # copy all the textures into the output location
    shutil.copytree(
        path_to_textures / f"{folders[folder_idx]}",
        paste_textures_path,
        dirs_exist_ok=True,
        ignore=lambda x, y: [f for f in y if not f.endswith(".pcx")],
    )
