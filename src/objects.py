"""
HWAE (Hostile Waters Antaeus Eternal)

src.objects

Contains all info regarding objects for the level
"""

from logger import get_logger

logger = get_logger()

import math
from pickletools import TAKEN_FROM_ARGUMENT1
import random
from dataclasses import dataclass
from enum import IntEnum, auto
from pathlib import Path
from typing import Optional, Union

import numpy as np

from fileio.ob3 import Ob3File, MAP_SCALER
from noisegen import NoiseGenerator
from models import (
    Team,
    ZoneType,
    ZoneSize,
    ZoneMarker,
    ObjectContainer,
    ZoneSubType,
    ZONE_SIZE_TO_NUM_OBJECTS,
)
from terrain import TerrainHandler

# Import object containers after all other imports to prevent circular dependencies
from object_containers import (
    PUMP_OUTPOST_PRIORITY,
    PUMP_OUTPOST_ALL,
    BASE_PRIORITY1,
    BASE_PRIORITY2,
    BASE_ALL_OTHER,
    DESTROYED_BASE_PRIORITY,
    SCRAP_DESTROYED_BASE,
    SCRAP_BATTLE,
    SCRAP_FUEL_TANKS,
    WEAPON_CRATE_SCRAP_PRIORITY,
    WEAPON_CRATE_SCRAP_OTHERS,
    TEMPLATE_ALIEN_AA,
    TEMPLATE_ALIEN_RADAR,
)
from noisegen import NoiseGenerator


class LocationEnum(IntEnum):
    LAND = auto()
    WATER = auto()
    COAST = auto()


@dataclass
class ObjectHandler:
    terrain_handler: TerrainHandler
    ob3_interface: Ob3File
    noise_generator: NoiseGenerator

    def __post_init__(self):
        """Initialize the cached object mask"""
        self._cached_object_mask = np.ones(
            (
                self.terrain_handler.width,
                self.terrain_handler.length,
            )
        )
        self.zones = []

    def _update_mask_grid_with_radius(
        self, location_grid: np.ndarray, x: int, z: int, radius: int, set_to: int = 0
    ) -> None:
        """Updates the location grid to set_to in a radius around a location - used
        for object location masking or similar. Uses a simpler distance calculation
        since we only need integer radius.

        Args:
            location_grid (np.ndarray): Location grid to set 0 within
            x (int): x location
            z (int): z location
            radius (int): Radius to set within (must be integer)
            set_to (int): Value to set the location grid to
        """
        # Get bounds of the circle
        x_min = max(0, x - radius)
        x_max = min(self.terrain_handler.width, x + radius + 1)
        z_min = max(0, z - radius)
        z_max = min(self.terrain_handler.length, z + radius + 1)

        # For integer radius, we can just iterate through the square and check distance
        radius_sq = radius * radius  # Square once instead of sqrt
        for i in range(x_min, x_max):
            dx = i - x
            dx_sq = dx * dx
            for j in range(z_min, z_max):
                dz = j - z
                # If point is within radius, set it
                if dx_sq + dz * dz <= radius_sq:
                    location_grid[i, j] = set_to

        return location_grid

    def _update_cached_object_mask(self, x: int, z: int, required_radius: int) -> None:
        """Updates the cached object mask with a new object's radius

        Args:
            x (int): x location of new object
            z (int): z location of new object
            required_radius (int): radius to mark as occupied
        """
        self._cached_object_mask = self._update_mask_grid_with_radius(
            self._cached_object_mask, x, z, required_radius, set_to=0
        )

    def _get_binary_transition_mask(self, input_mask: np.ndarray) -> np.ndarray:
        """Generates a boolean edge transition mask, used for object radius checks
        as well as terrain transition checks (water-land etc). Iterates over the
        input mask, identifying the 2d cells where the state transitions to/from
        0. That cell is then marked as 1, all other cells are 0.

        Args:
            input_mask (np.ndarray): Input mask to check

        Returns:
            np.ndarray: Mask of edges from the input mask
        """
        # Create output mask of same shape as input
        transition_mask = np.zeros_like(input_mask, dtype=int)

        # Check horizontal transitions (left to right)
        horizontal_transitions = (input_mask[:, 1:] != input_mask[:, :-1]).astype(int)
        transition_mask[:, 1:] += horizontal_transitions
        transition_mask[:, :-1] += horizontal_transitions

        # Check vertical transitions (top to bottom)
        vertical_transitions = (input_mask[1:, :] != input_mask[:-1, :]).astype(int)
        transition_mask[1:, :] += vertical_transitions
        transition_mask[:-1, :] += vertical_transitions

        # Convert any non-zero values to 1
        transition_mask = (transition_mask > 0).astype(int)

        return transition_mask

    def _get_object_mask(self) -> np.ndarray:
        """Returns the cached object mask. The mask is maintained by _update_cached_object_mask
        which is called whenever a new object is added.

        Returns:
            np.ndarray: Object mask where 0 is occupied and 1 is free
        """
        return self._cached_object_mask

    def _get_zone_seperation_mask(self, extra_zone_spacing: int = 40) -> np.ndarray:
        """Returns a mask where 0 is free space and 1 is occupied space, used for
        zone separation (e.g. making sure there is reasonable space between zones)

        Returns:
            np.ndarray: Zone seperation mask
        """
        # start with all 1s (e.g. all area is permitted)
        zone_seperation_mask = np.ones(
            (
                self.terrain_handler.width,
                self.terrain_handler.length,
            )
        )
        # then check each zone (remove the zone from each)
        for zone in self.zones:
            zone_seperation_mask = self._update_mask_grid_with_radius(
                zone_seperation_mask, zone.x, zone.z, extra_zone_spacing, set_to=0
            )
        return zone_seperation_mask

    def _get_all_zone_mask(self, exclude_zones: list[ZoneMarker] = []) -> np.ndarray:
        """Returns the cached zone mask. The mask is not maintained by a cache and
        is calculated each time from scratch

        Args:
            exclude_zones (list[ZoneMarker], optional): Zones to exclude. Defaults to [].

        Returns:
            np.ndarray: Zone mask where 0 is occupied and 1 is free
        """
        # start with all 1s (e.g. all area is permitted)
        zone_mask = np.ones(
            (
                self.terrain_handler.width,
                self.terrain_handler.length,
            )
        )
        # then check each zone (remove the zone from each)
        for zone in self.zones:
            if zone in exclude_zones:
                continue
            zone_mask = self._update_mask_grid_with_radius(
                zone_mask,
                zone.x,
                zone.z,
                zone.radius,
                set_to=0,
            )
        return zone_mask

    def _get_zone_mask_for_zone_objects(self, zone: ZoneMarker) -> np.ndarray:
        """Returns the zone mask based on the zone radius (for placing objects
        inside a zone)

        Args:
            zone (ZoneMarker): Zone object defining the radius

        Returns:
            np.ndarray: Zone mask where 0 is occupied and 1 is free
        """
        return self.get_inclusion_mask_at_location(zone.x, zone.z, zone.radius)

    def get_inclusion_mask_at_location(self, x: int, z: int, radius: int) -> np.ndarray:
        """Returns a mask where 0 is free space and 1 is occupied space, at a
        given location

        Args:
            x (int): x location
            z (int): z location
            radius (int): Radius of the location

        Returns:
            np.ndarray: Inclusion mask
        """
        inclusion_mask = np.zeros(
            (
                self.terrain_handler.width,
                self.terrain_handler.length,
            )
        )
        inclusion_mask = self._update_mask_grid_with_radius(
            inclusion_mask, x, z, radius, set_to=1
        )
        return inclusion_mask

    def get_exclusion_mask_at_location(self, x: int, z: int, radius: int) -> np.ndarray:
        """Returns a mask where 0 is free space and 1 is occupied space, at a
        given location

        Args:
            x (int): x location
            z (int): z location
            radius (int): Radius of the location

        Returns:
            np.ndarray: Exclusion mask
        """
        exclusion_mask = np.zeros(
            (
                self.terrain_handler.width,
                self.terrain_handler.length,
            )
        )
        exclusion_mask = self._update_mask_grid_with_radius(
            exclusion_mask, x, z, radius, set_to=0
        )
        return exclusion_mask

    def _get_land_mask(self, cutoff_height=-20) -> np.ndarray:
        """Generates a boolean map grid, where 1 is land and 0 is water via terrain
        lookup. Is returned in the same dimensions as the terrain (e.g. LEV scale).

        Args:
            cutoff_height (float, optional): Height above which is considered land.
            Defaults to -20.

        Returns:
            np.ndarray: Land mask
        """
        # assume more water than land, so start with zeros
        mask = np.zeros(
            (
                self.terrain_handler.width,
                self.terrain_handler.length,
            )
        )
        # check each point against the raw terrain height
        for x in range(self.terrain_handler.width):
            for z in range(self.terrain_handler.length):
                if self.terrain_handler.get_height(x, z) > cutoff_height:
                    mask[x, z] = 1
        # setback everything radius 2 from the edge - to avoid things appearing
        # ... awkwardly on the edge of a cliff etc
        binary_terrain = self.terrain_handler._get_height_2d_array().copy()
        binary_terrain[binary_terrain < 0] = 0
        binary_terrain[binary_terrain > 0] = 1
        edge_mask = self._get_binary_transition_mask(binary_terrain)
        for x in range(self.terrain_handler.width):
            for z in range(self.terrain_handler.length):
                if edge_mask[x, z] == 1:
                    mask = self._update_mask_grid_with_radius(mask, x, z, 2, set_to=1)
        return mask

    def _get_water_mask(self, cutoff_height=-20) -> np.ndarray:
        """Generates a boolean map grid, where 1 is water and 0 is land via terrain
        lookup. Is returned in the same dimensions as the terrain (e.g. LEV scale).

        Args:
            cutoff_height (float, optional): Height above which is considered water.
            Defaults to -20.

        Returns:
            np.ndarray: Water mask
        """
        # assume more water than land, so start with zeros
        mask = np.zeros(
            (
                self.terrain_handler.width,
                self.terrain_handler.length,
            )
        )
        # check each point against the raw terrain height
        for x in range(self.terrain_handler.width):
            for z in range(self.terrain_handler.length):
                if self.terrain_handler.get_height(x, z) < cutoff_height:
                    mask[x, z] = 1
        # dont add the special edge mask (to avoid putting sea objects on the land)
        return mask

    def _get_coast_mask(self, cutoff_height: int = -20, radius: int = 50) -> np.ndarray:
        """Generates a boolean map grid, where 1 is coast and 0 not coast, within a
        radius of the max width/length of the terrain. Default radius is 50

        Args:
            cutoff_height (int, optional): Height above which is considered coast.
            Defaults to -20.
            radius (int, optional): Radius of the coast mask. Defaults to 50.

        Returns:
            np.ndarray: Coast mask
        """
        # assume more water than land, so start with zeros
        mask = np.zeros(
            (
                self.terrain_handler.width,
                self.terrain_handler.length,
            )
        )

        # find edges where water meets land, by finding edges of a binary masked
        # ... terrain map
        binary_terrain = self.terrain_handler._get_height_2d_array().copy()
        binary_terrain[binary_terrain < 0] = 0
        binary_terrain[binary_terrain > 0] = 1
        edge_mask = self._get_binary_transition_mask(binary_terrain)

        # Only apply radius around points that are both edges and above cutoff height
        for x in range(self.terrain_handler.width):
            for z in range(self.terrain_handler.length):
                if edge_mask[x, z] == 1:
                    mask = self._update_mask_grid_with_radius(
                        mask, x, z, radius, set_to=1
                    )
        # now multiply this against the land mask - so we exclude land, giving us only
        # ... coast
        return mask * self._get_water_mask(cutoff_height=cutoff_height)

    def _find_location(
        self,
        where: LocationEnum = LocationEnum.LAND,
        required_radius: float = 1,
        consider_objects: bool = True,
        consider_zones: bool = False,
        extra_zone_spacing: bool = False,
        in_zone: ZoneMarker = None,
        extra_masks: np.ndarray = None,
    ) -> tuple[float, float]:
        """Finds a random location on the land for the specified object. Will avoid
        clashing with other objects within their object's radius, including the
        optional required_radius (default 1 units on original LEV scale)

        Args:
            where (LocationEnum): Where to find the location (land, water, coast)
            required_radius (float, optional): Keep-clear radius of this new
            ...object. Defaults to 1 (unit = the original LEV scale e.g. 256x256).
            consider_objects (bool, optional): Whether to consider other objects.
            ...Defaults to True.
            consider_zones (bool, optional): Whether to consider other zones.
            ...Defaults to False.
            extra_zone_spacing (bool, optional): Whether to consider extra
            ...spacing around zones. Defaults to False.
            in_zone (ZoneMarker, optional): Zone to place the object in. Defaults to None.
        Returns:
            tuple[float, float]: x,z location of the object
        """
        # start with all 1s
        mask = np.ones(
            (
                self.terrain_handler.width,
                self.terrain_handler.length,
            )
        )

        # check if we have a zone to place the object in
        if in_zone is not None:
            mask *= self._get_zone_mask_for_zone_objects(in_zone)

        # get correct reference mask from where
        if where == LocationEnum.WATER:
            mask *= self._get_water_mask()
        elif where == LocationEnum.COAST:
            mask *= self._get_coast_mask()
        else:
            mask *= self._get_land_mask()

        # Create a heatmap visualization of the mask
        # import matplotlib.pyplot as plt

        # plt.figure(figsize=(10, 10))
        # plt.imshow(mask, cmap="hot", interpolation="nearest")
        # plt.colorbar(label="Mask Value")
        # plt.title("Mask Heatmap")
        # plt.xlabel("X")
        # plt.ylabel("Z")
        # plt.show()

        # apply that mask to the other masks specified in the argument
        if consider_objects:
            mask *= self._get_object_mask()
        if consider_zones and in_zone is None:
            mask *= self._get_all_zone_mask()

        # plt.figure(figsize=(10, 10))
        # plt.imshow(mask, cmap="hot", interpolation="nearest")
        # plt.colorbar(label="Mask Value")
        # plt.title("Mask Heatmap")
        # plt.xlabel("X")
        # plt.ylabel("Z")
        # plt.show()
        if extra_zone_spacing:
            mask *= self._get_zone_seperation_mask(
                extra_zone_spacing=extra_zone_spacing
            )
        if extra_masks is not None:
            mask *= extra_masks

        # plt.figure(figsize=(10, 10))
        # plt.imshow(mask, cmap="hot", interpolation="nearest")
        # plt.colorbar(label="Mask Value")
        # plt.title("Mask Heatmap")
        # plt.xlabel("X")
        # plt.ylabel("Z")
        # plt.show()
        # detect edges, and for each edge draw a circle of radius required_radius
        # ... (rounded up to closest int)
        required_radius = max(1, round(required_radius))
        edge_mask = self._get_binary_transition_mask(mask)
        for x in range(self.terrain_handler.width):
            for z in range(self.terrain_handler.length):
                if edge_mask[x, z] == 1:
                    mask = self._update_mask_grid_with_radius(
                        mask,
                        x,
                        z,
                        required_radius // 2,
                        set_to=0,  # mark as not allowed
                    )

        # check if we have any non-zero values in the edge mask
        if np.any(mask):
            return self.noise_generator.select_random_entry_from_2d_array(mask)
        logger.info("Find location: no suitable location found (empty mask)")
        return None

    def add_carrier_and_return_mask(
        self, required_radius: int = 30, mask_radius: int = 60
    ) -> np.ndarray:
        """Finds a location for the carrier, by using a coast search with a large
        required radius, then adds the object directly (special as it also sets the
        rotation of the object)

        Args:
            required_radius (int, optional): Required radius of the carrier. Defaults to 30.
            mask_radius (int, optional): Radius of the mask. Defaults to 60.

        Returns:
            np.ndarray: Mask in the carrier's radius for placing extra objects/zones
        """
        # find a coast location
        logger.info("ADD Carrier: Starting")
        x, z = self._find_location(
            where=LocationEnum.COAST, required_radius=required_radius
        )

        # Calculate angle from north to inward-facing vector
        center_x = self.terrain_handler.width / 2
        center_z = self.terrain_handler.length / 2
        angle = np.rad2deg(np.arctan2(center_z - z, center_x - x))
        logger.info("ADD Carrier: Calculated location and angle")

        # Update the cached object mask before adding the object
        self._update_cached_object_mask(x, z, required_radius)

        # add directly via ob3 interface, as this is a bit special
        self.ob3_interface.add_object(
            object_type="Carrier",
            location=[x, 10, z],
            team=Team.PLAYER,
            y_rotation=angle,
        )
        # and add magpie
        self.ob3_interface.add_object(
            object_type="dedicatedlifter",
            location=[x, 25, z],
            team=Team.PLAYER,
            y_rotation=angle,
        )
        logger.info("ADD Carrier: Calculating mask...")
        # start with array of 0s (assume radius is small)
        mask = np.zeros(
            (self.terrain_handler.width, self.terrain_handler.length), dtype=np.uint8
        )
        # then loop through and set 1 for locations within radius
        for i in range(self.terrain_handler.width):
            for j in range(self.terrain_handler.length):
                # if inside the radius, set 1
                if (i - x) ** 2 + (j - z) ** 2 <= mask_radius**2:
                    mask[i, j] = 1
                # if inside the object's required_radius, set 0 (avoid clash)
                if (i - x) ** 2 + (j - z) ** 2 <= required_radius**2:
                    mask[i, j] = 0
        return mask

    def add_object_template_on_land_random(
        self,
        object_template: list[ObjectContainer],
        consider_zones: bool = False,
        in_zone: ZoneMarker = None,
        extra_masks: np.ndarray = None,
        team_override: Union[int | Team] = None,
    ) -> None:
        """A special version of add on land - it identifies a location, but then adds
        multiple objects based on the relative positioning to the first

        Args:
            object_template (list[ObjectContainer]): list of [reference, additional1, additional2, ...]
            consider_zones (bool, optional): If True, the function will consider zones when placing objects. Defaults to False.
            in_zone (ZoneMarker, optional): The zone to place the objects in. Defaults to None.
            extra_masks (np.ndarray, optional): An extra mask to consider when placing objects. Defaults to None.
        """
        logger.info(f"Starting template add ({len(object_template)} objects)")
        # get info from the reference object
        ref_object = object_template[0]
        # get a lotation like normal below defaults to add on land
        returnval = self._find_location(
            required_radius=ref_object.required_radius,
            consider_zones=consider_zones,
            in_zone=in_zone,
            extra_masks=extra_masks,
        )
        if returnval is None:
            return
        x, z = returnval
        # find height at the specified x and z location (in LEV 3D space)
        height = self.terrain_handler.get_height(x, z)
        # check the height isnt negative, else its water so dont add
        reference_object_y_offset = ref_object.y_offset
        if height + reference_object_y_offset < 0:
            return

        # Update the cached object mask before adding the object
        self._update_cached_object_mask(x, z, int(ref_object.required_radius))

        # now use the normal add object method
        team = ref_object.team
        if team_override:
            team = team_override
        self.ob3_interface.add_object(
            object_type=ref_object.object_type,
            location=np.array([x, height + ref_object.y_offset, z]),
            attachment_type=ref_object.attachment_type,
            team=team.value if isinstance(team, Team) else team,
            y_rotation=ref_object.y_rotation,
        )

        # START of template repeat (for additional objects defined in this template)
        for obj_dict in object_template[1:]:
            # calculate the relative location
            location = np.array(
                [
                    x + obj_dict.template_x_offset,
                    height + reference_object_y_offset + obj_dict.template_y_offset,
                    z + obj_dict.template_z_offset,
                ]
            )
            team = obj_dict.team
            if team_override:
                team = team_override
            # and add the subsquent object
            self.ob3_interface.add_object(
                object_type=obj_dict.object_type,
                location=location,
                attachment_type=obj_dict.attachment_type,
                team=team.value if isinstance(team, Team) else team,
                y_rotation=obj_dict.y_rotation,
            )
        logger.info(f"Added {len(object_template)} objects via template")

    def add_object_on_land_random(
        self,
        object_type: str,
        attachment_type: str = "",
        team: Union[int | Team] = Team.ENEMY,
        y_offset: float = 0,
        y_rotation: float = 0,
        required_radius: float = 1,
        consider_zones: bool = False,
        in_zone: ZoneMarker = None,
    ) -> int:
        """Creates a new object in the level, selects a random land location, then
        uses the normal add object method with the height determined from the terrain

        Args:
            object_type (str): Type of the object
            location (np.array): Location of the object in LEV 3D space [x, y, z]
            attachment_type (str, optional): Type of attachment. Defaults to "".
            team (Union[int | Team], optional): Team number. Defaults to Team.ENEMY.
            y_rotation (float, optional): Rotation of the object in degrees. Defaults to 0.
            y_offset (float, optional): Vertical offset of the object. Defaults to 0.
            required_radius (float, optional): Keep-clear radius of this new object. Defaults to 1.
            consider_zones (bool, optional): Whether to consider other zones. Defaults to False.
            in_zone (ZoneMarker, optional): Zone to place the object in. Defaults to None.

        Returns:
            int: The ID of the new object
        """
        # below defaults to add on land
        returnval = self._find_location(
            required_radius=required_radius,
            consider_zones=consider_zones,
            in_zone=in_zone,
        )
        if returnval is None:
            return
        x, z = returnval
        # find height at the specified x and z location (in LEV 3D space)
        height = self.terrain_handler.get_height(x, z)
        # check the height isnt negative, else its water so dont add
        if height + y_offset < 0:
            return

        # Update the cached object mask before adding the object
        self._update_cached_object_mask(x, z, int(required_radius))

        # now use the normal add object method
        return self.ob3_interface.add_object(
            object_type=object_type,
            location=np.array([x, height + y_offset, z]),
            attachment_type=attachment_type,
            team=team.value if isinstance(team, Team) else team,
            y_rotation=y_rotation,
        )

    def add_alien_misc(
        self, map_size: str, carrier_xz: tuple[float, float] = None
    ) -> None:
        """Adds a few misc objects to the level (radar, AA guns etc)

        Args:
            map_size (str): Size of the map
            carrier_xz (tuple[float, float], optional): Carrier location in xz. Defaults to None.



        """
        # TODO in future, switch below on map size - the below seems reasonable
        # ... for 'large' 256x256
        extra_mask = None
        if carrier_xz is not None:
            # create an exclusion mask within radius of 60 of the carrier (e.g.
            # ... dont put a radar where the carrier will see it)
            extra_mask = self._update_mask_grid_with_radius(
                np.ones(
                    (self.terrain_handler.width, self.terrain_handler.length),
                    dtype=np.uint8,
                ),
                carrier_xz[0],
                carrier_xz[1],
                60,
                set_to=0,
            )

        # NOTE currently only templates
        objs = [TEMPLATE_ALIEN_AA] * 2 + [TEMPLATE_ALIEN_RADAR] * 2
        for obj in objs:
            if isinstance(obj, tuple):
                self.add_object_template_on_land_random(
                    object_template=obj,
                    consider_zones=True,
                    extra_masks=extra_mask,
                )
        logger.info(f"Done adding {len(objs)} alien misc objects")

    def add_scenery(self, map_size: str) -> None:
        """Adds a lot of random/different scenery objects to the level"""
        # TODO in future, switch below on map size - the below seems reasonable
        # ... for 'large' 256x256
        objs = (
            ["troprockcd"] * 8
            + ["troprockbd"] * 7
            + ["troprockad"] * 6
            + ["troprockcw"] * 5
            + ["troprockaw"] * 2
            + ["palm1"] * 80
            + ["plant1"] * 30
            + ["palm2"] * 50
            + ["palm3"] * 25
            + ["rubblea"] * 5
            + ["rubbleb"] * 5
            + ["rubblec"] * 5
            + ["rubbled"] * 5
            + ["rubblee"] * 5
        )
        for obj in objs:
            self.add_object_on_land_random(
                obj,
                team=Team.NEUTRAL,
                required_radius=2,
                consider_zones=True,
            )
        logger.info(f"Done adding {len(objs)} scenery objects")

    def add_zone(
        self,
        zone_type: ZoneType,
        zone_size: ZoneSize,
        zone_subtype: ZoneSubType,
        zone_index: Union[int, None] = None,
        extra_masks: Optional[np.ndarray] = None,
        extra_zone_spacing: int = 40,
    ) -> Optional[ZoneMarker]:
        """Adds a zone marker to the map based on the size via a lookup.

        Args:
            zone_type (ZoneType): Type of zone to create
            zone_size (ZoneSize): Size of the zone to create
            zone_subtype (ZoneSubType): Special type for the zone
            zone_index (int): Index of the zone (used for enemy team grouping)
            extra_masks (Optional[np.ndarray], optional): Additional mask to consider for placement. Defaults to None.
            extra_zone_spacing (bool, optional): Whether to consider the extra spacing around zones. Defaults to True.

        Returns:
            Optional[ZoneMarker]: The created zone marker if successful, None otherwise
        """
        # Try each size, starting with the requested size and going smaller if needed
        current_size = zone_size

        while current_size >= ZoneSize.TINY:
            # create zone marker object with current size
            new_zone = ZoneMarker(
                x=0,
                z=0,
                zone_type=zone_type,
                zone_size=current_size,
                zone_subtype=zone_subtype,
                zone_index=zone_index,
            )

            # find a land location we can place the radius zone at (with some buffer)
            # ... with special args to consider only other zones
            location = self._find_location(
                where=LocationEnum.LAND,
                required_radius=new_zone.radius,
                consider_objects=False,
                consider_zones=True,
                extra_zone_spacing=extra_zone_spacing,
                extra_masks=extra_masks,
            )

            # and update the zone marker with the actual location
            if location is not None:
                new_zone.x = location[0]
                new_zone.z = location[1]
                # TODO do these need to be backwards?
                self.zones.append(new_zone)
                return new_zone

            # If we couldn't place it, try a smaller size
            if current_size > ZoneSize.TINY:
                logger.info(
                    f"Could not find location for zone {zone_type} {current_size} {zone_subtype}, trying smaller size"
                )
                current_size = ZoneSize(current_size - 1)
            else:
                # We've tried the smallest size and still couldn't place it
                break

        logger.info(
            f"Could not find location for zone {zone_type} {zone_size} {zone_subtype} even at smallest size"
        )
        return None

    def populate_zone(self, zone: ZoneMarker) -> None:
        """Populates a zone with objects based on the zone type and size.

        Args:
            zone (ZoneMarker): Zone to populate
        """
        # get the probability list from models for the zone type
        logger.info("Populating zone: " + str(zone))
        # look up how many objects to add to the zone, based on its size
        num_objects = ZONE_SIZE_TO_NUM_OBJECTS[zone.zone_size]
        # iterate through zones
        p1_object_dict = {}  # select these first
        p1_num = 0  # how many to select
        p2_object_dict = {}  # then select these
        p2_num = 0  # how many to select
        all_other_object_dict = {}  # then fill with the objs here
        z_t = zone.zone_type
        z_s = zone.zone_subtype

        if z_t == ZoneType.SCRAP and z_s == ZoneSubType.DESTROYED_BASE:
            # no priority dict - burnt out building
            p1_object_dict = DESTROYED_BASE_PRIORITY
            p1_num = 1
            all_other_object_dict = SCRAP_DESTROYED_BASE
        if z_t == ZoneType.SCRAP and z_s == ZoneSubType.OLD_TANK_BATTLE:
            # default - just general scrap
            all_other_object_dict = SCRAP_BATTLE
        elif z_t == ZoneType.SCRAP and z_s == ZoneSubType.FUEL_TANKS:
            # default - just general scrap
            all_other_object_dict = SCRAP_FUEL_TANKS
        elif z_t == ZoneType.SCRAP and z_s == ZoneSubType.WEAPON_CRATE:
            p1_object_dict = WEAPON_CRATE_SCRAP_PRIORITY
            p1_num = 3
            all_other_object_dict = WEAPON_CRATE_SCRAP_OTHERS
        elif z_t == ZoneType.BASE and z_s == ZoneSubType.PUMP_OUTPOST:
            # get at least 4 oil pumps
            p1_object_dict = PUMP_OUTPOST_PRIORITY
            p1_num = 4
            # then fill from the generic list for others
            all_other_object_dict = PUMP_OUTPOST_ALL
        elif z_t == ZoneType.BASE and z_s == ZoneSubType.GENERIC_BASE:
            # at least one production / command building (SCALES WITH SIZE)
            p1_object_dict = BASE_PRIORITY1
            p1_num = 1 * zone.zone_size.value
            # then at least two power stores
            p2_object_dict = BASE_PRIORITY2
            p2_num = 2
            # then fill from the generic list for others
            all_other_object_dict = BASE_ALL_OTHER
        else:
            logger.info(
                f"No default case for zone type {zone.zone_type} and special {zone.zone_subtype}"
            )

        # NOW implement
        priority_1_objs = [
            self.noise_generator.select_random_from_weighted_dict(p1_object_dict)
            for _ in range(p1_num)
        ]
        priority_2_objs = [
            self.noise_generator.select_random_from_weighted_dict(p2_object_dict)
            for _ in range(p2_num)
        ]
        all_base_objs = [
            self.noise_generator.select_random_from_weighted_dict(all_other_object_dict)
            for _ in range(num_objects - p1_num - p2_num)
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
        for obj in priority_1_objs + priority_2_objs + all_base_objs:
            # check if obj is a list (template) or a single object
            if isinstance(obj, tuple):
                self.add_object_template_on_land_random(
                    obj, in_zone=zone, team_override=zone.zone_index
                )
            else:
                self.add_object_on_land_random(
                    obj.object_type,
                    attachment_type=obj.attachment_type,
                    team=obj.team if zone.zone_index is None else zone.zone_index,
                    required_radius=obj.required_radius,
                    y_rotation=self.noise_generator.randint(0, 360),
                    y_offset=obj.y_offset,
                    in_zone=zone,
                )
        logger.info("Populating zone: " + str(zone) + " completed")

    def create_patrol_points_hull(self, n_points: int = 3) -> None:
        """Generates a convex hull around the patrol points

        Args:
            n_points (int): Number of patrol points to use
        """
        # select 5 points at random using noisegen from the map coords
        points = []
        for _ in range(n_points):
            x, z = self.noise_generator.select_random_entry_from_2d_array(
                self._get_land_mask()
            )
            y = self.terrain_handler.get_height(x, z) + self.noise_generator.randint(
                55, 100
            )
            points.append((x, y, z))
        # if we stick to 3 points, we dont need to use a convex hull - triangles
        # ... are always convex
        return points

    def add_object_centered_on_zone(self, object_type: str, zone: ZoneMarker) -> int:
        """Adds an object centered on the zone

        Args:
            object_type (str): Type of object
            zone (ZoneMarker): Zone object defining the location

        Returns:
            int: The ID of the new object
        """
        x, z = zone.x, zone.z
        y = self.terrain_handler.get_height(x, z)
        self.ob3_interface.add_object(
            object_type=object_type,
            location=[x, y, z],
            team=Team.NEUTRAL,
        )
