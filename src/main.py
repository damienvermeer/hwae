"""
HWAE (Hostile Waters Antaeus Eternal)

Python package (released as a pyinstaller exe) to generate additional maps for Hostile Waters: Antaeus Rising (2001)
"""

import logging
import numpy as np

from fileio.lev import LevFile
from fileio.cfg import CfgFile
from fileio.ob3 import Ob3File

from noisegen import NoiseGenerator
from objects import ObjectHandler, Team
from terrain import TerrainHandler
from texture import select_map_texture_group
from minimap import generate_minimap

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    # load lev
    lev_data = LevFile(r"C:\HWAR\HWAR\modtest2\Level22\level22 original.lev")
    # load cfg
    cfg_data = CfgFile(r"C:\HWAR\HWAR\modtest2\Level22\level22 - differentetxtures.cfg")
    # create a blank ob3
    ob3_data = Ob3File("")
    # create a common noise generator
    noise_generator = NoiseGenerator(seed=0)

    # select texture group
    select_map_texture_group(
        cfg_data, noise_generator, r"C:\HWAR\HWAR\modtest2\Level52"
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
        terrain_handler, cfg_data, r"C:\HWAR\HWAR\modtest2\Level52\map.pcx"
    )
    # save all files
    for file in [lev_data, cfg_data, ob3_data]:
        file.save(r"C:\HWAR\HWAR\modtest2\Level52", "Level52")
