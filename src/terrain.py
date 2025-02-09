"""
HWAE (Hostile Waters Antaeus Eternal)

src.terrain

Contains all info regarding terrain for the level
"""

from dataclasses import dataclass
from fileio.lev import LevFile
from noisegen import NoiseGenerator
import numpy as np
import os
from PIL import Image


@dataclass
class TerrainHandler:
    lev_interface: LevFile
    noise_gen: NoiseGenerator

    def __post_init__(self):
        # set width and length from the loaded file
        self.width = self.lev_interface.header.width
        self.length = self.lev_interface.header.length

        # load the 1 dimensional array of terrain points from the file
        # ... and convert it into a 2d numpy array
        self.terrain_points = np.array(self.lev_interface.terrain_points).reshape(
            (self.width, self.length)
        )

    def get_height(self, x: int, y: int) -> float:
        return self.terrain_points[x, y].height

    def set_height(self, x: int, y: int, height: float) -> None:
        self.terrain_points[x, y].height = height

    def randomise_texture_dirs(self) -> None:
        """Randomises the texture directions of all textures on the terrain. For
        now, this is an easy way to get some variety.
        """
        for x in range(self.width):
            for y in range(self.length):
                self.terrain_points[x, y].texture_dir = self.noise_gen.randint(0, 8)

    def _scale_array(
        self, arr: np.ndarray, min_val: float, max_val: float
    ) -> np.ndarray:
        """Scales a 2D NumPy array to a specified range while maintaining the original distribution.

        Args:
            arr (np.ndarray): The 2D NumPy array of _LevTerrainPoint objects
            min_val (float): The desired minimum value after scaling
            max_val (float): The desired maximum value after scaling

        Returns:
            np.ndarray: The original array with heights scaled to the new range
        """
        # Extract heights into a new array
        heights = np.array([[point.height for point in row] for row in arr])

        # Get the actual min/max values from the heights
        current_min = np.min(heights)
        current_max = np.max(heights)

        # Avoid division by zero if array is constant
        if current_max == current_min:
            # Set all heights to min_val
            for row in arr:
                for point in row:
                    point.height = min_val
            return arr

        # Scale the heights
        scale_factor = (max_val - min_val) / (current_max - current_min)
        for x in range(arr.shape[0]):
            for y in range(arr.shape[1]):
                arr[x, y].height = (
                    min_val + (heights[x, y] - current_min) * scale_factor
                )

        return arr

    def set_terrain_from_noise(self) -> None:
        """Sets the terrain heightmap from a noise map. For now, this is just a
        simple implementation, where the height is the value of the noise at the
        corresponding position.
        """
        # Step 1 - generate a base map
        # generate a base noise map with the same dimensions as the map
        noise_map = self.noise_gen.random_noisemap(self.width, self.length, cutoff=0.3)
        for x in range(self.width):
            for y in range(self.length):
                self.terrain_points[x, y].height = noise_map[x, y]

        # Step 2 - load a template map outline, to enforce we get an island
        # TODO neater
        script_dir = os.path.dirname(os.path.abspath(__file__))
        mapgen_dir = os.path.join(script_dir, "assets", "mapgen")
        num_mapgen_templates = len(os.listdir(mapgen_dir))
        # pick a mapgen template at random
        mapgen_template = self.noise_gen.randint(0, num_mapgen_templates - 1)
        with Image.open(os.path.join(mapgen_dir, f"{mapgen_template}.png")) as fimg:
            # rotate by a random angle
            img = fimg.rotate(
                self.noise_gen.randint(0, 360), Image.NEAREST, expand=True
            )
            # normlaise to [0,1]
            img = img.convert("L")
            img = np.array(img) / 255
            # resize to match world
            img = np.array(Image.fromarray(img).resize(self.terrain_points.shape))
            # now apply this as a multiplicative mask to the base map (as they are
            # ... the same dimensions now)
            for x in range(self.width):
                for y in range(self.length):
                    self.terrain_points[x, y].height *= img[x, y]

        # Step 3 - scale the terrain based on testing
        self.terrain_points = self._scale_array(self.terrain_points, -1000, 2200)

        # Step 4 - apply final cutoff (to remove underwater height changes)
        for x in range(self.width):
            for y in range(self.length):
                if self.terrain_points[x, y].height < -100:
                    self.terrain_points[x, y].height = -100

        # Step 5 - remove holes from appearing in the map by setting the flags
        # ... of every point to 1
        for x in range(self.width):
            for y in range(self.length):
                self.terrain_points[x, y].flags = 1  # 'TP_DRAW' mode
