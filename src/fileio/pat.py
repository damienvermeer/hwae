"""
HWAE (Hostile Waters Antaeus Eternal)

fileio.pat

Contains all info to read and write HWAR's .pat (patrol) file type
"""

from dataclasses import dataclass, field
from src.logger import get_logger
from pathlib import Path
import re
import time
from typing import List, Tuple

logger = get_logger()
from src.fileio.ob3 import MAP_SCALER


@dataclass
class PatrolRecord:
    """Container for a patrol record with a title and list of coordinates"""

    title: str
    coordinates: List[Tuple[float, float, float]] = field(default_factory=list)

    def __post_init__(self):
        """Check if the coordinates are valid"""
        # apply the scales to the OB3 coordinates
        self.coordinates = [
            (x * 10 * MAP_SCALER, y * MAP_SCALER, z * 10 * MAP_SCALER)
            for x, y, z in self.coordinates
        ]


@dataclass
class PatFile:
    """Container for a PAT (patrol) file"""

    full_file_path: str
    patrol_records: List[PatrolRecord] = field(default_factory=list)

    def __post_init__(self):
        """Read the specified file and set the internal data"""
        if self.full_file_path and Path(self.full_file_path).exists():
            with open(self.full_file_path, "r") as f:
                data = f.read()

            # Parse the data
            self._parse_pat_data(data)

    def _parse_pat_data(self, data: str) -> None:
        """Parse the patrol file data into patrol records

        Args:
            data (str): The raw file data to parse
        """
        current_record = None

        # Parse the data
        for line in data.splitlines():
            line = line.strip()
            # Skip empty lines
            if not line:
                continue

            if line.startswith("[") and line.endswith("]"):
                # New section found, create a new patrol record
                title = line.strip("[]")
                current_record = PatrolRecord(title=title)
                self.patrol_records.append(current_record)
            elif current_record is not None and "," in line:
                # Parse coordinate line (x, y, z)
                try:
                    coords = [float(c.strip()) for c in line.split(",")]
                    if len(coords) == 3:
                        current_record.coordinates.append(
                            (coords[0], coords[1], coords[2])
                        )
                except ValueError:
                    logger.warning(f"Invalid coordinate format in line: {line}")

    def __getitem__(self, title: str) -> PatrolRecord:
        """Gets a patrol record by title

        Args:
            title (str): Title of the patrol record to get

        Returns:
            PatrolRecord: The patrol record with the specified title

        Raises:
            KeyError: If the patrol record doesn't exist
        """
        for record in self.patrol_records:
            if record.title == title:
                return record
        raise KeyError(f"Patrol record '{title}' not found")

    def add_patrol_record(
        self, title: str, coordinates: List[Tuple[float, float, float]] = None
    ) -> PatrolRecord:
        """Add a new patrol record

        Args:
            title (str): Title for the patrol record
            coordinates (List[Tuple[float, float, float]], optional): List of coordinate tuples. Defaults to None.

        Returns:
            PatrolRecord: The newly created patrol record
        """
        if coordinates is None:
            coordinates = []

        # Check if record with this title already exists
        try:
            existing_record = self[title]
            # If it exists, update its coordinates
            existing_record.coordinates = coordinates
            return existing_record
        except KeyError:
            # Create new record if it doesn't exist
            new_record = PatrolRecord(title=title, coordinates=coordinates)
            self.patrol_records.append(new_record)
            return new_record

    def __str__(self) -> str:
        """Returns the entire patrol data as a string

        Returns:
            str: Patrol data as a string
        """
        return_data = ""  # dont know if .pat supports headers

        for record in self.patrol_records:
            # Write section header
            return_data += f"[{record.title}]\n"
            # Write coordinates
            for coord in record.coordinates:
                return_data += f"{coord[0]:.4f}, {coord[1]:.4f}, {coord[2]:.4f}\n"
            # Add blank line between sections
            return_data += "\n"

        return return_data

    def save(self, save_in_folder: str, file_name: str) -> None:
        """Saves the PAT file to the specified path

        Args:
            save_in_folder (str): Location to save the file to
            file_name (str): Name of the file to save as
        """
        if not file_name.lower().endswith(".pat"):
            file_name += ".pat"
        logger.info(f"Saving PAT file to: {save_in_folder}/{file_name}")

        # Create output path and ensure directory exists
        output_path = Path(save_in_folder) / file_name
        Path(save_in_folder).mkdir(parents=True, exist_ok=True)

        # Write the file
        with open(output_path, "w") as f:
            f.write(self.__str__())
