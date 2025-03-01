"""
HWAE (Hostile Waters Antaeus Eternal)

fileio.ars

Contains all info to read and write HWAR's .ars file type (script/triggers)
"""

from dataclasses import dataclass, field
from src.logger import get_logger

logger = get_logger()
import os
import re
from typing import List
import pathlib

# Regex pattern for trigger header
TRIGGER_HEADER_PATTERN = re.compile(
    r'"([^"]+)" *: *(AIS_[A-Z]+) *:? *(\d+)? *:? *([^{\s]+)'
)


@dataclass
class _ARSCondition:
    """Represents a condition within a trigger"""

    type: str
    values: List[str]

    def pack(self) -> str:
        """Pack condition into string format"""
        output = f"Condition: {self.type}\n"
        for value in self.values:
            output += f"  {value}\n"
        return output


@dataclass
class _ARSAction:
    """Represents an action within a trigger"""

    type: str
    values: List[str]

    def pack(self) -> str:
        """Pack action into string format"""
        output = f"Action: {self.type}\n"
        if self.values:  # Only add values if they exist
            for value in self.values:
                output += f"  {value}\n"
        return output


@dataclass
class _ARSRecord:
    """Represents a single script/trigger record in the .ars file."""

    name: str
    player_type: str
    player_id: int
    is_and: bool = True  # Default to AND if not specified
    conditions: List[_ARSCondition] = field(default_factory=list)
    actions: List[_ARSAction] = field(default_factory=list)

    def pack(self) -> str:
        """Pack object into string format for saving back to .ars"""
        # construct the aiscript type - only include the player id if its specific
        if self.player_type == "AIS_SPECIFICPLAYER":
            aiscript_header = f"{self.player_type} : {self.player_id}"
        else:
            aiscript_header = f"{self.player_type}"
        # now construct
        output = (
            f'Trigger: "{self.name}" : {aiscript_header} : {"BOOL_AND" if self.is_and else "BOOL_OR"}\n'
            + "{\n"
        )
        for condition in self.conditions:
            output += condition.pack()
        for action in self.actions:
            output += action.pack()
        output += "}\n\n"
        return output


@dataclass
class ArsFile:
    """Container for an .ars file"""

    full_file_path: str
    objects: List[_ARSRecord] = field(default_factory=list)

    def __post_init__(self):
        """Load objects from .ars file"""
        if not self.full_file_path:
            logger.info("ARS: Created empty container")
            return
        logger.info("ARS: Loading triggers from file")
        with open(self.full_file_path, "r") as f:
            triggers = f.read().split("Trigger: ")
            for trigger in triggers[1:]:  # ignore header
                record = self._parse_trigger(trigger)
                self.objects.append(record)
        logger.info(f"Loaded {len(self.objects)} triggers")

    def _parse_trigger(self, trigger: str) -> _ARSRecord | None:
        """Parses a trigger into an _ARSRecord (including processing its
        conditions and actions)"""
        header, body = trigger.split("{", 1)
        # process header
        match = TRIGGER_HEADER_PATTERN.match(header)
        if not match:
            raise Exception(f"Failed to parse trigger: {trigger}")
        name, player_type, player_id_str, bool_type = match.groups()
        # For AIS_ANYPLAYER, there is no player_id
        player_id = int(player_id_str) if player_id_str else 0
        # create record
        record = _ARSRecord(name, player_type, player_id, bool_type == "BOOL_AND")

        # Use regex to split into chunks starting with Condition: or Action:
        chunks = re.split(r"(?=(?:Condition:|Action:))", body.replace("}", ""))

        for chunk in chunks:
            # identify lines in the grouped condition/action block
            lines = [x.strip() for x in chunk.strip().split("\n") if x.strip()]
            if not lines:  # Skip if no lines after stripping
                continue
            # check for conditions and actions
            first_line = lines[0]
            if first_line.startswith("Condition:"):
                aiscript_type = ("Condition", first_line.split(":", 1)[1].strip())
                trigger_data = lines[1:]  # All lines after the Condition: line
                # Always add the condition, even if it has no values
                self._add_parsed_action_or_condition(
                    record, aiscript_type, trigger_data
                )
            elif first_line.startswith("Action:"):
                aiscript_type = ("Action", first_line.split(":", 1)[1].strip())
                trigger_data = lines[1:]  # All lines after the Action: line
                # Always add the action, even if it has no values
                self._add_parsed_action_or_condition(
                    record, aiscript_type, trigger_data
                )
        # and return the record
        return record

    def _add_parsed_action_or_condition(
        self, record: _ARSRecord, aiscript_type: tuple, values: List[str]
    ):
        """Add parsed condition or action to record"""
        if aiscript_type[0] == "Condition":
            record.conditions.append(_ARSCondition(aiscript_type[1], values))
        else:
            record.actions.append(_ARSAction(aiscript_type[1], values))

    def load_additional_data(self, file_to_load: pathlib.Path) -> None:
        """Loads the record(s) from the specified file into the current object

        Args:
            file_to_load (pathlib.Path): The path to the file to load
        """
        logger.info("ARS reading additional data")
        with open(file_to_load, "r") as f:
            triggers = f.read().split("Trigger: ")
            for trigger in triggers[1:]:  # ignore header
                record = self._parse_trigger(trigger)
                self.objects.append(record)
        logger.info(f"Loaded {len(self.objects)} triggers")

    def add_action_to_existing_record(
        self, record_name: str, action_title: str, action_details: list[str]
    ) -> None:
        """Add an action to an existing record

        Args:
            record_name (str): The name of the record to add the action to
            action_title (str): The title of the action
            action_details (list[str]): The details of the action
        """
        for record in self.objects:
            if record.name == record_name:
                record.actions.append(_ARSAction(action_title, action_details))
                return
        logger.info(f"Record {record_name} not found, action not added")

    def get_actions_from_existing_record(
        self, record_name: str
    ) -> list[tuple[str, list[str]]]:
        """Get actions from existing record (by name)

        Returns:
            list[tuple[str, list[str]]]: The actions found, or an empty list if not found.
        """
        for record in self.objects:
            if record.name == record_name:
                return [(action.type, action.values) for action in record.actions]
        logger.info(f"Record {record_name} not found, actions not found")
        return []

    def save(self, save_in_folder: str, file_name: str) -> None:
        """Save triggers to file"""
        if not file_name.endswith(".ars"):
            file_name += ".ars"

        output_path = os.path.join(save_in_folder, file_name)
        os.makedirs(save_in_folder, exist_ok=True)

        if os.path.exists(output_path):
            os.remove(output_path)
            logger.info(f"Replaced existing file: {output_path}")

        with open(output_path, "w") as f:
            f.write("AIRS\n")
            for obj in self.objects:
                f.write(obj.pack())

        logger.info(f"Saved ARS file to: {output_path}")
