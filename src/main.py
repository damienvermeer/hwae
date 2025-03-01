"""
HWAE (Hostile Waters Antaeus Eternal)

Python package to generate additional maps for Hostile Waters: Antaeus Rising (2001)
"""

import os
import sys

# Add the src directory to the Python path so imports work without installation
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from ui import GUI

if __name__ == "__main__":
    app = GUI()
    app.run()
