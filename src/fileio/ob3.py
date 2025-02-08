"""
HWAE (Hostile Waters Antaeus Eternal)

fileio.ob3

Contains all info to read and write HWAR's .ob3 file type
"""

import struct
from dataclasses import dataclass, field
import logging
import os
import numpy as np
from typing import List

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
    object_type: bytes = b""
    attachment_type: bytes = b""
    # rotation matrix
    r1_a: float = 0.0
    r1_b: float = 0.0
    r1_c: float = 0.0
    r2_a: float = 0.0
    r2_b: float = 0.0
    r2_c: float = 0.0
    r3_a: float = 0.0
    r3_b: float = 0.0
    r3_c: float = 0.0
    # location floats
    _loc_x: float = 0.0
    _loc_y: float = 0.0
    _loc_z: float = 0.0
    normal: float = 0.0
    renderable_id: int = 0
    controllable_id: int = 0
    shadow_flags: int = 0
    permanent_flag: int = 0
    team_number: int = 0
    extra_data: bytes = b""
    my_id: int = 0

    def __post_init__(self) -> None:
        """Post constructor - clean up some of the info we dumped into the constructor"""
        # make nice rotation matrix
        self.rotation_matrix = np.array(
            [
                [self.r1_a, self.r1_b, self.r1_c],
                [self.r2_a, self.r2_b, self.r2_c],
                [self.r3_a, self.r3_b, self.r3_c],
            ]
        )
        # convert from silly units to nice x y z units
        self._loc_x /= MAP_SCALER
        self._loc_y /= MAP_SCALER
        self._loc_z /= MAP_SCALER
        # make location vector
        self.location = np.array([self._loc_x, self._loc_y, self._loc_z])
        # remove null bytes, strip and convert to string
        self.object_type = self.object_type.rstrip(b"\x00").decode("ascii")
        self.attachment_type = self.attachment_type.rstrip(b"\x00").decode("ascii")
        # normal is bool, but seems to being stored as a float. TODO do we convert?

    def pack(self) -> bytes:
        """Pack object into bytes for saving back to OB3"""
        # extract rotation matrix back into r1_a r1_b etc
        for i, row in enumerate(["r1", "r2", "r3"]):
            for j, col in enumerate(["a", "b", "c"]):
                setattr(self, f"{row}_{col}", self.rotation_matrix[i][j])
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
        """Load objects from ob3 file"""

        with open(self.full_file_path, "rb") as f:
            # Read OBJC header and discard
            f.read(4).decode("ascii")

            # Read number of objects
            num_objects = struct.unpack("<I", f.read(4))[0]
            logging.info(f"OB3 Read: Expecting {num_objects} objects")

            # start reading objects
            for object_id in range(num_objects):
                # read the next 4 bytes, this is the length of the object
                length_of_object_size = struct.unpack("<I", f.read(4))[0]
                # calculate the addon 'extra' size (we dont currently support addons)
                # ... so this goes into the pad bytes below
                extra_data_size = length_of_object_size - 140
                # unpack directly into the _OB3Object() constructor
                self.objects.append(
                    _OB3Object(
                        length_of_object_size,
                        *struct.unpack(
                            f"{OBJECT_DESC_FIXED_SECTION_STRUCT}{extra_data_size:.0f}x",
                            f.read(length_of_object_size - 4),
                        ),
                        # dont bother reading object id from struct - its 0 indexed
                        # ... so just use the value from the loop
                        object_id,
                    )
                )
            logging.info(
                f"OB3 Read: Finished reading - found {len(self.objects)} objects"
            )

    def save(self, save_in_folder: str, file_name: str) -> None:
        """Save objects to file

        Args:
            save_in_folder (str): Location to save the file to
            file_name (str): Name of the file to save as
        """
        # Ensure file has correct extension
        if not file_name.endswith(".ob3"):
            file_name += ".ob3"
        logging.info(f"Saving OB3 file to: {save_in_folder}/{file_name}")

        # Create output path and ensure directory exists
        output_path = os.path.join(save_in_folder, file_name)
        os.makedirs(save_in_folder, exist_ok=True)

        # Delete the file if it already exists
        if os.path.exists(output_path):
            os.remove(output_path)
            logging.info(f"Deleted existing file: {output_path}")

        # Open the file and write data
        with open(output_path, "wb") as f:
            # Write header
            f.write(b"OBJC")  # Magic number
            f.write(struct.pack("<I", len(self.objects)))  # Number of entries
            logging.info(f"Wrote header with {len(self.objects)} objects")

            # Write each object
            for obj in self.objects:
                f.write(obj.pack())

            logging.info(f"Successfully wrote {len(self.objects)} objects")

        logging.info(f"Successfully saved OB3 file to: {output_path}")
