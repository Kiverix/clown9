import a2s
import tkinter as tk
from tkinter import ttk, messagebox
from threading import Thread
import queue
from datetime import datetime

SERVER_ADDRESS = ('79.127.217.197', 22912)

class CombinedServerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("clown9.exe")
        self.root.geometry("800x800")
        
        # Create main container
        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Top section - Server info and map cycle
        self.top_frame = ttk.Frame(self.main_frame)
        self.top_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Server info panel (left)
        self.server_info_frame = ttk.LabelFrame(self.top_frame, text="Server Info", width=300)
        self.server_info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        self.map_label = ttk.Label(self.server_info_frame, text="Loading...", font=('Arial', 14))
        self.map_label.pack(pady=5)
        
        self.player_count_label = ttk.Label(self.server_info_frame, text="Players: -/-", font=('Arial', 12))
        self.player_count_label.pack()
        
        # Map cycle panel (right)
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
        
        # Players section
        self.players_frame = ttk.LabelFrame(self.main_frame, text="Players Online")
        self.players_frame.pack(fill=tk.BOTH, expand=True)
        
        # Treeview for players
        self.players_tree = ttk.Treeview(self.players_frame, columns=('name', 'score', 'duration'), show='headings')
        self.players_tree.heading('name', text='Player Name')
        self.players_tree.heading('score', text='Score')
        self.players_tree.heading('duration', text='Time Played (sec)')
        
        self.players_tree.column('name', width=400)
        self.players_tree.column('score', width=150, anchor=tk.CENTER)
        self.players_tree.column('duration', width=150, anchor=tk.CENTER)
        
        self.scrollbar = ttk.Scrollbar(self.players_frame, orient=tk.VERTICAL, command=self.players_tree.yview)
        self.players_tree.configure(yscrollcommand=self.scrollbar.set)
        
        self.players_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bottom controls
        self.bottom_frame = ttk.Frame(self.main_frame)
        self.bottom_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Refresh button
        self.refresh_button = ttk.Button(self.bottom_frame, text="Refresh Now", command=self.refresh_data)
        self.refresh_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Auto-refresh toggle
        self.auto_refresh_var = tk.BooleanVar(value=True)
        self.auto_refresh_check = ttk.Checkbutton(
            self.bottom_frame, 
            text="Auto-refresh every 5 seconds", 
            variable=self.auto_refresh_var,
            command=self.toggle_auto_refresh
        )
        self.auto_refresh_check.pack(side=tk.LEFT)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_bar = ttk.Label(self.main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        self.status_bar.pack(fill=tk.X, pady=(10, 0))
        
        # Queue for thread communication
        self.queue = queue.Queue()
        
        # Schedule for auto-refresh
        self.auto_refresh_id = None
        
        # Initial data load
        self.refresh_data()
        
        # Start update checks
        self.root.after(100, self.process_queue)
        self.root.after(50, self.update_map_display)
        
        # Start auto-refresh if enabled
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
        self.current_map_label.config(text=f"Current map: {current_map}")
        self.adjacent_label.config(text=f"Previous: {prev_map} | Next: {next_map}")
        self.countdown_label.config(text=f"Next cycle in: {mins_left:02d}m {secs_left:02d}s")
        
        self.root.after(50, self.update_map_display)
    
    def refresh_data(self):
        self.status_var.set("Querying server...")
        self.refresh_button.config(state=tk.DISABLED)
        
        # Run the query in a separate thread to avoid freezing the GUI
        Thread(target=self.query_server, daemon=True).start()
    
    def query_server(self):
        try:
            # Get server info
            info = a2s.info(SERVER_ADDRESS)
            
            # Get player list
            players = a2s.players(SERVER_ADDRESS)
            
            # Put results in the queue
            self.queue.put(('success', info, players))
            
        except Exception as e:
            self.queue.put(('error', str(e)))
    
    def process_queue(self):
        try:
            result = self.queue.get_nowait()
            
            if result[0] == 'success':
                info, players = result[1], result[2]
                
                # Update server info
                self.map_label.config(text=f"Map: {info.map_name}")
                self.player_count_label.config(text=f"Players: {info.player_count}/{info.max_players}")
                
                # Clear existing player list
                for item in self.players_tree.get_children():
                    self.players_tree.delete(item)
                
                # Add players to the treeview
                for player in players:
                    self.players_tree.insert('', tk.END, values=(
                        player.name,
                        player.score,
                        f"{player.duration:.1f}"
                    ))
                
                self.status_var.set(f"Last updated: {datetime.now().strftime('%H:%M:%S')} | {len(players)} players online")
            
            elif result[0] == 'error':
                messagebox.showerror("Error", f"Failed to query server:\n{result[1]}")
                self.status_var.set("Error querying server")
            
            self.refresh_button.config(state=tk.NORMAL)
            
        except queue.Empty:
            pass
        
        self.root.after(100, self.process_queue)

if __name__ == "__main__":
    root = tk.Tk()
    app = CombinedServerApp(root)
    root.mainloop()