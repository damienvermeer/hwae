from dataclasses import dataclass
from enum import IntEnum, auto
from enums import Team
from typing import Union


class ZoneType(IntEnum):
    """Type of zone"""

    BASE = auto()
    SCRAP = auto()


class ZoneSubType(IntEnum):
    # SCRAP
    DESTROYED_BASE = auto()
    OLD_TANK_BATTLE = auto()
    FUEL_TANKS = auto()
    WEAPON_CRATE = auto()  # weapon crate special
    # ENEMY BASE like
    PUMP_OUTPOST = auto()
    GENERIC_BASE = auto()


class ZoneSize(IntEnum):
    """Size of zone"""

    # BELOW also used to scale some building inside zone

    TINY = 1
    SMALL = 2
    MEDIUM = 3
    LARGE = 4
    XLARGE = 6


ZONE_SIZE_TO_RADIUS = {
    ZoneSize.TINY: 5,
    ZoneSize.SMALL: 8,
    ZoneSize.MEDIUM: 11,
    ZoneSize.LARGE: 16,
    ZoneSize.XLARGE: 19,
}

ZONE_TYPE_TO_TEXTURE_ID = {
    ZoneType.BASE: 8,
    ZoneType.SCRAP: 11,
}

ZONE_SIZE_TO_NUM_OBJECTS = {
    ZoneSize.TINY: 15,
    ZoneSize.SMALL: 15,
    ZoneSize.MEDIUM: 15,
    ZoneSize.LARGE: 15,
    ZoneSize.XLARGE: 15,
}


@dataclass
class ZoneMarker:
    """Marker for a zone in the map"""

    x: float
    z: float
    zone_type: ZoneType
    zone_size: ZoneSize
    zone_subtype: ZoneSubType
    zone_index: Union[int, None] = None  # used for enemy team grouping

    @property
    def radius(self) -> float:
        """Returns the radius of the zone based on its size

        Returns:
            float: Radius in map units
        """
        return ZONE_SIZE_TO_RADIUS[self.zone_size]

    @property
    def texture_id(self) -> str:
        """Returns the texture ID to use for this zone type

        Returns:
            str: Texture ID from the texture description file
        """
        return ZONE_TYPE_TO_TEXTURE_ID[self.zone_type]


@dataclass(frozen=True)
class ObjectContainer:
    """Container for object data used in zone population"""

    object_type: str
    team: Team
    required_radius: float
    y_offset: float = 0
    y_rotation: float = 0
    attachment_type: str = ""
    template_x_offset: float = 0
    template_z_offset: float = 0
    template_y_offset: float = 0
