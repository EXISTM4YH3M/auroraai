import tkinter as tk
from PIL import Image, ImageTk
import random
import math
import threading
import time
import os
import importlib
import api
import subprocess

class FloatingImageApp:
    def __init__(self, root):
        self.root = root
        self.root.attributes('-fullscreen', True)
        self.root.configure(bg='black')
        root.title("Aurora AI")  # Set the window title
        root.iconbitmap("src/icon.ico")
        
        # Initialize previous content as None
        self.previous_content = None

        # Load the initial image
        self.image_path = 'src/eyes/eyes.png'
        self.image = Image.open(self.image_path).resize((500, 500), Image.Resampling.LANCZOS)
        self.photo = ImageTk.PhotoImage(self.image)

        # Create a canvas to hold the image
        self.canvas = tk.Canvas(root, bg='black', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Add the image to the canvas
        self.image_id = self.canvas.create_image(0, 0, anchor=tk.CENTER, image=self.photo)

        # Initialize position and velocity
        self.x_pos = self.root.winfo_screenwidth() // 2
        self.y_pos = self.root.winfo_screenheight() // 2
        self.x_velocity = random.uniform(-0.5, 0.5)  # Initial velocity for x
        self.y_velocity = random.uniform(-0.5, 0.5)  # Initial velocity for y
        self.radius = 100  # Radius to limit movement
        self.center_x = self.x_pos
        self.center_y = self.y_pos

        # Physics parameters
        self.friction = 0.98  # Simulate gradual slowing
        self.acceleration = 0.01  # Gradual acceleration to change direction
        self.min_velocity = 0.1  # Minimum velocity to prevent stopping

        # Additional UI elements
        self.loading_throbber = None
        self.text_output = None
        self.waiting_image_id = None

        # Start the animation
        self.animate()

        # Start the API monitoring thread
        self.monitor_api()

        # Bind escape key to exit full screen
        self.root.bind('<Escape>', lambda e: self.root.destroy())

    def load_api_variables(self):
        # Dynamically reload the api.py file to reflect changes
        importlib.reload(api)
        self.api = api  # Make api variables available

    def animate(self):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Update velocity with slight random acceleration
        self.x_velocity += random.uniform(-self.acceleration, self.acceleration)
        self.y_velocity += random.uniform(-self.acceleration, self.acceleration)

        # Apply friction to smooth the movement
        self.x_velocity *= self.friction
        self.y_velocity *= self.friction

        # Ensure minimum velocity
        if abs(self.x_velocity) < self.min_velocity:
            self.x_velocity = self.min_velocity * (1 if self.x_velocity > 0 else -1)
        if abs(self.y_velocity) < self.min_velocity:
            self.y_velocity = self.min_velocity * (1 if self.y_velocity > 0 else -1)

        # Update position
        self.x_pos += self.x_velocity
        self.y_pos += self.y_velocity

        # Bounce off boundaries within radius and screen limits
        if abs(self.x_pos - self.center_x) > self.radius or not (250 < self.x_pos < screen_width - 250):
            self.x_velocity *= -1
        if abs(self.y_pos - self.center_y) > self.radius or not (250 < self.y_pos < screen_height - 250):
            self.y_velocity *= -1

        # Move the image
        self.canvas.coords(self.image_id, self.x_pos, self.y_pos)

        # Schedule the next frame
        self.root.after(16, self.animate)  # 60 FPS (16 ms per frame)

    def read_api_file(self):
        # Path to the api.py file
        api_file_path = 'api.py'
        if os.path.exists(api_file_path):
            with open(api_file_path, 'r') as file:
                return file.read()
        return None

    def load_api(self):
        """Loads and returns the API object dynamically from api.py"""
        # Read the current content of api.py
        current_content = self.read_api_file()

        # Create a new empty namespace (object-like)
        api_namespace = type('api', (object,), {})()

        # Dynamically execute the content of api.py and populate the api_namespace
        exec(current_content, globals(), vars(api_namespace))

        # Return the dynamically created api object
        return api_namespace
        
    def monitor_api(self):
    
        self.load_api_variables()
        
        # Read current content of the api.py file
        current_content = self.read_api_file()

        if current_content != self.previous_content:
            # If content has changed, update the previous content and check for variables
            self.previous_content = current_content

            # Dynamically evaluate variables from api.py using exec
            exec(current_content, globals(), locals())

            # Check the 'processing' variable
            if self.api.processing:
                if not self.loading_throbber:
                    self.loading_throbber = self.canvas.create_text(
                        self.root.winfo_screenwidth() - 50, 50,
                        text="",
                        fill="Blue",
                        font=("Helvetica", 20),
                        anchor=tk.SE
                    )
            else:
                if self.loading_throbber:
                    self.canvas.delete(self.loading_throbber)
                    self.loading_throbber = None

            # Check the 'emotion' variable
            if hasattr(api, 'emotion'):
                try:
                    new_image_path = f"src/eyes/{api.emotion}.png"
                    new_image = Image.open(new_image_path).resize((500, 500), Image.Resampling.LANCZOS)
                    self.photo = ImageTk.PhotoImage(new_image)
                    self.canvas.itemconfig(self.image_id, image=self.photo)
                except FileNotFoundError:
                    pass  # Ignore if the image doesn't exist

            # Check the 'output' variable
            if hasattr(api, 'output'):
                if not self.text_output:
                    self.text_output = self.canvas.create_text(
                        self.root.winfo_screenwidth() // 2,
                        self.root.winfo_screenheight() - 50,
                        text=api.output,
                        fill="white",
                        font=("Helvetica", 16)
                    )
                else:
                    self.canvas.itemconfig(self.text_output, text=api.output)


            if self.api.waiting == True:
                try:
                    new_image_path = f"src/eyes/waiting.png"
                    new_image = Image.open(new_image_path).resize((500, 500), Image.Resampling.LANCZOS)
                    self.photo = ImageTk.PhotoImage(new_image)
                    self.canvas.itemconfig(self.image_id, image=self.photo)
                except FileNotFoundError:
                    pass  # Ignore if the image doesn't exist
            else:
                try:
                    new_image_path = f"src/eyes/eyes.png"
                    new_image = Image.open(new_image_path).resize((500, 500), Image.Resampling.LANCZOS)
                    self.photo = ImageTk.PhotoImage(new_image)
                    self.canvas.itemconfig(self.image_id, image=self.photo)
                except FileNotFoundError:
                    pass  # Ignore if the image doesn't exist
                
        # Schedule the next check
        self.root.after(100, self.monitor_api)  # Check for updates every 100ms


if __name__ == "__main__":
    root = tk.Tk()
    app = FloatingImageApp(root)
    root.mainloop()
