import tkinter as tk

class FramelessApp:
    def __init__(self, master):
        self.master = master
        self.master.title("PRO | Spoti")
        
        # Set window dimensions
        self.width = 1000
        self.height = 563
        
        # Calculate center position
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        x = (screen_width - self.width) // 2
        y = (screen_height - self.height) // 2
        
        # Set window geometry
        self.master.geometry(f"{self.width}x{self.height}+{x}+{y}")
        
        # Set window background
        self.bg_image = tk.PhotoImage(file="bag2.png")
        self.canvas = tk.Canvas(self.master, width=self.width, height=self.height)
        self.canvas.pack()
        self.canvas.create_image(0, 0, anchor="nw", image=self.bg_image)
        
        # Create image buttons
        self.button_image = tk.PhotoImage(file="example.png").subsample(2)  # Adjust subsample factor as needed
        
        button_positions = [(27, 188), (27, 307), (275, 188), (275, 307)]  # Adjust button positions here
        button_commands = [self.task1, self.task2, self.task3, self.task4]  # Assign tasks to buttons
        
        for button_position, command in zip(button_positions, button_commands):
            button_x, button_y = button_position
            button = tk.Button(self.master, image=self.button_image, bd=0, command=command, compound=tk.LEFT)
            button_window = self.canvas.create_window(button_x, button_y, anchor="nw", window=button)
        
        # Keep window on top
        self.master.attributes("-topmost", True)
        
        # Make window frameless
        self.master.overrideredirect(True)
        
        # Bind events for dragging the window
        self.canvas.bind("<ButtonPress-1>", self.start_move)
        self.canvas.bind("<ButtonRelease-1>", self.stop_move)
        self.canvas.bind("<B1-Motion>", self.on_motion)
        
    def start_move(self, event):
        self.x = event.x
        self.y = event.y
        
    def stop_move(self, event):
        self.x = None
        self.y = None
        
    def on_motion(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.master.winfo_x() + deltax
        y = self.master.winfo_y() + deltay
        self.master.geometry(f"+{x}+{y}")
        
    def task1(self):
        print("Task 1")
        
    def task2(self):
        print("Task 2")
        
    def task3(self):
        print("Task 3")
        
    def task4(self):
        print("Task 4")

def main():
    root = tk.Tk()
    app = FramelessApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
