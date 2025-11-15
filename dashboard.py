import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import random
import time
import threading
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

class RocketGroundStation:
    def __init__(self, root):
        self.root = root
        self.root.title("🚀 Rocket Ground Station")
        self.root.geometry("1000x700")
        self.root.configure(bg="#111")

        self.connected = False
        self.running = False
        self.altitude_data = []
        self.time_data = []
        self.start_time = None

        # --- UI Layout ---
        self.create_header()
        self.create_telemetry_panel()
        self.create_plot_panel()
        self.create_console()

    def create_header(self):
        frame = tk.Frame(self.root, bg="#222")
        frame.pack(fill="x", pady=10)

        tk.Label(frame, text="Rocket Ground Station", fg="white", bg="#222",
                 font=("Arial", 20, "bold")).pack(side="left", padx=20)

        self.connect_btn = ttk.Button(frame, text="Connect", command=self.toggle_connection)
        self.connect_btn.pack(side="right", padx=10)

    def create_telemetry_panel(self):
        frame = tk.LabelFrame(self.root, text="Telemetry", fg="white", bg="#111",
                              font=("Arial", 14, "bold"), labelanchor="n")
        frame.pack(fill="x", padx=20, pady=10)

        self.telemetry_vars = {
            "Altitude (m)": tk.StringVar(value="0"),
            "Velocity (m/s)": tk.StringVar(value="0"),
            "Temperature (°C)": tk.StringVar(value="0"),
            "Pressure (kPa)": tk.StringVar(value="0"),
            "Acceleration (m/s²)": tk.StringVar(value="0"),
        }

        for i, (label, var) in enumerate(self.telemetry_vars.items()):
            tk.Label(frame, text=label, fg="white", bg="#111", font=("Arial", 12)).grid(row=i, column=0, sticky="w", padx=10, pady=5)
            tk.Label(frame, textvariable=var, fg="#00ff00", bg="#111", font=("Consolas", 12)).grid(row=i, column=1, sticky="w", padx=10)

    def create_plot_panel(self):
        frame = tk.LabelFrame(self.root, text="Altitude Graph", fg="white", bg="#111",
                              font=("Arial", 14, "bold"), labelanchor="n")
        frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.figure = Figure(figsize=(6, 4), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_title("Altitude over Time")
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Altitude (m)")
        self.ax.grid(True)

        self.canvas = FigureCanvasTkAgg(self.figure, frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def create_console(self):
        frame = tk.LabelFrame(self.root, text="Console Log", fg="white", bg="#111",
                              font=("Arial", 14, "bold"), labelanchor="n")
        frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.console = scrolledtext.ScrolledText(frame, height=8, bg="#000", fg="#0f0", insertbackground="white",
                                                 font=("Consolas", 10))
        self.console.pack(fill="both", expand=True)
        self.log("System initialized. Waiting for connection...")

    # --- Core logic ---
    def toggle_connection(self):
        if not self.connected:
            self.connected = True
            self.connect_btn.config(text="Disconnect")
            self.start_time = time.time()
            self.running = True
            self.log("Connected to rocket telemetry system.")
            threading.Thread(target=self.update_telemetry_loop, daemon=True).start()
        else:
            self.connected = False
            self.connect_btn.config(text="Connect")
            self.running = False
            self.log("Disconnected from rocket.")

    def update_telemetry_loop(self):
        while self.running:
            # Simulate telemetry (replace with real data)
            altitude = random.uniform(0, 1000)
            velocity = random.uniform(0, 200)
            temperature = random.uniform(10, 90)
            pressure = random.uniform(90, 110)
            acceleration = random.uniform(-5, 5)

            self.telemetry_vars["Altitude (m)"].set(f"{altitude:.2f}")
            self.telemetry_vars["Velocity (m/s)"].set(f"{velocity:.2f}")
            self.telemetry_vars["Temperature (°C)"].set(f"{temperature:.2f}")
            self.telemetry_vars["Pressure (kPa)"].set(f"{pressure:.2f}")
            self.telemetry_vars["Acceleration (m/s²)"].set(f"{acceleration:.2f}")

            elapsed = time.time() - self.start_time
            self.altitude_data.append(altitude)
            self.time_data.append(elapsed)

            # Limit data length for performance
            if len(self.time_data) > 100:
                self.altitude_data.pop(0)
                self.time_data.pop(0)

            # Update plot
            self.ax.clear()
            self.ax.plot(self.time_data, self.altitude_data, color="cyan")
            self.ax.set_title("Altitude over Time")
            self.ax.set_xlabel("Time (s)")
            self.ax.set_ylabel("Altitude (m)")
            self.ax.grid(True)
            self.canvas.draw()

            self.log(f"Telemetry updated | Alt: {altitude:.1f} m | Vel: {velocity:.1f} m/s")
            time.sleep(1)

    def log(self, message):
        self.console.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {message}\n")
        self.console.see(tk.END)


if __name__ == "__main__":
    root = tk.Tk()
    app = RocketGroundStation(root)
    root.mainloop()
