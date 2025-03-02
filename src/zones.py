"""
HWAE (Hostile Waters Antaeus Eternal)

src.objects

Contains all info regarding objects for the level
"""

from dataclasses import dataclass
import numpy as np
from logger import get_logger
from typing import Union

logger = get_logger()

from noisegen import NoiseGenerator
from objects import ObjectHandler
from models import ZoneSubType, ZoneSize, ZoneType, ZONE_SIZE_TO_RADIUS

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
        ZoneSubType.GENERIC_BASE: 999,
    },
    ZoneType.SCRAP: {
        ZoneSubType.DESTROYED_BASE: 999,
        ZoneSubType.OLD_TANK_BATTLE: 999,
        ZoneSubType.WEAPON_CRATE: 1,
        ZoneSubType.FUEL_TANKS: 999,
    },
}
PUMP_ZONES_PER_BASE_ZONE = {
    ZoneSize.TINY: [ZoneSize.TINY],
    ZoneSize.SMALL: [ZoneSize.TINY],
    ZoneSize.MEDIUM: [ZoneSize.SMALL],
    ZoneSize.LARGE: [ZoneSize.SMALL, ZoneSize.TINY],
    ZoneSize.XLARGE: [ZoneSize.SMALL, ZoneSize.SMALL],
}


@dataclass
class ZoneManager:
    object_handler: ObjectHandler
    noise_generator: NoiseGenerator
    # NOTE - zones themselves live in object manager
    special_zones_allocated = []
    last_used_index = 1

    def generate_random_zones(
        self, n_zones: int, zone_type: ZoneType, zone_size: Union[None, ZoneSize] = None
    ) -> None:
        """Generates n_zones based on a random selection based on weighting defined above

        Args:
            n_zones (int): Number of zones to generate
            zone_type (ZoneType): Type of zone to generate
            zone_size (Union[None, ZoneSize], optional): Size of zone to generate. Defaults to None.
        """
        _zones_to_place = []
        for _ in range(n_zones):
            if zone_type == ZoneType.BASE:
                self.last_used_index += 1
                use_this_index = self.last_used_index
            else:
                use_this_index = None
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
            if zone_size is None:
                zone_size = self.noise_generator.select_random_from_weighted_dict(
                    ALLOWED_ZONE_SIZE_WEIGHTS[zone_type][zone_subtype]
                )
            else:
                zone_size = zone_size

            # add to allocated list
            self.special_zones_allocated.append(zone_subtype)
            # index needs to start at 1, else we can put enemy base on player team
            _zones_to_place.append((zone_type, zone_size, zone_subtype, use_this_index))
            # if zone type is BASE - then also add a number of linked pump zones
            # ... based on the size
            if zone_type == ZoneType.BASE:
                for pumpzone_size in PUMP_ZONES_PER_BASE_ZONE[zone_size]:
                    _zones_to_place.append(
                        (
                            zone_type,
                            pumpzone_size,
                            ZoneSubType.PUMP_OUTPOST,
                            use_this_index,
                        )
                    )

        # sort zones via largest to smallest radius
        _zones_to_place.sort(key=lambda x: ZONE_SIZE_TO_RADIUS[x[1]], reverse=True)
        # add the non pump outpost zones
        for zone_to_add in [
            x for x in _zones_to_place if x[2] != ZoneSubType.PUMP_OUTPOST
        ]:
            zone = self.object_handler.add_zone(*zone_to_add)
            if zone is None:
                logger.warning(f"Failed to add zone {zone_to_add}")

        # now they've been added, add the linked pump zones
        for zone_to_add in [
            x for x in _zones_to_place if x[2] == ZoneSubType.PUMP_OUTPOST
        ]:
            # find the base zone with the same index
            base_zones = [
                x for x in self.object_handler.zones if x.zone_index == zone_to_add[3]
            ]
            if not base_zones:
                logger.warning(f"No base zone found with index {zone_to_add[3]}")
                continue

            base_zone = base_zones[0]
            # and add a pump zone within a radius of the base zone
            zone = self.object_handler.add_zone(
                *zone_to_add,
                extra_masks=self.object_handler.get_inclusion_mask_at_location(
                    base_zone.x, base_zone.z, 40
                )
                * self.object_handler._get_all_zone_mask([base_zone]),
                extra_zone_spacing=20,  # try reduced spacing
            )
            if zone is None:
                logger.warning(
                    f"Failed to add pump zone {zone_to_add} near base zone {base_zone}"
                )

    def add_tiny_scrap_near_carrier_and_calc_rally(
        self, carrier_mask: np.ndarray
    ) -> None:
        """Adds a tiny scrap zone near the carrier, then uses this location to calculate a rally point for the carrier.

        Args:
            carrier_mask (np.ndarray): Mask of the carrier
        """
        logger.info("Adding tiny scrap zone near carrier")
        # pick a zone subtype at random from ALLOWED_ZONE_SUBTYPES[ZoneType.SCRAP]
        zone_subtype = self.noise_generator.select_random_from_weighted_dict(
            ZONE_SUBTYPE_WEIGHTS[ZoneType.SCRAP]
        )
        # update the allowed max subtype zones to have 1 fewer
        ALLOWED_MAX_SUBTYPE_ZONES[ZoneType.SCRAP][zone_subtype] -= 1
        zone = self.object_handler.add_zone(
            ZoneType.SCRAP,
            ZoneSize.TINY,
            zone_subtype,
            extra_masks=carrier_mask,
        )

        if zone is None:
            logger.warning("Failed to add tiny scrap zone near carrier")
            return

        # create a custom mask within a radius of 15 of the new scrap zone
        nearby_scrap_mask = self.object_handler._update_mask_grid_with_radius(
            np.zeros_like(carrier_mask),
            radius=15,
            x=self.object_handler.zones[0].x,
            z=self.object_handler.zones[0].z,
            set_to=1,
        )
        # find a location
        x, z = self.object_handler._find_location(
            required_radius=4,
            consider_zones=True,
            extra_masks=nearby_scrap_mask,
        )
        return x, z
