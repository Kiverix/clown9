import a2s
import tkinter as tk
from tkinter import ttk, messagebox
from threading import Thread
import queue
from datetime import datetime
import os
import webbrowser
import winsound
import unicodedata
import sys
import time
import threading

# Constants for server addresses
CGE7_193 = ('79.127.217.197', 22912) # The real cge7-193
#CGE7_193 = ('192.168.1.56', 27015) # Test server, do not use it.
SOURCE_TV = ('79.127.217.197', 22913)

# Constants for sound files
SOUND_FILES = {
    'ordinance': 'ordinance.wav',
    'ord_err': 'ord_err.wav',
    'ord_cry': 'ord_cry.wav',
    'ord_ren': 'ord_ren.wav',
    'mapswitch': 'mapswitch.wav',
    'ord_mapchange': 'ord_mapchange.wav',
    'thirty': 'thirty.wav',
    'fifteen': 'fifteen.wav',
    'five': 'five.wav',
    'new_cycle': 'new_cycle.wav',
    'open': 'open.wav',
    'close': 'close.wav',
    'toggle': 'toggle.wav'
}

class CombinedServerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("clown9.exe")
        self.root.geometry("800x800")
        
        # Initialize state variables
        self.initialize_state()
        
        # Set window icon
        self.set_window_icon()
        
        # Build UI
        self.create_widgets()
        self.setup_ui()
        
        # Start background processes
        self.start_background_processes()
        
        # Handle window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def initialize_state(self):
        """Initialize all state variables"""
        self.dark_mode = True
        self.current_command_sequence = []
        self.in_ordinance_map = False
        self.visited_maps = []
        self.ordinance_started = False
        self.ordinance_sound_played = False
        self.last_ord_err_sound_time = 0
        self.query_fail_count = 0
        self.max_query_fails = 5
        self.queue = queue.Queue()
        self.auto_refresh_id = None
        self.player_data = []
        self.player_data_time = None
        self.sound_played_minute = None
        self.connecting_dots = 0
        self.simulation_mode = False
        self.last_seen_map = None
        self.last_seen_ordinance_state = None
        self.connection_gap_count = 0
        self.max_connection_gap = 3
        self.last_input_time = None
        self.input_cooldown = 5
        self.previous_map_name = None
        self.last_map_name = None
        self.map_sound_played = {}
        self.last_time_sound_minute = None
        self.refresh_players_next = False
        self.last_ordinance_map = None  # Track last ordinance map for repeated inputs

    def set_window_icon(self):
        """Set the window icon if available"""
        try:
            icon_path = os.path.join(os.path.dirname(sys.argv[0]), "resources", "sourceclown.ico")
            self.root.iconbitmap(icon_path)
        except Exception:
            pass

    def create_widgets(self):
        """Create all UI widgets"""
        # Main container
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Top section with server info and map cycle
        self.create_top_section()
        
        # Players list section
        self.create_players_section()
        
        # Bottom controls
        self.create_bottom_controls()
        
        # Status bar and footer
        self.create_status_bar_and_footer()

    def create_top_section(self):
        """Create the top section with server info and map cycle"""
        self.top_frame = ttk.Frame(self.main_frame)
        self.top_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Server info frame
        self.server_info_frame = ttk.LabelFrame(self.top_frame, text="Server Info", width=300)
        self.server_info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        self.map_label = tk.Label(self.server_info_frame, text="Loading...", font=('Arial', 14))
        self.map_label.pack(pady=5)
        
        self.player_count_label = tk.Label(self.server_info_frame, text="Players: -/-", font=('Arial', 12))
        self.player_count_label.pack()
        
        self.joinable_label = tk.Label(self.server_info_frame, text="", font=('Arial', 10, "bold"))
        self.joinable_label.pack()

        self.sourcetv_status_label = tk.Label(self.server_info_frame, text="SourceTV: Checking...", font=('Arial', 10))
        self.sourcetv_status_label.pack(pady=(10, 0))

        # Ordinance commands frame
        self.ordinance_frame = ttk.LabelFrame(self.server_info_frame, text="Current Ordinance Commands")
        self.ordinance_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.ordinance_label = tk.Label(
            self.ordinance_frame,
            text="No commands to record yet",
            font=("Arial", 10),
            wraplength=250,
            justify="left"
        )
        self.ordinance_label.pack()

        # Map cycle frame
        self.map_cycle_frame = ttk.LabelFrame(self.top_frame, text="Map Cycle", width=300)
        self.map_cycle_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.current_map_label = tk.Label(
            self.map_cycle_frame, 
            text="Current map: Loading...",
            font=("Arial", 14, "bold"),
            justify="center"
        )
        self.current_map_label.pack(pady=(5, 0))
        
        self.adjacent_label = tk.Label(
            self.map_cycle_frame,
            font=("Arial", 10),
            justify="center"
        )
        self.adjacent_label.pack()
        
        self.countdown_label = tk.Label(
            self.map_cycle_frame,
            font=("Arial", 10, "bold"),
            justify="center"
        )
        self.countdown_label.pack()
        
        self.time_label = tk.Label(
            self.map_cycle_frame,
            font=("Arial", 10),
            justify="center"
        )
        self.time_label.pack()
        
        # Restart status label
        self.restart_status_label = tk.Label(
            self.map_cycle_frame,
            font=("Arial", 12, "bold"),
            justify="center"
        )
        self.restart_status_label.pack()

    def create_players_section(self):
        """Create the players list section"""
        self.players_frame = ttk.LabelFrame(self.main_frame, text="Players Online")
        self.players_frame.pack(fill=tk.BOTH, expand=True)
        
        self.players_tree = ttk.Treeview(self.players_frame, columns=('name', 'score', 'duration'), show='headings')
        self.players_tree.heading('name', text='Player Name')
        self.players_tree.heading('score', text='Score')
        self.players_tree.heading('duration', text='Time Played')
        
        self.players_tree.column('name', width=400)
        self.players_tree.column('score', width=150, anchor=tk.CENTER)
        self.players_tree.column('duration', width=150, anchor=tk.CENTER)
        
        self.scrollbar = ttk.Scrollbar(self.players_frame, orient=tk.VERTICAL, command=self.players_tree.yview)
        self.players_tree.configure(yscrollcommand=self.scrollbar.set)
        
        self.players_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def create_bottom_controls(self):
        """Create the bottom control buttons"""
        self.bottom_frame = ttk.Frame(self.main_frame)
        self.bottom_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.refresh_button = ttk.Button(self.bottom_frame, text="Refresh Now", command=self.refresh_data)
        self.refresh_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.auto_refresh_var = tk.BooleanVar(value=True)
        self.auto_refresh_check = ttk.Checkbutton(
            self.bottom_frame, 
            text="Auto-refresh every 5 seconds", 
            variable=self.auto_refresh_var,
            command=self.toggle_auto_refresh
        )
        self.auto_refresh_check.pack(side=tk.LEFT)
        
        self.dark_mode_button = ttk.Button(
            self.bottom_frame,
            text="Toggle Dark Mode",
            command=self.toggle_dark_mode,
        )
        self.dark_mode_button.pack(side=tk.LEFT, padx=10)
        
        self.simulate_button = ttk.Button(
            self.bottom_frame,
            text="Simulate Ordinance Maps",
            command=self.toggle_simulation
        )
        self.simulate_button.pack(side=tk.LEFT, padx=10)

    def create_status_bar_and_footer(self):
        """Create the status bar and footer links"""
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_bar = ttk.Label(self.main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        self.status_bar.pack(fill=tk.X, pady=(10, 0))

        # Footer links
        footer_frame = ttk.Frame(self.main_frame)
        footer_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.link_label = tk.Label(
            footer_frame,
            text="gaq9.com",
            fg="blue",
            cursor="hand2",
            font=("Arial", 10, "underline")
        )
        self.link_label.pack(side=tk.LEFT, anchor="sw")
        self.link_label.bind("<Button-1>", lambda e: webbrowser.open_new("https://gaq9.com"))

        self.kulcs_label = tk.Label(
            footer_frame,
            text="Kulcs means Key in Hungarian. General VC did not 'carry' the investigation.",
            font=("Arial", 10, "bold")
        )
        self.kulcs_label.pack(side=tk.RIGHT, anchor="se")

    def setup_ui(self):
        """Set initial UI colors"""
        if self.dark_mode:
            self.apply_dark_theme()
        else:
            self.apply_light_theme()

    def start_background_processes(self):
        """Start all background update processes"""
        self.refresh_data()
        self.root.after(100, self.process_queue)
        self.root.after(50, self.update_map_display)
        self.root.after(1000, self.update_player_durations)
        self.toggle_auto_refresh()
        self.root.after(250, self.animate_connecting)
        self.root.after(750, self.check_sourcetv)

    def toggle_dark_mode(self):
        """Toggle between dark and light mode"""
        self.dark_mode = not self.dark_mode
        self.play_sound('toggle')  # Play toggle.wav on theme switch
        if self.dark_mode:
            self.apply_dark_theme()
        else:
            self.apply_light_theme()
    
    def apply_dark_theme(self):
        """Apply dark theme colors"""
        bg_color = "#2d2d2d"
        fg_color = "#ffffff"
        entry_bg = "#3d3d3d"
        frame_bg = "#252525"
        
        self.root.configure(bg=bg_color)
        
        style = ttk.Style()
        style.theme_use('alt')
        
        style.configure('TFrame', background=bg_color)
        style.configure('TLabelframe', background=bg_color, foreground=fg_color)
        style.configure('TLabelframe.Label', background=bg_color, foreground=fg_color)
        
        tk_labels = [
            self.map_label, self.player_count_label, self.joinable_label,
            self.current_map_label, self.adjacent_label, self.countdown_label,
            self.time_label, self.kulcs_label, self.ordinance_label,
            self.restart_status_label
        ]
        
        for label in tk_labels:
            label.configure(bg=bg_color, fg=fg_color)
        
        self.link_label.configure(bg=bg_color, fg="blue")
        
        style.configure("Treeview", 
                       background=entry_bg,
                       foreground=fg_color,
                       fieldbackground=entry_bg)
        style.configure("Treeview.Heading", 
                       background=frame_bg,
                       foreground=fg_color)
        style.map('Treeview', background=[('selected', '#4a6987')])
        
        style.configure('TButton', 
                       background=frame_bg, 
                       foreground=fg_color,
                       bordercolor=frame_bg)
        
        style.configure('TCheckbutton', 
                       background=bg_color, 
                       foreground=fg_color)
        
        style.configure('TLabel', background=frame_bg, foreground=fg_color)
        
        self.refresh_ui_state()

    def apply_light_theme(self):
        """Apply light theme colors"""
        style = ttk.Style()
        style.theme_use('default')
        
        self.root.configure(bg="SystemButtonFace")
        
        tk_labels = [
            self.map_label, self.player_count_label, self.joinable_label,
            self.current_map_label, self.adjacent_label, self.countdown_label,
            self.time_label, self.kulcs_label, self.ordinance_label,
            self.restart_status_label
        ]
        
        for label in tk_labels:
            label.configure(bg="SystemButtonFace", fg="black")
        
        self.link_label.configure(bg="SystemButtonFace", fg="blue")
        
        self.refresh_ui_state()

    def refresh_ui_state(self):
        """Refresh UI state after theme change"""
        self.status_var.set("Querying server...")
        self.refresh_button.config(state=tk.DISABLED)
        Thread(target=self.query_server, daemon=True).start()

    def toggle_auto_refresh(self):
        """Toggle auto refresh on/off"""
        if self.auto_refresh_var.get():
            self.schedule_auto_refresh()
        else:
            if self.auto_refresh_id:
                self.root.after_cancel(self.auto_refresh_id)
                self.auto_refresh_id = None
    
    def schedule_auto_refresh(self):
        """Schedule the next auto refresh"""
        if self.auto_refresh_var.get():
            self.refresh_data()
            self.auto_refresh_id = self.root.after(5000, self.schedule_auto_refresh)

    def get_map_based_on_utc_hour(self, hour=None):
        """Get map name based on UTC hour"""
        if hour is None:
            hour = datetime.utcnow().hour
        
        map_hours = {
            0: "askask",
            1: "ask",
            2: "ask",
            3: "askask",
            4: "ask",
            5: "dustbowl",
            6: "askask",
            7: "ask",
            8: "ask",
            9: "askask",
            10: "ask",
            11: "dustbowl",
            12: "askask",
            13: "ask",
            14: "ask",
            15: "askask",
            16: "ask",
            17: "dustbowl",
            18: "askask",
            19: "ask",
            20: "dustbowl",
            21: "askask",
            22: "ask",
            23: "dustbowl"
        }
        return map_hours[hour]
    
    def get_adjacent_maps(self):
        """Get previous and next map in cycle with time remaining"""
        current_hour = datetime.utcnow().hour
        current_minute = datetime.utcnow().minute
        current_second = datetime.utcnow().second
        
        prev_hour = current_hour - 1
        if prev_hour < 0:
            prev_hour = 23
        prev_map = self.get_map_based_on_utc_hour(prev_hour)
        
        next_hour = current_hour + 1
        if next_hour > 23:
            next_hour = 0
        next_map = self.get_map_based_on_utc_hour(next_hour)
        
        seconds_remaining = (59 - current_second) % 60
        minutes_remaining = (59 - current_minute) % 60
        
        return prev_map, next_map, minutes_remaining, seconds_remaining
    
    def play_sound(self, sound_key):
        """Play a sound file in a separate thread"""
        def play():
            try:
                sound_file = SOUND_FILES.get(sound_key)
                if sound_file:
                    sound_path = os.path.join(os.path.dirname(sys.argv[0]), "resources", sound_file)
                    if os.path.exists(sound_path):
                        winsound.PlaySound(sound_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
            except Exception:
                pass
                
        threading.Thread(target=play, daemon=True).start()

    def update_map_display(self):
        """Update the map and time display"""
        utc_now = datetime.utcnow()
        local_now = datetime.now()
        
        utc_time = utc_now.strftime("%H:%M:%S")
        local_time = local_now.strftime("%H:%M:%S")
        
        current_map = self.get_map_based_on_utc_hour()
        prev_map, next_map, mins_left, secs_left = self.get_adjacent_maps()
        
        # Determine restart status
        current_minute = utc_now.minute
        current_second = utc_now.second
        
        if current_minute == 59 and current_second >= 0:
            restart_status = "FIRST RESTART"
            status_color = "blue"
        elif current_minute == 0 and current_second <= 10:
            restart_status = "SECOND RESTART"
            status_color = "blue"
        else:
            restart_status = "IN SESSION"
            status_color = "green"
        
        self.time_label.config(text=f"UTC: {utc_time} | Local: {local_time}")
        self.current_map_label.config(text=f"Current Map Cycle: {current_map}")
        self.adjacent_label.config(text=f"Previous Map Cycle: {prev_map} | Next Map Cycle: {next_map}")
        self.countdown_label.config(text=f"Next cycle in: {mins_left:02d}m {secs_left:02d}s")
        self.restart_status_label.config(text=f"Server Status: {restart_status}", fg=status_color)

        # Play time warning sounds
        self.handle_time_warning_sounds(utc_now)

        # Play new cycle sound at hour change
        if utc_now.minute == 59 and utc_now.second == 0:
            if self.sound_played_minute != utc_now.hour:
                self.play_sound('new_cycle')
                self.sound_played_minute = utc_now.hour
        elif utc_now.minute != 59:
            self.sound_played_minute = None
        
        self.root.after(50, self.update_map_display)

    def handle_time_warning_sounds(self, utc_now):
        """Handle playing time warning sounds"""
        current_minute = utc_now.minute
        current_second = utc_now.second
        
        if current_second == 0:  # Only check at the start of each minute
            if current_minute == 30 and self.last_time_sound_minute != 30:
                self.play_sound('thirty')
                self.last_time_sound_minute = 30
            elif current_minute == 45 and self.last_time_sound_minute != 45:
                self.play_sound('fifteen')
                self.last_time_sound_minute = 45
            elif current_minute == 55 and self.last_time_sound_minute != 55:
                self.play_sound('five')
                self.last_time_sound_minute = 55
            elif current_minute not in (30, 45, 55):
                self.last_time_sound_minute = None

    def refresh_data(self):
        """Refresh server data"""
        self.status_var.set("Querying server...")
        self.refresh_button.config(state=tk.DISABLED)
        Thread(target=self.query_server, daemon=True).start()
    
    def query_server(self):
        """Query the server for information"""
        try:
            info = a2s.info(CGE7_193)
            players = a2s.players(CGE7_193)

            # Reset gap counter on successful connection
            self.connection_gap_count = 0

            # Process map information
            current_map = self.process_map_info(info)

            # Handle ordinance tracking
            self.handle_ordinance_tracking(current_map, players)

            # Update last seen state
            self.last_seen_map = current_map
            self.last_seen_ordinance_state = {
                "started": self.ordinance_started,
                "visited_maps": self.visited_maps.copy()
            }
            
            self.queue.put(('success', info, players))
            
        except Exception as e:
            self.handle_query_error()

    def process_map_info(self, info):
        """Process and normalize map information"""
        if not hasattr(self, 'previous_map_name'):
            self.previous_map_name = None
            
        prev_map = self.previous_map_name
        current_map_name = info.map_name.lower() if info.map_name else "unknown"

        # Handle unknown map cases
        if current_map_name == "unknown":
            if prev_map == "2fort":
                info.map_name = self.get_map_based_on_utc_hour()
                current_map_name = info.map_name.lower()
            elif prev_map in ("ask", "askask"):
                info.map_name = "mazemazemazemaze"
                current_map_name = "mazemazemazemaze"
            elif prev_map == "noaccess":
                info.map_name = "kurt"
                current_map_name = "kurt"

        # Save for next call
        self.previous_map_name = current_map_name
        return current_map_name

    def handle_ordinance_tracking(self, current_map, players):
        """Handle ordinance map tracking logic with support for repeated maps"""
        # Handle ordinance tracking during connection gaps
        if (self.last_seen_map == current_map and 
            self.last_seen_ordinance_state is not None):
            # We've reconnected to same map - maintain ordinance state
            self.ordinance_started = self.last_seen_ordinance_state["started"]
            self.visited_maps = self.last_seen_ordinance_state["visited_maps"]
        
        # Handle map sound effects
        self.handle_map_sounds(current_map)

        # Ordinance input tracking
        if current_map == "ordinance":
            if not self.ordinance_started:
                self.ordinance_started = True
                self.current_command_sequence = ["ORDINANCE"]
                self.visited_maps = []
                self.last_input_time = None
                self.last_ordinance_map = None  # Track last ordinance map
                self.update_ordinance_display()
        elif current_map.startswith('ord_'):
            if self.ordinance_started:
                self.process_ordinance_command(current_map, players)
        else:
            if self.ordinance_started:
                self.ordinance_started = False
                self.update_ordinance_display()

    def handle_map_sounds(self, current_map):
        """Handle playing sounds for map changes"""
        # Reset sound flag if map changes
        if not hasattr(self, 'last_map_name'):
            self.last_map_name = None
            
        last_map_name = self.last_map_name

        # If map changed, reset sound flag for this map
        if last_map_name != current_map:
            self.map_sound_played[current_map] = False

        # Play sound only if not played for this map visit
        if not self.map_sound_played.get(current_map, False):
            if current_map == "ordinance":
                self.play_sound('ordinance')
                self.ordinance_sound_played = True
            else:
                self.ordinance_sound_played = False

            if current_map == 'ord_error':
                self.play_sound('ord_err')
                self.last_ord_err_sound_time = time.time()

            if current_map == 'ord_cry':
                self.play_sound('ord_cry')

            if (current_map.startswith('ord_') and
                current_map != 'ord_ren' and
                current_map != 'ord_error' and
                current_map != 'ord_cry'):
                self.play_sound('ord_mapchange')
            elif not current_map.startswith('ord'):
                # Only play mapswitch.wav if this is not the very first map after app start
                if self.last_map_name is not None:
                    self.play_sound('mapswitch')

            self.map_sound_played[current_map] = True

        self.last_map_name = current_map

    def process_ordinance_command(self, current_map, players):
        """Process an ordinance command from map name with support for repeated maps"""
        map_cmd = current_map[4:].lower()
        valid_commands = {
            "xufunc": "XU",
            "ydfunc": "YD",
            "xdfunc": "XD",
            "yufunc": "YU",
            "zufunc": "ZU",
            "zdfunc": "ZD",
            "afunc": "A",
            "bfunc": "B",
            "cfunc": "C",
            "ren": "REN"
        }

        if map_cmd in valid_commands:
            cmd_short = valid_commands[map_cmd]
            current_time = time.time()
            
            # Always count the command if:
            # 1. It's different from the last one, or
            # 2. It's the same but we've verified the map actually changed via SourceTV
            should_count = False
            
            # Check if this is a different command than last time
            if not self.visited_maps or cmd_short != self.visited_maps[-1]:
                should_count = True
            # Same command - verify map actually changed via SourceTV
            elif current_map != self.last_ordinance_map:
                should_count = True
                # Double-check with SourceTV if available
                try:
                    sourcetv_info = a2s.info(SOURCE_TV, timeout=1.0)
                    if sourcetv_info.map_name.lower() == current_map:
                        should_count = True
                    else:
                        should_count = False  # SourceTV shows different map
                except:
                    pass  # If SourceTV check fails, proceed with our assumption
            
            if should_count:
                self.visited_maps.append(cmd_short)
                self.last_input_time = current_time
                self.last_ordinance_map = current_map
                self.update_ordinance_display()
                
                if map_cmd == "ren":
                    self.save_ordinance_sequence(players)
                    self.ordinance_started = False
                    self.last_input_time = None
                    self.last_ordinance_map = None

    def handle_query_error(self):
        """Handle errors when querying the server"""
        self.connection_gap_count += 1
        
        # If we're within allowed gap limit and were tracking ordinance, maintain state
        if (self.connection_gap_count <= self.max_connection_gap and 
            self.last_seen_ordinance_state is not None):
            
            # Reset input timer to allow repeats after gap
            self.last_input_time = None
            
            # Create dummy info with last seen map
            class DummyInfo:
                def __init__(self, map_name):
                    self.map_name = map_name
                    self.player_count = 0
                    self.max_players = 0
            
            info = DummyInfo(self.last_seen_map)
            self.queue.put(('success', info, []))
            
            self.status_var.set(f"Connection gap {self.connection_gap_count}/{self.max_connection_gap} - maintaining state")
        else:
            # Too many gaps or no previous state - go offline
            if self.connection_gap_count >= self.max_connection_gap:
                self.queue.put(('offline', None))
            else:
                self.queue.put(('error', str()))

    def update_ordinance_display(self):
        """Update the ordinance command display"""
        display_text = ""
        
        # Show current sequence if any
        if self.ordinance_started:
            display_text = "Current sequence: ORDINANCE " + " ".join(self.visited_maps)
        elif self.visited_maps:
            display_text = "Last sequence: ORDINANCE " + " ".join(self.visited_maps)
        
        if not display_text:
            display_text = "No commands recorded"
        
        self.ordinance_label.config(text=display_text.strip())
    
    def animate_connecting(self):
        """Animate connecting dots for player names"""
        self.connecting_dots = (self.connecting_dots + 1) % 4
        self.root.after(200, self.animate_connecting)

    def clean_player_name(self, name):
        """Clean and normalize player names for display"""
        if not name or name.lower() == "unknown":
            dots = '.' * self.connecting_dots
            return f"connecting{dots}"
        try:
            name = unicodedata.normalize('NFKC', name)
            name = ''.join(c for c in name if c.isprintable())
            return name
        except Exception:
            return name
    
    def process_queue(self):
        """Process messages from the server query queue"""
        try:
            result = self.queue.get_nowait()

            if result[0] == 'success':
                self.handle_success_result(*result[1:])
            elif result[0] == 'error':
                self.status_var.set("Error querying server, retrying...")
                self.refresh_data()
            elif result[0] == 'offline':
                self.handle_offline_result()

            self.refresh_button.config(state=tk.NORMAL)

        except queue.Empty:
            pass
        
        self.root.after(100, self.process_queue)

    def handle_success_result(self, info, players):
        """Handle successful server query result"""
        map_name = info.map_name if info.map_name else "unknown"
        self.map_label.config(text=f"Map: {map_name}")
        self.player_count_label.config(text=f"Players: {info.player_count}/{info.max_players}")

        if map_name.lower() == "2fort":
            self.joinable_label.config(
                text="Server is joinable on TF2. Join before it's too late!", 
                foreground="green"
            )
        else:
            self.joinable_label.config(
                text="Server is NOT joinable on TF2. Please wait for the next hour.", 
                foreground="red"
            )

        # Always refresh player list with server info
        self.update_player_list(players)

        self.status_var.set(f"Last updated: {datetime.now().strftime('%H:%M:%S')} | {len(players)} players online")

    def handle_offline_result(self):
        """Handle server offline result"""
        self.map_label.config(text="CGE7-193 IS OFFLINE")
        self.player_count_label.config(text="NOTIFY OTHER USERS")
        self.joinable_label.config(text="Server is not responding", foreground="red")
        self.status_var.set("Server is offline - last checked: " + datetime.now().strftime('%H:%M:%S'))

        # Clear player list
        for item in self.players_tree.get_children():
            self.players_tree.delete(item)

    def update_player_list(self, players):
        """Update the player list with new data"""
        for item in self.players_tree.get_children():
            self.players_tree.delete(item)

        self.player_data = []
        for player in players:
            self.player_data.append({
                "name": player.name,
                "score": player.score,
                "duration": float(player.duration)
            })
        self.player_data_time = datetime.now()

        for pdata in self.player_data:
            name = self.clean_player_name(pdata["name"])
            minutes = int(pdata["duration"]) // 60
            seconds = int(pdata["duration"]) % 60
            duration_str = f"{minutes}:{seconds:02d}"
            item_id = self.players_tree.insert('', tk.END, values=(
                name,
                pdata["score"],
                duration_str
            ))
            self.apply_player_name_styling(name, item_id)

    def apply_player_name_styling(self, name, item_id):
        """Apply special styling to certain player names"""
        lower_name = name.lower()
        
        # Red for certain names
        if any(term in lower_name for term in ["strider", "fuck interloper", "000.jar"]):
            self.players_tree.tag_configure("red_name", foreground="red")
            self.players_tree.item(item_id, tags=("red_name",))
        # Bold light blue for trusted names
        elif any(term in lower_name for term in [
            "weej", "sierra", "clown", "toaleken", "tomokush", 
            "novaandrew", "roulxs", "aruzaniac", "alistair"
        ]):
            self.players_tree.tag_configure("bold_blue", foreground="#4fc3f7", font=("Arial", 10, "bold"))
            self.players_tree.item(item_id, tags=("bold_blue",))

    def update_player_durations(self):
        """Update player durations in the list every second"""
        if self.player_data and self.player_data_time:
            elapsed = (datetime.now() - self.player_data_time).total_seconds()
            for idx, pdata in enumerate(self.player_data):
                name = self.clean_player_name(pdata["name"])
                updated_duration = pdata["duration"] + elapsed
                minutes = int(updated_duration) // 60
                seconds = int(updated_duration) % 60
                duration_str = f"{minutes}:{seconds:02d}"
                item_id = self.players_tree.get_children()[idx]
                self.players_tree.item(item_id, values=(
                    name,
                    pdata["score"],
                    duration_str
                ))
        # Refresh durations every second
        self.root.after(1000, self.update_player_durations)
        self.root.after(5000, self.refresh_data)

    def check_sourcetv(self):
        """Check if SourceTV is online and update label"""
        try:
            info = a2s.info(SOURCE_TV, timeout=2.0)
            status_text = "Online"
            status_color = "green"
        except Exception:
            status_text = "Offline"
            status_color = "red"

        self.sourcetv_status_label.config(
            text=f"SourceTV: {status_text}",
            fg=status_color
        )
        
        self.root.after(1000, self.check_sourcetv)

    def save_ordinance_sequence(self, players):
        """Save the current ordinance sequence to file"""
        sequence_str = "ORDINANCE " + " ".join(self.visited_maps)
        utc_now = datetime.utcnow()
        utc_str = utc_now.strftime("%Y-%m-%d %H:%M:%S UTC")
        local_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S Local")
        timestamp = utc_now.strftime("%Y-%m-%d_%H-%M-%S_UTC")
        
        # Get the directory where the script is running
        base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        output_dir = os.path.join(base_dir, "ordinance_output")
        
        # Create the output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        filename = f"ordinance_sequence_{timestamp}.txt"
        filepath = os.path.join(output_dir, filename)

        # Get connected players at ren
        player_list = []
        for p in players:
            if hasattr(p, 'name') and p.name:
                player_list.append(self.clean_player_name(p.name))
        player_list_str = "\n".join(player_list)

        with open(filepath, "w") as f:
            f.write(f"UTC Timestamp: {utc_str}\n")
            f.write(f"Local Timestamp: {local_now}\n")
            f.write("Ordinance Sequence:\n")
            f.write(sequence_str + "\n\n")
            f.write("Connected Players at REN:\n")
            f.write(player_list_str + "\n")

        # Play the ord_ren sound when file is created
        self.play_sound('ord_ren')

        # Append to master log (no player list)
        master_log_path = os.path.join(output_dir, "ordinance_master_log.txt")
        with open(master_log_path, "a") as f:
            f.write(f"{utc_str} | {local_now}: {sequence_str}\n")

        self.current_command_sequence = []
        self.visited_maps = []  # Clear visited maps after REN
        self.update_ordinance_display()

    def toggle_simulation(self):
        """Toggle simulation mode on/off"""
        self.simulation_mode = not self.simulation_mode

        if self.simulation_mode:
            # Stop auto-refresh during simulation
            if self.auto_refresh_id:
                self.root.after_cancel(self.auto_refresh_id)
                self.auto_refresh_id = None
            self.simulate_button.config(text="Stop Simulation")
            self.status_var.set("Ordinance simulation started")
            Thread(target=self.start_simulation, daemon=True).start()
        else:
            self.simulate_button.config(text="Simulate Ordinance Maps")
            self.status_var.set("Ordinance simulation stopped")
            # Resume auto-refresh if enabled
            if self.auto_refresh_var.get():
                self.schedule_auto_refresh()

    def start_simulation(self):
        """Cycle through simulated ordinance maps, stop and reload on ord_ren"""
        import random

        # Define multiple simulation map cycles
        simulation_cycles = [
            [
                "ord_xdfunc",
                "ord_ydfunc",
                "ord_ren"
            ],
            [
                "ord_xufunc",
                "ord_yufunc",
                "ord_zdfunc",
                "ord_ren"
            ],
            [
                "ord_afunc",
                "ord_bfunc",
                "ord_cfunc",
                "ord_ren"
            ]
        ]
        cycle_index = 0
        
        # Prepare simulation log file with UTC timestamp in filename
        sim_utc_now = datetime.utcnow()
        sim_timestamp = sim_utc_now.strftime("%Y-%m-%d_%H-%M-%S_UTC")
        base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        sim_output_dir = os.path.join(base_dir, "ordinance_simulation_output")
        os.makedirs(sim_output_dir, exist_ok=True)
        sim_log_path = os.path.join(sim_output_dir, f"simulation_results_{sim_timestamp}.txt")
        with open(sim_log_path, "w") as sim_log:
            sim_log.write("Ordinance Simulation Results\n")
            sim_log.write("="*32 + "\n\n")

            while self.simulation_mode and cycle_index < len(simulation_cycles):
                simulation_maps = simulation_cycles[cycle_index]
                simulated_players = [
                    f"SimPlayer{random.randint(1,99)}",
                    f"SimPlayer{random.randint(100,199)}",
                    f"SimPlayer{random.randint(200,299)}"
                ]
                
                # Start with ordinance map to trigger ORDINANCE
                self.map_label.config(text=f"Map: ordinance (Simulation)")
                self.ordinance_started = True
                self.current_command_sequence = ["ORDINANCE"]
                self.visited_maps = []
                self.update_ordinance_display()
                self.play_sound('ordinance')
                
                # Wait a moment before starting sequence
                for _ in range(10):
                    if not self.simulation_mode:
                        return
                    self.root.after(100)
                    self.root.update()
                
                for map_name in simulation_maps:
                    if not self.simulation_mode:
                        return

                    # Update the map display
                    self.map_label.config(text=f"Map: {map_name} (Simulation)")

                    # Play ord_err sound if needed
                    if map_name == 'ord_err':
                        self.play_sound('ord_err')

                    # Play ord_mapchange.wav on ord_ map change (except ord_ren)
                    if map_name.startswith('ord_') and map_name != 'ord_ren' and map_name != 'ord_err':
                        self.play_sound('ord_mapchange')

                    # Simulate player list in the UI
                    for item in self.players_tree.get_children():
                        self.players_tree.delete(item)
                    for pname in simulated_players:
                        self.players_tree.insert('', tk.END, values=(
                            pname, 
                            random.randint(0,100), 
                            f"{random.randint(0,59)}:{random.randint(0,59):02d}"
                        ))

                    # Process the map name (like it was a real map change)
                    if map_name.startswith('ord_'):
                        self.process_simulated_ordinance_command(map_name)
                    
                    # If ord_ren is reached, log the result, update display, then clear visited maps and break to load next cycle
                    if map_name == "ord_ren":
                        self.log_simulation_result(sim_log, cycle_index, simulated_players)
                        self.update_ordinance_display()  # Show REN before clearing
                        self.play_sound('ord_ren')
                        # Wait a moment so user can see REN in the UI
                        for _ in range(10):  # ~1 second
                            if not self.simulation_mode:
                                return
                            self.root.after(100)
                            self.root.update()
                        self.ordinance_started = False
                        self.visited_maps.clear()
                        self.update_ordinance_display()
                        break
                    
                    # Wait 3 seconds before next map
                    for _ in range(30):
                        if not self.simulation_mode:
                            return
                        self.root.after(100)
                        self.root.update()
                cycle_index += 1

            # After all cycles complete or simulation stopped
            self.simulation_mode = False
            self.simulate_button.config(text="Simulate Ordinance Maps")
            self.map_label.config(text="Map: Simulation Complete")
            self.status_var.set("Ordinance simulation completed")
            # Resume auto-refresh if enabled
            if self.auto_refresh_var.get():
                self.schedule_auto_refresh()

    def process_simulated_ordinance_command(self, map_name):
        """Process a simulated ordinance command"""
        map_cmd = map_name[4:].lower()
        valid_commands = {
            "xufunc": "XU",
            "ydfunc": "YD",
            "xdfunc": "XD",
            "yufunc": "YU",
            "zufunc": "ZU",
            "zdfunc": "ZD",
            "afunc": "A",
            "bfunc": "B",
            "cfunc": "C",
            "ren": "REN"
        }

        if map_cmd in valid_commands:
            cmd_short = valid_commands[map_cmd]
            if cmd_short not in self.visited_maps:
                self.visited_maps.append(cmd_short)
                self.update_ordinance_display()

    def log_simulation_result(self, log_file, cycle_index, simulated_players):
        """Log the result of a simulation cycle"""
        utc_now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        local_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S Local")
        log_file.write(f"Cycle {cycle_index+1}:\n")
        log_file.write("  Ordinance Sequence: ORDINANCE " + " ".join(self.visited_maps) + "\n")
        log_file.write(f"  Time at REN: {utc_now} | {local_now}\n")
        log_file.write("  Players at REN:\n")
        for pname in simulated_players:
            log_file.write(f"    {pname}\n")
        log_file.write("\n")

    def on_close(self):
        """Handle window close event"""
        try:
            sound_path = os.path.join(os.path.dirname(sys.argv[0]), "resources", "close.wav")
            if os.path.exists(sound_path):
                winsound.PlaySound(sound_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
                # Wait a bit so the sound can play before closing
                self.root.after(175, self.root.destroy)
                return
        except Exception:
            pass
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    # Play open.wav on launch
    try:
        sound_path = os.path.join(os.path.dirname(sys.argv[0]), "resources", "open.wav")
        if os.path.exists(sound_path):
            winsound.PlaySound(sound_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
    except Exception:
        pass
    app = CombinedServerApp(root)
    root.mainloop()