"""
HWAE (Hostile Waters Antaeus Eternal)

construction.py

Contains all info to set the .ars file based on the selected construction options
"""

from src.noisegen import NoiseGenerator
from src.fileio.ars import ArsFile
from dataclasses import dataclass
import logging
import os
import time
import copy


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

    def select_random_construction_availability(self) -> None:
        """Randomly selects available vehicles, buildings and items for construction
        including soulcatcher chips.

        To avoid making the levels impossible, scarab and pegasus are in every level.
        Recycler and soulcatcher are in every level, with at least 3 soul catcher chips.
        """
        # Step 1 - vehicles
        picked_sublist = self.noise_generator.select_random_sublist_from_list(
            AVAILABLE_VEHCILES, min_n=2
        )
        for vehicle in picked_sublist:
            # add an action to the existing "BUILD_SETUP" record
            self.ars_file.add_action_to_existing_record(
                record_name="BUILD_SETUP",
                action_title="AIScript_MakeAvailableForBuilding",
                action_details=[
                    "AIS_SPECIFICPLAYER : 0",
                    f"AIS_UNITTYPE_SPECIFIC : {vehicle}",
                ],
            )
        logging.info(f"Added {len(picked_sublist)} vehicles")

        # Step 2 - soulcatchers (ensure at least 4)
        picked_soulcatchers = self.noise_generator.select_random_sublist_from_list(
            AVAILABLE_SOULCATCHERS, min_n=4
        )
        for soulcatcher in picked_soulcatchers:
            self.ars_file.add_action_to_existing_record(
                record_name="BUILD_SETUP",
                action_title="AIScript_MakeAvailableForBuilding",
                action_details=[
                    "AIS_SPECIFICPLAYER : 0",
                    f"AIS_UNITTYPE_SPECIFIC : {soulcatcher}",
                ],
            )
        logging.info(f"Added {len(picked_soulcatchers)} soulcatchers")

        # Step 3 - weapons (ensure at least 1 non-EMP weapon)
        non_emp_weapons = [w for w in AVAILABLE_WEAPONS if w != "EMP"]
        # First pick at least one non-EMP weapon
        picked_weapons = self.noise_generator.select_random_sublist_from_list(
            non_emp_weapons, min_n=1, max_n=1
        )
        # Then potentially add more weapons including EMP
        additional_weapons = self.noise_generator.select_random_sublist_from_list(
            AVAILABLE_WEAPONS, min_n=0
        )
        picked_weapons.extend(
            [w for w in additional_weapons if w not in picked_weapons]
        )
        for weapon in picked_weapons:
            self.ars_file.add_action_to_existing_record(
                record_name="BUILD_SETUP",
                action_title="AIScript_MakeAvailableForBuilding",
                action_details=[
                    "AIS_SPECIFICPLAYER : 0",
                    f"AIS_UNITTYPE_SPECIFIC : {weapon}",
                ],
            )
        logging.info(f"Added {len(picked_weapons)} weapons")

        # Step 4 - addons
        picked_addons = self.noise_generator.select_random_sublist_from_list(
            AVAILABLE_ADDONS, min_n=1
        )
        for addon in picked_addons:
            self.ars_file.add_action_to_existing_record(
                record_name="BUILD_SETUP",
                action_title="AIScript_MakeAvailableForBuilding",
                action_details=[
                    "AIS_SPECIFICPLAYER : 0",
                    f"AIS_UNITTYPE_SPECIFIC : {addon}",
                ],
            )
        logging.info(f"Added {len(picked_addons)} addons")

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
        logging.info(f"Remaining weapons to choose from: '{weapons_to_choose_from}'")
        if not weapons_to_choose_from:
            return None
        return self.noise_generator.select_random_from_list(weapons_to_choose_from)
