# HWAE - Hostile Waters: Antaeus Eternal

A random map generator for the classic game ![Hostile Waters: Antaeus Rising (2001)](https://www.gog.com/en/game/hostile_waters_antaeus_rising).

## 📖 Introduction

HWAE creates random skirmish-style maps for Hostile Waters: Antaeus Rising. The generator randomizes:

- Terrain generation and texturing
- Location of scrap resources
- Location, quantity, size, and contents of enemy bases
- Construction options (vehicles, weapons, soulcatcher AI companions, addons)

The software automatically modifies the Levels.lst file (creating a backup) so Hostile Waters will launch the new map immediately after generation.

This isn't a full-blown level editor (which would require game engine integration) – it's a map creator with some limited configuration options.

## ✨ Capabilities

- **Random Map Generation**: Creates terrain with textures and scenery
- **Carrier Placement**: Automatically selects an optimal location for the Antaeus carrier
- **Equipment Selection**: Randomly selects vehicles, weapons, soulcatcher AI companions, and addons
  - Always includes at least 6 soul catchers
  - Always includes Pegasus and Scarab vehicles
  - Always includes soulcatcher addon and recycler addon
  - Always includes either shield or armor addon
- **Enemy Bases**: Generates one or more enemy bases of various sizes, including pump outposts
  - Always includes at least 1 tiny enemy base
- **Resource Areas**: Creates scrap/recycling areas of various types and sizes
  - Always includes one scrap area near the carrier spawn
- **Team Balance**: Automatically assigns teams to each base for balanced gameplay
- **Enemy Units**: Adds scattered enemy units on patrol, AA guns, and radar installations
## 🔧 Installation

### Option 1: Using the Executable (Recommended)

1. Download the latest release from the [Releases](https://github.com/hwar-speed/hwae/releases) tab
2. Extract the ZIP archive to a location of your choice
3. Run `HW Antaeus Eternal.exe` - it may take 30 seconds to launch.

### Option 2: Running from Source

1. Clone this repository
2. Install Python 3.12
3. Create a virtual environment and install dependencies:
   ```
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```
4. Run the application:
   ```
   python src/main.py
   ```

## 🎮 How to Use

1. Launch the application
2. Click "Select HostileWaters.exe" and navigate to your Hostile Waters installation
3. Choose "Generate map (random)" for a completely random map, or "Generate map (from JSON)" to use a configuration file
4. Wait for the generation process to complete (takes up to 90 seconds)
5. Launch Hostile Waters and the new map will be available to play

## 🐛 How to Report Issues

- Use the [Issues tab](https://github.com/hwar-speed/hwae/issues) on GitHub to report bugs or suggest features
- Please include the .json and .csv files from the level folder as they are helpful for debugging and reproducing issues
- Alternatively, fix the issue yourself and submit a Pull Request

## 🎯 Mission Types

Currently, only one mission type is supported:
- **Destroy all alien production buildings**: Eliminate all enemy production facilities to win

A weapon crate optional objective has been implemented as a demonstration of how to create optional objectives. Sampling the weapon crate will give you an extra weapon.

## 🔄 Modifying a Generated Map

Each generated map includes a JSON configuration file in its folder with customizable options:
- Starting energy
- Number of enemy bases
- Optional lists for extra weapons, addons, vehicles, and soulcatchers

To modify an existing map:
1. Use the "Generate map (from JSON)" option in the application
2. Select the JSON file from a previously generated map
3. The map will be regenerated with the same terrain and enemy bases as before (unless the number of scrap or enemy bases is modified) but with the modified construction options

See `construction.py` for the names of available weapons, addons, vehicles, and soulcatchers.

## ⚠️ Limitations

### Saving/Loading Level Causes Geometry Issues

For unknown reasons, saving and loading a game on custom maps causes geometry corruption. 

The game remains playable, but terrain may appear distorted. This appears to be a loading issue rather than a saving issue, as loading a quicksave from a custom level in an original level produces the same corruption.

### No Mission Briefings

The briefing system in Hostile Waters appears to use hard-coded indices into the `BRIEFS.DAT` file, making it difficult to implement custom briefings. In-game objectives work correctly, but pre-mission briefings and tutorials do not appear possible without modifying the main Hostile Waters executable.

### Current Limitations (Potential Future Improvements)

- **Enemy Types**: Currently only supports alien enemy types. Hybrid or Cabal unit types can be added with modifications to the code.
- **Map Size**: Currently only supports large maps (equal in size to Level 19 "Frozen Treats" in the base game). The code is structured to support additional sizes, but requires template .lev and .cfg files.
- **Visual Style**: Currently supports a game look/feel similar to the first ~5 levels. The code structure allows for extension to other visual styles (for example, the snow/ice style of later maps in the base game).
- **Zone Shapes**: Currently zones (enemy bases/scrap locations) are perfect circles, which can look somewhat artificial. The terrain smoothing around these locations is also a bit rough.