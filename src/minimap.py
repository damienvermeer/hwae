"""Functions for generating the minimap (map.pcx) file"""

from PIL import Image
from fileio import cfg
from terrain import TerrainHandler
from fileio.cfg import CfgFile
import copy
from pathlib import Path
import numpy as np


def generate_minimap(
    terrain_data: TerrainHandler, cfg_interface: CfgFile, save_location: str
) -> None:
    """
    Generates a minimap from a terrain handler and config file.
    Downsamples terrain data, creates a minimap, and saves it as a PCX image,
    preserving the original PCX file's format (palette, etc.).

    Args:
        terrain_data (TerrainHandler): Data about the terrain
        cfg_interface (CfgFile): Interface to the config file
        save_location (str): Location to save the minimap
    """
    # Step 1 - down/upsample the 2D terrain data from its current size to 128x128
    original_terrain = copy.deepcopy(terrain_data.terrain_points).reshape(
        terrain_data.width, terrain_data.length
    )
    # downsampling
    stride_x = terrain_data.width // 128
    stride_z = terrain_data.length // 128
    reshaped_terrain = original_terrain[::stride_x, ::stride_z]
    # check for bad rounding etc
    if reshaped_terrain.shape[0] > 128 or reshaped_terrain.shape[1] > 128:
        reshaped_terrain = reshaped_terrain[:128, :128]

    # Step 2 - generate a texture lookup list from the config file
    minimap_texture_lookup = get_texture_lookup_list(cfg_interface)

    # Step 3 - using the terrain dimensions, generate a 2D array of the same size
    # ... and apply the average colour of the terrain at that position
    minimap = np.zeros((128, 128, 3), dtype=np.uint8)  # 3 for RGB channels
    for row_id in range(128):
        for col_id in range(128):
            # use the material of this pixel to get the colour, and apply
            # ... to the minimap
            applied_texture = reshaped_terrain[row_id, col_id].mat
            minimap[row_id, col_id] = minimap_texture_lookup[applied_texture]

    # Step 4 - apply water with blue colour for now
    minimap[
        np.array([[point.height for point in row] for row in reshaped_terrain]) < 0
    ] = (66, 156, 181)

    # Step 5 - load template map file, apply palette and save
    minimap_img = Image.fromarray(minimap)
    template_map = Path(__file__).resolve().parent / "assets" / "map.pcx"
    with Image.open(template_map) as img:
        # load from array
        minimap_img = minimap_img.convert("RGB").quantize(palette=img)
    # mirror the minimap horizontally
    minimap_img = minimap_img.transpose(Image.FLIP_TOP_BOTTOM)
    # save the minimap as a PCX file
    minimap_img.save(save_location)


def get_texture_lookup_list(cfg_interface: CfgFile) -> list:
    """Parses the config file and generates a lookup list, of
    average colour for each texture present in the cfg file

    Args:
        cfg_interface (CfgFile): Interface to the config file

    Returns:
        list: List of tuples, where each tuple is (r, g, b)
    """
    minimap_texture_lookup = []
    for line in cfg_interface.get("Land Textures").split("\n"):
        # chop off everything after the first space in the line
        fname = line.split(" ")[0]
        texture_file_path = (
            Path(__file__).resolve().parent / "assets" / "textures" / fname
        )
        with Image.open(texture_file_path) as img:
            # load all pixels and calculate the average colour
            img = img.convert("RGB")  # Convert to RGB mode
            pixels = img.getdata()
            total_r, total_g, total_b = map(sum, zip(*pixels))
            count = img.width * img.height
            avg_r = total_r / count
            avg_g = total_g / count
            avg_b = total_b / count
            minimap_texture_lookup.append((avg_r, avg_g, avg_b))
    return minimap_texture_lookup
