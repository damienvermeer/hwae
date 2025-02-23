"""
HWAE (Hostile Waters Antaeus Eternal)

src.objects

Contains all info regarding objects for the level
"""

from dataclasses import dataclass
from enum import IntEnum, auto
import numpy as np
import logging

from src.fileio.ob3 import Ob3File, MAP_SCALER
from src.noisegen import NoiseGenerator
from src.objects import ObjectHandler
from src.models import ZoneMarker, ZoneSubType, ZoneSize, ZoneType, ZONE_SIZE_TO_RADIUS

ZONE_TYPE_WEIGHTS = {
    ZoneType.BASE: 1,
    ZoneType.SCRAP: 1,
}
ALLOWED_ZONE_SIZE_WEIGHTS = {
    ZoneType.BASE: {
        ZoneSubType.PUMP_OUTPOST: {
            ZoneSize.TINY: 3,
            ZoneSize.SMALL: 2,
        },
        ZoneSubType.GENERIC_BASE: {
            ZoneSize.SMALL: 3,
            ZoneSize.MEDIUM: 4,
            ZoneSize.LARGE: 2,
            ZoneSize.XLARGE: 1,
        },
    },
    ZoneType.SCRAP: {
        ZoneSubType.DESTROYED_BASE: {
            ZoneSize.TINY: 1,
            ZoneSize.SMALL: 3,
        },
        ZoneSubType.OLD_TANK_BATTLE: {ZoneSize.TINY: 1},
        ZoneSubType.WEAPON_CRATE: {ZoneSize.TINY: 1},
        ZoneSubType.FUEL_TANKS: {
            ZoneSize.TINY: 3,
            ZoneSize.SMALL: 1,
        },
    },
}
ALLOWED_ZONE_SUBTYPES = {
    ZoneType.BASE: [
        ZoneSubType.PUMP_OUTPOST,
        ZoneSubType.GENERIC_BASE,
    ],
    ZoneType.SCRAP: [
        ZoneSubType.DESTROYED_BASE,
        ZoneSubType.OLD_TANK_BATTLE,
        ZoneSubType.WEAPON_CRATE,
        ZoneSubType.FUEL_TANKS,
    ],
}
ZONE_SUBTYPE_WEIGHTS = {
    ZoneType.BASE: {
        ZoneSubType.PUMP_OUTPOST: 1,
        ZoneSubType.GENERIC_BASE: 1,
    },
    ZoneType.SCRAP: {
        ZoneSubType.DESTROYED_BASE: 1,
        ZoneSubType.OLD_TANK_BATTLE: 1,
        ZoneSubType.WEAPON_CRATE: 1,
        ZoneSubType.FUEL_TANKS: 1,
    },
}
ALLOWED_MAX_SUBTYPE_ZONES = {
    ZoneType.BASE: {
        ZoneSubType.PUMP_OUTPOST: 3,
        ZoneSubType.GENERIC_BASE: 999,
    },
    ZoneType.SCRAP: {
        ZoneSubType.DESTROYED_BASE: 999,
        ZoneSubType.OLD_TANK_BATTLE: 999,
        ZoneSubType.WEAPON_CRATE: 1,
        ZoneSubType.FUEL_TANKS: 999,
    },
}


@dataclass
class ZoneManager:
    object_handler: ObjectHandler
    noise_generator: NoiseGenerator
    # NOTE - zones themselves live in object manager
    special_zones_allocated = []

    def generate_random_zones(self, n_zones: int, zone_type: ZoneType) -> None:
        """Generates n_zones based on a random selection based on weighting defined above

        Args:
            n_zones (int): Number of zones to generate
        """
        _zones_to_place = []
        for _ in range(n_zones):
            # construct a dict of the possible special
            # ... zones and their weights from ZONE_SPECIAL_WEIGHTS
            possible_special_zones_dict = {
                zone_subtype: ZONE_SUBTYPE_WEIGHTS[zone_type][zone_subtype]
                for zone_subtype in ZONE_SUBTYPE_WEIGHTS[zone_type]
                if ALLOWED_MAX_SUBTYPE_ZONES[zone_type][zone_subtype] > 0
            }
            # select a random subtype from the masked list
            zone_subtype = self.noise_generator.select_random_from_weighted_dict(
                possible_special_zones_dict
            )
            # update the allowed max subtype zones to have 1 fewer
            ALLOWED_MAX_SUBTYPE_ZONES[zone_type][zone_subtype] -= 1
            # look up the weighting for the zone sizes and select one
            zone_size = self.noise_generator.select_random_from_weighted_dict(
                ALLOWED_ZONE_SIZE_WEIGHTS[zone_type][zone_subtype]
            )
            # add to allocated list
            self.special_zones_allocated.append(zone_subtype)
            _zones_to_place.append((zone_type, zone_size, zone_subtype))

        # sort zones via largest to smallest radius
        _zones_to_place.sort(key=lambda x: ZONE_SIZE_TO_RADIUS[x[1]], reverse=True)

        # finally add the zones
        for zone_to_add in _zones_to_place:
            self.object_handler.add_zone(*zone_to_add)

    def add_tiny_scrap_near_carrier_and_calc_rally(
        self, carrier_mask: np.ndarray
    ) -> None:
        """Adds a tiny scrap zone near the carrier, then uses this location to calculate a rally point for the carrier.

        Args:
            carrier_mask (np.ndarray): Mask of the carrier
        """
        logging.info("Adding tiny scrap zone near carrier")
        # pick a zone subtype at random from ALLOWED_ZONE_SUBTYPES[ZoneType.SCRAP]
        zone_subtype = self.noise_generator.select_random_from_weighted_dict(
            ZONE_SUBTYPE_WEIGHTS[ZoneType.SCRAP]
        )
        self.object_handler.add_zone(
            ZoneType.SCRAP,
            ZoneSize.TINY,
            zone_subtype,
            extra_masks=carrier_mask,
        )
        # create a custom mask within a radius of 6 of the new scrap zone
        nearby_scrap_mask = self.object_handler._update_mask_grid_with_radius(
            np.zeros_like(carrier_mask),
            radius=8,
            x=self.object_handler.zones[0].x,
            z=self.object_handler.zones[0].z,
            set_to=1,
        )
        # find a location
        x, z = self.object_handler._find_location(
            required_radius=1,
            consider_zones=True,
            extra_masks=nearby_scrap_mask,
        )
        return x, z

    def add_medium_base_somewhere(self) -> None:
        """Adds a medium base zone somewhere in line with all standard masks"""
        self.object_handler.add_zone(
            ZoneType.BASE,
            ZoneSize.MEDIUM,
            ZoneSubType.GENERIC_BASE,
        )
