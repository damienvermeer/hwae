"""
HWAE (Hostile Waters Antaeus Eternal)

zones.base_zone.py

Contains abstract base class for zones
"""

from dataclasses import dataclass, field
import numpy as np
from logger import get_logger
from typing import Union

logger = get_logger()

from noisegen import NoiseGenerator
from models import (
    ZoneSubType,
    ZoneSize,
    ZoneType,
    ObjectContainer,
    ZONE_SIZE_TO_RADIUS,
    ZONE_SIZE_TO_NUM_OBJECTS,
    ZONE_TYPE_TO_TEXTURE_ID,
)
from abc import ABC, abstractmethod


@dataclass
class ZoneObjectDetails:
    """Small container class for zone object details

    Args:
        other_objs (dict[ObjectContainer, int]): Other objects to be placed in the zone
        priority_1_objs (dict[ObjectContainer, int]): Priority 1 objects to be placed in the zone (optional)
        p1_num (int): Number of priority 1 objects to be placed in the zone (optional)
        priority_2_objs (dict[ObjectContainer, int]): Priority 2 objects to be placed in the zone (optional)
        p2_num (int): Number of priority 2 objects to be placed in the zone (optional)
    """

    other_objs: dict[ObjectContainer, int]
    priority_1_objs: dict[ObjectContainer, int] = field(default_factory=dict)
    p1_num: int = 0
    priority_2_objs: dict[ObjectContainer, int] = field(default_factory=dict)
    p2_num: int = 0


@dataclass
class Zone(ABC):
    """Revised zone definition, which contains methods to
    populate zones and add ARS logic
    """

    x: float
    z: float
    zone_size: ZoneSize
    zone_index: Union[int, None] = None  # used for enemy team grouping

    def __post_init__(self) -> None:
        """Below are overriden by child classes"""
        self.zone_type: ZoneType = None
        self.zone_subtype: ZoneSubType = None

    def __repr__(self) -> str:
        return f"Zone(zone_type={self.zone_type}, zone_size={self.zone_size}, zone_subtype={self.zone_subtype}, zone_index={self.zone_index}, x={self.x}, z={self.z})"

    @property
    def radius(self) -> float:
        """Returns the radius of the zone based on its size

        Returns:
            float: Radius in map units
        """
        return ZONE_SIZE_TO_RADIUS[self.zone_size]

    @property
    def radius(self) -> float:
        """
        Returns the radius of the zone based on its size

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

    def mask(self) -> np.ndarray:
        return self._mask()

    def update_mission_logic(self, ars_data: "ArsFile") -> None:
        """Updates the

        Args:
            ars_data (ArsFile): _description_

        Returns:
            _type_: _description_
        """
        return self._update_mission_logic(ars_data=ars_data)

    @property
    def max_objects(self) -> int:
        return ZONE_SIZE_TO_NUM_OBJECTS[self.zone_size]

    def populate(
        self, noise_generator: NoiseGenerator, object_handler: "ObjectHandler"
    ) -> None:
        """Populates this zone with objects based on the zone type and size.

        Args:
            noise_generator (NoiseGenerator): Noise generator to use for populating the zone
            object_handler (ObjectHandler): Object handler to use for populating the zone
        """
        logger.info("Populating zone: " + str(self))
        # call the zone's populate function to get a list of iems
        zone_object_details = self._populate()

        # now generate lists from the priority objects
        p1_num = zone_object_details.p1_num
        p2_num = zone_object_details.p2_num
        priority_1_objs = [
            noise_generator.select_random_from_weighted_dict(
                zone_object_details.priority_1_objs
            )
            for _ in range(p1_num)
        ]
        priority_2_objs = [
            noise_generator.select_random_from_weighted_dict(
                zone_object_details.priority_2_objs
            )
            for _ in range(p2_num)
        ]
        all_base_objs = [
            noise_generator.select_random_from_weighted_dict(
                zone_object_details.other_objs
            )
            for _ in range(self.max_objects - p1_num - p2_num)
        ]

        # put them in the zone, after sorting descending by radius
        def _get_required_radius(
            obj: ObjectContainer | tuple[ObjectContainer, ...]
        ) -> int:
            if isinstance(obj, tuple):
                return obj[0].required_radius
            else:
                return obj.required_radius

        priority_1_objs.sort(key=lambda x: _get_required_radius(x), reverse=True)
        priority_2_objs.sort(key=lambda x: _get_required_radius(x), reverse=True)
        all_base_objs.sort(key=lambda x: _get_required_radius(x), reverse=True)

        # now start adding objects to the zone
        for obj in priority_1_objs + priority_2_objs + all_base_objs:
            # check if obj is a list (template) or a single object
            if isinstance(obj, tuple):
                object_handler.add_object_template_on_land_random(
                    obj, in_zone=self, team_override=self.zone_index
                )
            else:
                object_handler.add_object_on_land_random(
                    obj.object_type,
                    attachment_type=obj.attachment_type,
                    team=obj.team if self.zone_index is None else self.zone_index,
                    required_radius=obj.required_radius,
                    y_rotation=noise_generator.randint(0, 360),
                    y_offset=obj.y_offset,
                    in_zone=self,
                )
        logger.info("Finished populating zone")

    @abstractmethod
    def _populate(self) -> ZoneObjectDetails:

        pass

    @abstractmethod
    def _mask(self) -> np.ndarray:
        pass

    @abstractmethod
    def _update_mission_logic(self, ars_data: "ArsFile") -> None:
        pass
