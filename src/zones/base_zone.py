"""
HWAE (Hostile Waters Antaeus Eternal)

zones.base_zone.py

Contains abstract base class for zones
"""

from dataclasses import dataclass, field
import numpy as np
from logger import get_logger

logger = get_logger()
from typing import Union, TYPE_CHECKING

from fileio.ars import ArsFile
from fileio.ail import AilFile
from fileio.ait import AitFile
from construction import ConstructionManager
from pathlib import Path
from PIL import Image

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
    terrain_max_width: int
    terrain_max_length: int
    zone_size: ZoneSize
    zonegen_root: Path
    terrain_max_width: int
    terrain_max_length: int
    noise_generator: NoiseGenerator
    zone_index: Union[int, None] = None  # used for enemy team grouping

    def __post_init__(self) -> None:
        """Below are overriden by child classes"""
        self.zone_type: ZoneType = None
        self.zone_subtype: ZoneSubType = None
        self.zone_subtype: ZoneSubType = None
        self._mask: np.ndarray | None = None

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
        """Returns (and if not created, generates) a permissive mask for this zone.

        Returns:
            np.ndarray: A permissive mask for this zone
        """
        if self._mask is not None:
            return self._mask
        # else we need to calculate it
        # start with a full 0 mask of the terrain
        self._mask = np.zeros(
            (
                self.terrain_max_width,
                self.terrain_max_length,
            )
        )
        # call the child class's method to get a list of acceptable mask files
        mask_files = self._get_acceptable_mask_files(self.zonegen_root)
        # pick one at random
        mask_file = self.noise_generator.select_random_from_list(mask_files)
        # load the mask file and rescale based on zone size
        logger.info(f"Selected zone mask template: {mask_file}")

        with Image.open(mask_file) as fimg:
            # rotate by a random angle
            angle = self.noise_generator.randint(0, 360)
            logger.info(f"Rotating template by {angle} degrees")
            img = fimg.rotate(angle, Image.NEAREST, expand=True)
            # normalize to [0,1] and then clip anything greater than 0.1 to 1
            img = img.convert("L")
            img_array = np.array(img) / 255
            img_array = np.where(img_array > 0.1, 1, 0)

            # resize to match zone dimensions (which for now is radius)
            radius = ZONE_SIZE_TO_RADIUS[self.zone_size] + 2  # TESTING slight extra
            mask_size = radius * 2  # diameter

            # Convert to binary image before resizing to maintain binary values
            binary_img = Image.fromarray((img_array * 255).astype(np.uint8))
            resized_img = binary_img.resize((mask_size, mask_size))
            img_resized = np.array(resized_img) / 255

            # Ensure binary values after resize (threshold again)
            img_resized = np.where(img_resized > 0.1, 1, 0)

            # Calculate the position to place the mask in the terrain grid
            # Convert x,z coordinates to grid indices
            center_x, center_z = int(self.x), int(self.z)

            # Calculate the bounds for placing the mask
            x_start = max(0, center_x - mask_size // 2)
            z_start = max(0, center_z - mask_size // 2)
            x_end = min(self.terrain_max_width, center_x + mask_size // 2)
            z_end = min(self.terrain_max_length, center_z + mask_size // 2)

            # Calculate the corresponding region in the mask image
            mask_x_start = max(0, -(center_x - mask_size // 2))
            mask_z_start = max(0, -(center_z - mask_size // 2))
            mask_x_end = mask_x_start + (x_end - x_start)
            mask_z_end = mask_z_start + (z_end - z_start)

            # Place the mask in the terrain grid
            if (
                x_end > x_start
                and z_end > z_start
                and mask_x_end > mask_x_start
                and mask_z_end > mask_z_start
            ):
                mask_section = img_resized[
                    mask_x_start:mask_x_end, mask_z_start:mask_z_end
                ]
                self._mask[x_start:x_end, z_start:z_end] = mask_section

                # Final check to ensure binary values
                self._mask = np.where(self._mask > 0.1, 1, 0)

            logger.info(
                f"Placed zone mask at position ({center_x}, {center_z}) with radius {radius}"
            )

        return self._mask

    def update_mission_logic(
        self,
        level_logic: ArsFile,
        location_data: AilFile,
        text_data: AitFile,
        template_root: Path,
        construction_manager: ConstructionManager,
    ) -> None:
        """Updates the mission logic for this zone.

        Args:
            level_logic (ArsFile): ARS file to update
            location_data (AilFile): AIL file to update
            text_data (AitFile): AIT file to update
            template_root (Path): Root directory for template files
            construction_manager (ConstructionManager): Construction manager to use
        """
        return self._update_mission_logic(
            level_logic=level_logic,
            location_data=location_data,
            text_data=text_data,
            template_root=template_root,
            construction_manager=construction_manager,
        )

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
    def _get_acceptable_mask_files(self, zonegen_root: Path) -> list[Path]:
        pass

    @abstractmethod
    def _update_mission_logic(
        self,
        level_logic: ArsFile,
        location_data: AilFile,
        text_data: AitFile,
        template_root: Path,
        construction_manager: ConstructionManager,
    ) -> None:
        pass
