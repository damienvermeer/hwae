"""
HWAE (Hostile Waters Antaeus Eternal)

zones.base_zone.py

Contains abstract base class for zones
"""

from logger import get_logger

logger = get_logger()

from fileio.ars import ArsFile
from fileio.ail import AilFile
from fileio.ait import AitFile
from construction import ConstructionManager

import numpy as np
from models import ZoneType, ZoneSubType
from zones.base_zone import Zone, ZoneObjectDetails
from object_containers import (
    DESTROYED_BASE_PRIORITY,
    SCRAP_DESTROYED_BASE,
    SCRAP_BATTLE,
    SCRAP_FUEL_TANKS,
    WEAPON_CRATE_SCRAP_PRIORITY,
    WEAPON_CRATE_SCRAP_OTHERS,
)
from pathlib import Path


class DestroyedBaseZone(Zone):
    """A zone with a destroyed base"""

    def __post_init__(self) -> None:
        super().__post_init__()
        self.zone_type = ZoneType.SCRAP
        self.zone_subtype = ZoneSubType.DESTROYED_BASE

    def _populate(self) -> ZoneObjectDetails:
        """Returns a ZoneObjectDetails object containing the objects to be placed in this zone."""
        # always get 1 burnt building
        new_details = ZoneObjectDetails(
            priority_1_objs=DESTROYED_BASE_PRIORITY,
            p1_num=1,
            other_objs=SCRAP_DESTROYED_BASE,
        )
        return new_details

    def _mask(self) -> np.ndarray:
        pass

    def _update_mission_logic(
        self,
        level_logic: ArsFile,
        location_data: AilFile,
        text_data: AitFile,
        template_root: Path,
        construction_manager: ConstructionManager,
    ) -> None:
        pass  # no special logic required for this zone


class OldTankBattleZone(Zone):
    """A zone with an old tank battle"""

    def __post_init__(self) -> None:
        super().__post_init__()
        self.zone_type = ZoneType.SCRAP
        self.zone_subtype = ZoneSubType.OLD_TANK_BATTLE

    def _populate(self) -> ZoneObjectDetails:
        # nothing special
        new_details = ZoneObjectDetails(
            other_objs=SCRAP_BATTLE,
        )
        return new_details

    def _mask(self) -> np.ndarray:
        pass

    def _update_mission_logic(
        self,
        level_logic: ArsFile,
        location_data: AilFile,
        text_data: AitFile,
        template_root: Path,
        construction_manager: ConstructionManager,
    ) -> None:
        pass  # no special logic required for this zone


class OilTankZone(Zone):
    """A zone with oil tanks"""

    def __post_init__(self) -> None:
        super().__post_init__()
        self.zone_type = ZoneType.SCRAP
        self.zone_subtype = ZoneSubType.FUEL_TANKS

    def _populate(self) -> ZoneObjectDetails:
        """Returns a ZoneObjectDetails object containing the objects to be placed in this zone."""
        # nothing special
        new_details = ZoneObjectDetails(
            other_objs=SCRAP_FUEL_TANKS,
        )
        return new_details

    def _mask(self) -> np.ndarray:
        pass

    def _update_mission_logic(
        self,
        level_logic: ArsFile,
        location_data: AilFile,
        text_data: AitFile,
        template_root: Path,
        construction_manager: ConstructionManager,
    ) -> None:
        pass  # no special logic required for this zone


class WeaponCrateZone(Zone):
    """A zone with weapon crates (which gives
    the player a weapon if they sample it)"""

    def __post_init__(self) -> None:
        super().__post_init__()
        self.zone_type = ZoneType.SCRAP
        self.zone_subtype = ZoneSubType.WEAPON_CRATE

    def _populate(self) -> ZoneObjectDetails:
        """Returns a ZoneObjectDetails object containing the objects to be placed in this zone."""
        # at least 3 weapon crates
        new_details = ZoneObjectDetails(
            priority_1_objs=WEAPON_CRATE_SCRAP_PRIORITY,
            p1_num=3,
            other_objs=WEAPON_CRATE_SCRAP_OTHERS,
        )
        return new_details

    def _mask(self) -> np.ndarray:
        pass

    def _update_mission_logic(
        self,
        level_logic: ArsFile,
        location_data: AilFile,
        text_data: AitFile,
        template_root: Path,
        construction_manager: ConstructionManager,
    ) -> None:
        """Update mission and location logic given the zone type and
        location

        Args:
            level_logic (ArsFile): ARS file to update
            location_data (AilFile): AIL file to update
        """
        logger.info("Setting up weapon crate zone")

        # first check we have a spare weapon - if we dont, we cant
        # ... do anything else
        spare_weapon = construction_manager.find_weapon_not_in_ars_build()
        if spare_weapon is None:
            logger.warning("No spare weapon found - cannot set up weapon crate zone")
            return

        # ARS logic
        level_logic.load_additional_data(
            template_root / "zone_specific" / "weapon_crate.ars"
        )
        level_logic.add_action_to_existing_record(
            record_name="HWAE_zone_specific weapon ready",
            action_title="AIScript_MakeAvailableForBuilding",
            action_details=[
                "AIS_SPECIFICPLAYER : 0",
                f"AIS_UNITTYPE_SPECIFIC : {spare_weapon}",
            ],
        )

        # TEXT LOGIC
        text_data.add_text_record(
            name="hwae_weapon_crate__sample_crate",
            content="[Optional] Sample the weapon crate",
        )
        text_data.add_text_record(
            name="hwae_weapon_crate__weapon_ready_in",
            content=f"New weapon ({spare_weapon}) ready in:",
        )

        # LOCATION LOGIC
        location_data.add_area_record(
            name="near_crate_zone",
            bounding_box=(self.z - 30, self.x - 30, self.z + 30, self.x + 30),
        )
