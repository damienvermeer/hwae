"""
HWAE (Hostile Waters Antaeus Eternal)

Python package (released as a pyinstaller exe) to generate additional maps for Hostile Waters: Antaeus Rising (2001)
"""

import logging

from fileio.lev import LevFile

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    lev = LevFile(r"C:\HWAR\HWAR\modtest2\Level22\level22 original.lev")
    lev.save(r"C:\HWAR\HWAR\modtest2\Level22", "level22.lev")
