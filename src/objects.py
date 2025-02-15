"""
HWAE (Hostile Waters Antaeus Eternal)

src.objects

Contains all info regarding objects for the level
"""

from dataclasses import dataclass
import numpy as np
from enum import IntEnum
from typing import Union

from fileio.ob3 import Ob3File

from noisegen import NoiseGenerator
from terrain import TerrainHandler


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

    def find_location_for_cruiser(self) -> tuple[tuple[int, int, int], float]:
        """Finds a location for the cruiser, by using a custom find_location search
        which looks for only water tiles with a distance of >20 from the coast

        Returns:
            tuple[int, int, int]: Selected location of the cruiser (x,y,z)
            float: Angle of the cruiser (y degrees)
        """
        # find_location algorithm, first create a mapsize x*z grid and set
        # ... all to 0s (invalid spawn)
        location_grid = np.zeros(
            (
                self.terrain_handler.width,
                self.terrain_handler.length,
            )
        )
        # set acceptable spawn within 10% map dims radius of any terrain point (this
        # ... is a crude way to capture the shore, if we then crop out land)
        radius = 0.1 * max(self.terrain_handler.width, self.terrain_handler.length)
        for x in range(self.terrain_handler.width):
            for z in range(self.terrain_handler.length):
                height = self.terrain_handler.get_height(x, z)
                if height > -20:
                    location_grid = self._set_location_grid_in_radius(
                        location_grid, x, z, radius, set_to=1
                    )
        # after applying the above, now mark all terrain (height > -20) as invalid
        for x in range(self.terrain_handler.width):
            for z in range(self.terrain_handler.length):
                if self.terrain_handler.get_height(x, z) > -20:
                    location_grid[x, z] = 0
        # use the noise_generator to select a random location from the location_grid
        # ... (where 1 = valid spawn location)
        xfinal, zfinal = self.noise_generator.select_random_entry_from_2d_array(
            location_grid
        )

        import matplotlib.pyplot as plt

        # Draw heatmap of location_grid
        plt.figure(figsize=(10, 8))
        plt.imshow(location_grid, cmap="viridis", interpolation="nearest")
        plt.colorbar(label="Spawn Probability")

        # Add a large black dot at the selected location
        plt.plot(zfinal, xfinal, "ko", markersize=10)

        plt.title("Cruiser Spawn Location Heatmap")
        plt.xlabel("Z-axis")
        plt.ylabel("X-axis")
        plt.show()

        # Calculate angle from north to inward-facing vector
        center_x = self.terrain_handler.width / 2
        center_z = self.terrain_handler.length / 2
        angle = np.arctan2(center_z - zfinal, center_x - xfinal)
        angle = np.rad2deg(angle)

        # the 15 below is to ensure the cruiser is not directly on the waterline
        return [zfinal, 15, xfinal], angle
