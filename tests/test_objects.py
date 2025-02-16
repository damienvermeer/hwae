import numpy as np
import pytest
from unittest.mock import MagicMock, patch
from src.objects import ObjectHandler


@patch("src.objects.ObjectHandler.__init__", lambda self, *args: None)
def test_get_land_mask():
    # Create object handler with mock terrain handler
    obj_handler = ObjectHandler()
    obj_handler.terrain_handler = MagicMock()
    obj_handler.terrain_handler.width = 3
    obj_handler.terrain_handler.length = 3

    # Mock get_height to return a simple height map:
    # [-30, -10, 0]
    # [-20, 10, 20]
    # [0, 30, 40]
    height_map = [[-30, -10, 0], [-20, 10, 20], [0, 30, 40]]
    obj_handler.terrain_handler.get_height = lambda x, z: height_map[x][z]

    # Test land mask with default cutoff (-20)
    land_mask = obj_handler._get_land_mask()
    expected_land = np.array(
        [
            [0, 1, 1],  # -30 < -20, -10 > -20, 0 > -20
            [0, 1, 1],  # -20 = -20, 10 > -20, 20 > -20
            [1, 1, 1],  # 0 > -20, 30 > -20, 40 > -20
        ]
    )
    np.testing.assert_array_equal(land_mask, expected_land)

    # Test with different cutoff height
    land_mask = obj_handler._get_land_mask(cutoff_height=0)
    expected_land = np.array(
        [
            [0, 0, 0],  # all <= 0
            [0, 1, 1],  # -20 < 0, 10 > 0, 20 > 0
            [0, 1, 1],  # 0 = 0, 30 > 0, 40 > 0
        ]
    )
    np.testing.assert_array_equal(land_mask, expected_land)


@patch("src.objects.ObjectHandler.__init__", lambda self, *args: None)
def test_get_water_mask():
    # Create object handler with mock terrain handler
    obj_handler = ObjectHandler()
    obj_handler.terrain_handler = MagicMock()
    obj_handler.terrain_handler.width = 3
    obj_handler.terrain_handler.length = 3

    # Mock get_height to return a simple height map:
    # [-30, -10, 0]
    # [-20, 10, 20]
    # [0, 30, 40]
    height_map = [[-30, -10, 0], [-20, 10, 20], [0, 30, 40]]
    obj_handler.terrain_handler.get_height = lambda x, z: height_map[x][z]

    # Test water mask with default cutoff (-20)
    water_mask = obj_handler._get_water_mask()
    expected_water = np.array(
        [
            [1, 0, 0],  # -30 < -20, -10 > -20, 0 > -20
            [1, 0, 0],  # -20 = -20, 10 > -20, 20 > -20
            [0, 0, 0],  # 0 > -20, 30 > -20, 40 > -20
        ]
    )
    np.testing.assert_array_equal(water_mask, expected_water)

    # Test with different cutoff height
    water_mask = obj_handler._get_water_mask(cutoff_height=0)
    expected_water = np.array(
        [
            [1, 1, 1],  # all <= 0
            [1, 0, 0],  # -20 < 0, 10 > 0, 20 > 0
            [1, 0, 0],  # 0 = 0, 30 > 0, 40 > 0
        ]
    )
    np.testing.assert_array_equal(water_mask, expected_water)


@patch("src.objects.ObjectHandler.__init__", lambda self, *args: None)
def test_get_binary_transition_mask():
    # Create object handler with mock terrain handler
    obj_handler = ObjectHandler()
    
    # Test with a simple 4x4 binary mask:
    # [0 0 0 0]
    # [0 1 1 0]
    # [0 1 1 0]
    # [0 0 0 0]
    input_mask = np.array([
        [0, 0, 0, 0],
        [0, 1, 1, 0],
        [0, 1, 1, 0],
        [0, 0, 0, 0],
    ])
    
    transition_mask = obj_handler._get_binary_transition_mask(input_mask)
    
    # Expected result - 1s at both horizontal and vertical transitions:
    # [0 1 1 0]  # Top edge of the block
    # [1 1 1 1]  # Left/right edges + interior
    # [1 1 1 1]  # Left/right edges + interior
    # [0 1 1 0]  # Bottom edge of the block
    expected_mask = np.array([
        [0, 1, 1, 0],  # Vertical transitions to row below
        [1, 1, 1, 1],  # Horizontal transitions + vertical
        [1, 1, 1, 1],  # Horizontal transitions + vertical
        [0, 1, 1, 0],  # Vertical transitions to row above
    ])
    
    np.testing.assert_array_equal(transition_mask, expected_mask)
    
    # Test with a more complex pattern:
    # [0 1 0]
    # [1 0 1]
    # [0 1 0]
    input_mask = np.array([
        [0, 1, 0],
        [1, 0, 1],
        [0, 1, 0],
    ])
    
    transition_mask = obj_handler._get_binary_transition_mask(input_mask)
    
    # Every cell should be marked as a transition since each cell
    # has at least one different neighbor (horizontally or vertically)
    expected_mask = np.ones((3, 3))
    
    np.testing.assert_array_equal(transition_mask, expected_mask)
