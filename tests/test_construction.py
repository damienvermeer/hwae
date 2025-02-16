"""
Tests for the Construction Manager
"""

import pytest
from src.construction import ConstructionManager, AVAILABLE_WEAPONS
from src.fileio.ars import ArsFile, _ARSRecord
from src.noisegen import NoiseGenerator
from pathlib import Path


def test_find_weapon_not_in_ars_build():
    """Test finding weapons not in build trigger"""
    # Create a noise generator with a fixed seed for reproducibility
    noise_gen = NoiseGenerator(seed=42)

    # Create an empty ARS file with BUILD_SETUP trigger
    ars_file = ArsFile("")
    build_trigger = _ARSRecord(
        name="BUILD_SETUP",
        conditions=["AIScript_ElapsedTime", "AIS_GREATEREQUAL : 0"],
        actions=[],
        player_id=0,
        player_type="AIS_SPECIFICPLAYER",
    )
    ars_file.objects.append(build_trigger)

    # Create construction manager
    construction_mgr = ConstructionManager(ars_file, noise_gen)

    # Test 1: When no weapons are in build trigger
    weapon = construction_mgr.find_weapon_not_in_ars_build()
    assert (
        weapon in AVAILABLE_WEAPONS
    ), "Should return a valid weapon when none are in trigger"

    # Test 2: Add one weapon to build trigger
    first_weapon = weapon
    ars_file.add_action_to_existing_record(
        record_name="BUILD_SETUP",
        action_title="AIScript_MakeAvailableForBuilding",
        action_details=[
            "AIS_SPECIFICPLAYER : 0",
            f"AIS_UNITTYPE_SPECIFIC : {first_weapon}",
        ],
    )

    # Should return a different weapon
    second_weapon = construction_mgr.find_weapon_not_in_ars_build()
    assert second_weapon in AVAILABLE_WEAPONS, "Should return a valid weapon"
    assert (
        second_weapon != first_weapon
    ), "Should return a different weapon than first one"

    # Test 3: Add all weapons except one to build trigger
    weapons_in_trigger = {first_weapon}  # Track what we've added
    for weapon in AVAILABLE_WEAPONS:
        if weapon not in weapons_in_trigger:
            ars_file.add_action_to_existing_record(
                record_name="BUILD_SETUP",
                action_title="AIScript_MakeAvailableForBuilding",
                action_details=[
                    "AIS_SPECIFICPLAYER : 0",
                    f"AIS_UNITTYPE_SPECIFIC : {weapon}",
                ],
            )
            weapons_in_trigger.add(weapon)
            if len(weapons_in_trigger) == len(AVAILABLE_WEAPONS) - 1:
                break

    # Should return the last remaining weapon
    last_weapon = construction_mgr.find_weapon_not_in_ars_build()
    assert last_weapon in AVAILABLE_WEAPONS, "Should return a valid weapon"
    assert (
        last_weapon not in weapons_in_trigger
    ), "Should return a weapon not yet in trigger"
    weapons_in_trigger.add(last_weapon)

    # Test 4: Add final weapon to build trigger
    ars_file.add_action_to_existing_record(
        record_name="BUILD_SETUP",
        action_title="AIScript_MakeAvailableForBuilding",
        action_details=[
            "AIS_SPECIFICPLAYER : 0",
            f"AIS_UNITTYPE_SPECIFIC : {last_weapon}",
        ],
    )

    # Should return None when all weapons are in trigger
    assert (
        construction_mgr.find_weapon_not_in_ars_build() is None
    ), "Should return None when all weapons are in trigger"
