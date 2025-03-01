"""
HWAE (Hostile Waters Antaeus Eternal)

ui.py

Contains the UI for the map generator
"""

# python imports
import tkinter as tk
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox
import threading
import json
import os
import sys
import traceback
import webbrowser
from pathlib import Path
import sv_ttk
from tkinter import ttk

# local imports
from constants import VERSION_STR, PROGRESS_STEPS, NEW_LEVEL_NAME
from generate import generate_new_map
from logger import get_logger
from paths import get_assets_path

logger = get_logger()


class GUI:
    """GUI for generating maps"""

    def __init__(self):
        """Initialize the UI"""
        # create root and set theme
        self.root = tk.Tk()
        sv_ttk.set_theme(root=self.root, theme="light")
        self.root.title(f"Hostile Waters: Antaeus Eternal")
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.resizable(False, False)
        self.root.iconbitmap(get_assets_path() / "icon.ico")

        # Set up the main frame
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # set internal states
        self.hwar_folder = None
        self.generation_in_progress = False
        self.current_progress_step = 0
        self.total_progress_steps = PROGRESS_STEPS
        self.error_message = ""

        # Create UI elements
        content_frame = ttk.Frame(self.main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Left column for text and buttons
        left_column = ttk.Frame(content_frame)
        left_column.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        # Right column for image
        right_column = ttk.Frame(content_frame)
        right_column.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Add text label above the buttons
        button_frame = ttk.Frame(left_column)
        button_frame.pack(fill=tk.X, pady=(0, 5))

        # Version label on the left side of the frame
        version_label = ttk.Label(button_frame, text=f"Version: {VERSION_STR}")
        version_label.pack(side=tk.LEFT)

        # GitHub button on the right side of the frame
        self.github_button = ttk.Button(
            button_frame,
            text="Issues?",
            command=self._open_github,
        )
        self.github_button.pack(side=tk.RIGHT)

        # Select HWAR executable button
        self.select_exe_button = ttk.Button(
            left_column,
            text="Select HostileWaters.exe",
            command=self._select_hwar_executable,
        )
        self.select_exe_button.pack(fill=tk.X, pady=(0, 5))

        # Random map generation button (initially disabled)
        self.random_button = ttk.Button(
            left_column,
            text="Generate map (random)",
            command=self._start_random_generation,
            state="disabled",
        )
        self.random_button.pack(fill=tk.X, pady=(0, 5))

        # JSON map generation button (initially disabled)
        self.json_button = ttk.Button(
            left_column,
            text="Generate map (from JSON)",
            command=self._select_json_file,
            state="disabled",
        )
        self.json_button.pack(fill=tk.X)

        # Add image directly to the right column
        self.image_label = ttk.Label(right_column)
        img = tk.PhotoImage(file=str(get_assets_path() / "hwar_cover.png"))
        self.image_label.config(image=img)
        self.image_label.image = img  # Keep a reference to prevent garbage collection
        self.image_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Progress bar at the bottom
        self.progress_bar = ttk.Progressbar(
            self.main_frame, orient=tk.HORIZONTAL, length=100, mode="determinate"
        )
        self.progress_bar.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))

        # Status label below progress bar
        self.status_label = ttk.Label(self.main_frame, text="")
        self.status_label.pack(fill=tk.X, side=tk.BOTTOM, pady=(5, 0))

    def _select_hwar_executable(self):
        """Open file dialog to select HostileWaters.exe"""
        exe_path = filedialog.askopenfilename(
            title="Select HostileWaters.exe",
            filetypes=[
                ("Hostile Waters Executable", "HostileWaters.exe"),
                ("All files", "*.*"),
            ],
        )

        if exe_path:
            # Set the hwar_folder to the parent folder of the executable
            self.hwar_folder = Path(exe_path).parent

            # Enable the generation buttons
            self.random_button["state"] = "normal"
            self.json_button["state"] = "normal"

    def _select_json_file(self):
        """Open file dialog to select JSON file and start generation"""
        if not self._check_level_exists_and_confirm():
            # User canceled, reset UI if needed
            self._reset_ui_after_generation()
            return

        file_path = filedialog.askopenfilename(
            title="Select JSON Configuration File",
            filetypes=[("JSON files", "*.json")],
        )
        if file_path:
            self._start_map_generation(file_path)

    def _on_close(self):
        """Handle window close event"""
        if self.generation_in_progress:
            if messagebox.askyesno(
                "Confirm Exit",
                "A map generation is in progress. Are you sure you want to exit?",
            ):
                self.root.destroy()
        else:
            if messagebox.askyesno("Confirm Exit", "Are you sure you want to exit?"):
                self.root.destroy()

    def _start_random_generation(self):
        """Start random map generation with default configuration"""
        if self._check_level_exists_and_confirm():
            self._start_map_generation("")  # empty string will use the default config
        else:
            # User canceled, reset UI if needed
            self._reset_ui_after_generation()

    def _check_level_exists_and_confirm(self):
        """Check if the level folder exists and ask for confirmation to delete it

        Returns:
            bool: True if the user confirms or the folder doesn't exist, False otherwise
        """
        if not self.hwar_folder:
            return False

        level_path = self.hwar_folder / NEW_LEVEL_NAME

        if level_path.exists():
            response = messagebox.askyesno(
                "Level Exists",
                f"The level folder '{NEW_LEVEL_NAME}' already exists.\n\n"
                f"Do you want to delete the existing level and create a new one?",
                icon="warning",
            )
            return response

        return True

    def flag_as_complete(self):
        """Flag the current generation as complete"""
        # Schedule the UI update on the main thread
        self.root.after(0, self._update_ui_after_completion)

    def _update_ui_after_completion(self):
        """Update the UI after completion (called from the main thread)"""
        # Reset generation flag
        self.generation_in_progress = False
        self.current_progress_step = 0

        # enable all buttons
        self.select_exe_button["state"] = "normal"
        self.random_button["state"] = "normal"
        self.json_button["state"] = "normal"
        # set the display text to "Completed"
        self.status_label.config(text="Generation Complete!")
        # empty the progress bar
        self.progress_bar["value"] = 0

    def _generate_map_with_exception_handling(self, **kwargs):
        """Generate map with exception handling

        Args:
            **kwargs: Keyword arguments to pass to generate_new_map
        """
        try:
            generate_new_map(**kwargs)
        except Exception as e:
            # Log the exception
            logger.error(f"Error during map generation: {str(e)}")
            logger.error(traceback.format_exc())

            # Show error message on the main thread
            # Use a direct function call instead of a lambda to avoid reference issues
            self.error_message = str(e)
            self.root.after(0, self._show_error_and_reset)

    def _show_error_and_reset(self):
        """Show error message and reset UI state"""
        messagebox.showerror(
            "Map Generation Error",
            f"An error occurred during map generation:\n\n{self.error_message}\n\n"
            f"Check the CSV log file in the level folder for details.",
        )
        # Reset UI state
        self._update_ui_after_completion()

    def _start_map_generation(self, config_path):
        """Start map generation with the specified configuration

        Args:
            config_path (str): Path to the JSON configuration file or "default"
        """
        if not self.generation_in_progress and self.hwar_folder:
            self.generation_in_progress = True
            self.progress_bar["value"] = 0

            # Disable buttons during generation
            self.select_exe_button["state"] = "disabled"
            self.random_button["state"] = "disabled"
            self.json_button["state"] = "disabled"

            # Start the generation thread
            generation_thread = threading.Thread(
                target=self._generate_map_with_exception_handling,
                kwargs={
                    "progress_callback": self.update_progress_bar_to_next_step,
                    "complete_callback": self.flag_as_complete,
                    "config_path": config_path,
                    "exe_parent": self.hwar_folder,
                },
            )
            generation_thread.daemon = True
            generation_thread.start()

    def update_progress_bar_to_next_step(self, status_text=""):
        """Update the progress bar to the next step

        Args:
            status_text (str): Text to display in the status label
        """
        self.current_progress_step += 1
        progress_value = int(
            (self.current_progress_step / self.total_progress_steps) * 100
        )
        self.root.after(0, self._update_progress, progress_value, status_text)

    def _update_progress(self, value, status_text=""):
        """Update the progress bar value and status label

        Args:
            value (int): New progress value (0-100)
            status_text (str): Text to display in the status label
        """
        self.progress_bar["value"] = value
        self.status_label.config(text=status_text)

    def _reset_ui_after_generation(self):
        """Reset the UI after generation is complete"""
        self.generation_in_progress = False
        self.select_exe_button["state"] = "normal"
        self.random_button["state"] = "normal"
        self.json_button["state"] = "normal"
        self.status_label.config(text="")

    def _open_github(self):
        """Open the GitHub repository in the default web browser"""
        webbrowser.open("https://github.com/hwar-speed/hwae/issues/new")

    def run(self):
        """Run the UI main loop"""
        self.root.mainloop()
