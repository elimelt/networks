from datetime import datetime
import matplotlib.pyplot as plt
import io
import base64
import os

LOG_FILE_PATH = './availability.log'

# Extract timestamps and events from log data
def fetch_log_data():
    if os.path.exists(LOG_FILE_PATH):
        with open(LOG_FILE_PATH, 'r') as f:
            return f.read().splitlines()
    else:
        return []

def plot_timeline(log_data):
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

    event_colors = {'up': 'green', 'down': 'red'}

    unique_hosts = list(set(hosts))
    y_positions = {host: i * 5 for i, host in enumerate(unique_hosts)}

    fig, ax = plt.subplots(figsize=(10, 6))

    for timestamp, host, status in zip(timestamps, hosts, statuses):
        color = event_colors.get(status, 'gray')
        y = y_positions[host]
        ax.plot([timestamp, timestamp], [y, y + 1], color=color, linewidth=8)

    ax.set_yticks([y_positions[host] + 0.5 for host in unique_hosts])
    ax.set_yticklabels(unique_hosts)
    ax.set_xlabel('Timestamp')
    ax.set_title('Server uptime')

    plt.grid(True)
    plt.tight_layout()
    return plt

def plot_to_base64(plt):
    my_stringIObytes = io.BytesIO()
    plt.savefig(my_stringIObytes, format='jpg')
    my_stringIObytes.seek(0)
    my_base64_jpgData = base64.b64encode(my_stringIObytes.read()).decode()
    return my_base64_jpgData

def to_html():
    logs = fetch_log_data()
    plt = plot_timeline(logs)
    img = f'<img src="data:image/png;base64,{plot_to_base64(plt)}">'
    logs = f'{"<br>".join(logs)}'
    log_component = f'<div class="log-comp"><h2>Log</h2><p>{logs}</p></div>'
    img_component = f'<div class="img-comp"><h2>Plot</h2>{img}</div>'
    style = '''
        <style>
            .log-comp, .img-comp {
                display: inline-block;
                vertical-align: top;
                padding: 10px;
            }
            h2 {
                font-size: 20px;
                margin-bottom: 10px;
            }
            p {
                font-size: 16px;
                margin: 0;
            }
            .img-comp img {
                max-width: 100%;
                height: auto;
            }
        </style>
    '''
    charset = '<meta charset="UTF-8">'
    viewport = '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
    lang = 'lang="en"'
    title = '<title>Project 1 Server Monitoring</title>'
    return f'<html {lang}><head>{charset}{viewport}{title}{style}</head><body>{log_component}{img_component}</body></html>'

print(to_html())