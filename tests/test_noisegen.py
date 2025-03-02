"""
Tests for the NoiseGenerator class
"""

import os
import sys
import pytest
import numpy as np
from pathlib import Path

# Add the src directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(os.path.dirname(current_dir), 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from noisegen import NoiseGenerator


@pytest.fixture
def noise_generator(monkeypatch):
    """Create a NoiseGenerator instance with mocked randint"""
    generator = NoiseGenerator(seed=0)
    # Mock sequence of random values to make test deterministic
    random_values = iter([0, 0, 1, 1, 2, 2])

    def mock_randint(self, a, b):
        return next(random_values)

    monkeypatch.setattr(NoiseGenerator, "randint", mock_randint)
    return generator


def test_select_random_entry_from_2d_array(noise_generator):
    """Test that select_random_entry_from_2d_array only selects non-zero entries"""
    # Create a 3x3 test array with known 1s and 0s
    test_array = np.array([[0, 1, 0], [0, 0, 1], [1, 0, 0]])

    # Known positions of 1s are: (0,1), (1,2), (2,0)
    valid_positions = {(0, 1), (1, 2), (2, 0)}

    # Test multiple selections with our mocked random values
    for _ in range(3):
        x, y = noise_generator.select_random_entry_from_2d_array(test_array)
        # Assert that the selected position is one of the valid positions (contains 1)
        assert (x, y) in valid_positions
        # Double check that the value at the selected position is actually 1
        assert test_array[x, y] == 1
