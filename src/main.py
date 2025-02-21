"""
HWAE (Hostile Waters Antaeus Eternal)

Python package (released as a pyinstaller exe) to generate additional maps for Hostile Waters: Antaeus Rising (2001)
"""

import logging
import shutil
from pathlib import Path
import os

from fileio.cfg import CfgFile
from fileio.lev import LevFile
from fileio.ob3 import Ob3File
from fileio.ars import ArsFile
from src.object_containers import ALL_BASE
import src.object_templates as ot

from construction import ConstructionManager
from noisegen import NoiseGenerator
from objects import ObjectHandler, Team
from terrain import TerrainHandler
from texture import select_map_texture_group
from minimap import generate_minimap
from zones import ZoneManager, ZoneType, ZoneSize, ZoneSpecial

logging.basicConfig(level=logging.INFO)


def main():
    # TODO somehow specify the output location
    OUTPUT_PATH = Path(r"C:\HWAR\HWAR\modtest2")
    NEW_LEVEL_NAME = "Level53"
    noise_generator = NoiseGenerator(seed=2)

    # TODO select from alternative map sizes - only large (L22, 256*256) for now
    map_size_template = "large"
    template_root = Path(__file__).resolve().parent / "assets" / "templates"
    texture_root = Path(__file__).resolve().parent / "assets" / "textures"

    # STEP 1 - SET UP FILE OBJECTS AND COPY FILES WE DONT NEED TO MODIFY
    # Create all the file objects we need for the level
    cfg_data = CfgFile(template_root / f"{map_size_template}.cfg")
    lev_data = LevFile(template_root / f"{map_size_template}.lev")
    ars_data = ArsFile(template_root / "common.ars")
    ob3_data = Ob3File("")  # no template ob3 required
    # S0U file is basic for now - we have merged everything into a single file
    os.makedirs(OUTPUT_PATH / NEW_LEVEL_NAME, exist_ok=True)
    shutil.copy(
        template_root / "common.s0u",
        OUTPUT_PATH / NEW_LEVEL_NAME / f"{NEW_LEVEL_NAME}.s0u",
    )
    # TODO .ait text file

    # STEP 6 - RANDOMLY UNLOCK VEHICLES/ADDONS/EJ
    construction_manager = ConstructionManager(ars_data, noise_generator)
    construction_manager.select_random_construction_availability()
    # select a random EJ between 3000 to 8000 in blocks of 250
    cfg_data["LevelCash"] = noise_generator.randint(12, 32) * 250
    logging.info(f"Set EJ: {cfg_data['LevelCash']}")

    # STEP 2 - PREPARE TERRAIN AND SET TERRAIN TEXTURES
    # select a random texture group from the texture directory, copy it to the
    # ... new map location and load the texture info into the CFG (for minimap)
    select_map_texture_group(
        path_to_textures=texture_root,
        cfg=cfg_data,
        noise_gen=noise_generator,
        paste_textures_path=OUTPUT_PATH / NEW_LEVEL_NAME,
    )
    # create a terrain handler and set the terrain from noise
    terrain_handler = TerrainHandler(lev_data, noise_generator)
    terrain_handler.set_terrain_from_noise()

    # STEP 5 - CHOOSE THE MISSION TYPE
    # TODO - for now, we just have the "destroy_all" type
    mission_type = "destroy_all"
    ars_data.load_additional_data(template_root / f"{mission_type}.ars")

    # STEP xxx - CREATE AN OBJECT HANDLER
    # create an objecthandler
    object_handler = ObjectHandler(terrain_handler, ob3_data, noise_generator)
    # add carrier first as it needs to be object id 1 for common .ars logic
    carrier_mask = object_handler.add_carrier_and_return_mask()

    # STEP xxx - SELECT ZONES, COLOUR & FLATTEN TERRAIN
    num_zones = noise_generator.randint(4, 11)
    zone_manager = ZoneManager(object_handler, noise_generator)
    # add a small scrap zone near the carrier - so the player has some EJ
    object_handler.add_zone(
        ZoneType.BASE,
        ZoneSize.SMALL,
        ZoneSpecial.NONE,
    )
    object_handler.add_zone(
        ZoneType.SCRAP,
        ZoneSize.SMALL,
        ZoneSpecial.NONE,
        extra_masks=carrier_mask,
    )
    zone_manager.generate_random_zones(num_zones)
    for zone in object_handler.zones:
        terrain_handler.apply_texture_based_on_zone(zone)
        terrain_handler.flatten_terrain_based_on_zone(zone)
        object_handler.populate_zone(zone)

    # STEP XXX - POPULATE THE MAP WITH OTHER OBJECTS
    # object_handler.add_scenery(map_size=map_size_template)
    # for _ in range(50):
    #     obj = noise_generator.select_random_from_weighted_dict(ALL_BASE)
    #     object_handler.add_object_on_land_random(
    #         object_type=obj.object_type,
    #         team=Team.ENEMY,
    #         required_radius=obj.required_radius,
    #         attachment_type=obj.attachment_type,
    #         consider_zones=True,
    #     )
    # object_handler.add_object_on_land_random(
    #     "recharge_crate",
    #     team=Team.NEUTRAL,
    #     required_radius=1,
    # )

    # STEP 5 - GENERATE MINIMAP FROM FINAL MAP TEXTURES
    generate_minimap(
        terrain_handler, cfg_data, OUTPUT_PATH / NEW_LEVEL_NAME / "map.pcx"
    )
    # STEP 6 - RANDOMLY UNLOCK VEHICLES/ADDONS
    construction_manager = ConstructionManager(ars_data, noise_generator)
    construction_manager.select_random_construction_availability()

    # STEP 7 - FINALISE SCRIPT/TRIGGERS
    if True:  # TODO if a crate zone is present
        ars_data.load_additional_data(
            template_root / "zone_specific" / "weapon_crate.ars"
        )
        spare_weapon = construction_manager.find_weapon_not_in_ars_build()
        if spare_weapon is not None:
            ars_data.add_action_to_existing_record(
                record_name="HWAE_zone_specific weapon ready",
                action_title="AIScript_MakeAvailableForBuilding",
                action_details=[
                    "AIS_SPECIFICPLAYER : 0",
                    f"AIS_UNITTYPE_SPECIFIC : {spare_weapon}",
                ],
            )

    # STEP 7 - SAVE ALL FILES TO OUTPUT LOCATION
    for file in [lev_data, cfg_data, ob3_data, ars_data]:
        file.save(OUTPUT_PATH / NEW_LEVEL_NAME, NEW_LEVEL_NAME)


if __name__ == "__main__":
    # profiler = cProfile.Profile()
    # profiler.enable()

    main()

    # profiler.disable()
    # stats = pstats.Stats(profiler)
    # stats.sort_stats("cumulative")
    # stats.dump_stats("profile_output.prof")  # Can be viewed with snakeviz

    # TESTING - draw an assortment of random units (without clustering)

    # for _ in range(3):
    #     object_handler.add_object_on_land_random(
    #         "AlienTower",
    #         team=Team.ENEMY,
    #         required_radius=5,
    #         attachment_type="LightningGun",
    #     )
    # for _ in range(3):
    #     object_handler.add_object_on_land_random(
    #         "ALIENGROUNDPROD",
    #         team=Team.ENEMY,
    #         required_radius=15,
    #     )
    # for _ in range(6):
    #     object_handler.add_object_on_land_random(
    #         "ALIENPUMP",
    #         team=Team.ENEMY,
    #         required_radius=15,
    #     )
    # for _ in range(6):
    #     object_handler.add_object_on_land_random(
    #         "alienpowerstore",
    #         team=Team.ENEMY,
    #         required_radius=15,
    #     )
    # for _ in range(6):
    #     object_handler.add_object_on_land_random(
    #         "LightWalker",
    #         team=Team.ENEMY,
    #         required_radius=2,
    #     )

    # object_handler.add_object(
    #     "ALIENGROUNDPROD",
    #     location=[41, 15, 155],
    #     team=Team.PLAYER,
    # )
    # object_handler.add_object("dedicatedlifter", np.array([95, 15, 100]), team=0)
    # object_handler.add_object_on_ground(
    #     "ALIENGROUNDPROD", location_x=256 / 2, location_z=256 / 2, team=1
    # )
    # create minimap
