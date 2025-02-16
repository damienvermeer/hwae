"""
HWAE (Hostile Waters Antaeus Eternal)

src.terrain

Contains all info regarding terrain for the level
"""

from dataclasses import dataclass
import logging
import math
from enum import IntEnum, auto
from pathlib import Path
from typing import Any, Optional

from PIL import Image
import numpy as np

from src.fileio.lev import LevFile
from src.fileio.ob3 import MAP_SCALER
from src.noisegen import NoiseGenerator
from src.models import ZoneMarker
import os


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

    def get_raw_height(self, x: int, z: int) -> float:
        return self.terrain_points[x, z].height

    def get_height(self, x: int, z: int) -> float:
        return self.terrain_points[x, z].height / MAP_SCALER

    def _get_height_2d_array(self) -> np.ndarray:
        return np.array(
            [
                [point.height / MAP_SCALER for point in row]
                for row in self.terrain_points
            ]
        )

    def set_height(self, x: int, z: int, height: float) -> None:
        self.terrain_points[x, z].height = height

    def get_max_height(self) -> float:
        return np.max(
            np.array([[point.height for point in row] for row in self.terrain_points])
        )

    def get_min_height(self) -> float:
        return np.min(
            np.array([[point.height for point in row] for row in self.terrain_points])
        )

    def _scale_array(
        self, arr: np.ndarray, min_val: float, max_val: float
    ) -> np.ndarray:
        """
        Scales a 2D NumPy array to a specified range while maintaining the original distribution.

        This function scales the heights of the _LevTerrainPoint objects in the input array
        to the specified range while maintaining the original distribution. This is done by
        first finding the current min and max values of the heights, and then scaling the heights
        to the specified range using a linear transformation.

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
        logging.info("Starting terrain generation...")

        # Step 1 - generate a base map
        logging.info("Step 1: Generating base noise map...")
        # generate a base noise map with the same dimensions as the map
        noise_map = self.noise_gen.random_noisemap(self.width, self.length, cutoff=0.3)
        for x in range(self.width):
            for y in range(self.length):
                self.terrain_points[x, y].height = noise_map[x, y]

        # Step 2 - load a template map outline, to enforce we get an island
        logging.info("Step 2: Applying island template...")
        # TODO neater
        script_dir = os.path.dirname(os.path.abspath(__file__))
        mapgen_dir = os.path.join(script_dir, "assets", "mapgen")
        num_mapgen_templates = len(os.listdir(mapgen_dir))
        # pick a mapgen template at random
        mapgen_template = self.noise_gen.randint(1, num_mapgen_templates - 1)
        logging.info(f"Selected template: {mapgen_template}.png")
        with Image.open(os.path.join(mapgen_dir, f"{mapgen_template}.png")) as fimg:
            # rotate by a random angle
            angle = self.noise_gen.randint(0, 360)
            logging.info(f"Rotating template by {angle} degrees")
            img = fimg.rotate(angle, Image.NEAREST, expand=True)
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
        logging.info("Step 3: Scaling terrain heights...")
        self.terrain_points = self._scale_array(self.terrain_points, -1000, 3200)

        # Step 4 - apply final cutoff (to remove underwater height changes)
        logging.info("Step 4: Applying underwater height cutoff...")
        for x in range(self.width):
            for y in range(self.length):
                if self.terrain_points[x, y].height < -150:
                    self.terrain_points[x, y].height = -1500

        # Step 5 - remove holes from appearing in the map by setting the flags
        logging.info("Step 5: Setting terrain flags...")
        # ... of every point to 1
        for x in range(self.width):
            for y in range(self.length):
                self.terrain_points[x, y].flags = 1  # 'TP_DRAW' mode
                # set each texture a random direction (gives some visual variety)
                self.terrain_points[x, y].texture_dir = self.noise_gen.randint(0, 8)

        # Step 6 - apply random map textures
        logging.info("Step 6: Applying terrain textures...")
        # 1 sea, 1 shore, 5 normal, 1 hill, 1 peak
        # Step 6a - get a noisemap we will use for the variety in textures, with more
        # ... noise in it. scale the map between 0 and 4 (integers only)
        N = 5  # number of 'normal textures'
        noise_map = self.noise_gen.random_noisemap(
            self.width, self.length, persistence=1
        )
        # Map noise values (0-1) to texture indices (0-N) with decreasing frequency
        # Create thresholds that give exponentially less space to higher values
        thresholds = np.array(
            [0.4, 0.65, 0.8, 0.9, 0.95, 1.0]
        )  # Each range is smaller than the previous
        noise_map = np.digitize(noise_map, thresholds)

        # Step 6b - apply the noisemap to the terrain (the terrain_points) with
        # ... an offset to cover the sea and shore
        logging.info("Applying base terrain textures...")
        for x in range(self.width):
            for y in range(self.length):
                self.terrain_points[x, y].mat = noise_map[x, y] + 2

        # Step 6c - apply height-bound materials (sea, shore)
        logging.info("Applying height-based terrain textures...")
        max_height = self.get_max_height()
        for x in range(self.width):
            for y in range(self.length):
                if self.terrain_points[x, y].height < -10:
                    self.terrain_points[x, y].mat = 0  # sea
                    self.terrain_points[x, y].flags = 2  # 'TP_WET' mode
                elif -10 <= self.terrain_points[x, y].height <= 80:
                    self.terrain_points[x, y].mat = 1  # shore
                elif self.terrain_points[x, y].height > 0.8 * max_height:
                    self.terrain_points[x, y].mat = 5  # hills
                elif self.terrain_points[x, y].height > 0.9 * max_height:
                    self.terrain_points[x, y].mat = 6  # peaks

        logging.info("Terrain generation complete!")

    def apply_texture_based_on_zone(self, zone: ZoneMarker) -> None:
        """Applies the texture with texture_id in the radius defined by the zone
        object (used for setting special textures like pavement/alien blood etc)

        Args:
            zone (ZoneMarker): Zone object defining the radius and texture
        """
        # first select all the terrain points which are within a radius of the zone
        # ... location
        logging.info("Applying zone texture: Selecting terrain points within radius")
        for x in range(self.width):
            for y in range(self.length):
                if (x - zone.x) ** 2 + (y - zone.z) ** 2 <= zone.radius**2:
                    # slight chance to use a different texture
                    texture_offset = self.noise_gen.randint(0, 5) // 4
                    self.terrain_points[x, y].mat = zone.texture_id + texture_offset
        logging.info("Applying zone texture: Completed")

    def flatten_terrain_based_on_zone(self, zone: ZoneMarker) -> None:
        """Flattens the terrain based on the zone radius

        Args:
            zone (ZoneMarker): Zone object defining the radius
        """
        # find the average height of the terrain within the zone
        logging.info("Zone: Flattening terrain: Finding average height")
        avg_height = 0
        count = 0
        for x in range(self.width):
            for y in range(self.length):
                if (x - zone.x) ** 2 + (y - zone.z) ** 2 <= zone.radius**2:
                    avg_height += self.terrain_points[x, y].height
                    count += 1
        avg_height /= count
        logging.info("Zone: Flattening terrain: Found average height")
        # set the height of all points within the zone to the average height
        for x in range(self.width):
            for y in range(self.length):
                if (x - zone.x) ** 2 + (y - zone.z) ** 2 <= zone.radius**2:
                    self.terrain_points[x, y].height = avg_height
        logging.info("Zone: Flattening terrain: Completed")

    # def _generate_upscaled_height_array(
    #     self, scale: int = 10
    # ) -> tuple[np.ndarray, int, int]:
    #     """Upscales the height array by a factor of scale, with intermediate
    #     points linearly interpolated between the original points.

    #     Args:
    #         scale (int, optional): Scale to apply in each direction. Defaults to 10 (
    #         turns 256x256 into 2560x2560).

    #     Returns:
    #         np.ndarray: Upscaled 2 dimensional height array
    #         int: Width of the upscaled array
    #         int: Length of the upscaled array
    #     """
    #     # Get original height array
    #     height_array = self._get_height_2d_array()
    #     logging.info("Terrain upscale: Got original height array")

    #     # Create coordinate arrays for output
    #     x = np.linspace(0, self.width - 1, self.width * scale)
    #     z = np.linspace(0, self.length - 1, self.length * scale)
    #     logging.info("Terrain upscale: Created coordinate arrays")

    #     # Get integer and fractional parts
    #     x0 = x.astype(np.int32)
    #     z0 = z.astype(np.int32)
    #     x1 = np.minimum(x0 + 1, self.width - 1)
    #     z1 = np.minimum(z0 + 1, self.length - 1)
    #     xf = x - x0
    #     zf = z - z0
    #     logging.info("Terrain upscale: Computed integer and fractional parts")

    #     # Create meshgrids for vectorized computation
    #     XF, ZF = np.meshgrid(xf, zf, indexing="ij")
    #     X0, Z0 = np.meshgrid(x0, z0, indexing="ij")
    #     X1, Z1 = np.meshgrid(x1, z1, indexing="ij")
    #     logging.info("Terrain upscale: Created meshgrids")

    #     # Get corner values using advanced indexing
    #     v00 = height_array[X0, Z0]
    #     v01 = height_array[X0, Z1]
    #     v10 = height_array[X1, Z0]
    #     v11 = height_array[X1, Z1]
    #     logging.info("Got corner values")

    #     # Vectorized bilinear interpolation
    #     result = (
    #         v00 * (1 - XF) * (1 - ZF)
    #         + v01 * (1 - XF) * ZF
    #         + v10 * XF * (1 - ZF)
    #         + v11 * XF * ZF
    #     )
    #     logging.info("Terrain upscale: Completed bilinear interpolation")

    #     # Handle exact integer positions
    #     exact_x = XF == 0
    #     exact_z = ZF == 0
    #     exact_points = exact_x & exact_z
    #     if np.any(exact_points):
    #         result[exact_points] = height_array[X0[exact_points], Z0[exact_points]]

    #     logging.info("Terrain upscale: Completed height array upscaling")
    #     return result, self.width * scale, self.length * scale
