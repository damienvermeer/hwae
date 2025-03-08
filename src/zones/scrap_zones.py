"""
HWAE (Hostile Waters Antaeus Eternal)

zones.base_zone.py

Contains abstract base class for zones
"""

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

    def _update_mission_logic(self, ars_data: "ArsFile") -> None:
        pass


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

    def _update_mission_logic(self, ars_data: "ArsFile") -> None:
        pass


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

    def _update_mission_logic(self, ars_data: "ArsFile") -> None:
        pass


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

    def _update_mission_logic(self, ars_data: "ArsFile") -> None:
        pass
