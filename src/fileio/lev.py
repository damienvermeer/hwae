"""
HWAE (Hostile Waters Antaeus Eternal)

fileio.lev

Contains all info to read and write HWAR's .lev file type
"""

import struct
from dataclasses import dataclass, field
from typing import List
from pathlib import Path
from src.logger import get_logger

logger = get_logger()


LEV_HEADER_STRUCT = "<LLLLffLLLLLL"
LEV_TERRAIN_POINT_STRUCT = "<fHHBBBBBBBB"


@dataclass
class _LevHeader:
    """Container class for the header of a LEV file"""

    four_cc: int
    terrain_point_data_offset: int
    width: int
    length: int
    highest_point: float
    lowest_point: float
    object_list_offset: int
    model_list_offset: int
    extra_model_list_offset: int
    land_palette_offset: int
    level_config_offset: int
    end_of_last_bit: int

    def pack(self) -> bytes:
        """Pack header into bytes"""
        return struct.pack(
            LEV_HEADER_STRUCT,
            self.four_cc,
            self.terrain_point_data_offset,
            self.width,
            self.length,
            self.highest_point,
            self.lowest_point,
            self.object_list_offset,
            self.model_list_offset,
            self.extra_model_list_offset,
            self.land_palette_offset,
            self.level_config_offset,
            self.end_of_last_bit,
        )


@dataclass
class _LevTerrainPoint:
    """Container class for a terrain point"""

    height: float
    normal: int
    flags: int = 0
    palette_index: int = 0
    flow_direction: int = 0
    strata_index: int = 0
    mat: int = 0
    texture_dir: int = 0
    u_off: int = 0
    v_off: int = 0
    ai_node_type: int = 0

    def pack(self) -> bytes:
        """Pack terrain point into bytes"""
        return struct.pack(
            LEV_TERRAIN_POINT_STRUCT,
            self.height,
            self.normal,
            self.flags,
            self.palette_index,
            self.flow_direction,
            self.strata_index,
            self.mat,
            self.texture_dir,
            self.u_off,
            self.v_off,
            self.ai_node_type,
        )


@dataclass
class _Color:
    """RGB color data"""

    x: float
    y: float
    z: float

    def pack(self) -> bytes:
        """Pack color into bytes"""
        return struct.pack("<fff", self.x, self.y, self.z)


@dataclass
class LevFile:
    """Container for a LEV file"""

    full_file_path: str
    header: _LevHeader = None
    terrain_points: List[_LevTerrainPoint] = field(default_factory=list)
    object_data: bytes = b""
    model_data: bytes = b""
    colours: List[_Color] = field(default_factory=list)
    config_data: bytes = b""

    def __post_init__(self):
        """Read the specified file and set the internal data"""
        # Initialize default values
        self.data = b""
        
        if not self.full_file_path or not Path(self.full_file_path).exists():
            logger.warning(f"LEV file not found or empty path: {self.full_file_path}")
            return
            
        logger.info(f"Initializing LEV file from: {self.full_file_path}")
        # get the data
        with open(self.full_file_path, "rb") as f:
            self.data = f.read()
        logger.info(f"Read {len(self.data)} bytes from file")

        # parse the header - currently assumes all file types are LEVEL1_4CC
        header_data_raw = self.data[: struct.calcsize(LEV_HEADER_STRUCT)]
        self.header = _LevHeader(*struct.unpack(LEV_HEADER_STRUCT, header_data_raw))
        logger.info("Parsed LEV file header")

        # now we need to load in the terrain data itself
        terrain_start = struct.calcsize(LEV_HEADER_STRUCT)
        terrain_end = self.header.object_list_offset
        terrain_data = self.data[terrain_start:terrain_end]
        self.terrain_points = []
        for i in range(0, len(terrain_data), struct.calcsize(LEV_TERRAIN_POINT_STRUCT)):
            point_data = terrain_data[i : i + struct.calcsize(LEV_TERRAIN_POINT_STRUCT)]
            self.terrain_points.append(
                _LevTerrainPoint(*struct.unpack(LEV_TERRAIN_POINT_STRUCT, point_data))
            )
        logger.info(f"Loaded {len(self.terrain_points)} terrain points")

        # import the object list data
        self.object_data = self.data[
            self.header.object_list_offset : self.header.model_list_offset
        ]
        logger.info(f"Loaded {len(self.object_data)} bytes of object data")

        # import the model list data
        if self.header.model_list_offset != 0 and self.header.land_palette_offset != 0:
            self.model_data = self.data[
                self.header.model_list_offset : self.header.land_palette_offset
            ]
            logger.info(f"Loaded {len(self.model_data)} bytes of model data")
        else:
            self.model_data = b""
            logger.info("No model data present (offsets are 0)")

        # Load color palette data
        if (
            self.header.land_palette_offset != 0
            and self.header.level_config_offset != 0
        ):
            color_data = self.data[
                self.header.land_palette_offset : self.header.level_config_offset
            ]
            color_size = struct.calcsize("<fff")
            for i in range(0, len(color_data), color_size):
                color_bytes = color_data[i : i + color_size]
                x, y, z = struct.unpack("<fff", color_bytes)
                self.colours.append(_Color(x, y, z))
            logger.info(f"Loaded {len(self.colours)} colors from palette")
        else:
            logger.info("No color palette data present")

        # import the config data
        self.config_data = self.data[
            self.header.level_config_offset : self.header.end_of_last_bit
        ]
        logger.info(f"Loaded {len(self.config_data)} bytes of config data")

    def save(self, save_in_folder: str, file_name: str) -> None:
        """Saves the LEV file to the specified path, using the data stored
        in this instance

        Args:
            save_in_folder (str): Location to save the file to
            file_name (str): Name of the file to save as
        """
        if not file_name.lower().endswith(".lev"):
            file_name += ".lev"
        logger.info(f"Saving LEV file to: {save_in_folder}/{file_name}")

        # Calculate initial offset after header
        offset = struct.calcsize(LEV_HEADER_STRUCT)

        # Add terrain points size
        terrain_size = struct.calcsize(LEV_TERRAIN_POINT_STRUCT) * len(
            self.terrain_points
        )
        self.header.object_list_offset = offset + terrain_size
        offset = self.header.object_list_offset

        # Add object data size
        self.header.model_list_offset = offset + len(self.object_data)
        offset = self.header.model_list_offset

        # Add model data size
        self.header.land_palette_offset = offset + len(self.model_data)
        offset = self.header.land_palette_offset

        # Add color palette size
        color_size = struct.calcsize("<fff") * len(self.colours)
        self.header.level_config_offset = offset + color_size
        offset = self.header.level_config_offset

        # Add config data size
        self.header.end_of_last_bit = offset + len(self.config_data)

        # Create output path and ensure directory exists
        output_path = Path(save_in_folder) / file_name
        Path(save_in_folder).mkdir(parents=True, exist_ok=True)

        # Check if file exists
        if Path(output_path).exists():
            logger.warning(f"File {output_path} already exists, overwriting")

        # open the file in the location
        with open(output_path, "wb") as f:
            # pack and write the header
            f.write(self.header.pack())
            logger.info("Wrote header")

            # pack and write the terrain points
            f.write(b"".join(point.pack() for point in self.terrain_points))
            logger.info(f"Wrote {len(self.terrain_points)} terrain points")

            # write the object data
            f.write(self.object_data)
            logger.info(f"Wrote {len(self.object_data)} bytes of object data")

            # write the model data
            f.write(self.model_data)
            logger.info(f"Wrote {len(self.model_data)} bytes of model data")

            # write the color palette
            for color in self.colours:
                f.write(color.pack())
            logger.info(f"Wrote {len(self.colours)} colors to palette")

            # write the config data
            f.write(self.config_data)
            logger.info(f"Wrote {len(self.config_data)} bytes of config data")

        logger.info(f"Successfully saved LEV file to: {output_path}")
