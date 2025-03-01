"""
HWAE (Hostile Waters Antaeus Eternal)

fileio.cfg

Contains all info to read and write HWAR's .cfg file type
"""

from dataclasses import dataclass
from src.logger import get_logger

logger = get_logger()
import os
import time


@dataclass
class _CfgRecord:
    """Container for a CFG file record - so we can maintain order,
    just in case HWAR expects a certain CFG section order"""

    section: str
    value: list[str]


@dataclass
class CfgFile:
    """Container for a CFG file"""

    full_file_path: str

    def __post_init__(self):
        """Read the specified file and set the internal data"""
        with open(self.full_file_path, "r") as f:
            data = f.read()
        # split into lines, then split into section headers and
        # ... make a dict
        self.records = []
        current_record = None

        # Parse the data
        for line in data.splitlines():
            line = line.strip()
            # strip comments and whitespace
            if ";" in line:
                line = line.split(";")[0].strip()
            if not line:
                continue

            if line.startswith("["):
                # New section found, create a new record
                if current_record is not None:
                    self.records.append(current_record)
                current_record = _CfgRecord(line.strip("[]"), [])
            elif current_record is not None:
                # Add content to current section
                current_record.value.append(line)

        # Don't forget to add the last record
        if current_record is not None:
            self.records.append(current_record)

    def __getitem__(self, section: str) -> str:
        """Gets a section value using dictionary style access

        Args:
            section (str): Section name to get

        Returns:
            str: The joined value of the section

        Raises:
            KeyError: If the section doesn't exist
        """
        for record in self.records:
            if record.section == section:
                return record.value
        raise KeyError(f"Section '{section}' not found")

    def __setitem__(self, section: str, value: str | list[str]) -> None:
        """Sets a section value using dictionary style access

        Args:
            section (str): Section name to set
            value (str | list[str]): Value to set. Can be either a string (which will be split into lines if it contains newlines)
                                    or a list of strings.
        """
        # Convert value to list of lines
        if isinstance(value, str):
            value_lines = value.split("\n")
        elif isinstance(value, list):
            value_lines = value
        else:
            value_lines = [str(value)]

        # remove comment lines
        value_lines = [line for line in value_lines if not line.strip().startswith(";")]

        # Try to find and update existing section
        for record in self.records:
            if record.section == section:
                record.value = value_lines
                return

        # Section doesn't exist, append new one
        self.records.append(_CfgRecord(section, value_lines))

    def __str__(self) -> str:
        """Returns the entire config data as a string

        Returns:
            str: Config data as a string
        """
        # create header
        return_data = f";Created by HWAE at {time.strftime('%d\\%m\\%Y (%H:%M)')}\n"
        for record in self.records:
            # Write section header
            return_data += f"[{record.section}]\n"
            # Write section values
            for value in record.value:
                return_data += f"{value}\n"
            # Add blank line between sections
            return_data += "\n"
        return return_data

    def save(self, save_in_folder: str, file_name: str) -> None:
        """Saves the CFG file to the specified path, using the data stored
        in this instance

        Args:
            save_in_folder (str): Location to save the file to
            file_name (str): Name of the file to save as
        """
        if not file_name.endswith(".cfg"):
            file_name += ".cfg"
        logger.info(f"Saving CFG file to: {save_in_folder}/{file_name}")

        # Create output path and ensure directory exists
        output_path = os.path.join(save_in_folder, file_name)
        os.makedirs(save_in_folder, exist_ok=True)

        # Write the file
        with open(output_path, "w") as f:
            # Add header comment with timestamp
            f.write(self.__str__())
