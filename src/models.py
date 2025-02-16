from dataclasses import dataclass
from enum import IntEnum


class Team(IntEnum):
    PLAYER = 0
    ENEMY = 1
    # TODO support multiple teams (requires .for file likely)
    NEUTRAL = 4294967295  # FFFF


@dataclass
class ObjectContainer:
    object_type: str
    team: Team
    required_radius: float
    y_offset: float = 0
    y_rotation: float = 0
    attachment_type: str = ""
    template_x_offset: float = 0
    template_z_offset: float = 0
    template_y_offset: float = 0
