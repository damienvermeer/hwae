import numpy as np
import pytest
from unittest.mock import MagicMock, patch
from src.terrain import TerrainHandler


@patch("src.terrain.TerrainHandler.__init__", lambda self, *args: None)
@patch(
    "src.terrain.TerrainHandler._get_height_2d_array",
    lambda self, *args: np.array([[0, 1], [1, 4]], dtype=np.float64),
)
def test_generate_upscaled_height_array():
    # Create terrain handler with mock noise generator
    terrain = TerrainHandler()
    terrain.width = 2
    terrain.length = 2

    # Test with scale=3 to create a 6x6 grid
    result, width, length = terrain._generate_upscaled_height_array(scale=3)
    assert result.shape == (6, 6)
    assert width == 6
    assert length == 6

    print("Result array:")
    print(result)

    # Check corner values match original points
    np.testing.assert_almost_equal(result[0, 0], 0)  # top-left = 0
    np.testing.assert_almost_equal(result[0, -1], 1)  # top-right = 1
    np.testing.assert_almost_equal(result[-1, 0], 1)  # bottom-left = 1
    np.testing.assert_almost_equal(result[-1, -1], 4)  # bottom-right = 4

    # Check middle points are correctly interpolated
    # For a 6x6 grid, points are at 0, 0.2, 0.4, 0.6, 0.8, 1.0 of the way across
    np.testing.assert_almost_equal(result[0, 3], 0.6)  # top row, 60% across = 0.6
    np.testing.assert_almost_equal(result[3, 0], 0.6)  # left column, 60% down = 0.6
    np.testing.assert_almost_equal(result[3, 3], 1.92)  # center point


@patch("src.terrain.TerrainHandler.__init__", lambda self, *args: None)
@patch(
    "src.terrain.TerrainHandler._get_height_2d_array",
    lambda self, *args: np.array([[0, 1], [1, 4]], dtype=np.float64),
)
def test_upscale_downsample_consistency():
    # Create terrain handler
    terrain = TerrainHandler()
    terrain.width = 2
    terrain.length = 2

    # Original height array
    original = np.array([[0, 1], [1, 4]], dtype=np.float64)

    # Upscale by 2 (creating a 4x4 grid)
    result, width, length = terrain._generate_upscaled_height_array(scale=2)
    assert result.shape == (4, 4)
    assert width == 4
    assert length == 4

    print("Upscaled array (4x4):")
    print(result)

    # When upscaling by 2, the points are at:
    # 0, 0.333, 0.666, 1.0
    # So we need to sample at indices 0 and 3 to get original values
    downsampled = result[::3, ::3]
    assert downsampled.shape == (2, 2)

    print("\nDownsampled array (2x2):")
    print(downsampled)
    print("\nOriginal array (2x2):")
    print(original)

    # Verify downsampled array matches original
    np.testing.assert_array_almost_equal(downsampled, original)
