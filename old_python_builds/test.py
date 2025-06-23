import a2s
import tkinter as tk
from tkinter import ttk, messagebox
from threading import Thread
import queue

SERVER_ADDRESS = ('79.127.217.197', 22912)

class ServerQueryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Server Query Tool")
        self.root.geometry("500x400")

        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(self.main_frame, text="Server Info", font=('Arial', 12, 'bold')).grid(row=0, column=0, sticky=tk.W)
        
        self.info_frame = ttk.LabelFrame(self.main_frame, text="Current Map")
        self.info_frame.grid(row=1, column=0, sticky="ew", pady=5)
        
        self.map_label = ttk.Label(self.info_frame, text="Loading...", font=('Arial', 14))
        self.map_label.pack(pady=5)

        ttk.Label(self.main_frame, text="Players Online", font=('Arial', 12, 'bold')).grid(row=2, column=0, sticky=tk.W, pady=(10,0))
        
        self.players_frame = ttk.Frame(self.main_frame)
        self.players_frame.grid(row=3, column=0, sticky="nsew")

        self.players_tree = ttk.Treeview(self.players_frame, columns=('name', 'score', 'duration'), show='headings')
        self.players_tree.heading('name', text='Player Name')
        self.players_tree.heading('score', text='Score')
        self.players_tree.heading('duration', text='Time Played (min)')
        
        self.players_tree.column('name', width=250)
        self.players_tree.column('score', width=100, anchor=tk.CENTER)
        self.players_tree.column('duration', width=120, anchor=tk.CENTER)
        
        self.scrollbar = ttk.Scrollbar(self.players_frame, orient=tk.VERTICAL, command=self.players_tree.yview)
        self.players_tree.configure(yscrollcommand=self.scrollbar.set)
        
        self.players_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.refresh_button = ttk.Button(self.main_frame, text="Refresh", command=self.refresh_data)
        self.refresh_button.grid(row=4, column=0, pady=10)

        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_bar = ttk.Label(self.main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        self.status_bar.grid(row=5, column=0, sticky="ew", pady=(5,0))

        self.queue = queue.Queue()
        
        self.refresh_data()
        
        self.root.after(100, self.process_queue)
    
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
    
    def process_queue(self):
        try:
            result = self.queue.get_nowait()
            
            if result[0] == 'success':
                info, players = result[1], result[2]
                
                self.map_label.config(text=f"{info.map_name} ({info.player_count}/{info.max_players} players)")
                
                for item in self.players_tree.get_children():
                    self.players_tree.delete(item)
                
                for player in players:
                    self.players_tree.insert('', tk.END, values=(
                        player.name,
                        player.score,
                        f"{player.duration:.1f}"
                    ))
                
                self.status_var.set(f"Last updated: {len(players)} players online")
            
            elif result[0] == 'error':
                messagebox.showerror("Error", f"Failed to query server:\n{result[1]}")
                self.status_var.set("Error querying server")
            
            self.refresh_button.config(state=tk.NORMAL)
            
        except queue.Empty:
            pass
        
        self.root.after(100, self.process_queue)

if __name__ == "__main__":
    root = tk.Tk()
    app = ServerQueryApp(root)
    root.mainloop()