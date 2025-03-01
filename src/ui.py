"""
HWAE (Hostile Waters Antaeus Eternal)

ui.py

Contains the UI for the map generator
"""

# python imports
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, font
import threading
import time
import pathlib

# pip imports
import sv_ttk

# local imports
from src.constants import VERSION_STR, PROGRESS_STEPS
from src.generate import generate_new_map


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

        # Set up the main frame
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # set internal states
        self.hwar_folder = None
        self.generation_in_progress = False
        self.current_progress_step = 0
        self.total_progress_steps = PROGRESS_STEPS

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
        self.label = ttk.Label(left_column, text=f"Version: {VERSION_STR}")
        self.label.pack(anchor=tk.W, pady=(0, 5))

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
        img = tk.PhotoImage(
            file=r"C:\Users\verme\Documents\GitHub\hwae\src\assets\hwar_cover.png"
        )
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
            self.hwar_folder = pathlib.Path(exe_path).parent

            # Enable the generation buttons
            self.random_button["state"] = "normal"
            self.json_button["state"] = "normal"

    def _select_json_file(self):
        """Open file dialog to select JSON file and start generation"""
        json_path = filedialog.askopenfilename(
            title="Select JSON Configuration",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )

        if json_path:
            self._start_map_generation(json_path)

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
        self._start_map_generation("default")

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
                target=generate_new_map,
                kwargs={
                    "progress_callback": self.update_progress_bar_to_next_step,
                    "config_path": config_path,
                    "exe_parent": self.hwar_folder,
                },
            )
            generation_thread.daemon = True
            generation_thread.start()

    def _generate_map(self, config_path):
        """Generate a map with the specified configuration

        Args:
            config_path (str): Path to the JSON configuration file or "default"
        """
        try:
            # Reset progress step counter
            self.current_progress_step = 0

            # Define status messages for each step

            # Simulate map generation with progress updates
            for i in range(self.total_progress_steps):
                # Update progress bar to next step
                self.update_progress_bar_to_next_step("")
                # Simulate work
                time.sleep(0.5)  # Longer delay for fewer steps

        finally:
            # Re-enable buttons and reset progress flag
            self.root.after(0, self._reset_ui_after_generation)

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

    def run(self):
        """Run the UI main loop"""
        self.root.mainloop()
