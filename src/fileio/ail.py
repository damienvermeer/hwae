"""
HWAE (Hostile Waters Antaeus Eternal)

fileio.ail

Contains all info to read and write HWAR's .ail (area/location) file type
"""

from dataclasses import dataclass, field
from src.logger import get_logger

logger = get_logger()
import os
from typing import List, Tuple


@dataclass
class AreaRecord:
    """Container for an area record with a name and bounding box coordinates"""

    name: str
    # Bounding box coordinates as (left, top, right, bottom)
    bounding_box: Tuple[int, int, int, int] = field(
        default_factory=lambda: (0, 0, 0, 0)
    )


@dataclass
class AilFile:
    """Container for an AIL (area/location) file"""

    full_file_path: str
    area_records: List[AreaRecord] = field(default_factory=list)

    def __post_init__(self):
        """Read the specified file and set the internal data"""
        if os.path.exists(self.full_file_path):
            with open(self.full_file_path, "r") as f:
                data = f.read()

            # Parse the data
            self._parse_ail_data(data)

    def _parse_ail_data(self, data: str) -> None:
        """Parse the area/location file data into area records

        Args:
            data (str): The raw file data to parse
        """
        current_record = None
        line_count = 0
        section_line_count = 0

        # Parse the data
        for line in data.splitlines():
            line = line.strip()
            line_count += 1

            # Skip empty lines
            if not line:
                continue

            if line == "[Section]":
                # New section found, reset section line counter
                section_line_count = 0
            elif section_line_count == 0:
                # This is the area name line (first line after [Section])
                current_record = AreaRecord(name=line)
                self.area_records.append(current_record)
                section_line_count += 1
            elif section_line_count == 1 and current_record is not None:
                # This is the bounding box line (second line after [Section])
                try:
                    coords = [int(c.strip()) for c in line.split(",")]
                    if len(coords) == 4:
                        current_record.bounding_box = (
                            coords[0],
                            coords[1],
                            coords[2],
                            coords[3],
                        )
                    else:
                        logger.warning(
                            f"Invalid bounding box format in line {line_count}: {line}"
                        )
                except ValueError:
                    logger.warning(
                        f"Invalid bounding box format in line {line_count}: {line}"
                    )
                section_line_count += 1

    def __getitem__(self, name: str) -> AreaRecord:
        """Gets an area record by name

        Args:
            name (str): Name of the area record to get

        Returns:
            AreaRecord: The area record with the specified name

        Raises:
            KeyError: If the area record doesn't exist
        """
        for record in self.area_records:
            if record.name == name:
                return record
        raise KeyError(f"Area record '{name}' not found")

    def add_area_record(
        self, name: str, bounding_box: Tuple[int, int, int, int] = None
    ) -> AreaRecord:
        """Add a new area record

        Args:
            name (str): Name for the area record
            bounding_box (Tuple[int, int, int, int], optional): Bounding box coordinates (left, top, right, bottom).
                                                               Defaults to (0, 0, 0, 0).

        Returns:
            AreaRecord: The newly created area record
        """
        if bounding_box is None:
            bounding_box = (0, 0, 0, 0)

        # Check if record with this name already exists
        try:
            existing_record = self[name]
            # If it exists, update its bounding box
            existing_record.bounding_box = bounding_box
            return existing_record
        except KeyError:
            # Create new record if it doesn't exist
            new_record = AreaRecord(name=name, bounding_box=bounding_box)
            self.area_records.append(new_record)
            return new_record

    def __str__(self) -> str:
        """Returns the entire area/location data as a string

        Returns:
            str: Area/location data as a string
        """
        return_data = ""

        for record in self.area_records:
            # Write section header
            return_data += "[Section]\n"
            # Write area name
            return_data += f"{record.name}\n"
            # Write bounding box coordinates
            bbox = record.bounding_box
            return_data += f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}\n"
            # Add blank line between sections (optional)
            return_data += "\n"

        return return_data

    def save(self, save_in_folder: str, file_name: str) -> None:
        """Saves the AIL file to the specified path

        Args:
            save_in_folder (str): Location to save the file to
            file_name (str): Name of the file to save as
        """
        if not file_name.endswith(".ail"):
            file_name += ".ail"
        logger.info(f"Saving AIL file to: {save_in_folder}/{file_name}")

        # Create output path and ensure directory exists
        output_path = os.path.join(save_in_folder, file_name)
        os.makedirs(save_in_folder, exist_ok=True)

        # Write the file
        with open(output_path, "w") as f:
            f.write(self.__str__())
