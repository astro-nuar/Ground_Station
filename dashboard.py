import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import random
import time
import threading
import queue
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

class RocketGroundStation:
    def __init__(self, root):
        self.root = root
        self.root.title("🚀 NuAR Ground Station")
        self.root.geometry("1920x1080")
        self.root.configure(bg="#111")

        #Start in fullscreen. Press F11 to toggle, Escape to exit.
        self.fullscreen = True
        try:
            self.root.attributes("-fullscreen", True)
        except Exception:
            #fallback to maximized state if -fullscreen not supported
            try:
                self.root.state('zoomed')
            except Exception:
                pass

        self.connected = False
        self.running = False
        self.altitude_data = []
        self.time_data = []
        self.start_time = None

        self.data_queue = queue.Queue()

        # --- UI Layout ---
        self.create_header()

        self.root.after(16, self.process_queue)

        #Main area: two columns. Left = telemetry, Right = plot + console
        self.main_frame = tk.Frame(self.root, bg="#111")
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=10)
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=4)

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
        frame = tk.LabelFrame(self.main_frame, text="Telemetry", fg="white", bg="#111",
                      font=("Arial", 14, "bold"), labelanchor="n")
        frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.telemetry_vars = {
            "Altitude (m)": tk.StringVar(value="0"),
            "Velocity (m/s)": tk.StringVar(value="0"),
            "Temperature (°C)": tk.StringVar(value="0"),
            "Pressure (mbar)": tk.StringVar(value="0"),
            "Acceleration (m/s²)": tk.StringVar(value="0"),
            "Airbrake (%)": tk.StringVar(value="0"),
            "Parachute Main": tk.StringVar(value="Not Deployed"),
            "Parachute Rogue": tk.StringVar(value="Not Deployed"),
            "Rocket Phases": tk.StringVar(value="Pre Arm"), #phases of rocket:pre arm,arm, rocket on,apogee,main, rogue,on  the ground.
            "Time Elapsed": tk.StringVar(value="00:00"),
            "Time To Launch": tk.StringVar(value="00:00"),
            "FPS": tk.StringVar(value="0"),

        }

        for i, (label, var) in enumerate(self.telemetry_vars.items()):
            tk.Label(frame, text=label, fg="white", bg="#111", font=("Arial", 12)).grid(row=i, column=0, sticky="w", padx=10, pady=5)
            tk.Label(frame, textvariable=var, fg="#00ff00", bg="#111", font=("Consolas", 12)).grid(row=i, column=1, sticky="w", padx=10)

    def create_plot_panel(self):
        # Right-side container (plot on top, console below)
        self.right_container = tk.Frame(self.main_frame, bg="#111")
        self.right_container.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.right_container.grid_rowconfigure(0, weight=1)
        self.right_container.grid_rowconfigure(1, weight=1)
        self.right_container.grid_columnconfigure(0, weight=1)

        frame = tk.LabelFrame(self.right_container, text="Altitude Graph", fg="white", bg="#111",
                              font=("Arial", 14, "bold"), labelanchor="n")
        frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        self.figure = Figure(figsize=(6, 4), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_title("Altitude over Time")
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Altitude (m)")
        self.ax.grid(True)

        self.line, = self.ax.plot([], [], color="cyan")

        self.canvas = FigureCanvasTkAgg(self.figure, frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def create_console(self):
        frame = tk.LabelFrame(self.right_container, text="Console Log", fg="white", bg="#111",
                      font=("Arial", 14, "bold"), labelanchor="n")
        frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        self.console = scrolledtext.ScrolledText(frame, height=8, bg="#000", fg="#0f0", insertbackground="white",
                                                 font=("Consolas", 16))
        self.console.pack(fill="both", expand=True)
        self.log("System initialized. Waiting for connection...")

    # --- Core logic ---

    def process_queue(self):
        """Called in main thread via `after` — consume queued samples and update the line."""
        updated = False
        while not self.data_queue.empty():
            t, a = self.data_queue.get()
            self.time_data.append(t)
            self.altitude_data.append(a)
            updated = True

        if updated:
            # update line data (fast)
            self.line.set_data(self.time_data, self.altitude_data)

            # update limits
            x_min, x_max = 0, max(self.time_data) if self.time_data else 1
            y_min, y_max = 0, max(self.altitude_data) if self.altitude_data else 1
            if x_min == x_max:
                x_max += 0.1
            if y_min == y_max:
                y_max += 0.1
            self.ax.set_xlim(left=x_min, right=x_max)
            self.ax.set_ylim(bottom=y_min, top=y_max)

            # lightweight redraw request (safe and efficient)
            self.canvas.draw_idle()

        # schedule next run (~60Hz)
        self.root.after(16, self.process_queue)

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

    def calculate_fps(self,elapsed_b, elapsed_a):
        try:
            return 1.0 / (elapsed_a - elapsed_b)
        except Exception:
            return 0.0

    def update_telemetry_loop(self):
        elapsed_b = 0
        while self.running:
            #Simulate telemetry (replace with real from the antena later)
            #The receiving and reading data should come here
            elapsed = time.time() - self.start_time

            altitude = random.uniform(0, 1000)
            velocity = random.uniform(0, 200)
            temperature = random.uniform(10, 90)
            pressure = random.uniform(90, 110)
            acceleration = random.uniform(-5, 5)
            airbrake = "Not airbraking yet"
            parachute_main = "Not parachuting yet"
            parachute_rogue = "Not parachuting yet"
            rocket_phase = "Not rocket phasing yet"

            fps = self.calculate_fps(elapsed_b, elapsed)
            
            mins, secs = divmod(int(elapsed), 60)
            tenths = int((elapsed - int(elapsed)) * 10)
            formatted_elapsed = f"{mins:02d}:{secs:02d}.{tenths}"

            self.telemetry_vars["Altitude (m)"].set(f"{altitude:.2f}")
            self.telemetry_vars["Velocity (m/s)"].set(f"{velocity:.2f}")
            self.telemetry_vars["Temperature (°C)"].set(f"{temperature:.2f}")
            self.telemetry_vars["Pressure (mbar)"].set(f"{pressure:.2f}")
            self.telemetry_vars["Acceleration (m/s²)"].set(f"{acceleration:.2f}")
            self.telemetry_vars["Airbrake (%)"].set(f"{airbrake}")
            self.telemetry_vars["Parachute Main"].set(f"{parachute_main}")
            self.telemetry_vars["Parachute Rogue"].set(f"{parachute_rogue}")
            self.telemetry_vars["Rocket Phases"].set(f"{rocket_phase}")
            self.telemetry_vars["Time Elapsed"].set(formatted_elapsed)
            self.telemetry_vars["Time To Launch"].set(f"{500 - elapsed}")
            self.telemetry_vars["FPS"].set(f"{fps:.1f}")

            elapsed_b = time.time() - self.start_time

            try:
                self.data_queue.put_nowait((elapsed, altitude))
            except queue.Full:
                pass
            
            time.sleep(1/60)

    def log(self, message):
        self.console.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {message}\n")
        self.console.see(tk.END) 
        

if __name__ == "__main__":
    root = tk.Tk()
    app = RocketGroundStation(root)
    root.mainloop()
