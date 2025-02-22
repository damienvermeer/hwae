"""
HWAE (Hostile Waters Antaeus Eternal)

src.object_templates

This module contains templates for object placement (e.g. for placing groups of
alien AA guns, or groups of scrap/salvage)
"""

from src.enums import Team
from src.object_containers import ObjectContainer

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
