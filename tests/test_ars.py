"""
Tests for the ARS file parser
"""

import os
import pytest
import re
from src.fileio.ars import ArsFile
from tempfile import NamedTemporaryFile


def normalize_spaces(content: str) -> str:
    """Normalize spaces between colons in trigger headers"""
    lines = []
    for line in content.split("\n"):
        if line.startswith("Trigger:"):
            # Split by quotes to preserve spaces within quoted strings
            parts = line.split('"')
            if len(parts) >= 3:  # We have a proper trigger line
                header = parts[2]  # The part after the name
                # Normalize spaces around colons
                header = re.sub(r"\s*:\s*", " : ", header)
                line = f'Trigger: "{parts[1]}"{header}'
        lines.append(line)
    return "\n".join(lines).strip()


def extract_triggers(content: str) -> list[str]:
    """Extract individual triggers from content"""
    triggers = []
    current_trigger = []
    in_trigger = False

    for line in content.split("\n"):
        if line.startswith("AIRS"):
            continue
        if line.startswith("Trigger:"):
            if current_trigger:
                triggers.append("\n".join(current_trigger))
                current_trigger = []
            in_trigger = True
        if in_trigger:
            current_trigger.append(line)

    if current_trigger:
        triggers.append("\n".join(current_trigger))

    return triggers


def normalize_trigger_content(content: str) -> str:
    """Normalize trigger content by:
    1. Preserving the AIRS header
    2. Normalizing spaces around colons in trigger headers
    3. Normalizing spaces around values in conditions and actions
    4. Preserving indentation structure for the trigger body
    5. Removing extra newlines at end of file
    """
    lines = []
    in_trigger_body = False

    # Split into lines and process each one
    content_lines = content.splitlines()

    # Handle AIRS header if present
    if content_lines and content_lines[0].strip() == "AIRS":
        lines.append("AIRS")
        content_lines = content_lines[1:]

    for line in content_lines:
        # Remove trailing whitespace but preserve indentation
        line = line.rstrip()
        if not line:
            continue

        stripped_line = line.strip()
        if stripped_line.startswith("Trigger:"):
            # Normalize trigger header line
            parts = line.split('"')
            if len(parts) >= 3:
                header = parts[2].strip()
                # Normalize spaces around colons
                header = re.sub(r"\s*:\s*", " : ", header)
                line = f'Trigger: "{parts[1]}"{header}'
            in_trigger_body = False
        elif stripped_line == "{":
            in_trigger_body = True
            lines.append("{")
            continue
        elif stripped_line == "}":
            in_trigger_body = False
            lines.append("}")
            continue
        elif in_trigger_body:
            # Inside trigger body, preserve indentation for structure
            if stripped_line.startswith(("Condition:", "Action:")):
                # Normalize label spacing
                parts = stripped_line.split(":", 1)
                line = f"{parts[0]}: {parts[1].strip()}"
            else:
                # Preserve indentation with normalized value
                line = f"  {stripped_line}"

        lines.append(line)

    # Remove empty lines at the end
    while lines and not lines[-1].strip():
        lines.pop()

    return "\n".join(lines)


def test_read_write_consistency():
    """Test that reading from and writing to an ARS file preserves the content"""
    # Create a temporary file
    with NamedTemporaryFile(mode="w", suffix=".ars", delete=False) as f:
        temp_path = f.name
        # Copy the test file to temp location
        with open("tests/readwrite.ars", "r") as f1:
            original_content = f1.read()
            f.write(original_content)

    try:
        # Load and save the file
        ars = ArsFile(temp_path)
        save_dir = os.path.dirname(temp_path)
        save_name = "saved.ars"
        ars.save(save_dir, save_name)
        saved_path = os.path.join(save_dir, save_name)

        # Compare the files
        with open(temp_path, "r") as f1, open(saved_path, "r") as f2:
            original = normalize_trigger_content(f1.read())
            saved = normalize_trigger_content(f2.read())

            # Split into individual triggers for better error messages
            original_triggers = [t for t in original.split("Trigger: ") if t.strip()]
            saved_triggers = [t for t in saved.split("Trigger: ") if t.strip()]

            # Compare number of triggers
            assert len(original_triggers) == len(
                saved_triggers
            ), f"Number of triggers differs: {len(original_triggers)} != {len(saved_triggers)}"

            # Compare triggers one by one
            for i, (orig, save) in enumerate(zip(original_triggers, saved_triggers)):
                orig_norm = normalize_trigger_content(orig)
                save_norm = normalize_trigger_content(save)
                assert (
                    orig_norm == save_norm
                ), f"Trigger {i} differs:\nOriginal:\n{orig}\nSaved:\n{save}"

    finally:
        # Clean up the temporary files
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        if os.path.exists(saved_path):
            os.unlink(saved_path)


def test_player_types():
    """Test that different player types are handled correctly"""
    test_content = """AIRS
Trigger: "test1" : AIS_SPECIFICPLAYER : 0 : BOOL_AND
{
Action: AIScript_Victory
  AIS_SPECIFICPLAYER : 0
}

Trigger: "test2" : AIS_ENEMIES : BOOL_AND
{
Action: AIScript_Victory
  AIS_ENEMIES 
}

Trigger: "test3" : AIS_ANYPLAYER : BOOL_AND
{
Action: AIScript_Victory
  AIS_ANYPLAYER 
}
"""
    # Create a temporary file with test content
    with NamedTemporaryFile(mode="w", suffix=".ars", delete=False) as f:
        f.write(test_content)
        test_file = f.name

    try:
        # Read the file
        ars = ArsFile(test_file)

        # Verify the triggers were loaded correctly
        assert len(ars.objects) == 3, "Should have loaded 3 triggers"

        # Check each trigger's player type
        assert ars.objects[0].player_type == "AIS_SPECIFICPLAYER"
        assert ars.objects[1].player_type == "AIS_ENEMIES"
        assert ars.objects[2].player_type == "AIS_ANYPLAYER"

        # Check player IDs
        assert ars.objects[0].player_id == 0  # Specific player should have ID
        assert ars.objects[1].player_id == 0  # Others should default to 0
        assert ars.objects[2].player_id == 0

        # Save and reload to verify persistence
        with NamedTemporaryFile(mode="w", suffix=".ars", delete=False) as f:
            save_path = f.name
            save_dir = os.path.dirname(save_path)
            save_name = os.path.basename(save_path)

        ars.save(save_dir, save_name)

        # Load saved file
        ars2 = ArsFile(save_path)

        # Verify same content
        assert len(ars2.objects) == 3
        for orig, saved in zip(ars.objects, ars2.objects):
            assert orig.player_type == saved.player_type
            assert orig.player_id == saved.player_id

    finally:
        # Clean up
        if os.path.exists(test_file):
            os.unlink(test_file)
        if os.path.exists(save_path):
            os.unlink(save_path)


def test_no_value_actions():
    """Test that actions without values are handled correctly"""
    test_content = """AIRS
Trigger: "test1" : AIS_ANYPLAYER : BOOL_AND
{
Action: AIScript_BreakWarmap
Action: AIScript_PlaySound
  "0408"
}
"""
    # Create a temporary file with test content
    test_file = None
    save_path = None

    try:
        with NamedTemporaryFile(mode="w", suffix=".ars", delete=False) as f:
            f.write(test_content)
            test_file = f.name

        # Read the file
        ars = ArsFile(test_file)

        # Verify the trigger was loaded correctly
        assert len(ars.objects) == 1
        record = ars.objects[0]

        # Check actions
        assert len(record.actions) == 2
        assert record.actions[0].type == "AIScript_BreakWarmap"
        assert len(record.actions[0].values) == 0  # No values
        assert record.actions[1].type == "AIScript_PlaySound"
        assert record.actions[1].values == ['"0408"']

        # Save and reload to verify persistence
        with NamedTemporaryFile(mode="w", suffix=".ars", delete=False) as f:
            save_path = f.name
            save_dir = os.path.dirname(save_path)
            save_name = os.path.basename(save_path)

        ars.save(save_dir, save_name)

        # Load saved file and verify content matches
        with open(save_path, "r") as f:
            saved_content = f.read()

        # Normalize both contents for comparison
        test_content = test_content.replace(" ", "").replace("\n", "")
        saved_content = saved_content.replace(" ", "").replace("\n", "")
        assert test_content == saved_content

    finally:
        # Clean up
        if test_file and os.path.exists(test_file):
            os.unlink(test_file)
        if save_path and os.path.exists(save_path):
            os.unlink(save_path)


def test_whitespace_handling():
    """Test that whitespace variations are handled correctly in ARS files"""
    content = """AIRS
Trigger: "Test Trigger" : AIS_SPECIFICPLAYER : 1 : BOOL_AND
{
Condition: AIScript_CountdownTimer
  5  
  AIS_EQUALTO  
  10  
Action:  AIScript_TriggerGrowingBuilding  
  1746  
}
"""

    with NamedTemporaryFile(mode="w", suffix=".ars", delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        # Load and save the file
        ars = ArsFile(temp_path)
        save_dir = os.path.dirname(temp_path)
        save_name = "saved.ars"
        ars.save(save_dir, save_name)
        saved_path = os.path.join(save_dir, save_name)

        # Compare the files
        with open(temp_path, "r") as f1, open(saved_path, "r") as f2:
            original = normalize_trigger_content(f1.read())
            saved = normalize_trigger_content(f2.read())

            # Print normalized content for debugging
            print("Original normalized:")
            print(original)
            print("\nSaved normalized:")
            print(saved)

            assert original == saved

            # Verify specific formatting
            expected_lines = [
                "AIRS",
                'Trigger: "Test Trigger" : AIS_SPECIFICPLAYER : 1 : BOOL_AND',
                "{",
                "Condition: AIScript_CountdownTimer",
                "  5",
                "  AIS_EQUALTO",
                "  10",
                "Action: AIScript_TriggerGrowingBuilding",
                "  1746",
                "}",
            ]

            for line in expected_lines:
                assert line in saved.splitlines()
    finally:
        os.unlink(temp_path)
        if os.path.exists(saved_path):
            os.unlink(saved_path)
