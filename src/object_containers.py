from src.models import (
    Team,
    ObjectContainer,
)
from enum import IntEnum, auto
from dataclasses import dataclass


class Team(IntEnum):
    """Team enumeration for objects"""

    PLAYER = 0
    ENEMY = 1
    NEUTRAL = 2


### BASE OBJECTS
BASE_WALL_GUN = ObjectContainer(
    object_type="AlienTower",
    team=Team.ENEMY,
    required_radius=1,
    attachment_type="WallLaser",
)
BASE_LIGHTNING_GUN = ObjectContainer(
    object_type="AlienTower",
    team=Team.ENEMY,
    required_radius=1,
    attachment_type="LightningGun",
)
BASE_BLAST_TOWER = ObjectContainer(
    object_type="BlastTower",
    team=Team.ENEMY,
    required_radius=1,
    y_offset=2,
)
BASE_OIL_PUMP = ObjectContainer(
    object_type="ALIENPUMP",
    team=Team.ENEMY,
    required_radius=2,
)
BASE_ALIEN_POWER_STORE = ObjectContainer(
    object_type="alienpowerstore",
    team=Team.ENEMY,
    required_radius=2,
    y_offset=3,
)
BASE_PRIORITY1 = {
    BASE_OIL_PUMP: 1,
    BASE_ALIEN_POWER_STORE: 1,
}
BASE_GROUND_PROD = ObjectContainer(
    object_type="ALIENGROUNDPROD",
    team=Team.ENEMY,
    required_radius=5,
)
BASE_AIR_PROD = ObjectContainer(
    object_type="AlienProdTower",
    team=Team.ENEMY,
    required_radius=3,
)
BASE_COM = ObjectContainer(
    object_type="ALIENCOMCENTER",
    team=Team.ENEMY,
    required_radius=5,
)
BASE_PRIORITY2 = {BASE_GROUND_PROD: 1, BASE_AIR_PROD: 1, BASE_COM: 1}
ALL_BASE = {
    BASE_WALL_GUN: 8,
    BASE_LIGHTNING_GUN: 8,
    BASE_BLAST_TOWER: 8,
    BASE_OIL_PUMP: 1,
    BASE_ALIEN_POWER_STORE: 3,
    BASE_GROUND_PROD: 1,
    BASE_AIR_PROD: 1,
    BASE_COM: 1,
}


### SCRAP OBJECTS
SCRAP_TRANSMITTER = ObjectContainer(
    object_type="transmitter",
    team=Team.NEUTRAL,
    required_radius=4,
)
SCRAP_L1SCAVBENTPIPE = ObjectContainer(
    object_type="l1scavbentpipe",
    team=Team.NEUTRAL,
    required_radius=4,
)
SCRAP_L1SCAVHOLEPIPE = ObjectContainer(
    object_type="l1scavholepipe",
    team=Team.NEUTRAL,
    required_radius=4,
)
SCRAP_TANKWRECK = ObjectContainer(
    object_type="Tankwreck",
    team=Team.NEUTRAL,
    required_radius=4,
)
SCRAP_L2FUELTANK = ObjectContainer(
    object_type="l2fueltank",
    team=Team.NEUTRAL,
    required_radius=4,
)
SCRAP_L2FUELSILO = ObjectContainer(
    object_type="l2silo",
    team=Team.NEUTRAL,
    required_radius=4,
)
# SOME OF THE BELOW OBJECTS ARE CRASHING THE GAME?
ALL_SCRAP = {
    # SCRAP_TRANSMITTER: 1,
    # SCRAP_L1SCAVBENTPIPE: 2,
    # SCRAP_L1SCAVHOLEPIPE: 2,
    SCRAP_TANKWRECK: 3,
    # SCRAP_L2FUELTANK: 2,
    # SCRAP_L2FUELSILO: 2,
}
