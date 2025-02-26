"""
HWAE (Hostile Waters Antaeus Eternal)

src.noisegen

Noise generation functions for terrain, textures etc
"""

from dataclasses import dataclass
import random
import numpy as np
from perlin_numpy import generate_fractal_noise_2d


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
        cutoff: float = 0,
    ):
        """Generate a random 2d noise map using perlin noise

        Args:
            width (int): width of the noise map
            height (int): height of the noise map
            cutoff (float, optional): Cutoff value (any values less than cutoff will be set to 0). Defaults to 0.

        Returns:
            np.ndarray: 2D noise map
        """
        # create perlin noise map
        map = generate_fractal_noise_2d((height, width), (8, 8), 5)
        # scale the entire map to have a value between 0 and 1
        map = (map - np.min(map)) / (np.max(map) - np.min(map))
        # apply floor/cutoff (typically used for terrain)
        map[map < cutoff] = 0
        return map

    def select_random_entry_from_2d_array(self, arr: np.ndarray) -> tuple[int, int]:
        """Select a random entry from a 2D array (only if the array value is > 0)

        Args:
            arr (np.ndarray): 2D array to select a point from

        Returns:
            tuple[int, int]: The x and y coordinates of the selected point in the array
        """
        # iterate over the array dimensions, creating a list of tuples if
        # ... the array value is > 0
        possible_values = [
            (x, z)
            for x in range(arr.shape[0])
            for z in range(arr.shape[1])
            if arr[x, z] > 0
        ]
        # select a random value from the possible_values
        result = possible_values[self.randint(0, len(possible_values))]
        # deconstruct
        return result[0], result[1]

    def select_random_from_list(self, in_list: list) -> object:
        """Selects a random object from a list

        Args:
            in_list (list): List to select from

        Returns:
            object: Random object from the list
        """
        return in_list[self.randint(0, len(in_list))]

    def select_random_sublist_from_list(
        self, in_list: list, min_n: int = 1, max_n: int = 9999
    ) -> list:
        """Selects a random sublist from a list, where the sublist length is between min_n and max_n.
        If the list length is less than min_n, the function will return a sublist of length min_n.
        If the list length is greater than max_n, the function will return a sublist of length max_n.

        Args:
            in_list (list): List to select from
            min_n (int): Minimum length of the sublist. Defaults to 1.
            max_n (int): Maximum length of the sublist. Defaults to 9999.

        Returns:
            list: Random sublist from the input list
        """
        list_length = len(in_list)
        if list_length <= min_n:
            return in_list[:min_n]  # Return up to min_n elements
        if list_length <= max_n:
            k = min_n if min_n == list_length else self.randint(min_n, list_length)
        else:
            k = min_n if min_n == max_n else self.randint(min_n, max_n)
        return random.sample(in_list, k=k)

    def select_random_from_weighted_dict(self, in_dict: dict) -> object:
        """Selects a random object from a dictionary, where the values are weights

        Args:
            in_dict (dict): Dictionary to select from, where keys are items and values
                are their weights/likelihoods

        Returns:
            object: Random object from the dictionary, weighted by the likelihood values
        """
        # Create a flat list where each key appears value times
        weighted_keys = []
        for key, weight in in_dict.items():
            weighted_keys.extend([key] * weight)
        # Select randomly from this weighted list
        return self.select_random_from_list(weighted_keys)
