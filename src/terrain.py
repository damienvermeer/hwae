"""
HWAE (Hostile Waters Antaeus Eternal)

src.terrain

Contains all info regarding terrain for the level
"""

from dataclasses import dataclass
from logger import get_logger
from paths import get_assets_path

logger = get_logger()

from PIL import Image
import numpy as np

from fileio.lev import LevFile
from fileio.ob3 import MAP_SCALER
from noisegen import NoiseGenerator
from zones.base_zone import Zone


@dataclass
class TerrainHandler:
    """Class for handling the terrain of the level"""

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
        logger.info("Starting terrain generation...")

        # Step 1 - generate a base map
        logger.info("Step 1: Generating base noise map...")
        # generate a base noise map with the same dimensions as the map
        noise_map = self.noise_gen.random_noisemap(self.width, self.length, cutoff=0.3)
        for x in range(self.width):
            for y in range(self.length):
                self.terrain_points[x, y].height = noise_map[x, y]

        # Step 2 - load a template map outline, to enforce we get an island
        logger.info("Step 2: Applying island template...")
        # TODO neater
        mapgen_dir = get_assets_path() / "mapgen"
        mapgen_files = list(mapgen_dir.glob("*.png"))
        num_mapgen_templates = len(mapgen_files)
        # pick a mapgen template at random
        mapgen_template = self.noise_gen.randint(1, num_mapgen_templates - 1)
        logger.info(f"Selected template: {mapgen_template}.png")
        with Image.open(mapgen_dir / f"{mapgen_template}.png") as fimg:
            # rotate by a random angle
            angle = self.noise_gen.randint(0, 360)
            logger.info(f"Rotating template by {angle} degrees")
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
        logger.info("Step 3: Scaling terrain heights...")
        self.terrain_points = self._scale_array(self.terrain_points, -1000, 3200)

        # Step 4 - apply final cutoff (to remove underwater height changes)
        logger.info("Step 4: Applying underwater height cutoff...")
        for x in range(self.width):
            for y in range(self.length):
                if self.terrain_points[x, y].height < -150:
                    self.terrain_points[x, y].height = -1500

        # Step 5 - remove holes from appearing in the map by setting the flags
        logger.info("Step 5: Setting terrain flags...")
        # ... of every point to 1
        for x in range(self.width):
            for y in range(self.length):
                self.terrain_points[x, y].flags = 1  # 'TP_DRAW' mode
                # set each texture a random direction (gives some visual variety)
                self.terrain_points[x, y].texture_dir = self.noise_gen.randint(0, 8)

        # Step 6 - apply random map textures
        logger.info("Step 6: Applying terrain textures...")
        noise_map = self.noise_gen.random_noisemap(self.width, self.length)
        # Map noise values (0-1) to texture indices (0-N) with decreasing frequency
        # Create thresholds that give exponentially less space to higher values
        thresholds = np.array(
            [0.4, 0.65, 0.8, 0.9, 0.95, 1.0]
        )  # Each range is smaller than the previous
        noise_map = np.digitize(noise_map, thresholds)

        # Step 6b - apply the noisemap to the terrain (the terrain_points) with
        # ... an offset to cover the sea and shore
        logger.info("Applying base terrain textures...")
        for x in range(self.width):
            for y in range(self.length):
                self.terrain_points[x, y].mat = noise_map[x, y] + 2

        # Step 6c - apply height-bound materials (sea, shore)
        logger.info("Applying height-based terrain textures...")
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

        logger.info("Terrain generation complete!")

    def apply_texture_based_on_zone(self, zone: Zone) -> None:
        """Applies the texture with texture_id in the radius defined by the zone
        object (used for setting special textures like pavement/alien blood etc)

        Args:
            zone (Zone): Zone object defining the radius and texture
        """
        # first select all the terrain points which are within the zone's mask
        logger.info("Applying zone texture: Selecting terrain points mask")
        zone_mask = zone.mask()
        for x in range(self.width):
            for y in range(self.length):
                if zone_mask[x, y]:
                    # slight chance to use a different texture
                    texture_offset = self.noise_gen.select_random_from_list(
                        [0] * 5 + [1] + [2]
                    )
                    self.terrain_points[x, y].mat = zone.texture_id + texture_offset
        logger.info("Applying zone texture: Completed")

    def flatten_terrain_based_on_zone(
        self, zone: Zone, smooth_radius: int = 10
    ) -> None:
        """
        Flattens and smooths the terrain around a flattened zone using a falloff function.

        Args:
            zone (Zone): Zone object defining the mask
            smooth_radius (int): Radius of smoothing area outside the zone
        """
        import numpy as np

        zone_mask = zone.mask()
        zone_center = (zone.x, zone.z)
        zone_radius = zone.radius

        # Get the zone's average height
        avg_height = 0
        count = 0
        for x in range(self.width):
            for y in range(self.length):
                if zone_mask[x, y]:
                    avg_height += max(60, self.terrain_points[x, y].height)
                    count += 1

        if count > 0:
            avg_height /= count

        # Set min height - to avoid spawning things in water
        avg_height = max(avg_height, 60)

        # Set all points inside the zone to the average height
        for x in range(self.width):
            for y in range(self.length):
                if zone_mask[x, y]:
                    self.terrain_points[x, y].height = avg_height

        # Simple linear falloff around the zone
        # First identify the boundary points of the zone
        boundary_points = []
        for x in range(self.width):
            for y in range(self.length):
                if zone_mask[x, y]:
                    # Check if this is a boundary point (has at least one non-zone neighbor)
                    if ((x > 0 and not zone_mask[x-1, y]) or
                        (x < self.width-1 and not zone_mask[x+1, y]) or
                        (y > 0 and not zone_mask[x, y-1]) or
                        (y < self.length-1 and not zone_mask[x, y+1])):
                        boundary_points.append((x, y))
        
        # Apply falloff to points outside the zone
        for x in range(self.width):
            for y in range(self.length):
                # Skip points inside the zone
                if zone_mask[x, y]:
                    continue
                
                # Find minimum distance to any boundary point
                min_dist = smooth_radius + 1
                for bx, by in boundary_points:
                    # Use Manhattan distance for simplicity
                    dist = abs(x - bx) + abs(y - by)
                    if dist < min_dist:
                        min_dist = dist
                
                # Apply falloff if within smooth_radius
                if min_dist <= smooth_radius:
                    # Linear falloff factor
                    falloff = 1.0 - (min_dist / smooth_radius)
                    
                    # Apply linear interpolation
                    original_height = self.terrain_points[x, y].height
                    self.terrain_points[x, y].height = (
                        falloff * avg_height + (1 - falloff) * original_height
                    )
        
        logger.info(f"Zone: Flattening terrain: Set zone to height {avg_height} with simple linear falloff")
