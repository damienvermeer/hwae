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
from src.logger import setup_logger, close_logger
from config_loader import load_config, MapConfig
from src.constants import NEW_LEVEL_NAME


def generate_new_map(
    progress_callback: callable,
    complete_callback: callable,
    config_path: str,
    exe_parent: Path,
) -> None:
    """Generates a new game map with randomized elements for Hostile Waters: Antaeus Rising.

    This function handles the entire process of generating a new map, including setting up
    file objects, selecting textures, generating terrain, and populating the map with objects
    and zones. The map is saved to the specified output location.

    Args:
        progress_callback (callable): A callback function to update the progress of map generation.
        complete_callback (callable): A callback function to indicate that the generation is complete.
        config_path (str): The path to the configuration file.
        exe_parent (Path): The parent path where the output files will be saved.
    """

    # STEP 1 - INITALISATION -----------------------------------------------------------
    progress_callback("Starting...")

    # Set up the logger
    logger = setup_logger(exe_parent / NEW_LEVEL_NAME)

    # Load configuration
    map_config = load_config(config_path) if config_path else load_config()
    logger.info(f"Using configuration: {map_config}")

    # Initialize noise generator (seed will be set by config if specified)
    if map_config.seed == -1:
        noise_generator = NoiseGenerator()
        logger.info(f"Using random seed of {noise_generator.get_seed()}")
    else:
        logger.info(f"Using seed: {map_config.seed}")
        noise_generator = NoiseGenerator(seed=map_config.seed)

    # Use map size from config
    map_size_template = "large"  # CURRENTLY NO OTHER SUPPORTED
    template_root = Path(__file__).resolve().parent / "assets" / "templates"
    texture_root = Path(__file__).resolve().parent / "assets" / "textures"

    # STEP 2 - CLEAN EXISTING FILES ----------------------------------------------------
    progress_callback("Cleaning existing files")
    # check if the map folder exists - if so, remove all files in it
    if os.path.exists(exe_parent / NEW_LEVEL_NAME):
        shutil.rmtree(exe_parent / NEW_LEVEL_NAME, ignore_errors=True)

    # STEP 3 - SET UP COMMON FILES -----------------------------------------------------
    progress_callback("Importing common data")
    logger.info("Setting up file objects and copying template files")
    cfg_data = CfgFile(template_root / f"{map_size_template}.cfg")
    lev_data = LevFile(template_root / f"{map_size_template}.lev")
    ars_data = ArsFile(template_root / "common.ars")
    ait_data = AitFile(template_root / "common.ait")
    ob3_data = Ob3File("")
    pat_data = PatFile("")
    ail_data = AilFile("")
    os.makedirs(exe_parent / NEW_LEVEL_NAME, exist_ok=True)
    shutil.copy(
        template_root / "common.s0u",
        exe_parent / NEW_LEVEL_NAME / f"{NEW_LEVEL_NAME}.s0u",
    )
    shutil.copy(
        template_root / "common.for",
        exe_parent / NEW_LEVEL_NAME / f"{NEW_LEVEL_NAME}.for",
    )

    # STEP 3 - GENERATE PALETTE --------------------------------------------------------
    progress_callback("Generating palette")
    logger.info("Selecting map texture group")
    select_map_texture_group(
        path_to_textures=texture_root,
        cfg=cfg_data,
        noise_gen=noise_generator,
        paste_textures_path=exe_parent / NEW_LEVEL_NAME,
    )
    logger.info("Generating terrain from noise")
    terrain_handler = TerrainHandler(lev_data, noise_generator)
    terrain_handler.set_terrain_from_noise()

    # STEP 4 - HANDLE COMMON ARS -------------------------------------------------------
    progress_callback("Loading map logic")
    mission_type = "destroy_all"  # ONLY TYPE OF MISSION SUPPORTED FOR NOW
    logger.info(f"Setting mission type: {mission_type}")
    ars_data.load_additional_data(template_root / f"{mission_type}.ars")
    # set carrier shells
    carrier_shells = noise_generator.randint(1, 4)
    logger.info(f"Setting carrier shells: {carrier_shells}")
    ars_data.add_action_to_existing_record(
        record_name="HWAE set carrier shells",
        action_title="AIScript_SetCarrierShells",
        action_details=[str(carrier_shells)],
    )

    # STEP 5 - OBJECT INIT -------------------------------------------------------
    progress_callback("Object initalisation")
    logger.info("Creating object handler")
    object_handler = ObjectHandler(terrain_handler, ob3_data, noise_generator)
    logger.info("Adding carrier")
    carrier_mask = object_handler.add_carrier_and_return_mask()

    # STEP 6 - ZONE MANAGER -------------------------------------------------------
    progress_callback("Creating default zones")
    logger.info("Creating zone manager")
    zone_manager = ZoneManager(object_handler, noise_generator)

    logger.info("Adding scrap zone near carrier")
    xr, zr = zone_manager.add_tiny_scrap_near_carrier_and_calc_rally(carrier_mask)
    logger.info("Adding map revealer")
    object_handler.add_object_centered_on_zone("MapRevealer1", object_handler.zones[0])
    yr = terrain_handler.get_height(xr, zr)
    cfg_data["RallyPoint"] = f"{zr*10*51.7:.6f},{yr:.6f},{xr*10*51.7:.6f}"

    # STEP 7 - ZONE (ENEMY) -------------------------------------------------------
    progress_callback("Creating enemy base zones")
    logger.info("Generating enemy base zones")
    num_extra_enemy_bases = (
        map_config.num_extra_enemy_bases - 1
        # ^ take off 1 as we always get at least 1 base
        if map_config.num_extra_enemy_bases >= 0
        else noise_generator.randint(0, 4)
    )
    zone_manager.generate_random_zones(num_extra_enemy_bases, ZoneType.BASE)

    # STEP 8 - ZONE (SCRAP) -------------------------------------------------------
    progress_callback("Creating scrap zones")
    logger.info("Generating additional scrap zones")
    num_scrap_zones = (
        map_config.num_scrap_zones
        if map_config.num_scrap_zones >= 0
        else noise_generator.randint(1, 3)
    )
    zone_manager.generate_random_zones(num_scrap_zones, zone_type=ZoneType.SCRAP)

    # STEP 9 - ZONE POPULATE -------------------------------------------------------
    progress_callback("Processing zones (texturing, flattening, populating)")
    logger.info("Processing zones (texturing, flattening, populating)")
    for zone in object_handler.zones:
        terrain_handler.apply_texture_based_on_zone(zone)
        terrain_handler.flatten_terrain_based_on_zone(zone)
        object_handler.populate_zone(zone)

    # STEP 10 - MISC OBJECTS -------------------------------------------------------
    progress_callback("Adding other objects...")
    logger.info("Adding scenery")
    object_handler.add_scenery(map_size_template)
    logger.info("Adding alien miscellaneous objects")
    object_handler.add_alien_misc(carrier_xz=[xr, zr], map_size=map_size_template)
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
        if new_obj_id is None:
            continue
        ars_data.add_action_to_existing_record(
            record_name="HWAE patrol 1",
            action_title="AIScript_AssignRoute",
            action_details=['"patrol1"', f"{new_obj_id - 1}"],
        )

    # STEP 11 - MINIMAP -------------------------------------------------------
    progress_callback("Generating minimap")
    logger.info("Generating minimap")
    generate_minimap(terrain_handler, cfg_data, exe_parent / NEW_LEVEL_NAME / "map.pcx")

    # STEP 12 - CONSTRUCTION ----------------------------------------------------------
    # do this as late as possible - so if it changes, it doesnt change the level
    progress_callback("Selecting vehicles & addons")
    logger.info("Setting up construction availability")
    construction_manager = ConstructionManager(ars_data, noise_generator, map_config)
    construction_manager.select_random_construction_availability()

    # Set EJ if not already set by configuration
    if map_config.starting_ej == -1:
        cfg_data["LevelCash"] = noise_generator.randint(12, 32) * 250
        logger.info(f"Set random EJ: {cfg_data['LevelCash']}")

    # STEP 13 - FINALISE SCRIPT/TRIGGERS -------------------------------------------------------
    progress_callback("Finalizing scripts and triggers")
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

    # STEP 14 - SAVE -------------------------------------------------------
    progress_callback("Saving all files")
    logger.info("Saving all files to output location")
    for file in [lev_data, cfg_data, ob3_data, ars_data, pat_data, ail_data]:
        file.save(exe_parent / NEW_LEVEL_NAME, NEW_LEVEL_NAME)
    # save ait in special place
    ait_path = pathlib.Path(exe_parent / "Text" / "English")
    ait_path.mkdir(parents=True, exist_ok=True)
    ait_data.save(ait_path, NEW_LEVEL_NAME)
    logger.info("Cleaning up .aim files")
    for aim_file in (exe_parent / NEW_LEVEL_NAME).glob("*.aim"):
        os.remove(aim_file)

    logger.info("Map generation complete!")
    # save the json config used into the new level directory (but set the seed
    # ... to the seed we have used though)
    map_config.seed = noise_generator.get_seed()
    map_config.to_json(exe_parent / NEW_LEVEL_NAME / "HWAE_config.json")
    close_logger()
    progress_callback("Done")
    complete_callback()
