"""
HWAE (Hostile Waters Antaeus Eternal)

Python package (released as a pyinstaller exe) to generate additional maps for Hostile Waters: Antaeus Rising (2001)
"""

import logging
import numpy as np
from pathlib import Path

from fileio.cfg import CfgFile
from fileio.lev import LevFile
from fileio.ob3 import Ob3File
from fileio.ars import ArsFile

from noisegen import NoiseGenerator
from objects import ObjectHandler, Team
from terrain import TerrainHandler
from texture import select_map_texture_group
from minimap import generate_minimap

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    # TODO somehow specify the output location
    NEW_LEVEL_NAME = "Level53"
    noise_generator = NoiseGenerator(seed=1)

    # TODO select a template
    # select large template root
    template_root = Path(__file__).resolve().parent / "assets" / "templates"

    # Create fileio objects we need to create the level
    cfg_data = CfgFile(template_root / "large.cfg")
    lev_data = LevFile(template_root / "large.lev")
    ars_data = ArsFile(template_root / "common.ars")
    ob3_data = Ob3File("")  # we dont need to load an existing ob3

    # select texture group
    select_map_texture_group(
        cfg_data, noise_generator, rf"C:\HWAR\HWAR\modtest2\{NEW_LEVEL_NAME}"
    )
    # create a terrain handler
    terrain_handler = TerrainHandler(lev_data, noise_generator)
    terrain_handler.set_terrain_from_noise()
    # create an objecthandler
    object_handler = ObjectHandler(terrain_handler, ob3_data)
    object_handler.add_object(
        "Carrier",
        np.array([100, 6, 100]),
        team=0,
    )
    # object_handler.add_object("dedicatedlifter", np.array([95, 15, 100]), team=0)
    object_handler.add_object_on_ground(
        "ALIENGROUNDPROD", location_x=256 / 2, location_z=256 / 2, team=1
    )
    object_handler.add_object_on_ground(
        "command",
        location_x=256 / 2 - 5,
        location_z=256 / 2 + 2,
        y_offset=10,
        team=Team.NEUTRAL,
    )
    # create minimap
    generate_minimap(
        terrain_handler, cfg_data, rf"C:\HWAR\HWAR\modtest2\{NEW_LEVEL_NAME}\map.pcx"
    )
    # save all files
    for file in [lev_data, cfg_data, ob3_data, ars_data]:
        file.save(rf"C:\HWAR\HWAR\modtest2\{NEW_LEVEL_NAME}", NEW_LEVEL_NAME)
