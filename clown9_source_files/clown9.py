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

SERVER_ADDRESS = ('79.127.217.197', 22912)

class CombinedServerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("clown9.exe")
        self.root.geometry("800x600")

        try:
            self.root.iconbitmap("sourceclown.ico")
        except:
            pass

        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.top_frame = ttk.Frame(self.main_frame)
        self.top_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.server_info_frame = ttk.LabelFrame(self.top_frame, text="Server Info", width=300)
        self.server_info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        self.map_label = ttk.Label(self.server_info_frame, text="Loading...", font=('Arial', 14))
        self.map_label.pack(pady=5)
        
        self.player_count_label = ttk.Label(self.server_info_frame, text="Players: -/-", font=('Arial', 12))
        self.player_count_label.pack()
        
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
        
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_bar = ttk.Label(self.main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        self.status_bar.pack(fill=tk.X, pady=(10, 0))

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

        self.kulcs_label = tk.Label(
            self.main_frame,
            text="Key means Kulcs in Hungarian",
            font=("Arial", 10, "bold"),
            anchor="e"
        )
        self.kulcs_label.pack(side=tk.RIGHT, anchor="se", pady=(0, 5))

        self.queue = queue.Queue()
        self.auto_refresh_id = None
        
        self.player_data = []
        self.player_data_time = None

        self.sound_played_minute = None
        
        self.refresh_data()
        self.root.after(100, self.process_queue)
        self.root.after(50, self.update_map_display)
        self.root.after(1000, self.update_player_durations)
        self.toggle_auto_refresh()
    
    def toggle_auto_refresh(self):
        if self.auto_refresh_var.get():
            self.schedule_auto_refresh()
        else:
            if self.auto_refresh_id:
                self.root.after_cancel(self.auto_refresh_id)
                self.auto_refresh_id = None
    
    def schedule_auto_refresh(self):
        if self.auto_refresh_var.get():
            self.refresh_data()
            self.auto_refresh_id = self.root.after(5000, self.schedule_auto_refresh)
    
    def get_map_based_on_utc_hour(self, hour=None):
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
        
        seconds_remaining = (60 - current_second) % 60
        minutes_remaining = (59 - current_minute) % 60
        
        return prev_map, next_map, minutes_remaining, seconds_remaining
    
    def update_map_display(self):
        utc_now = datetime.utcnow()
        local_now = datetime.now()
        
        utc_time = utc_now.strftime("%H:%M:%S")
        local_time = local_now.strftime("%H:%M:%S")
        
        current_map = self.get_map_based_on_utc_hour()
        prev_map, next_map, mins_left, secs_left = self.get_adjacent_maps()
        
        self.time_label.config(text=f"UTC: {utc_time} | Local: {local_time}")
        self.current_map_label.config(text=f"Current Map Cycle: {current_map}")
        self.adjacent_label.config(text=f"Previous Map Cycle: {prev_map} | Next Map Cycle: {next_map}")
        self.countdown_label.config(text=f"Next cycle in: {mins_left:02d}m {secs_left:02d}s")

        if mins_left == 0 and secs_left >= 59:
            if self.sound_played_minute != utc_now.hour:
                sound_path = os.path.join(os.getcwd(), "AIM_Sound.mp3")
                if os.path.exists(sound_path):
                    try:
                        winsound.PlaySound(sound_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
                    except Exception:
                        pass
                self.sound_played_minute = utc_now.hour
        elif mins_left != 0:
            self.sound_played_minute = None
        
        self.root.after(50, self.update_map_display)
    
    def refresh_data(self):
        self.status_var.set("Querying server...")
        self.refresh_button.config(state=tk.DISABLED)
        Thread(target=self.query_server, daemon=True).start()
    
    def query_server(self):
        try:
            info = a2s.info(SERVER_ADDRESS)
            players = a2s.players(SERVER_ADDRESS)
            self.queue.put(('success', info, players))
        except Exception as e:
            self.queue.put(('error', str(e)))
    
    def clean_player_name(self, name):
        if not name or name.lower() == "unknown":
            return "connecting..."
        try:
            name = unicodedata.normalize('NFKC', name)
            name = ''.join(c for c in name if c.isprintable())
            return name
        except Exception:
            return name
    
    def process_queue(self):
        try:
            result = self.queue.get_nowait()
            
            if result[0] == 'success':
                info, players = result[1], result[2]
                map_name = info.map_name if info.map_name else "unknown"
                self.map_label.config(text=f"Map: {map_name}")
                self.player_count_label.config(text=f"Players: {info.player_count}/{info.max_players}")
                
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
                    self.players_tree.insert('', tk.END, values=(
                        name,
                        pdata["score"],
                        duration_str
                    ))
                
                self.status_var.set(f"Last updated: {datetime.now().strftime('%H:%M:%S')} | {len(players)} players online")
            
            elif result[0] == 'error':
                self.status_var.set("Error querying server, retrying...")
                self.refresh_data()
            
            self.refresh_button.config(state=tk.NORMAL)
            
        except queue.Empty:
            pass
        
        self.root.after(100, self.process_queue)

    def update_player_durations(self):
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
    
if __name__ == "__main__":
    root = tk.Tk()
    app = CombinedServerApp(root)
    root.mainloop()

# Made by "the clown", @chernobyl_bag on Anomalous Materials