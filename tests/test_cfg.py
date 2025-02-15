"""
Tests for the CFG file parser
"""

import os
import pytest
from src.fileio.cfg import CfgFile
from tempfile import NamedTemporaryFile


def test_empty_lines_and_comments():
    """Test that empty lines and comments are handled correctly"""
    # Create a temporary file with test content
    with NamedTemporaryFile(mode="w", suffix=".cfg", delete=False) as f:
        f.write(
            """
; This is a comment
[Section1]
value1
   ; Indented comment
[Section2]

value2
; Comment after empty line
[Section3]
; Comment in section
value3
"""
        )
        temp_path = f.name

    try:
        # Parse the file
        cfg = CfgFile(temp_path)

        # Check sections are parsed correctly
        assert len(cfg.records) == 3
        assert cfg.records[0].section == "Section1"
        assert cfg.records[0].value == ["value1"]
        assert cfg.records[1].section == "Section2"
        assert cfg.records[1].value == ["value2"]
        assert cfg.records[2].section == "Section3"
        assert cfg.records[2].value == ["value3"]
    finally:
        # Cleanup
        os.unlink(temp_path)


def test_inline_comments():
    """Test that inline comments are handled correctly"""
    with NamedTemporaryFile(mode="w", suffix=".cfg", delete=False) as f:
        f.write(
            """[Section1]
value1 ; comment after value
value2;no space before comment
value3 ;multiple;semicolons;here
"""
        )
        temp_path = f.name

    try:
        cfg = CfgFile(temp_path)
        assert len(cfg.records) == 1
        assert cfg.records[0].section == "Section1"
        assert cfg.records[0].value == ["value1", "value2", "value3"]
    finally:
        os.unlink(temp_path)


def test_whitespace_handling():
    """Test that whitespace is handled correctly"""
    with NamedTemporaryFile(mode="w", suffix=".cfg", delete=False) as f:
        f.write(
            """   [Section1]   
    value1    
  [Section2]  ; with comment  
      value2     ; with trailing comment   
[Section3]
value3a    value3b    ; comment with multiple spaces
    value4\t\t; tabs and spaces
"""
        )
        temp_path = f.name

    try:
        cfg = CfgFile(temp_path)
        assert len(cfg.records) == 3
        assert cfg.records[0].section == "Section1"
        assert cfg.records[0].value == ["value1"]
        assert cfg.records[1].section == "Section2"
        assert cfg.records[1].value == ["value2"]
        assert cfg.records[2].section == "Section3"
        assert cfg.records[2].value == ["value3a    value3b", "value4"]
    finally:
        os.unlink(temp_path)


def test_empty_file():
    """Test handling of empty files"""
    with NamedTemporaryFile(mode="w", suffix=".cfg", delete=False) as f:
        temp_path = f.name

    try:
        cfg = CfgFile(temp_path)
        assert len(cfg.records) == 0
    finally:
        os.unlink(temp_path)


def test_only_comments():
    """Test handling of files with only comments"""
    with NamedTemporaryFile(mode="w", suffix=".cfg", delete=False) as f:
        f.write(
            """; Comment 1
; Comment 2
  ; Indented comment
"""
        )
        temp_path = f.name

    try:
        cfg = CfgFile(temp_path)
        assert len(cfg.records) == 0
    finally:
        os.unlink(temp_path)


def test_dict_style_access():
    """Test dictionary-style access to CFG sections"""
    with NamedTemporaryFile(mode="w", suffix=".cfg", delete=False) as f:
        f.write(
            """[Section1]
value1
value2
[Section2]
test
"""
        )
        temp_path = f.name

    try:
        cfg = CfgFile(temp_path)

        # Test getting existing sections
        assert cfg["Section1"] == ["value1", "value2"]
        assert cfg["Section2"] == ["test"]

        # Test setting existing section with single value
        cfg["Section1"] = "new_value"
        assert cfg["Section1"] == ["new_value"]

        # Test setting existing section with list
        cfg["Section1"] = ["line1", "line2"]
        assert cfg["Section1"] == ["line1", "line2"]

        # Test setting new section
        cfg["Section3"] = "test3"
        assert cfg["Section3"] == ["test3"]

        # Test setting multiline value as string
        cfg["Section4"] = "line1\nline2\nline3"
        assert cfg["Section4"] == ["line1", "line2", "line3"]
        assert len(cfg.records[-1].value) == 3

        # Test setting multiline value as list
        cfg["Section5"] = ["line1", "line2", "line3"]
        assert cfg["Section5"] == ["line1", "line2", "line3"]
        assert len(cfg.records[-1].value) == 3

        # Test setting non-string value
        cfg["Number"] = 42
        assert cfg["Number"] == ["42"]

        # Test KeyError on non-existent section
        with pytest.raises(KeyError) as exc_info:
            _ = cfg["NonexistentSection"]
        assert "NonexistentSection" in str(exc_info.value)

    finally:
        os.unlink(temp_path)


def test_dict_style_save():
    """Test that dictionary-style modifications are properly saved"""
    with NamedTemporaryFile(mode="w", suffix=".cfg", delete=False) as f:
        f.write("[Initial]\nvalue\n")
        temp_path = f.name

    try:
        cfg = CfgFile(temp_path)

        # Modify and add sections
        cfg["Initial"] = ["modified"]
        cfg["New"] = ["new_value"]
        cfg["Multiline"] = ["line1", "line2"]

        # Save to new file
        save_dir = os.path.dirname(temp_path)
        new_filename = os.path.basename(temp_path) + "_new"
        cfg.save(save_dir, new_filename)

        # Read back and verify
        new_path = os.path.join(save_dir, new_filename + ".cfg")
        new_cfg = CfgFile(new_path)
        assert new_cfg["Initial"] == ["modified"]
        assert new_cfg["New"] == ["new_value"]
        assert new_cfg["Multiline"] == ["line1", "line2"]

    finally:
        os.unlink(temp_path)
        if os.path.exists(new_path):
            os.unlink(new_path)
