"""
HWAE (Hostile Waters Antaeus Eternal)

src.objects

Contains all info regarding objects for the level
"""

from dataclasses import dataclass
from types import new_class
from terrain import TerrainHandler
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
    terrain_handler: TerrainHandler
    ob3_interface: Ob3File

    def add_object_on_ground(
        self,
        object_type: str,
        location_x: float,
        location_z: float,
        attachment_type: str = "",
        team: Union[int | Team] = Team.ENEMY,
        y_offset: float = 0,
    ) -> None:
        """Creates a new object in the level, sitting on the ground using the loaded
        terrain as reference with an optional vertical offset

        Args:
            object_type (str): Type of the object
            location_x (float): x-location of the object
            location_z (float): z-location of the object
            attachment_type (str, optional): Type of attachment. Defaults to "".
            team (Union[int | Team], optional): Team number. Defaults to Team.ENEMY.
            y_offset (float, optional): Vertical offset from terrain. Defaults to 0.
        """
        # find height at the specified x and z location (in LEV 3D space)
        height = self.terrain_handler.get_height(int(location_x), int(location_z))
        # now use the normal add object method
        self.ob3_interface.add_object(
            object_type=object_type,
            location=np.array([location_x, height + y_offset, location_z]),
            attachment_type=attachment_type,
            team=team.value if isinstance(team, Team) else team,
        )

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
            location (np.array): Location of the object in LEV 3D space [x, y, z]
            attachment_type (str, optional): Type of attachment. Defaults to "".
            team (Union[int | Team], optional): Team number. Defaults to Team.ENEMY.
        """
        # now use the OB3 to create an object
        self.ob3_interface.add_object(
            object_type=object_type,
            location=location,
            attachment_type=attachment_type,
            team=team.value if isinstance(team, Team) else team,
        )
