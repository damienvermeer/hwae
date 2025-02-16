from dataclasses import dataclass
from enum import IntEnum, auto


class Team(IntEnum):
    """Team enumeration for objects"""

    PLAYER = 0
    ENEMY = 1
    NEUTRAL = 2


class ZoneType(IntEnum):
    """Type of zone"""

    BASE = auto()
    SCRAP = auto()


class ZoneSize(IntEnum):
    """Size of zone"""

    SMALL = auto()
    MEDIUM = auto()
    LARGE = auto()
    XLARGE = auto()


class ZoneSpecial(IntEnum):
    NONE = auto()
    WEAPON_CRATE = auto()


ZONE_SIZE_TO_RADIUS = {
    ZoneSize.SMALL: 8,
    ZoneSize.MEDIUM: 11,
    ZoneSize.LARGE: 16,
    ZoneSize.XLARGE: 19,
}

ZONE_TYPE_TO_TEXTURE_ID = {
    ZoneType.BASE: 8,
    ZoneType.SCRAP: 10,
}

ZONE_SIZE_TO_NUM_OBJECTS = {
    ZoneSize.SMALL: 7,
    ZoneSize.MEDIUM: 11,
    ZoneSize.LARGE: 14,
    ZoneSize.XLARGE: 19,
}


@dataclass
class ZoneMarker:
    """Marker for a zone in the map"""

    x: float
    z: float
    zone_type: ZoneType
    zone_size: ZoneSize
    zone_special: ZoneSpecial

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
