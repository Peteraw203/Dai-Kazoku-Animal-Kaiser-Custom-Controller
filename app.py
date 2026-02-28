import customtkinter as ctk
import serial
import serial.tools.list_ports
import threading
import vgamepad as vg
import sys
import time
import json
import os
try:
    from PIL import Image
except ImportError:
    pass 

# Options for mapping dropdowns (Xbox Buttons)
XBOX_BUTTONS = {
    "XUSB_GAMEPAD_A": vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
    "XUSB_GAMEPAD_B": vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
    "XUSB_GAMEPAD_X": vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
    "XUSB_GAMEPAD_Y": vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
    "XUSB_GAMEPAD_LB": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
    "XUSB_GAMEPAD_RB": vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
    "XUSB_GAMEPAD_BACK": vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,
    "XUSB_GAMEPAD_START": vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
    "XUSB_GAMEPAD_DPAD_UP": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP,
    "XUSB_GAMEPAD_DPAD_DOWN": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN,
    "XUSB_GAMEPAD_DPAD_LEFT": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT,
    "XUSB_GAMEPAD_DPAD_RIGHT": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT,
}
BUTTON_OPTIONS = list(XBOX_BUTTONS.keys())

CONFIG_FILE = "controller_config.json"

class AnimalKaiserControllerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Window Configuration ---
        self.title("Animal Kaiser Controller Driver")
        self.geometry("850x450")
        self.configure(fg_color="#050505") # Main Black Background
        self.resizable(False, False)
        
        # Frameless window for custom styling matching the mockup
        #self.overrideredirect(True)

        self.serial_port = None
        self.serial_thread = None
        self.running = True
        
        # Virtual Gamepad Initialization
        try:
            self.gamepad = vg.VX360Gamepad()
            print("[Info] ViGEmBus Gamepad Berhasil Diinisialisasi!")
        except Exception as e:
            print(f"[Error] Gagal inisialisasi vgamepad (Cek driver ViGEmBus!): {e}")
            self.gamepad = None

        self.mapping = {
            "A": "XUSB_GAMEPAD_A",
            "S": "XUSB_GAMEPAD_B",
            "L": "XUSB_GAMEPAD_X",
            "K": "XUSB_GAMEPAD_Y"
        }
        
        # Load user saved settings if available
        self.load_settings()
        
        # Base colors from the image
        self.colors_off = ["#4bc565", "#ffe04a", "#ffe04a", "#4bc565"]
        self.colors_on  = ["#81c784", "#fff59d", "#fff59d", "#81c784"]

        self.setup_ui()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Drag mechanics for frameless window
        self.bind("<ButtonPress-1>", self.start_move)
        self.bind("<ButtonRelease-1>", self.stop_move)
        self.bind("<B1-Motion>", self.do_move)

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def stop_move(self, event):
        self.x = None
        self.y = None

    def do_move(self, event):
        if not hasattr(self, 'x') or self.x is None:
            return
        deltax = event.x - self.x
        deltay = event.y - self.y
        new_x = self.winfo_x() + deltax
        new_y = self.winfo_y() + deltay
        self.geometry(f"+{new_x}+{new_y}")

    def setup_ui(self):
        self.grid_rowconfigure(0, weight=0) # Top Red Bar
        self.grid_rowconfigure(1, weight=0) # Header
        self.grid_rowconfigure(2, weight=1) # Center/Visualizer
        self.grid_rowconfigure(3, weight=0) # Bottom/Settings
        self.grid_columnconfigure(0, weight=1)

        # ---------------------------------------------------------
        # TOP RED BAR
        # ---------------------------------------------------------
        self.top_bar = ctk.CTkFrame(self, fg_color="#b23a3a", height=12, corner_radius=0)
        self.top_bar.grid(row=0, column=0, sticky="ew")

        # ---------------------------------------------------------
        # HEADER
        # ---------------------------------------------------------
        self.header_frame = ctk.CTkFrame(self, fg_color="#050505")
        self.header_frame.grid(row=1, column=0, sticky="ew", pady=(15, 10), padx=30)
        self.header_frame.grid_columnconfigure(0, weight=1) # Left
        self.header_frame.grid_columnconfigure(1, weight=1) # Center Logo
        self.header_frame.grid_columnconfigure(2, weight=1) # Right title
        self.header_frame.grid_columnconfigure(3, weight=0) # Close buttons

        self.title_left = ctk.CTkLabel(
            self.header_frame, text="DAI KAZOKU", 
            font=ctk.CTkFont(size=32, weight="bold"), text_color="#ffffff"
        )
        self.title_left.grid(row=0, column=0, sticky="w")
        
        # Logo Placeholder / Image
        try:
            logo_img_data = Image.open("logo.png")
            
            # Sesuaikan ukuran size=(width, height)
            logo_image = ctk.CTkImage(light_image=logo_img_data, dark_image=logo_img_data, size=(150, 45))
            
            self.logo_label = ctk.CTkLabel(
                self.header_frame, 
                text="",  # Kosongkan text karena menggunakan gambar
                image=logo_image
            )
        except Exception as e:
            print(f"[Info] Gambar logo tidak dimuat ({e}), menggunakan teks default.")
            self.logo_label = ctk.CTkLabel(
                self.header_frame, text="ANIMAL KAISER", 
                font=ctk.CTkFont(size=20, slant="italic", weight="bold"), text_color="#ff9800"
            )
        
        self.logo_label.grid(row=0, column=1)

        self.title_right = ctk.CTkLabel(
            self.header_frame, text="CONTROLLER\nDRIVER", 
            font=ctk.CTkFont(size=22, weight="bold"), text_color="#ffffff", justify="left"
        )
        self.title_right.grid(row=0, column=2, sticky="e", padx=(0, 20))

        # Close / Minimize buttons
        self.btn_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.btn_frame.grid(row=0, column=3, sticky="e")

        self.min_btn = ctk.CTkButton(
            self.btn_frame, text="—", width=40, height=30, fg_color="transparent", 
            text_color="white", hover_color="#333333", font=ctk.CTkFont(size=20, weight="bold"),
            command=self.iconify
        )
        self.min_btn.pack(side="left", padx=5)

        self.close_btn = ctk.CTkButton(
            self.btn_frame, text="✕", width=40, height=30, fg_color="transparent", 
            text_color="white", hover_color="#e53935", font=ctk.CTkFont(size=20, weight="bold"),
            command=self.on_closing
        )
        self.close_btn.pack(side="left")

        # ---------------------------------------------------------
        # CENTER PANEL (Visualizer)
        # ---------------------------------------------------------
        self.center_frame = ctk.CTkFrame(self, fg_color="#4d4d4d", corner_radius=20) 
        self.center_frame.grid(row=2, column=0, padx=60, pady=10, sticky="nsew")
        self.center_frame.grid_rowconfigure(0, weight=1)
        self.center_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.shadow_frame = ctk.CTkFrame(self.center_frame, fg_color="#333333", corner_radius=20, height=30)
        self.shadow_frame.place(relx=0, rely=1.0, relwidth=1.0, relheight=0.1, anchor="sw")
        self.shadow_frame.lower() 

        self.ui_buttons = {}
        for i in range(4):
            btn_container = ctk.CTkFrame(self.center_frame, fg_color="transparent", width=120, height=120)
            btn_container.grid(row=0, column=i, padx=5, pady=30)
            btn_container.grid_propagate(False)

            outer_shadow = ctk.CTkButton(
                btn_container, text="", width=120, height=120, corner_radius=60, 
                fg_color="#368c46" if i in [0,3] else "#d4b83b", hover=False, state="disabled"
            )
            outer_shadow.place(relx=0.5, rely=0.53, anchor="center")

            outer_btn = ctk.CTkButton(
                btn_container, text="", width=120, height=120, corner_radius=60, 
                fg_color=self.colors_off[i], hover=False, state="disabled"
            )
            outer_btn.place(relx=0.5, rely=0.5, anchor="center")
            
            inner_lbl = ctk.CTkLabel(
                outer_btn, text=str(i+1), width=32, height=32, corner_radius=16,
                fg_color="#e53935", text_color="white", font=ctk.CTkFont(size=14, weight="bold")
            )
            inner_lbl.place(relx=0.5, rely=0.5, anchor="center")

            self.ui_buttons[f"BTN_{i+1}"] = outer_btn

        # ---------------------------------------------------------
        # BOTTOM PANEL (Settings)
        # ---------------------------------------------------------
        self.bottom_frame = ctk.CTkFrame(self, fg_color="#050505")
        self.bottom_frame.grid(row=3, column=0, sticky="ew", padx=80, pady=(10, 30))
        
        self.bottom_frame.grid_columnconfigure((0,2,4), weight=0)
        self.bottom_frame.grid_columnconfigure((1,3,5), weight=1)

        # Get the mapping values in array format [1, 2, 3, 4] for loop logic
        key_list = ["A", "S", "K", "L"]
        current_vals = [self.mapping.get(k, "XUSB_GAMEPAD_A") for k in key_list]

        for i, row, col in [(0, 0, 0), (1, 1, 0), (2, 0, 2), (3, 1, 2)]:
            lbl = ctk.CTkLabel(self.bottom_frame, text=f"{i+1}", font=ctk.CTkFont(size=18, weight="bold"), text_color="white")
            lbl.grid(row=row, column=col, padx=(10, 10), pady=10, sticky="e")
            
            var = ctk.StringVar(value=current_vals[i])
            combo = ctk.CTkOptionMenu(
                self.bottom_frame, values=BUTTON_OPTIONS, variable=var,
                width=160, height=32, corner_radius=16,
                fg_color="#a3a3a3", button_color="#8c8c8c", button_hover_color="#737373", text_color="black",
                dropdown_fg_color="#e0e0e0", dropdown_text_color="black",
                command=lambda val, idx=i: self.update_mapping(idx, val)
            )
            combo.grid(row=row, column=col+1, padx=(0, 20), pady=10, sticky="w")

        port_lbl = ctk.CTkLabel(self.bottom_frame, text="Port", font=ctk.CTkFont(size=18, weight="bold"), text_color="white")
        port_lbl.grid(row=0, column=4, padx=(10, 10), pady=10, sticky="e")

        self.port_var = ctk.StringVar(value="Searching...")
        self.port_combo = ctk.CTkOptionMenu(
            self.bottom_frame, values=["Searching..."], variable=self.port_var, 
            width=140, height=32, corner_radius=16,
            fg_color="#a3a3a3", button_color="#8c8c8c", button_hover_color="#737373", text_color="black",
            dropdown_fg_color="#e0e0e0", dropdown_text_color="black",
            command=self.on_port_select
        )
        self.port_combo.grid(row=0, column=5, padx=(0, 10), pady=10, sticky="w")
        
        self.port_combo.bind("<Enter>", lambda e: self.refresh_ports())
        self.refresh_ports()

    def update_mapping(self, idx, value):
        key_list = ["A", "S", "K", "L"]
        target_key = key_list[idx]
        self.mapping[target_key] = value
        self.save_settings()

    def load_settings(self):
        """Loads controller settings from JSON file if it exists."""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    saved_mapping = json.load(f)
                    
                    # Merge with defaults to ensure all keys exist
                    for k, v in saved_mapping.items():
                        if k in self.mapping and v in XBOX_BUTTONS:
                            self.mapping[k] = v
                print("[Info] Loaded settings from", CONFIG_FILE)
            except Exception as e:
                print(f"[Error] Failed to load settings: {e}")

    def save_settings(self):
        """Saves current controller settings to JSON file."""
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(self.mapping, f, indent=4)
        except Exception as e:
            print(f"[Error] Failed to save settings: {e}")

    def refresh_ports(self):
        """Fetches available COM ports from system and lists them."""
        ports = [port.device for port in serial.tools.list_ports.comports()]
        
        if not ports:
            ports = ["No Ports Found"]
        
        self.port_combo.configure(values=ports)
        if self.port_var.get() not in ports:
             self.port_var.set(ports[0])
             

    def on_port_select(self, p):
        if p == "No Ports Found" or not p:
            return
        
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
            time.sleep(0.5)

        try:
            self.serial_port = serial.Serial(p, 115200, timeout=1)
            print(f"[Info] Connected to {p} at 115200 bps")
            
            if self.serial_thread is None or not self.serial_thread.is_alive():
                self.running = True
                self.serial_thread = threading.Thread(target=self.serial_read_loop, daemon=True)
                self.serial_thread.start()
        except serial.SerialException as e:
            print(f"[Error] Failed to connect to {p}: {e}")

    def serial_read_loop(self):
        """Background thread loop to read serial data."""
        while self.running and self.serial_port and self.serial_port.is_open:
            try:
                if self.serial_port.in_waiting > 0:
                    raw_line = self.serial_port.readline()
                    line = raw_line.decode('utf-8', errors="ignore").strip()
                    if line:
                        self.process_serial_data(line)
            except Exception as e:
                print(f"[Error] Serial Read Exception: {e}")
                self.serial_port.close()
                break

    def process_serial_data(self, data):
        """Parses the data from ESP32: PRESS_A, RELEASE_A, etc."""
        if "_" not in data:
            return
            
        action, key = data.split("_", 1)
        
        if action == "PRESS":
            self.handle_press(key)
        elif action == "RELEASE":
            self.handle_release(key)

    def handle_press(self, key):
        key_map = {"A": 1, "S": 2, "K": 3, "L": 4}
        if key not in key_map: return
        
        idx = key_map[key] - 1
        
        ui_btn = self.ui_buttons[f"BTN_{idx+1}"]
        self.after(0, lambda btn=ui_btn, c=self.colors_on[idx]: btn.configure(fg_color=c))
        
        if not self.gamepad: return
        
        xbox_btn_name = self.mapping.get(key)
        if xbox_btn_name and xbox_btn_name in XBOX_BUTTONS:
            xbox_ctrl = XBOX_BUTTONS[xbox_btn_name]
            self.gamepad.press_button(button=xbox_ctrl)
            self.gamepad.update()

    def handle_release(self, key):
        key_map = {"A": 1, "S": 2, "K": 3, "L": 4}
        if key not in key_map: return
        
        idx = key_map[key] - 1
        
        ui_btn = self.ui_buttons[f"BTN_{idx+1}"]
        self.after(0, lambda btn=ui_btn, c=self.colors_off[idx]: btn.configure(fg_color=c))
        
        if not self.gamepad: return
        
        xbox_btn_name = self.mapping.get(key)
        if xbox_btn_name and xbox_btn_name in XBOX_BUTTONS:
            xbox_ctrl = XBOX_BUTTONS[xbox_btn_name]
            self.gamepad.release_button(button=xbox_ctrl)
            self.gamepad.update()

    def on_closing(self):
        """Cleanup resources on close"""
        self.running = False
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
            
        if self.serial_thread and self.serial_thread.is_alive():
            self.serial_thread.join(timeout=1.0)
            
        self.destroy()
        sys.exit(0)

if __name__ == "__main__":
    app = AnimalKaiserControllerApp()
    app.mainloop()