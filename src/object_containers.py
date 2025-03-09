from models import (
    Team,
    ObjectContainer,
)
from enum import IntEnum, auto
from dataclasses import dataclass


class Team(IntEnum):
    """Team enumeration for objects"""

    PLAYER = 0
    ENEMY = 1
    NEUTRAL = 4294967295  # 0xFFFFFFFF


# TEMPLATES

# tuple required for hashing
TEMPLATE_ALIEN_AA = tuple(
    [
        # first entry is the main object
        ObjectContainer(
            object_type="Alienspybase",
            team=Team.ENEMY,
            required_radius=2,
        ),
        # and subsequent entries are associated objects, so they
        # ... have x,y,z offsets relative to the first
        ObjectContainer(
            object_type="Alienackackgun",
            team=Team.ENEMY,
            required_radius=2,
            # below values came from ob3 review of an existing map/ob3 file
            template_x_offset=0.45655822656249256,
            template_y_offset=18.072725546874995,
            template_z_offset=0.008398056640626095,
        ),
    ]
)
TEMPLATE_ALIEN_RADAR = tuple(
    [
        # first entry is the main object
        ObjectContainer(
            object_type="Alienspybase",
            team=Team.ENEMY,
            required_radius=2,
        ),
        # and subsequent entries are associated objects, so they
        # ... have x,y,z offsets relative to the first
        ObjectContainer(
            object_type="Alienspytower",
            team=Team.ENEMY,
            required_radius=2,
            # below values came from ob3 review of an existing map/ob3 file
            template_x_offset=-0.15502599226306346,
            template_y_offset=21.23187597678917,
            template_z_offset=-0.0021609052224445015,
        ),
    ]
)
TEMPLATE_ALIEN_ENERGY_POWER_STORE_TRIANGLE = tuple(
    [
        ObjectContainer(
            object_type="alienpowerstore",
            team=Team.ENEMY,
            required_radius=3,
            y_offset=3,
        ),
        ObjectContainer(
            object_type="alienpowerstore",
            team=Team.ENEMY,
            required_radius=3,
            template_x_offset=2,
            template_z_offset=0,
        ),
        ObjectContainer(
            object_type="alienpowerstore",
            team=Team.ENEMY,
            required_radius=3,
            template_x_offset=1,
            template_z_offset=1.732,
        ),
    ]
)
TEMPLATE_ALIEN_GROUND_PROD_WITH_UNITS = tuple(
    [
        ObjectContainer(
            object_type="ALIENGROUNDPROD",
            team=Team.ENEMY,
            required_radius=5,
        ),
        ObjectContainer(
            object_type="LightWalker",
            team=Team.ENEMY,
            required_radius=3,
            template_x_offset=1.5,
            template_z_offset=-1.299,
        ),
        ObjectContainer(
            object_type="HeavyWalker",
            team=Team.ENEMY,
            required_radius=3,
            template_x_offset=0,
            template_z_offset=1.5,
        ),
    ]
)

TEMPLATE_ALIEN_AIR_PROD_WITH_UNITS = tuple(
    [
        ObjectContainer(
            object_type="AlienProdTower",
            team=Team.ENEMY,
            required_radius=3,
        ),
        ObjectContainer(
            object_type="SmallFlyer",
            team=Team.ENEMY,
            required_radius=3,
            template_x_offset=1.5,
            template_z_offset=-1.299,
        ),
        ObjectContainer(
            object_type="MediumFlyer",
            team=Team.ENEMY,
            required_radius=3,
            template_x_offset=0,
            template_z_offset=1.5,
        ),
    ]
)

TEMPLATE_ALIEN_LARGE_PROD_WITH_UNITS = tuple(
    [
        ObjectContainer(
            object_type="ALIENLARGEPROD",
            team=Team.ENEMY,
            required_radius=3,
        ),
        # below offsets are forming a triangle around the main object
        ObjectContainer(
            object_type="HoverLaser",
            team=Team.ENEMY,
            required_radius=3,
            template_x_offset=1.5,
            template_z_offset=-1.299,
        ),
        ObjectContainer(
            object_type="SiegeSlug",
            team=Team.ENEMY,
            required_radius=3,
            template_x_offset=0,
            template_z_offset=1.5,
        ),
    ]
)

TEMPLATE_6_BY_2_SILO = tuple(
    [
        ObjectContainer(
            object_type="l2silo",
            team=Team.NEUTRAL,
            required_radius=3,
            y_offset=5.5,
        ),
        ObjectContainer(
            object_type="l2silo",
            team=Team.NEUTRAL,
            required_radius=3,
            template_x_offset=0,
            template_z_offset=1,
        ),
        ObjectContainer(
            object_type="l2silo",
            team=Team.NEUTRAL,
            required_radius=3,
            template_x_offset=1,
            template_z_offset=0,
        ),
        ObjectContainer(
            object_type="l2silo",
            team=Team.NEUTRAL,
            required_radius=3,
            template_x_offset=1,
            template_z_offset=1,
        ),
        ObjectContainer(
            object_type="l2silo",
            team=Team.NEUTRAL,
            required_radius=3,
            template_x_offset=2,
            template_z_offset=0,
        ),
        ObjectContainer(
            object_type="l2silo",
            team=Team.NEUTRAL,
            required_radius=3,
            template_x_offset=2,
            template_z_offset=1,
        ),
    ]
)

TEMPLATE_4_BY_2_SILO = tuple(
    [
        ObjectContainer(
            object_type="l2silo",
            team=Team.NEUTRAL,
            required_radius=3,
            y_offset=5.5,
        ),
        ObjectContainer(
            object_type="l2silo",
            team=Team.NEUTRAL,
            required_radius=3,
            template_x_offset=0,
            template_z_offset=1,
        ),
        ObjectContainer(
            object_type="l2silo",
            team=Team.NEUTRAL,
            required_radius=3,
            template_x_offset=1,
            template_z_offset=0,
        ),
        ObjectContainer(
            object_type="l2silo",
            team=Team.NEUTRAL,
            required_radius=3,
            template_x_offset=1,
            template_z_offset=1,
        ),
    ]
)
TEMPLATE_SCRAP_3_OILTANKS = tuple(
    [
        ObjectContainer(
            object_type="l2fueltank",
            team=Team.NEUTRAL,
            required_radius=1,
            y_offset=1.752,
            y_rotation=90,
        ),
        ObjectContainer(
            object_type="l2fueltank",
            team=Team.NEUTRAL,
            required_radius=1,
            template_x_offset=0.5,
            y_rotation=90,
        ),
        ObjectContainer(
            object_type="l2fueltank",
            team=Team.NEUTRAL,
            required_radius=1,
            template_x_offset=1,
            y_rotation=90,
        ),
    ]
)
# END TEMPLATES

### BASE OBJECTS
# COMMON -----------------------------------------
BASE_WALL_GUN = ObjectContainer(
    object_type="AlienTower",
    team=Team.ENEMY,
    required_radius=2,
    attachment_type="WallLaser",
)
BASE_LIGHTNING_GUN = ObjectContainer(
    object_type="AlienTower",
    team=Team.ENEMY,
    required_radius=2,
    attachment_type="LightningGun",
)
BASE_BLAST_TOWER = ObjectContainer(
    object_type="BlastTower",
    team=Team.ENEMY,
    required_radius=2,
    y_offset=2,
)
# SPECIAL TYPE - PUMP OUTPOST -----------------------------------------
BASE_OIL_PUMP = ObjectContainer(
    object_type="ALIENPUMP",
    team=Team.ENEMY,
    required_radius=1,
)
PUMP_OUTPOST_PRIORITY = {BASE_OIL_PUMP: 1}
PUMP_OUTPOST_ALL = {
    BASE_WALL_GUN: 4,
    BASE_LIGHTNING_GUN: 2,
    BASE_BLAST_TOWER: 3,
    TEMPLATE_ALIEN_AA: 2,
    BASE_OIL_PUMP: 3,
    TEMPLATE_ALIEN_RADAR: 1,
}
# SPECIAL TYPE - BASE -----------------------------------------
BASE_ALIEN_POWER_STORE = ObjectContainer(
    object_type="alienpowerstore",
    team=Team.ENEMY,
    required_radius=2,
    y_offset=3,
)
BASE_GROUND_PROD = ObjectContainer(
    object_type="ALIENGROUNDPROD",
    team=Team.ENEMY,
    required_radius=5,
)
BASE_LARGE_PROD = ObjectContainer(
    object_type="ALIENLARGEPROD",
    team=Team.ENEMY,
    required_radius=6,
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
BASE_PRIORITY1 = {
    TEMPLATE_ALIEN_GROUND_PROD_WITH_UNITS: 6,
    TEMPLATE_ALIEN_AIR_PROD_WITH_UNITS: 6,
    TEMPLATE_ALIEN_LARGE_PROD_WITH_UNITS: 6,
    BASE_COM: 1,
}
BASE_PRIORITY2 = {
    TEMPLATE_ALIEN_ENERGY_POWER_STORE_TRIANGLE: 1,
}
BASE_ALL_OTHER = {
    BASE_WALL_GUN: 8,
    BASE_LIGHTNING_GUN: 8,
    BASE_BLAST_TOWER: 8,
    TEMPLATE_ALIEN_AA: 4,
    BASE_GROUND_PROD: 2,
    BASE_AIR_PROD: 2,
    BASE_LARGE_PROD: 2,
    TEMPLATE_ALIEN_GROUND_PROD_WITH_UNITS: 1,
    TEMPLATE_ALIEN_AIR_PROD_WITH_UNITS: 1,
    BASE_OIL_PUMP: 3,
    BASE_COM: 2,
    TEMPLATE_ALIEN_RADAR: 1,
}


### SCRAP OBJECTS
# common -----------------------------------------
SCRAP_DESTROYED_COPTER = ObjectContainer(
    object_type="Smashedcopter", team=Team.NEUTRAL, required_radius=1, y_offset=2
)
SCRAP_TANKWRECK = ObjectContainer(
    object_type="Tankwreck",
    team=Team.NEUTRAL,
    required_radius=1,
)
SCRAP_TANKWRECK1 = ObjectContainer(
    object_type="tankwreck1",
    team=Team.NEUTRAL,
    required_radius=1,
)
SCRAP_TANKWRECK2 = ObjectContainer(
    object_type="tankwreck2",
    team=Team.NEUTRAL,
    required_radius=1,
)
SCRAP_L2FUELTANK = ObjectContainer(
    object_type="l2fueltank",
    team=Team.NEUTRAL,
    required_radius=1,
    y_offset=1.752,
)
SCRAP_L2FUELSILO = ObjectContainer(
    object_type="l2silo",
    team=Team.NEUTRAL,
    required_radius=1,
    y_offset=5.5,
)
# SPECIAL - destroyed base ----------------------------------------------------------------------------------
SCRAP_L1SCAVBENTPIPE = ObjectContainer(
    object_type="l1scavbentpipe", team=Team.NEUTRAL, required_radius=1, y_offset=2
)
SCRAP_L1SCAVHOLEPIPE = ObjectContainer(
    object_type="l1scavholepipe", team=Team.NEUTRAL, required_radius=1, y_offset=2
)
SCRAP_L1SCAVBENTBACKGUN = ObjectContainer(
    object_type="l1scavbentbackgun", team=Team.NEUTRAL, required_radius=1, y_offset=2
)
SCRAP_L1SCAVBENTGUN = ObjectContainer(
    object_type="l1scavgunbroken02", team=Team.NEUTRAL, required_radius=1, y_offset=2
)
GENERIC_DESTROYED_GROUND_PROD = ObjectContainer(
    object_type="Smashedgroundprod", team=Team.NEUTRAL, required_radius=3, y_offset=2
)
GENERIC_DESTROYED_STORE = ObjectContainer(
    object_type="Smashedstore", team=Team.NEUTRAL, required_radius=1, y_offset=2
)
GENERIC_DESTROYED_WALL = ObjectContainer(
    object_type="Smashedwall", team=Team.NEUTRAL, required_radius=1, y_offset=2
)
DESTROYED_BASE_PRIORITY = {
    GENERIC_DESTROYED_GROUND_PROD: 5,
    GENERIC_DESTROYED_STORE: 1,
    GENERIC_DESTROYED_WALL: 1,
}
SCRAP_DESTROYED_BASE = {
    SCRAP_L1SCAVBENTPIPE: 5,
    SCRAP_L1SCAVHOLEPIPE: 5,
    SCRAP_L1SCAVBENTBACKGUN: 1,
    SCRAP_L1SCAVBENTGUN: 1,
    SCRAP_DESTROYED_COPTER: 1,
    SCRAP_TANKWRECK: 1,
    SCRAP_TANKWRECK1: 1,
    SCRAP_TANKWRECK2: 1,
    GENERIC_DESTROYED_STORE: 1,
}
# SPECIAL - tank/chopperbattle -----------------------------------------
SCRAP_BATTLE = {
    SCRAP_TANKWRECK: 1,
    SCRAP_TANKWRECK1: 1,
    SCRAP_TANKWRECK2: 1,
    SCRAP_DESTROYED_COPTER: 1,
}
# SPECIAL - weapon crate (special ars logic)-----------------------------------------
SCRAP_WEAPON_CRATE = ObjectContainer(
    object_type="recharge_crate",
    team=Team.NEUTRAL,
    required_radius=1,
)
SMALL_BOX = ObjectContainer(
    object_type="l6box",
    team=Team.NEUTRAL,
    required_radius=1,
)
GREEN_BOX = ObjectContainer(
    object_type="crate_green",
    team=Team.NEUTRAL,
    required_radius=1,
)
SCRAP_TRUCK = ObjectContainer(
    object_type="l3truck",
    team=Team.NEUTRAL,
    required_radius=1,
)
WEAPON_CRATE_SCRAP_PRIORITY = {
    SCRAP_WEAPON_CRATE: 1,
}
WEAPON_CRATE_SCRAP_OTHERS = {
    SMALL_BOX: 4,
    GREEN_BOX: 8,
    SCRAP_TRUCK: 1,
}
# SPECIAL - scrap fuel tanks -----------------------------------------
SCRAP_FUEL_TANKS = {
    TEMPLATE_6_BY_2_SILO: 2,
    TEMPLATE_4_BY_2_SILO: 2,
    TEMPLATE_SCRAP_3_OILTANKS: 2,
    SCRAP_L2FUELTANK: 1,
    SCRAP_L2FUELSILO: 1,
}
