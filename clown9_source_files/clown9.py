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

# server addresses
CGE7_193 = ('79.127.217.197', 22912)
SOURCE_TV = ('79.127.217.197', 22913)

class CombinedServerApp:
    def __init__(self, root):
        # main window setup
        self.root = root
        self.root.title("clown9.exe")
        self.root.geometry("800x800")

        # dark mode state
        self.dark_mode = True
        
        # ordinance tracking
        self.ordinance_commands = []
        self.current_command_sequence = []
        self.in_ordinance_map = False

        # server status tracking
        self.query_fail_count = 0
        self.max_query_fails = 5

        # set window icon
        try:
            self.root.iconbitmap("sourceclown.ico")
        except:
            pass
        
        # build ui
        self.create_widgets()
        self.setup_ui()
        
        # data and refresh setup
        self.queue = queue.Queue()
        self.auto_refresh_id = None
        self.player_data = []
        self.player_data_time = None
        self.sound_played_minute = None
        self.connecting_dots = 0
        
        # visited maps tracking
        self.visited_maps = []  # Track visited ordinance maps

        # simulation mode
        self.simulation_mode = False  # Track if we're in simulation mode
        
        # start refresh loops
        self.refresh_data()
        self.root.after(100, self.process_queue)
        self.root.after(50, self.update_map_display)
        self.root.after(1000, self.update_player_durations)
        self.toggle_auto_refresh()
        self.root.after(250, self.animate_connecting)
        self.root.after(10000, self.check_sourcetv)
    
    def create_widgets(self):
        # create all ui widgets
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.top_frame = ttk.Frame(self.main_frame)
        self.top_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.server_info_frame = ttk.LabelFrame(self.top_frame, text="Server Info", width=300)
        self.server_info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        self.map_label = tk.Label(self.server_info_frame, text="Loading...", font=('Arial', 14))
        self.map_label.pack(pady=5)
        
        self.player_count_label = tk.Label(self.server_info_frame, text="Players: -/-", font=('Arial', 12))
        self.player_count_label.pack()
        
        self.joinable_label = tk.Label(self.server_info_frame, text="", font=('Arial', 10, "bold"))
        self.joinable_label.pack()

        # sourcetv status label
        self.sourcetv_status_label = tk.Label(self.server_info_frame, text="SourceTV: Checking...", font=('Arial', 10))
        self.sourcetv_status_label.pack(pady=(10, 0))

        # ordinance commands frame
        self.ordinance_frame = ttk.LabelFrame(self.server_info_frame, text="Latest Ordinance Commands")
        self.ordinance_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.ordinance_label = tk.Label(
            self.ordinance_frame,
            text="No commands recorded",
            font=("Arial", 10),
            wraplength=250,
            justify="left"
        )
        self.ordinance_label.pack()

        # map cycle info
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
        
        # players list
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
        
        # bottom bar
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
            command=self.toggle_dark_mode
        )
        self.dark_mode_button.pack(side=tk.LEFT, padx=10)
        
        self.simulate_button = ttk.Button(
            self.bottom_frame,
            text="Simulate Ordinance Maps",
            command=self.toggle_simulation
        )
        self.simulate_button.pack(side=tk.LEFT, padx=10)
        
        # status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_bar = ttk.Label(self.main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        self.status_bar.pack(fill=tk.X, pady=(10, 0))

        # link label
        self.link_label = tk.Label(
            self.main_frame,
            text="gaq9.com",
            fg="blue",
            cursor="hand2",
            font=("Arial", 10, "underline"),
            anchor="w"
        )
        self.link_label.pack(side=tk.LEFT, anchor="sw", pady=(0, 5))
        self.link_label.bind("<Button-1>", lambda e: webbrowser.open_new("https://gaq9.com"))

        # kulcs label
        self.kulcs_label = tk.Label(
            self.main_frame,
            text="Kulcs means Key in Hungarian. General VC did not 'carry' the investigation.",
            font=("Arial", 10, "bold"),
            anchor="e"
        )
        self.kulcs_label.pack(side=tk.RIGHT, anchor="se", pady=(0, 5))
    
    def setup_ui(self):
        # set initial ui colors
        if self.dark_mode:
            self.apply_dark_theme()
        else:
            self.apply_light_theme()
    
    def toggle_dark_mode(self):
        # toggle dark/light mode
        self.dark_mode = not self.dark_mode
        if self.dark_mode:
            self.apply_dark_theme()
        else:
            self.apply_light_theme()
    
    def apply_dark_theme(self):
        # set dark theme colors
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
            self.time_label, self.kulcs_label, self.ordinance_label
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
        self.status_var.set("Querying server...")
        self.refresh_button.config(state=tk.DISABLED)
        Thread(target=self.query_server, daemon=True).start()
    
    def apply_light_theme(self):
        # set light theme colors
        style = ttk.Style()
        style.theme_use('default')
        
        self.root.configure(bg="SystemButtonFace")
        
        tk_labels = [
            self.map_label, self.player_count_label, self.joinable_label,
            self.current_map_label, self.adjacent_label, self.countdown_label,
            self.time_label, self.kulcs_label, self.ordinance_label
        ]
        
        for label in tk_labels:
            label.configure(bg="SystemButtonFace", fg="black")
        
        self.link_label.configure(bg="SystemButtonFace", fg="blue")
        self.status_var.set("Querying server...")
        self.refresh_button.config(state=tk.DISABLED)
        Thread(target=self.query_server, daemon=True).start()

    def toggle_auto_refresh(self):
        # toggle auto refresh
        if self.auto_refresh_var.get():
            self.schedule_auto_refresh()
        else:
            if self.auto_refresh_id:
                self.root.after_cancel(self.auto_refresh_id)
                self.auto_refresh_id = None
    
    def schedule_auto_refresh(self):
        # schedule auto refresh
        if self.auto_refresh_var.get():
            self.refresh_data()
            self.auto_refresh_id = self.root.after(5000, self.schedule_auto_refresh)
    
    def get_map_based_on_utc_hour(self, hour=None):
        # get map name based on utc hour
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
        # get previous and next map in cycle
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
    
    def update_map_display(self):
        # update map and time display
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
            status_color = "red"
        elif current_minute == 0 and current_second <= 10:  # Show for first 10 seconds of new hour
            restart_status = "SECOND RESTART"
            status_color = "red"
        else:
            restart_status = "IN SESSION"
            status_color = "green"
        
        self.time_label.config(text=f"UTC: {utc_time} | Local: {local_time}")
        self.current_map_label.config(text=f"Current Map Cycle: {current_map}")
        self.adjacent_label.config(text=f"Previous Map Cycle: {prev_map} | Next Map Cycle: {next_map}")
        self.countdown_label.config(text=f"Next cycle in: {mins_left:02d}m {secs_left:02d}s")
        
        # Add restart status label if it doesn't exist
        if not hasattr(self, 'restart_status_label'):
            self.restart_status_label = tk.Label(
                self.map_cycle_frame,
                font=("Arial", 12, "bold"),
                justify="center"
            )
            self.restart_status_label.pack()
        
        self.restart_status_label.config(text=f"Server Status: {restart_status}", fg=status_color)

        if utc_now.minute == 59 and utc_now.second == 0:
            if self.sound_played_minute != utc_now.hour:
                sound_path = os.path.join(os.getcwd(), "AIM_Sound.mp3")
                if os.path.exists(sound_path):
                    try:
                        winsound.PlaySound(sound_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
                    except Exception:
                        pass
                self.sound_played_minute = utc_now.hour
        elif utc_now.minute != 59:
            self.sound_played_minute = None
        
        self.root.after(50, self.update_map_display)
    
    def refresh_data(self):
        # refresh server data
        self.status_var.set("Querying server...")
        self.refresh_button.config(state=tk.DISABLED)
        Thread(target=self.query_server, daemon=True).start()
    
    def query_server(self):
        # query server and process ordinance logic
        try:
            info = a2s.info(CGE7_193)
            players = a2s.players(CGE7_193)

            # Reset fail count on successful query
            self.query_fail_count = 0

            if not info.map_name or info.map_name.lower() == "unknown":
                current_cycle_map = self.get_map_based_on_utc_hour()

                if current_cycle_map in ["ask", "askask"]:
                    info.map_name = current_cycle_map

            if info.map_name.lower() == "ordinance":
                if not self.in_ordinance_map:
                    self.in_ordinance_map = True
                    self.current_command_sequence = []
                self.process_ordinance_commands(players)
            else:
                if self.in_ordinance_map:
                    self.in_ordinance_map = False
                    if self.current_command_sequence:
                        self.ordinance_commands.append(" ".join(self.current_command_sequence) + " REN")
                        self.current_command_sequence = []
                        self.update_ordinance_display()

            self.queue.put(('success', info, players))
        except Exception as e:
            self.query_fail_count += 1
            if self.query_fail_count >= self.max_query_fails:
                self.queue.put(('offline', None))
            else:
                self.queue.put(('error', str(e)))

    def process_ordinance_commands(self, players):
        # Process both player commands and map names
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
        
        # Process player commands
        for player in players:
            if hasattr(player, 'name') and player.name:
                name = player.name.lower()
                for cmd_key, cmd_short in valid_commands.items():
                    if cmd_key in name:
                        if cmd_short not in self.current_command_sequence:
                            self.current_command_sequence.append(cmd_short)
        
        # Process map name
        try:
            info = a2s.info(CGE7_193)
            if info.map_name.lower().startswith('ord_'):
                map_cmd = info.map_name[4:].lower()  # Remove 'ord_' prefix
                if map_cmd in valid_commands:
                    cmd_short = valid_commands[map_cmd]
                    if cmd_short not in self.visited_maps:
                        self.visited_maps.append(cmd_short)
                        self.update_ordinance_display()
        except:
            pass
        
        # Check for REN condition
        if self.current_command_sequence and any("ren" in p.name.lower() for p in players if hasattr(p, 'name') and p.name):
            self.save_ordinance_sequence(players)
    
    def update_ordinance_display(self):
        # Update ordinance command display with both visited maps and player commands
        
        # Show visited maps if any
        if self.visited_maps:
            display_text = "Recent commands: " + ", ".join(self.visited_maps) + "\n"

        # Show player commands if any
        if self.ordinance_commands:
            for cmd in reversed(self.ordinance_commands[-3:]):
                display_text += f"• {cmd}\n"
        
        if not self.visited_maps and not self.ordinance_commands:
            display_text = "No commands recorded"
        
        self.ordinance_label.config(text=display_text.strip())
    
    def animate_connecting(self):
        # animate connecting dots
        self.connecting_dots = (self.connecting_dots + 1) % 4
        self.root.after(200, self.animate_connecting)

    def clean_player_name(self, name):
        # clean player name for display
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
        # process server response queue
        try:
            result = self.queue.get_nowait()

            if result[0] == 'success':
                info, players = result[1], result[2]
                map_name = info.map_name if info.map_name else "unknown"
                self.map_label.config(text=f"Map: {map_name}")
                self.player_count_label.config(text=f"Players: {info.player_count}/{info.max_players}")

                if map_name.lower() == "2fort":
                    self.joinable_label.config(text="Server is joinable on TF2. Join before it's too late!", foreground="green")
                else:
                    self.joinable_label.config(text="Server is NOT joinable on TF2. Please wait for the next hour.", foreground="red")

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
                    if name.strip().lower() == "the clown":
                        self.players_tree.tag_configure("bold_clown", font=("Arial", 10, "bold"))
                        self.players_tree.item(item_id, tags=("bold_clown",))

                self.status_var.set(f"Last updated: {datetime.now().strftime('%H:%M:%S')} | {len(players)} players online")

            elif result[0] == 'error':
                self.status_var.set("Error querying server, retrying...")
                self.refresh_data()

            elif result[0] == 'offline':
                # Server is offline - update display
                self.map_label.config(text="CGE7-193 IS OFFLINE")
                self.player_count_label.config(text="NOTIFY OTHER USERS")
                self.joinable_label.config(text="Server is not responding", foreground="red")
                self.status_var.set("Server is offline - last checked: " + datetime.now().strftime('%H:%M:%S'))

                # Clear player list
                for item in self.players_tree.get_children():
                    self.players_tree.delete(item)

            self.refresh_button.config(state=tk.NORMAL)

        except queue.Empty:
            pass

        self.root.after(100, self.process_queue)

    def update_player_durations(self):
        # update player durations in the list
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
        self.root.after(1000, self.update_player_durations)
    
    def check_sourcetv(self):
        # check if sourcetv is online and update label
        try:
            info = a2s.info(SOURCE_TV, timeout=2.0)
            sourcetv_status = "SourceTV: "
            status_text = "Online"
            status_color = "green"
        except Exception as e:
            sourcetv_status = "SourceTV: "
            status_text = "Offline"
            status_color = "red"

        self.sourcetv_status_label.config(
            text=sourcetv_status + status_text,
            fg=status_color
        )
        
        self.root.after(30000, self.check_sourcetv)

    def save_ordinance_sequence(self, players):
        # Save the current sequence to file
        sequence_str = " ".join(self.current_command_sequence) + " REN"
        utc_now = datetime.utcnow()
        utc_str = utc_now.strftime("%Y-%m-%d %H:%M:%S UTC")
        local_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S Local")
        timestamp = utc_now.strftime("%Y-%m-%d_%H-%M-%S_UTC")
        base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        output_dir = os.path.join(base_dir, "ord_output")
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

        # Append to master log
        master_log_path = os.path.join(output_dir, "ordinance_master_log.txt")
        with open(master_log_path, "a") as f:
            f.write(f"{utc_str} | {local_now}: {sequence_str} | Players: {', '.join(player_list)}\n")

        self.ordinance_commands.append(sequence_str)
        self.current_command_sequence = []
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
        sim_output_dir = os.path.join(base_dir, "ord_sim_output")
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
                for map_name in simulation_maps:
                    if not self.simulation_mode:
                        return

                    # Update the map display
                    self.map_label.config(text=f"Map: {map_name} (Simulation)")

                    # Simulate player list in the UI
                    for item in self.players_tree.get_children():
                        self.players_tree.delete(item)
                    for pname in simulated_players:
                        self.players_tree.insert('', tk.END, values=(pname, random.randint(0,100), f"{random.randint(0,59)}:{random.randint(0,59):02d}"))

                    # Process the map name (like it was a real map change)
                    if map_name.startswith('ord_'):
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

                    # If ord_ren is reached, log the result, update display, then clear visited maps and break to load next cycle
                    if map_name == "ord_ren":
                        # Log simulation result for this cycle
                        utc_now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
                        local_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S Local")
                        sim_log.write(f"Cycle {cycle_index+1}:\n")
                        sim_log.write("  Ordinance Sequence: " + ", ".join(self.visited_maps) + "\n")
                        sim_log.write(f"  Time at REN: {utc_now} | {local_now}\n")
                        sim_log.write("  Players at REN:\n")
                        for pname in simulated_players:
                            sim_log.write(f"    {pname}\n")
                        sim_log.write("\n")
                        self.update_ordinance_display()  # Show REN before clearing
                        # Wait a moment so user can see REN in the UI
                        for _ in range(10):  # ~1 second
                            if not self.simulation_mode:
                                return
                            self.root.after(100)
                            self.root.update()
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

# run the app
if __name__ == "__main__":
    root = tk.Tk()
    app = CombinedServerApp(root)
    root.mainloop()