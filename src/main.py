"""
HWAE (Hostile Waters Antaeus Eternal)

Python package (released as a pyinstaller exe) to generate additional maps for Hostile Waters: Antaeus Rising (2001)
"""

import logging

from fileio.lev import LevFile
from fileio.cfg import CfgFile
from fileio.ob3 import Ob3File

logging.basicConfig(level=logging.DEBUG)

if __name__ == "__main__":
    lev = LevFile(r"C:\HWAR\HWAR\modtest2\Level22\level22 original.lev")
    cfg = CfgFile(r"C:\HWAR\HWAR\modtest2\Level22\level22.cfg")
    ob3 = Ob3File(r"C:\HWAR\HWAR\modtest2\Level22\level 22 no magpie.ob3")

    for x in [ob3]:
        x.save(r"C:\HWAR\HWAR\modtest2\Level52", "Level52")
