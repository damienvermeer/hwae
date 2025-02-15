import numpy as np
import pytest
from unittest.mock import MagicMock, patch
from src.terrain import TerrainHandler


@patch("src.terrain.TerrainHandler.__init__", lambda self, *args: None)
def test_generate_upscaled_height_array():
    # create mock point
    class Point:
        def __init__(self, h):
            self.height = h

    # Create terrain handler with mock noise generator
    terrain = TerrainHandler()
    terrain.width = 2
    terrain.length = 2

    # Set up test heights in a 2x2 grid:
    # [0 1]
    # [1 4]
    heights = [[0, 1], [1, 4]]

    # Mock the get_height method to return our test data
    def mock_get_height(x, z):
        return heights[x][z]

    terrain.get_height = mock_get_height

    # Test with scale=3 to create a 6x6 grid
    result = terrain.generate_upscaled_height_array(scale=3)
    assert result.shape == (6, 6)

    print("Result array:")
    print(result)

    # Check corner values match original points
    np.testing.assert_almost_equal(result[0, 0], heights[0][0])  # top-left = 0
    np.testing.assert_almost_equal(result[0, -1], heights[0][1])  # top-right = 1
    np.testing.assert_almost_equal(result[-1, 0], heights[1][0])  # bottom-left = 1
    np.testing.assert_almost_equal(result[-1, -1], heights[1][1])  # bottom-right = 4

    # Check middle points are correctly interpolated
    # For a 6x6 grid, points are at 0, 0.2, 0.4, 0.6, 0.8, 1.0 of the way across
    np.testing.assert_almost_equal(result[0, 3], 0.6)  # top row, 60% across = 0.6
    np.testing.assert_almost_equal(result[3, 0], 0.6)  # left column, 60% down = 0.6
    np.testing.assert_almost_equal(result[3, 3], 1.92)  # center point


@patch("src.terrain.TerrainHandler.__init__", lambda self, *args: None)
def test_upscale_downsample_consistency():
    # Create terrain handler
    terrain = TerrainHandler()
    terrain.width = 2
    terrain.length = 2

    # Set up test heights
    heights = [[0, 1], [1, 4]]
    terrain.get_height = lambda x, z: heights[x][z]

    # Upscale by 2 (creating a 4x4 grid)
    result = terrain.generate_upscaled_height_array(scale=2)
    assert result.shape == (4, 4)

    print("Upscaled array (4x4):")
    print(result)

    # When upscaling by 2, the points are at:
    # 0, 0.333, 0.666, 1.0
    # So we need to sample at indices 0 and 3 to get original values
    downsampled = result[::3, ::3]
    assert downsampled.shape == (2, 2)

    # Original height array
    original = np.array(heights)

    print("\nDownsampled array (2x2):")
    print(downsampled)
    print("\nOriginal array (2x2):")
    print(original)

    # Verify downsampled array matches original
    np.testing.assert_array_almost_equal(downsampled, original)
