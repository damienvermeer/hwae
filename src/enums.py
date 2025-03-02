"""Common enums used across multiple modules"""

from enum import IntEnum


class Team(IntEnum):
    """Team enumeration for objects"""

    PLAYER = 0
    ENEMY = 1
    NEUTRAL = 4294967295  # 0xFFFFFFFF
