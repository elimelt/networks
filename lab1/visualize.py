from datetime import datetime
import matplotlib.pyplot as plt
import requests
import io
import base64

# Extract timestamps and events from log data
def fetch_log_data():
    url = 'http://attu1.cs.washington.edu:5555'
    r = requests.get(url)
    return r.text.splitlines()

import matplotlib.pyplot as plt
from datetime import datetime

def plot_timeline():
    log_data = fetch_log_data()

    # Extract timestamps and events from log data
    timestamps = []
    hosts = []
    statuses = []

    for log_entry in log_data:
        parts = log_entry.split(" - ")
        timestamp_str, event = parts[0], parts[1]
        timestamp = datetime.strptime(timestamp_str, "%m/%d/%Y, %H:%M:%S")

        timestamps.append(timestamp)
        host, status = event.split(' is ')
        hosts.append(host)
        statuses.append(status)

    # Map event types to colors
    event_colors = {'up': 'green', 'down': 'red'}

    # Get unique hosts and assign y-positions
    unique_hosts = list(set(hosts))
    y_positions = {host: i * 5 for i, host in enumerate(unique_hosts)}

    # Plotting
    fig, ax = plt.subplots(figsize=(10, 6))

    for timestamp, host, status in zip(timestamps, hosts, statuses):
        color = event_colors.get(status, 'gray')
        y = y_positions[host]
        ax.plot([timestamp, timestamp], [y, y + 1], color=color, linewidth=8)

    # Customize plot
    ax.set_yticks([y_positions[host] + 0.5 for host in unique_hosts])
    ax.set_yticklabels(unique_hosts)
    ax.set_xlabel('Timestamp')
    ax.set_title('Server uptime')

    # Show plot
    plt.grid(True)
    plt.tight_layout()
    return plt

def plot_to_base64(plt):
    my_stringIObytes = io.BytesIO()
    plt.savefig(my_stringIObytes, format='jpg')
    my_stringIObytes.seek(0)
    my_base64_jpgData = base64.b64encode(my_stringIObytes.read()).decode()
    return my_base64_jpgData

def to_html(plt):
    img = f'<img src="data:image/png;base64,{plot_to_base64(plt)}">'

    return f"<html><body>{img}</body></html>"
