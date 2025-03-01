"""
HWAE (Hostile Waters Antaeus Eternal)

Python package (released as a pyinstaller exe) to generate additional maps for Hostile Waters: Antaeus Rising (2001)
"""

import pathlib
import shutil
from pathlib import Path
import os

from fileio.cfg import CfgFile
from fileio.lev import LevFile
from fileio.ob3 import Ob3File
from fileio.ars import ArsFile
from fileio.pat import PatFile
from fileio.ail import AilFile
from fileio.ait import AitFile
import src.object_templates as ot

from construction import ConstructionManager
from noisegen import NoiseGenerator
from objects import ObjectHandler
from enums import Team
from terrain import TerrainHandler
from texture import select_map_texture_group
from minimap import generate_minimap
from zones import ZoneManager, ZoneType, ZoneSize, ZoneSubType
from src.logger import setup_logger


def main():
    # TODO somehow specify the output location
    OUTPUT_PATH = Path(r"C:\HWAR\HWAR\modtest2")
    NEW_LEVEL_NAME = "Level53"
    
    # Set up the logger
    logger = setup_logger(OUTPUT_PATH / NEW_LEVEL_NAME)
    
    noise_generator = NoiseGenerator(seed=9977)
    # 9977 strange terrain textures
    # 435345 performance shit?

    # TODO select from alternative map sizes - only large (L22, 256*256) for now
    map_size_template = "large"
    template_root = Path(__file__).resolve().parent / "assets" / "templates"
    texture_root = Path(__file__).resolve().parent / "assets" / "textures"

    # STEP 1 - SET UP FILE OBJECTS AND COPY FILES WE DONT NEED TO MODIFY
    # Create all the file objects we need for the level
    logger.info("Setting up file objects and copying template files")
    cfg_data = CfgFile(template_root / f"{map_size_template}.cfg")
    lev_data = LevFile(template_root / f"{map_size_template}.lev")
    ars_data = ArsFile(template_root / "common.ars")
    ait_data = AitFile(template_root / "common.ait")
    ob3_data = Ob3File("")  # no template ob3 required
    pat_data = PatFile("")  # no template pat required
    ail_data = AilFile("")  # no template ail required
    # S0U file is basic for now - we have merged everything into a single file
    os.makedirs(OUTPUT_PATH / NEW_LEVEL_NAME, exist_ok=True)
    shutil.copy(
        template_root / "common.s0u",
        OUTPUT_PATH / NEW_LEVEL_NAME / f"{NEW_LEVEL_NAME}.s0u",
    )
    # and .for (force/teams file)
    shutil.copy(
        template_root / "common.for",
        OUTPUT_PATH / NEW_LEVEL_NAME / f"{NEW_LEVEL_NAME}.for",
    )
    # TODO .ait text file

    # STEP xxx - RANDOMLY UNLOCK VEHICLES/ADDONS/EJ
    logger.info("Selecting random construction availability")
    construction_manager = ConstructionManager(ars_data, noise_generator)
    construction_manager.select_random_construction_availability()
    # select a random EJ between 3000 to 8000 in blocks of 250
    cfg_data["LevelCash"] = noise_generator.randint(12, 32) * 250
    logger.info(f"Set EJ: {cfg_data['LevelCash']}")

    # STEP 2 - PREPARE TERRAIN AND SET TERRAIN TEXTURES
    # select a random texture group from the texture directory, copy it to the
    # ... new map location and load the texture info into the CFG (for minimap)
    logger.info("Selecting map texture group")
    select_map_texture_group(
        path_to_textures=texture_root,
        cfg=cfg_data,
        noise_gen=noise_generator,
        paste_textures_path=OUTPUT_PATH / NEW_LEVEL_NAME,
    )
    # create a terrain handler and set the terrain from noise
    logger.info("Generating terrain from noise")
    terrain_handler = TerrainHandler(lev_data, noise_generator)
    terrain_handler.set_terrain_from_noise()

    # STEP 5 - CHOOSE THE MISSION TYPE
    # TODO - for now, we just have the "destroy_all" type
    mission_type = "destroy_all"
    logger.info(f"Setting mission type: {mission_type}")
    ars_data.load_additional_data(template_root / f"{mission_type}.ars")

    # STEP xxx - CREATE AN OBJECT HANDLER
    # create an objecthandler
    logger.info("Creating object handler")
    object_handler = ObjectHandler(terrain_handler, ob3_data, noise_generator)
    # add carrier first as it needs to be object id 1 for common .ars logic
    logger.info("Adding carrier")
    carrier_mask = object_handler.add_carrier_and_return_mask()

    # STEP xxx - SELECT ZONES, COLOUR & FLATTEN TERRAIN
    logger.info("Creating zone manager")
    zone_manager = ZoneManager(object_handler, noise_generator)
    # add a small scrap zone near the carrier - so the player has some EJ
    logger.info("Adding scrap zone near carrier")
    xr, zr = zone_manager.add_tiny_scrap_near_carrier_and_calc_rally(carrier_mask)
    # put a map revealer location at the center of the first zone
    logger.info("Adding map revealer")
    object_handler.add_object_centered_on_zone("MapRevealer1", object_handler.zones[0])
    yr = terrain_handler.get_height(xr, zr)
    cfg_data["RallyPoint"] = f"{zr*10*51.7:.6f},{yr:.6f},{xr*10*51.7:.6f}"
    # ensure at least one enemy base - else we win straight away
    logger.info("Generating enemy base zone")
    zone_manager.generate_random_zones(1, ZoneType.BASE)
    # create extra zones and populate them all
    logger.info("Generating additional scrap zones")
    zone_manager.generate_random_zones(
        noise_generator.randint(1, 3), zone_type=ZoneType.SCRAP
    )
    # TEMP set rally point - TODO function & TODO find location
    # ... within radius of a x,z point
    x = object_handler.zones[0].x
    z = object_handler.zones[0].z
    y = terrain_handler.get_height(x, z)

    logger.info("Generating additional base zones")
    zone_manager.generate_random_zones(
        noise_generator.randint(0, 3), zone_type=ZoneType.BASE
    )
    
    logger.info("Processing zones (texturing, flattening, populating)")
    for zone in object_handler.zones:
        terrain_handler.apply_texture_based_on_zone(zone)
        terrain_handler.flatten_terrain_based_on_zone(zone)
        object_handler.populate_zone(zone)

    # STEP XXX - POPULATE THE MAP WITH OTHER OBJECTS
    # add a few random alien aa guns, radars etc
    logger.info("Adding alien miscellaneous objects")
    object_handler.add_alien_misc(carrier_xz=[xr, zr], map_size=map_size_template)
    # object_handler.add_scenery(map_size=map_size_template)
    # pick 3-7 random points within the map, then generate a convex hull
    logger.info("Creating patrol points")
    patrol_points = object_handler.create_patrol_points_hull(
        n_points=noise_generator.randint(3, 7)
    )
    pat_data.add_patrol_record("patrol1", patrol_points)
    
    logger.info("Adding flying units with patrol routes")
    for _ in range(noise_generator.randint(3, 7)):
        new_obj_id = object_handler.add_object_on_land_random(
            "MediumFlyer" if noise_generator.randint(0, 11) > 5 else "SmallFlyer",
            team=7,
            required_radius=1,
            y_offset=15,
        )
        ars_data.add_action_to_existing_record(
            record_name="HWAE patrol 1",
            action_title="AIScript_AssignRoute",
            action_details=['"patrol1"', f"{new_obj_id - 1}"],
        )

    # STEP 5 - GENERATE MINIMAP FROM FINAL MAP TEXTURES
    logger.info("Generating minimap")
    generate_minimap(
        terrain_handler, cfg_data, OUTPUT_PATH / NEW_LEVEL_NAME / "map.pcx"
    )

    # STEP 7 - FINALISE SCRIPT/TRIGGERS
    logger.info("Finalizing scripts and triggers")
    weapon_zone = [
        x for x in object_handler.zones if x.zone_subtype == ZoneSubType.WEAPON_CRATE
    ]
    if weapon_zone:  # TODO if a crate zone is present
        logger.info("Setting up weapon crate zone")
        weapon_zone = weapon_zone[0]
        ars_data.load_additional_data(
            template_root / "zone_specific" / "weapon_crate.ars"
        )
        # update ait so we dont get unlinked text
        ait_data.add_text_record(
            name="hwae_weapon_crate__sample_crate",
            content="Sample the weapon crate",
        )
        spare_weapon = construction_manager.find_weapon_not_in_ars_build()
        if spare_weapon is not None:
            logger.info(f"Adding spare weapon: {spare_weapon}")
            ars_data.add_action_to_existing_record(
                record_name="HWAE_zone_specific weapon ready",
                action_title="AIScript_MakeAvailableForBuilding",
                action_details=[
                    "AIS_SPECIFICPLAYER : 0",
                    f"AIS_UNITTYPE_SPECIFIC : {spare_weapon}",
                ],
            )
        # update the ail file - get the info from the crate zone
        zone_x, zone_z = weapon_zone.x, weapon_zone.z
        ail_data.add_area_record(
            name="near_crate_zone",
            bounding_box=(zone_z - 30, zone_x - 30, zone_z + 30, zone_x + 30),
        )
        # update ait so we dont get unlinked text
        ait_data.add_text_record(
            name="hwae_weapon_crate__weapon_ready_in",
            content=f"New weapon ({spare_weapon}) ready in:",
        )
    # set carrier shells
    carrier_shells = noise_generator.randint(1, 4)
    logger.info(f"Setting carrier shells: {carrier_shells}")
    ars_data.add_action_to_existing_record(
        record_name="HWAE set carrier shells",
        action_title="AIScript_SetCarrierShells",
        action_details=[str(carrier_shells)],
    )
    # STEP 7 - SAVE ALL FILES TO OUTPUT LOCATION
    logger.info("Saving all files to output location")
    for file in [lev_data, cfg_data, ob3_data, ars_data, pat_data, ail_data]:
        file.save(OUTPUT_PATH / NEW_LEVEL_NAME, NEW_LEVEL_NAME)
    # save ait in special place
    ait_path = pathlib.Path(OUTPUT_PATH / "Text" / "English")
    ait_path.mkdir(parents=True, exist_ok=True)
    ait_data.save(ait_path, NEW_LEVEL_NAME)

    # STEP xxx - delete any .aim file in the new level directory (force rebuild)
    logger.info("Cleaning up .aim files")
    for aim_file in (OUTPUT_PATH / NEW_LEVEL_NAME).glob("*.aim"):
        os.remove(aim_file)
    
    logger.info("Map generation complete!")


if __name__ == "__main__":
    # profiler = cProfile.Profile()
    # profiler.enable()

    main()

    # profiler.disable()
    # stats = pstats.Stats(profiler)
    # stats.sort_stats("cumulative")
    # stats.dump_stats("profile_output.prof")  # Can be viewed with snakeviz
