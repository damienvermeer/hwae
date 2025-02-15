"""
HWAE (Hostile Waters Antaeus Eternal)

src.objects

Contains all info regarding objects for the level
"""

from dataclasses import dataclass
import logging
import numpy as np
from enum import IntEnum
from typing import Union

from src.fileio.ob3 import Ob3File, MAP_SCALER
from src.noisegen import NoiseGenerator
from src.terrain import TerrainHandler


class Team(IntEnum):
    PLAYER = 0
    ENEMY = 1
    # TODO support multiple teams (requires .for file likely)
    NEUTRAL = 4294967295  # FFFF


@dataclass
class ObjectHandler:
    terrain_handler: TerrainHandler
    ob3_interface: Ob3File
    noise_generator: NoiseGenerator

    def add_object_on_ground(
        self,
        object_type: str,
        location_x: float,
        location_z: float,
        attachment_type: str = "",
        team: Union[int | Team] = Team.ENEMY,
        y_offset: float = 0,
        y_rotation: float = 0,
    ) -> None:
        """Creates a new object in the level, sitting on the ground using the loaded
        terrain as reference with an optional vertical offset

        Args:
            object_type (str): Type of the object
            location_x (float): x-location of the object
            location_z (float): z-location of the object
            attachment_type (str, optional): Type of attachment. Defaults to "".
            team (Union[int | Team], optional): Team number. Defaults to Team.ENEMY.
            y_offset (float, optional): Vertical offset from terrain. Defaults to 0.
        """
        # find height at the specified x and z location (in LEV 3D space)
        height = self.terrain_handler.get_height(int(location_x), int(location_z))
        # check the height isnt negative, else its water so dont add
        if height + y_offset < 0:
            return
        # now use the normal add object method
        self.ob3_interface.add_object(
            object_type=object_type,
            location=np.array([location_x, height + y_offset, location_z]),
            attachment_type=attachment_type,
            team=team.value if isinstance(team, Team) else team,
            y_rotation=y_rotation,
        )

    def add_object(
        self,
        object_type: str,
        location: np.array,
        attachment_type: str = "",
        team: Union[int | Team] = Team.ENEMY,
        y_rotation: float = 0,
    ) -> None:
        """Creates a new object in the level

        Args:
            object_type (str): Type of the object
            location (np.array): Location of the object in LEV 3D space [x, y, z]
            attachment_type (str, optional): Type of attachment. Defaults to "".
            team (Union[int | Team], optional): Team number. Defaults to Team.ENEMY.
            y_rotation (float, optional): Rotation of the object in degrees. Defaults to 0.
        """
        # now use the OB3 to create an object
        self.ob3_interface.add_object(
            object_type=object_type,
            location=location,
            attachment_type=attachment_type,
            team=team.value if isinstance(team, Team) else team,
            y_rotation=y_rotation,
        )

    def add_object_on_land_random(
        self,
        object_type: str,
        attachment_type: str = "",
        team: Union[int | Team] = Team.ENEMY,
        y_offset: float = 0,
        y_rotation: float = 0,
    ) -> None:
        """Creates a new object in the level, selects a random land location, then
        uses the normal add object method with the height determined from the terrain

        Args:
            object_type (str): Type of the object
            location (np.array): Location of the object in LEV 3D space [x, y, z]
            attachment_type (str, optional): Type of attachment. Defaults to "".
            team (Union[int | Team], optional): Team number. Defaults to Team.ENEMY.
            y_rotation (float, optional): Rotation of the object in degrees. Defaults to 0.
            y_offset (float, optional): Vertical offset of the object. Defaults to 0.
        """
        z, x = self.find_location_on_land()
        # find height at the specified x and z location (in LEV 3D space)
        height = self.terrain_handler.get_height(z, x)
        # check the height isnt negative, else its water so dont add
        if height + y_offset < 0:
            return
        # now use the normal add object method
        self.ob3_interface.add_object(
            object_type=object_type,
            location=np.array([x, height + y_offset, z]),
            attachment_type=attachment_type,
            team=team.value if isinstance(team, Team) else team,
            y_rotation=y_rotation,
        )

    def _set_location_grid_in_radius(
        self, location_grid: np.array, x: int, z: int, radius: int, set_to: int = 0
    ) -> None:
        """Sets the location grid to 0 in a radius around a location - used for
        find_location and custom find locations like find_location_for_cruiser

        Args:
            location_grid (np.array): Location grid to set 0 within
            x (int): x location
            z (int): z location
            radius (int): Radius to set within
            set_to (int): Value to set the location grid to
        """
        # Create a circle mask around this point
        # Get coordinates for points within radius
        x_min = int(max(0, x - radius))
        x_max = int(min(self.terrain_handler.width, x + radius + 1))
        z_min = int(max(0, z - radius))
        z_max = int(min(self.terrain_handler.length, z + radius + 1))

        # Create coordinate arrays for the circle region
        x_coords, z_coords = np.meshgrid(
            np.arange(x_min, x_max), np.arange(z_min, z_max), indexing="ij"
        )

        # Calculate distances from center point
        distances = np.sqrt((x_coords - x) ** 2 + (z_coords - z) ** 2)

        # Create a mask for points within the radius
        mask = distances <= radius

        # Apply the mask to set values
        location_grid[x_min:x_max, z_min:z_max][mask] = set_to
        return location_grid

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
        return 1 - self._get_land_mask(cutoff_height=cutoff_height)

    def _get_coast_mask(
        self, cutoff_height: int = -20, radius_percent: int = 10
    ) -> np.ndarray:
        """Generates a boolean map grid, where 1 is coast and 0 not coast, within a
        radius of the max width/length of the terrain. Default radius is 10%

        Args:
            cutoff_height (int, optional): Height above which is considered coast.
            Defaults to -20.
            radius_percent (int, optional): Radius of the coast mask. Defaults to 10[%].

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
        # set acceptable spawn within radius_percent% map dims radius of any terrain
        # ... point (this is a crude way to capture the shore, if we then crop out land)
        radius = (
            radius_percent
            / 100
            * max(self.terrain_handler.width, self.terrain_handler.length)
        )
        for x in range(self.terrain_handler.width):
            for z in range(self.terrain_handler.length):
                if self.terrain_handler.get_height(x, z) > cutoff_height:
                    mask = self._set_location_grid_in_radius(
                        mask, x, z, radius, set_to=1
                    )
        # repeat, but with half the radius - but mask as invalid (this is so we
        # ... dont get too close to shore)
        for x in range(self.terrain_handler.width):
            for z in range(self.terrain_handler.length):
                if self.terrain_handler.get_height(x, z) > cutoff_height:
                    mask = self._set_location_grid_in_radius(
                        mask, x, z, radius // 2, set_to=0
                    )
        # now multiply this against the land mask - so we exclude land, giving us only
        # ... coast
        return mask * self._get_water_mask(cutoff_height=cutoff_height)

    def find_location_on_water(
        self, new_obj_radius: float = 0.2
    ) -> tuple[float, float]:
        """Finds a random location on the water for the specified object. Will avoid
        clashing with other objects within their object's radius, including the
        optional new_obj_radius (default 0.2 units on original LEV scale)

        Args:
            new_obj_radius (float, optional): Keep-clear radius of this new
            object. Defaults to 0.2 (unit = the original LEV scale e.g. 256x256).

        Returns:
            tuple[float, float]: x,z location of the object
        """
        # TODO implement the radius checks against other objects
        # pick a random location within the coast mask
        return self.noise_generator.select_random_entry_from_2d_array(
            self._get_water_mask()
        )

    def find_location_on_coast(
        self, new_obj_radius: float = 0.2
    ) -> tuple[float, float]:
        """Finds a random location on the coast for the specified object. Will avoid
        clashing with other objects within their object's radius, including the
        optional new_obj_radius (default 0.2 units on original LEV scale)

        Args:
            new_obj_radius (float, optional): Keep-clear radius of this new
            object. Defaults to 0.2 (unit = the original LEV scale e.g. 256x256).

        Returns:
            tuple[float, float]: x,z location of the object
        """
        # TODO implement the radius checks against other objects
        # pick a random location within the coast mask
        return self.noise_generator.select_random_entry_from_2d_array(
            self._get_coast_mask()
        )

    def find_location_on_land(self, new_obj_radius: float = 0.2) -> tuple[float, float]:
        """Finds a random location on the land for the specified object. Will avoid
        clashing with other objects within their object's radius, including the
        optional new_obj_radius (default 0.2 units on original LEV scale)

        Args:
            new_obj_radius (float, optional): Keep-clear radius of this new
            object. Defaults to 0.2 (unit = the original LEV scale e.g. 256x256).

        Returns:
            tuple[float, float]: x,z location of the object
        """
        # TODO implement the radius checks against other objects
        return self.noise_generator.select_random_entry_from_2d_array(
            self._get_land_mask()
        )

    def find_location_for_cruiser(self) -> tuple[tuple[int, int, int], float]:
        """Finds a location for the cruiser, by using a custom find_location search
        which looks for only water tiles with a distance of >20 from the coast

        Returns:
            tuple[int, int, int]: Selected location of the cruiser (x,y,z)
            float: Angle of the cruiser (y degrees)
        """
        # find a coast location
        x, z = self.find_location_on_coast()

        # Calculate angle from north to inward-facing vector
        center_x = self.terrain_handler.width / 2
        center_z = self.terrain_handler.length / 2
        angle = np.rad2deg(np.arctan2(center_z - z, center_x - x))
        logging.info("FINDLOC: Calculated angle")

        # the 15 below is to ensure the cruiser is not directly on the waterline
        return [z, 15, x], angle
