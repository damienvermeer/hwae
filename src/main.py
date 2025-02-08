"""
HWAE (Hostile Waters Antaeus Eternal)

Python package (released as a pyinstaller exe) to generate additional maps for Hostile Waters: Antaeus Rising (2001)
"""

import logging

from fileio.lev import LevFile
from fileio.cfg import CfgFile

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    lev = LevFile(r"C:\HWAR\HWAR\modtest2\Level22\level22 original.lev")
    cfg = CfgFile(r"C:\HWAR\HWAR\modtest2\Level22\level22.cfg")

    for x in [lev, cfg]:
        x.save(r"C:\HWAR\HWAR\modtest2\Level22", "level22")
