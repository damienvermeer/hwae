"""
HWAE (Hostile Waters Antaeus Eternal)

src.objects

Contains all info regarding objects for the level
"""

from dataclasses import dataclass
from enum import IntEnum, auto

from src.fileio.ob3 import Ob3File, MAP_SCALER
from src.noisegen import NoiseGenerator
from src.objects import ObjectHandler
from src.models import ZoneMarker, ZoneSpecial, ZoneSize, ZoneType

ZONE_TYPE_WEIGHTS = {
    ZoneType.BASE: 1,
    ZoneType.SCRAP: 1,
}
ZONE_SIZE_WEIGHTS = {
    ZoneSize.SMALL: 4,
    ZoneSize.MEDIUM: 3,
    ZoneSize.LARGE: 2,
    ZoneSize.XLARGE: 1,
}
ALLOWED_ZONE_SIZES = {
    ZoneType.BASE: [ZoneSize.SMALL, ZoneSize.MEDIUM, ZoneSize.LARGE, ZoneSize.XLARGE],
    ZoneType.SCRAP: [ZoneSize.SMALL, ZoneSize.MEDIUM],
}
ALLOWED_ZONE_SPECIALS = {
    ZoneType.BASE: [],  # no special bases yet
    ZoneType.SCRAP: [ZoneSpecial.WEAPON_CRATE],
}

ZONE_SPECIAL_WEIGHTS = {
    ZoneSpecial.NONE: 3,
    ZoneSpecial.WEAPON_CRATE: 1,
}


@dataclass
class ZoneManager:
    object_handler: ObjectHandler
    noise_generator: NoiseGenerator
    # NOTE - zones themselves live in object manager
    special_zones_allocated = []

    def generate_random_zones(self, n_zones: int) -> None:
        """Generates n_zones based on a random selection based on weighting defined above

        Args:
            n_zones (int): Number of zones to generate
        """
        for _ in range(n_zones):
            # select a random zone type and size
            zone_type = self.noise_generator.select_random_from_weighted_dict(
                ZONE_TYPE_WEIGHTS
            )
            # Then filter zone sizes to only those allowed for this type
            allowed_sizes = ALLOWED_ZONE_SIZES[zone_type]
            filtered_size_weights = {
                size: ZONE_SIZE_WEIGHTS[size] for size in allowed_sizes
            }
            zone_size = self.noise_generator.select_random_from_weighted_dict(
                filtered_size_weights
            )

            # check if we are allowed to have a special zone
            zone_special = ZoneSpecial.NONE
            if ALLOWED_ZONE_SPECIALS[zone_type] != []:
                # this can have a special zone - but remove those that already exist
                possible_special_zones = [
                    zone
                    for zone in ALLOWED_ZONE_SPECIALS[zone_type].copy()
                    if zone not in self.special_zones_allocated
                ]
                # if none left, continue
                if possible_special_zones == []:
                    continue
                # ELSE we could have a zone, construct a dict of the possible special
                # ... zones and their weights from ZONE_SPECIAL_WEIGHTS
                possible_special_zones_dict = {
                    zone: ZONE_SPECIAL_WEIGHTS[zone] for zone in possible_special_zones
                }
                # select a random special zone
                zone_special = self.noise_generator.select_random_from_weighted_dict(
                    possible_special_zones_dict
                )
                # add to allocated list
                self.special_zones_allocated.append(zone_special)

            # finally add the zone
            self.object_handler.add_zone(
                zone_type, zone_size, zone_special, extra_masks=None
            )
