import tkinter as tk
from datetime import datetime

def get_map_based_on_utc_hour(hour=None):
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

def get_adjacent_maps():
    current_hour = datetime.utcnow().hour
    current_minute = datetime.utcnow().minute
    current_second = datetime.utcnow().second
    
    prev_hour = current_hour - 1
    if prev_hour < 0:
        prev_hour = 23
    prev_map = get_map_based_on_utc_hour(prev_hour)
    
    next_hour = current_hour + 1
    if next_hour > 23:
        next_hour = 0
    next_map = get_map_based_on_utc_hour(next_hour)
    
    seconds_remaining = (60 - current_second) % 60
    minutes_remaining = (59 - current_minute) % 60
    
    return prev_map, next_map, minutes_remaining, seconds_remaining

def update_display():
    utc_now = datetime.utcnow()
    local_now = datetime.now()
    
    utc_time = utc_now.strftime("%H:%M:%S.%f")[:-3]
    local_time = local_now.strftime("%H:%M:%S.%f")[:-3]
    
    current_map = get_map_based_on_utc_hour()
    prev_map, next_map, mins_left, secs_left = get_adjacent_maps()
    
    time_label.config(text=f"UTC Time: {utc_time} | Local Time: {local_time}")
    map_label.config(text=f"Current map: {current_map}")
    adjacent_label.config(text=f"Previous map cycle : {prev_map} | Next map cycle : {next_map}")
    countdown_label.config(text=f"Next cycle in: {mins_left:02d}m {secs_left:02d}s")
    
    root.after(50, update_display)

root = tk.Tk()
root.title("clown9.exe")
root.geometry("600x180")

map_label = tk.Label(
    root, 
    font=("Arial", 18, "bold"),
    justify="center"
)
map_label.pack(pady=(15, 5))

adjacent_label = tk.Label(
    root,
    font=("Arial", 12),
    justify="center"
)
adjacent_label.pack(pady=(0, 5))

countdown_label = tk.Label(
    root,
    font=("Arial", 12, "bold"),
    justify="center"
)
countdown_label.pack(pady=(0, 5))

time_label = tk.Label(
    root,
    font=("Arial", 12),
    justify="center"
)
time_label.pack()

update_display()

root.mainloop()

# Made by "the clown", @chernobyl_bag on Anomalous Materials