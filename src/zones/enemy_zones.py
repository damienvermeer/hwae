"""
HWAE (Hostile Waters Antaeus Eternal)

zones.enemy_zones.py

Contains details on zones for enemy bases
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
    BASE_PRIORITY1,
    BASE_PRIORITY2,
    BASE_ALL_OTHER,
    PUMP_OUTPOST_ALL,
    PUMP_OUTPOST_PRIORITY,
)
from pathlib import Path


class GenericBaseZone(Zone):
    """A zone with an enemy base"""

    def __post_init__(self) -> None:
        super().__post_init__()
        self.zone_type = ZoneType.BASE
        self.zone_subtype = ZoneSubType.GENERIC_BASE

    def _populate(self) -> ZoneObjectDetails:
        """Returns a ZoneObjectDetails object containing the objects to be placed in this zone."""
        # always get 1 burnt building
        new_details = ZoneObjectDetails(
            priority_1_objs=BASE_PRIORITY1,
            # below scales based on zone size
            p1_num=self.zone_size.value,
            priority_2_objs=BASE_PRIORITY2,
            p2_num=2,
            other_objs=BASE_ALL_OTHER,
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


class PumpOutpostZone(Zone):
    """A zone with a pump outpost"""

    def __post_init__(self) -> None:
        super().__post_init__()
        self.zone_type = ZoneType.BASE
        self.zone_subtype = ZoneSubType.PUMP_OUTPOST

    def _populate(self) -> ZoneObjectDetails:
        # nothing special
        new_details = ZoneObjectDetails(
            priority_1_objs=PUMP_OUTPOST_PRIORITY,
            p1_num=4,
            other_objs=PUMP_OUTPOST_ALL,
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
