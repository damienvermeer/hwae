"""
HWAE (Hostile Waters Antaeus Eternal)

src.noisegen

Noise generation functions for terrain, textures etc
"""

from dataclasses import dataclass
import random
import numpy as np
import noise


@dataclass
class NoiseGenerator:
    seed: int

    def __post_init__(self):
        random.seed(self.seed)
        np.random.seed(self.seed)

    def randint(self, min, max):
        return np.random.randint(min, max)

    def random_noisemap(
        self,
        width: int,
        height: int,
        scale: float = 0.5,
        octaves: int = 6,
        persistence: float = 0.5,
        lacunarity: float = 2.0,
        cutoff: float = 0,
    ):
        """Generate a random 2d noise map using perlin noise

        Args:
            width (int): width of the noise map
            height (int): height of the noise map
            scale (float, optional): Perlin noise scale. Defaults to 0.5.
            octaves (int, optional): Number of octaves. Defaults to 6.
            persistence (float, optional): Persistence. Defaults to 0.5.
            lacunarity (float, optional): Lacunarity. Defaults to 2.0.
            cutoff (float, optional): Cutoff value (any values less than cutoff will be set to 0). Defaults to 0.

        Returns:
            np.ndarray: 2D noise map
        """
        # start with a 0-1, 0-1 map
        mapx, mapy = np.meshgrid(np.linspace(0, 1, width), np.linspace(0, 1, height))
        # now apply perlin noise using vectorise (fast)
        map = np.vectorize(noise.pnoise2)(
            mapx / scale,
            mapy / scale,
            octaves=octaves,
            persistence=persistence,
            lacunarity=lacunarity,
            base=self.seed,  # use the global seed
        )
        # scale the entire map to have a value between 0 and 1
        map = (map - np.min(map)) / (np.max(map) - np.min(map))
        # apply floor/cutoff (typically used for terrain)
        map[map < cutoff] = 0
        return map
