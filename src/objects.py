"""
HWAE (Hostile Waters Antaeus Eternal)

src.objects

Contains all info regarding objects for the level
"""

from dataclasses import dataclass
from types import new_class
from fileio.ob3 import Ob3File
import numpy as np
from enum import IntEnum
from typing import Union


class Team(IntEnum):
    PLAYER = 0
    ENEMY = 1
    # TODO support multiple teams (requires .for file likely)
    NEUTRAL = 4294967295  # FFFF


@dataclass
class ObjectHandler:
    ob3_interface: Ob3File

    def add_object(
        self,
        object_type: str,
        location: np.array,
        attachment_type: str = "",
        team: Union[int | Team] = Team.ENEMY,
    ) -> None:
        """Creates a new object in the level

        Args:
            object_type (str): Type of the object
            location (np.array): Location of the object in 3D space [x, y, z]
            attachment_type (str, optional): Type of attachment. Defaults to "".
            team (Union[int | Team], optional): Team number. Defaults to Team.ENEMY.
        """
        self.ob3_interface.add_object(
            object_type=object_type,
            location=location,
            attachment_type=attachment_type,
            team=team.value if isinstance(team, Team) else team,
        )
