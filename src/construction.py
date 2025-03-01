"""
HWAE (Hostile Waters Antaeus Eternal)

construction.py

Contains all info to set the .ars file based on the selected construction options
"""

from src.noisegen import NoiseGenerator
from src.fileio.ars import ArsFile
from dataclasses import dataclass
from src.logger import get_logger

logger = get_logger()
import os
import time
import copy
from src.config_loader import MapConfig


AVAILABLE_VEHCILES = [
    "chopper",
    # ALWAYS IN "Harvester",
    # ALWAYS IN "Lifter",
    "HeavyTank",
    "Supertank",
    "Superchopper",
    "Hovertank",
    "Reconbuggy",
    "Staticplatform",
    "Bomber",
    "Superhover",
]
AVAILABLE_SOULCATCHERS = [
    # always picks at least 4
    "Ransom",
    "Borden",
    "Madsen",
    "Sinclair",
    "Kroker",
    "Patton",
    "Korolev",
    "Elroy",
    "Kenzie",
    "Lazare",
]

AVAILABLE_WEAPONS = [
    "Minigun",
    "Missile",
    "Flamer",
    "Lobber",
    "EMP",
    "Laser",
    # ALWAYS IN "carrierguns",
]
AVAILABLE_ADDONS = [
    # ALWAYS IN "soulunit",
    # ALWAYS IN "scavunit",
    "armour",
    "Cooler",
    "Shield",
    "Cloak",
    "Repair",
]


@dataclass
class ConstructionManager:
    ars_file: ArsFile
    noise_generator: NoiseGenerator
    map_config: MapConfig

    def _select_random_vehicles(self) -> None:
        picked_sublist = self.noise_generator.select_random_sublist_from_list(
            AVAILABLE_VEHCILES, min_n=2
        )
        for extra_vehicle in self.map_config.vehicle_include_list:
            logger.info(f"Adding extra vehicle: {extra_vehicle} as requested by config")
            if (
                extra_vehicle in picked_sublist
                or extra_vehicle not in AVAILABLE_VEHCILES
            ):
                logger.info(f"Vehicle {extra_vehicle} skipped")
                continue
            picked_sublist.append(extra_vehicle)
        for vehicle in picked_sublist:
            self.ars_file.add_action_to_existing_record(
                record_name="BUILD_SETUP",
                action_title="AIScript_MakeAvailableForBuilding",
                action_details=[
                    "AIS_SPECIFICPLAYER : 0",
                    f"AIS_UNITTYPE_SPECIFIC : {vehicle}",
                ],
            )
        logger.info(f"Added {len(picked_sublist)} vehicles")

    def _select_random_soulcatchers(self) -> None:
        picked_soulcatchers = self.noise_generator.select_random_sublist_from_list(
            AVAILABLE_SOULCATCHERS, min_n=6
        )
        for extra_soulcatcher in self.map_config.soulcatcher_include_list:
            logger.info(
                f"Adding extra soulcatcher: {extra_soulcatcher} as requested by config"
            )
            if (
                extra_soulcatcher in picked_soulcatchers
                or extra_soulcatcher not in AVAILABLE_SOULCATCHERS
            ):
                logger.info(f"Soulcatcher {extra_soulcatcher} skipped")
                continue
            picked_soulcatchers.append(extra_soulcatcher)
        for soulcatcher in picked_soulcatchers:
            self.ars_file.add_action_to_existing_record(
                record_name="BUILD_SETUP",
                action_title="AIScript_MakeAvailableForBuilding",
                action_details=[
                    "AIS_SPECIFICPLAYER : 0",
                    f"AIS_UNITTYPE_SPECIFIC : {soulcatcher}",
                ],
            )
        logger.info(f"Added {len(picked_soulcatchers)} soulcatchers")

    def _select_random_weapons(self) -> None:
        picked_weapons = self.noise_generator.select_random_sublist_from_list(
            [
                "Minigun",
                "Missile",
            ]
        )
        non_emp_weapons = [w for w in AVAILABLE_WEAPONS if w != "EMP"]
        # First pick at least one non-EMP weapon
        picked_weapons.extend(
            self.noise_generator.select_random_sublist_from_list(
                non_emp_weapons, min_n=1, max_n=1
            )
        )
        # Then potentially add more weapons including EMP (at least 1 more)
        additional_weapons = self.noise_generator.select_random_sublist_from_list(
            AVAILABLE_WEAPONS, min_n=0
        )
        picked_weapons.extend(
            [w for w in additional_weapons if w not in picked_weapons]
        )
        for extra_weapon in self.map_config.weapon_include_list:
            logger.info(f"Adding extra weapon: {extra_weapon} as requested by config")
            if extra_weapon in picked_weapons or extra_weapon not in AVAILABLE_WEAPONS:
                logger.info(f"Weapon {extra_weapon} skipped")
                continue
            picked_weapons.append(extra_weapon)
        logger.info(f"Added {len(picked_weapons)} total weapons")
        for weapon in picked_weapons:
            self.ars_file.add_action_to_existing_record(
                record_name="BUILD_SETUP",
                action_title="AIScript_MakeAvailableForBuilding",
                action_details=[
                    "AIS_SPECIFICPLAYER : 0",
                    f"AIS_UNITTYPE_SPECIFIC : {weapon}",
                ],
            )

    def _select_random_addons(self) -> None:
        picked_addons = self.noise_generator.select_random_sublist_from_list(
            AVAILABLE_ADDONS, min_n=1
        )
        for extra_addon in self.map_config.addon_include_list:
            logger.info(f"Adding extra addon: {extra_addon} as requested by config")
            if extra_addon in picked_addons or extra_addon not in AVAILABLE_ADDONS:
                logger.info(f"Addon {extra_addon} skipped")
                continue
            picked_addons.append(extra_addon)
        for addon in picked_addons:
            self.ars_file.add_action_to_existing_record(
                record_name="BUILD_SETUP",
                action_title="AIScript_MakeAvailableForBuilding",
                action_details=[
                    "AIS_SPECIFICPLAYER : 0",
                    f"AIS_UNITTYPE_SPECIFIC : {addon}",
                ],
            )
        logger.info(f"Added {len(picked_addons)} addons")

    def select_random_construction_availability(self) -> None:
        """Randomly selects available vehicles, buildings and items for construction
        including soulcatcher chips.

        To avoid making the levels impossible, scarab and pegasus are in every level.
        Recycler and soulcatcher are in every level, with at least 3 soul catcher chips.
        """
        self._select_random_vehicles()
        self._select_random_soulcatchers()
        self._select_random_weapons()
        self._select_random_addons()

    def find_weapon_not_in_ars_build(self) -> str:
        """Finds a weapon not in the ARS build order trigger. If all weapons are
        in the trigger, returns None.

        Returns:
            str: Name of the weapon not in the trigger, or None if all weapons are
            in the trigger
        """
        # get existing weapons in the BUILD_SETUP trigger
        trigger_info = self.ars_file.get_actions_from_existing_record("BUILD_SETUP")
        # iterate through the trigger info, constructing a list of existing weapon
        # ... types
        weapons_to_choose_from = copy.deepcopy(AVAILABLE_WEAPONS)
        for action_type, action_details in trigger_info:
            if action_type == "AIScript_MakeAvailableForBuilding":
                # Extract unit type from the second detail (AIS_UNITTYPE_SPECIFIC : UnitName)
                unit_type = action_details[1].split(" : ")[1]
                if unit_type in weapons_to_choose_from:
                    weapons_to_choose_from.remove(unit_type)
        logger.info(f"Remaining weapons to choose from: '{weapons_to_choose_from}'")
        if not weapons_to_choose_from:
            return None
        return self.noise_generator.select_random_from_list(weapons_to_choose_from)
