"""
HWAE (Hostile Waters Antaeus Eternal)

fileio.ob3

Contains all info to read and write HWAR's .ob3 file type
"""

import struct
from dataclasses import dataclass, field
from src.logger import get_logger
from pathlib import Path
import numpy as np
from typing import List, Union

logger = get_logger()

# NOTE: the 'f' after '12f' should be a bool (1 byte) - but seems to be a
# ... float in several levels. I'm not even sure what this float/bool is for?
OBJECT_DESC_FIXED_SECTION_STRUCT = "32s32s12ff5I"
# There seems to be a difference in units between ob3 and lev - for some reason
# ... this conversion factor will mean once loaded into python, the ob3 and lev
# ... units are the same
MAP_SCALER = 51.2


@dataclass
class _OB3Object:
    """Represents an object present in the ob3 file."""

    object_size_in_bytes: int = 148
    object_type: Union[bytes, str] = b""
    attachment_type: Union[bytes, str] = b""
    # rotation matrix (default to identity 3x3 matrix)
    r1_a: float = 1.0
    r1_b: float = 0.0
    r1_c: float = 0.0
    r2_a: float = 0.0
    r2_b: float = 1.0
    r2_c: float = 0.0
    r3_a: float = 0.0
    r3_b: float = 0.0
    r3_c: float = 1.0
    # location floats
    _loc_x: float = 0.0
    _loc_y: float = 0.0
    _loc_z: float = 0.0
    normal: float = 1.0  # no idea what this is for
    # other info
    renderable_id: int = -1  # not sure what for, default 0 - but if -1 set to my id
    controllable_id: int = 0
    shadow_flags: int = 139  # not sure what this means
    permanent_flag: int = 1  # not sure what this means
    team_number: int = 0
    extra_data: bytes = b""
    my_id: int = 0

    def __post_init__(self) -> None:
        """Post constructor - clean up some of the info we dumped into the constructor"""
        # actions here are ONLY required when loading from ob3 file
        # convert from silly units to nice x y z units
        self._loc_x /= MAP_SCALER
        self._loc_y /= MAP_SCALER
        self._loc_z /= MAP_SCALER
        # check if the object and attachment types are bytes, if so, decode
        # ... remove null bytes, strip and convert to string
        if isinstance(self.object_type, bytes):
            self.object_type = self.object_type.rstrip(b"\x00").decode("ascii")
        if isinstance(self.attachment_type, bytes):
            self.attachment_type = self.attachment_type.rstrip(b"\x00").decode("ascii")
        # complete other steps
        self.clean_object()

    def set_yaxis_rotation(self, deg: float) -> None:
        """Sets this object to a rotation around the y axis of 'deg' degrees

        Args:
            deg (float): Angle of rotation in degrees
        """
        if deg == 0:
            return  # no rotation
        c = np.cos(np.radians(deg))
        s = np.sin(np.radians(deg))
        # Set rotation matrix components for Y-axis rotation
        self.r1_a = c
        self.r1_b = 0
        self.r1_c = -s
        self.r2_a = 0
        self.r2_b = 1
        self.r2_c = 0
        self.r3_a = s
        self.r3_b = 0
        self.r3_c = c

    def clean_object(self) -> None:
        """Completes post-creation steps (create location vector, rotation matrix, etc.)

        Required to be re-triggered only if creating an object from scratch
        """
        # make location vector
        self.location = np.array([self._loc_x, self._loc_y, self._loc_z])
        # make nice rotation matrix
        self._rotation_matrix = np.array(
            [
                [self.r1_a, self.r1_b, self.r1_c],
                [self.r2_a, self.r2_b, self.r2_c],
                [self.r3_a, self.r3_b, self.r3_c],
            ]
        )
        # check if renderable_id is -1 - this means set it the same as my_id
        if self.renderable_id == -1:
            self.renderable_id = self.my_id

    def pack(self) -> bytes:
        """Pack object into bytes for saving back to OB3"""
        # extract rotation matrix back into r1_a r1_b etc
        for i, row in enumerate(["r1", "r2", "r3"]):
            for j, col in enumerate(["a", "b", "c"]):
                setattr(self, f"{row}_{col}", self._rotation_matrix[i][j])
        # and same for location
        self._loc_x = self.location[0]
        self._loc_y = self.location[1]
        self._loc_z = self.location[2]

        # Pack the data - note we need to provide all 8 padding bytes individually
        return struct.pack(
            f"<I{OBJECT_DESC_FIXED_SECTION_STRUCT}8B",
            self.object_size_in_bytes,
            # Convert type name and attachment name to bytes and pad to 32 bytes
            self.object_type.encode("ascii")[:32].ljust(32, b"\x00"),
            self.attachment_type.encode("ascii")[:32].ljust(32, b"\x00"),
            self.r1_a,
            self.r1_b,
            self.r1_c,
            self.r2_a,
            self.r2_b,
            self.r2_c,
            self.r3_a,
            self.r3_b,
            self.r3_c,
            self._loc_x * MAP_SCALER,
            self._loc_y * MAP_SCALER,
            self._loc_z * MAP_SCALER,
            self.normal,
            self.renderable_id,
            self.controllable_id,
            self.shadow_flags,
            self.permanent_flag,
            self.team_number,
            # (addons are here, but we dont yet support them) so -> 8 padding bytes
            *bytes(8),
        )


@dataclass
class Ob3File:
    """Container for an OB3 file"""

    full_file_path: str
    objects: List[_OB3Object] = field(default_factory=list)

    def __post_init__(self):
        """Load objects from ob3 file if one exists, if path
        is blank then create one from scratch"""
        if not self.full_file_path or not Path(self.full_file_path).exists():
            # nothing special requried to create a container ob3 file,
            # ... its just an empty list of objects
            logger.info("OB3: Created empty container")
            return

        with open(self.full_file_path, "rb") as f:
            # Read OBJC header and discard
            f.read(4).decode("ascii")

            # Read number of objects
            num_objects = struct.unpack("<I", f.read(4))[0]
            logger.info(f"OB3 Read: Expecting {num_objects} objects")

            # start reading objects
            for object_id in range(num_objects):
                # read the next 4 bytes, this is the length of the object
                length_of_object_size = struct.unpack("<I", f.read(4))[0]
                # calculate the addon 'extra' size (we dont currently support addons)
                # ... so this goes into the pad bytes below
                extra_data_size = length_of_object_size - 140
                # create the list of args from the data
                all_args = (
                    length_of_object_size,
                    *struct.unpack(
                        f"{OBJECT_DESC_FIXED_SECTION_STRUCT}{extra_data_size:.0f}x",
                        f.read(length_of_object_size - 4),
                    ),
                    # dont bother reading object id from struct - its 0 indexed
                    # ... so just use the value from the loop
                    object_id,
                )
                # and add the object
                self.objects.append(_OB3Object(*all_args))
            logger.info(
                f"OB3 Read: Finished reading - found {len(self.objects)} objects"
            )

    def add_object(
        self,
        object_type: str,
        location: np.array,
        attachment_type: str = "",
        team: int = 1,
        y_rotation: float = 0,
    ) -> int:
        """Add a new object to the OB3 file.

        Args:
            object_type (str): Type of the object
            location (tuple): Location of the object
            attachment_type (str): Type of attachment
            team (int): Team number (0=player, 1+=enemy, 0xFFFF=neutral)
            y_rotation (float): Rotation of the object in degrees

        Returns:
            int: The ID of the new object
        """
        # create a new _OB3Object with its default values
        new_obj = _OB3Object()
        # set the object type and location
        new_obj.object_type = object_type
        # NOTE: LEV vs OB3 has different scales. In OB3, the x and z values are
        # ... in 10x10 units, while in LEV they are 1x1 units.
        # NOTE in OB3, the x and z axis are swapped
        new_obj._loc_x = location[2] * 10
        new_obj._loc_y = location[1]
        new_obj._loc_z = location[0] * 10
        # set attachment type and team
        new_obj.attachment_type = attachment_type
        new_obj.team_number = team
        new_obj.controllable_id = team == 0  # only controllable if on my team
        # set its id, which is the next available id
        # changed from 0 indexed to 1 indexed (ars is 1 indexed)
        new_obj.my_id = new_obj.renderable_id = len(self.objects) + 1
        # apply rotation
        new_obj.set_yaxis_rotation(y_rotation)
        # call clean object (to set location values etc)
        new_obj.clean_object()
        self.objects.append(new_obj)
        logger.info(f"Added new object of type '{object_type}' with ID {new_obj.my_id}")
        return new_obj.my_id

    def save(self, save_in_folder: str, file_name: str) -> None:
        """Save objects to file

        Args:
            save_in_folder (str): Location to save the file to
            file_name (str): Name of the file to save as
        """
        # Ensure file has correct extension
        if not file_name.lower().endswith(".ob3"):
            file_name += ".ob3"
        logger.info(f"Saving OB3 file to: {save_in_folder}/{file_name}")

        # Create output path and ensure directory exists
        output_path = Path(save_in_folder) / file_name
        Path(save_in_folder).mkdir(parents=True, exist_ok=True)

        # Check if file exists
        if Path(output_path).exists():
            logger.warning(f"File {output_path} already exists, overwriting")

        # Write the file
        with open(output_path, "wb") as f:
            # Write header
            f.write(b"OBJC")  # Magic number
            f.write(struct.pack("<I", len(self.objects)))  # Number of entries
            logger.info(f"Wrote header with {len(self.objects)} objects")

            # Write each object
            for obj in self.objects:
                f.write(obj.pack())

            logger.info(f"Successfully wrote {len(self.objects)} objects")

        logger.info(f"Successfully saved OB3 file to: {output_path}")
