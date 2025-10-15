from flask import Flask, request, redirect, url_for
import requests
import time
import random
import uuid
from threading import Lock
from datetime import datetime
from io import StringIO

app = Flask(__name__)
app.secret_key = 'devil_secret_key_123'  # Change for production

# Global task storage
tasks = {}
task_lock = Lock()

# Rotating user agents
user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'
]

headers = {
    'Connection': 'keep-alive',
    'Cache-Control': 'max-age=0',
    'Upgrade-Insecure-Requests': '1',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,en;q=0.9',
    'referer': 'https://www.facebook.com/'
}

def validate_token(token):
    try:
        response = requests.get(
            f'https://graph.facebook.com/v15.0/me?access_token={token}',
            headers={'User-Agent': random.choice(user_agents)},
            timeout=10
        )
        return response.status_code == 200
    except:
        return False

def process_task(task_id, thread_id, haters_name, messages, valid_tokens, speed):
    post_url = f'https://graph.facebook.com/v15.0/{thread_id}/comments'
    total_comments = len(messages)
    max_tokens = len(valid_tokens)
    
    with task_lock:
        tasks[task_id] = {
            'status': 'running',
            'total': total_comments,
            'success': 0,
            'failed': 0,
            'current_comment': 0,
            'logs': [],
            'valid_tokens': len(valid_tokens),
            'invalid_tokens': 0,
            'start_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'active_users': 0,
            'last_activity': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    try:
        for comment_index, comment in enumerate(messages):
            if tasks[task_id]['status'] == 'stopped':
                break
                
            token_index = comment_index % max_tokens
            access_token = valid_tokens[token_index]
            comment_text = f"{haters_name} {comment.strip()}"
            
            current_headers = headers.copy()
            current_headers['User-Agent'] = random.choice(user_agents)
            
            try:
                response = requests.post(
                    post_url,
                    json={'access_token': access_token, 'message': comment_text},
                    headers=current_headers,
                    timeout=20
                )
                
                log_entry = {
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'comment_number': comment_index + 1,
                    'token_number': token_index + 1,
                    'status': 'success' if response.ok else 'failed',
                    'message': comment_text,
                    'response': response.json() if response.ok else {'error': response.text}
                }
                
                with task_lock:
                    if response.ok:
                        tasks[task_id]['success'] += 1
                    else:
                        tasks[task_id]['failed'] += 1
                    tasks[task_id]['current_comment'] = comment_index + 1
                    tasks[task_id]['logs'].append(log_entry)
                    tasks[task_id]['last_activity'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Random delay to avoid detection
                delay = speed + random.uniform(-0.5, 2.5)
                time.sleep(max(10, delay))  # Minimum 10 seconds
                
            except Exception as e:
                with task_lock:
                    tasks[task_id]['failed'] += 1
                    tasks[task_id]['logs'].append({
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'comment_number': comment_index + 1,
                        'token_number': token_index + 1,
                        'status': 'error',
                        'message': str(e)
                    })
                    tasks[task_id]['last_activity'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                time.sleep(30)
                
    except Exception as e:
        with task_lock:
            tasks[task_id]['status'] = 'error'
            tasks[task_id]['logs'].append({
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'status': 'critical_error',
                'message': str(e)
            })
    
    with task_lock:
        if tasks[task_id]['status'] == 'running':
            tasks[task_id]['status'] = 'completed'
        tasks[task_id]['end_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Generate unique task ID
        task_id = str(uuid.uuid4())
        
        # Process form data
        thread_id = request.form.get('threadId')
        haters_name = request.form.get('kidx')
        speed = max(20, int(request.form.get('time')))  # Minimum 20 seconds
        
        # Process tokens file
        tokens_file = request.files['txtFile']
        raw_tokens = tokens_file.read().decode().splitlines()
        
        # Validate tokens
        valid_tokens = [token.strip() for token in raw_tokens if validate_token(token.strip())]
        invalid_count = len(raw_tokens) - len(valid_tokens)
        
        # Process messages file
        messages_file = request.files['messagesFile']
        messages = messages_file.read().decode().splitlines()
        
        # Store task information
        with task_lock:
            tasks[task_id] = {
                'status': 'initializing',
                'total': len(messages),
                'success': 0,
                'failed': 0,
                'invalid_tokens': invalid_count,
                'valid_tokens': len(valid_tokens),
                'logs': [],
                'start_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'active_users': 1
            }
        
        # Start processing thread
        from threading import Thread
        Thread(target=process_task, args=(
            task_id,
            thread_id,
            haters_name,
            messages,
            valid_tokens,
            speed
        )).start()
        
        return redirect(url_for('status', task_id=task_id))
    
    # Return the HTML content directly
    return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🔥 DEVIL POST SERVER 🔥</title>
    <style>
        :root {
            --primary: #ff2d2d;
            --secondary: #2b2b2b;
            --accent: #ff6b6b;
            --text: #f0f0f0;
            --success: #28a745;
            --danger: #dc3545;
            --warning: #ffc107;
            --info: #17a2b8;
        }
        
        body {
            background: linear-gradient(135deg, #1a1a1a 0%, #0d0d0d 100%);
            color: var(--text);
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            min-height: 100vh;
            margin: 0;
            padding: 0;
            overflow-x: hidden;
        }
        
        .header {
            background: linear-gradient(90deg, var(--secondary) 0%, #1a1a1a 100%);
            padding: 1.5rem;
            border-bottom: 2px solid var(--primary);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        }
        
        .title {
            font-size: 2.5rem;
            font-weight: 700;
            background: linear-gradient(90deg, var(--primary) 0%, var(--accent) 100%);
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
            margin-bottom: 0.5rem;
        }
        
        .subtitle {
            color: var(--accent);
            font-size: 1.2rem;
            margin-bottom: 0;
        }
        
        .card {
            background: rgba(43, 43, 43, 0.8);
            border: 1px solid rgba(255, 45, 45, 0.3);
            border-radius: 8px;
            box-shadow: 0 6px 15px rgba(0, 0, 0, 0.2);
            backdrop-filter: blur(10px);
            margin-bottom: 2rem;
            transition: all 0.3s ease;
        }
        
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 12px 20px rgba(0, 0, 0, 0.3);
            border-color: rgba(255, 45, 45, 0.6);
        }
        
        .card-header {
            background: linear-gradient(90deg, rgba(255, 45, 45, 0.2) 0%, rgba(43, 43, 43, 0) 100%);
            border-bottom: 1px solid rgba(255, 45, 45, 0.3);
            font-weight: 600;
            color: var(--accent);
        }
        
        .form-control {
            background: rgba(30, 30, 30, 0.8);
            border: 1px solid rgba(255, 45, 45, 0.3);
            color: var(--text);
            border-radius: 4px;
            padding: 12px 15px;
            transition: all 0.3s;
        }
        
        .form-control:focus {
            background: rgba(40, 40, 40, 0.9);
            border-color: var(--primary);
            box-shadow: 0 0 0 0.2rem rgba(255, 45, 45, 0.25);
            color: var(--text);
        }
        
        .btn-devil {
            background: linear-gradient(90deg, var(--primary) 0%, #ff5252 100%);
            border: none;
            color: white;
            font-weight: 600;
            padding: 12px 25px;
            border-radius: 4px;
            text-transform: uppercase;
            letter-spacing: 1px;
            transition: all 0.3s;
            box-shadow: 0 4px 8px rgba(255, 45, 45, 0.3);
        }
        
        .btn-devil:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(255, 45, 45, 0.4);
            background: linear-gradient(90deg, #ff1a1a 0%, #ff5252 100%);
            color: white;
        }
        
        .status-success { color: var(--success); }
        .status-failed { color: var(--danger); }
        .status-running { color: var(--info); }
        .status-stopped { color: var(--warning); }
        
        .log-entry {
            background: rgba(30, 30, 30, 0.6);
            border-left: 4px solid var(--primary);
            margin-bottom: 8px;
            padding: 10px 15px;
            border-radius: 0 4px 4px 0;
            transition: all 0.2s;
        }
        
        .log-entry:hover {
            background: rgba(40, 40, 40, 0.8);
            transform: translateX(5px);
        }
        
        .log-success { border-left-color: var(--success); }
        .log-failed { border-left-color: var(--danger); }
        .log-error { border-left-color: var(--warning); }
        
        .stats-card {
            background: rgba(43, 43, 43, 0.6);
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .stats-value {
            font-size: 1.8rem;
            font-weight: 700;
            color: var(--accent);
        }
        
        .stats-label {
            font-size: 0.9rem;
            color: #aaa;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        footer {
            background: rgba(20, 20, 20, 0.8);
            padding: 1.5rem;
            margin-top: 3rem;
            border-top: 1px solid rgba(255, 45, 45, 0.2);
        }
        
        .glow {
            animation: glow 2s ease-in-out infinite alternate;
        }
        
        @keyframes glow {
            from { text-shadow: 0 0 5px #fff, 0 0 10px #fff, 0 0 15px var(--primary), 0 0 20px var(--primary); }
            to { text-shadow: 0 0 10px #fff, 0 0 20px #ff4da6, 0 0 30px var(--primary), 0 0 40px var(--primary); }
        }
        
        .progress-bar-devil {
            background: linear-gradient(90deg, var(--primary) 0%, #ff5252 100%);
            height: 6px;
            border-radius: 3px;
        }
        
        .token-badge {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: 600;
            margin-right: 5px;
            margin-bottom: 5px;
        }
        
        .valid-token { background: rgba(40, 167, 69, 0.2); color: var(--success); border: 1px solid var(--success); }
        .invalid-token { background: rgba(220, 53, 69, 0.2); color: var(--danger); border: 1px solid var(--danger); }
    </style>
</head>
<body>
    <header class="header text-center">
        <div class="container">
            <h1 class="title glow">DEVIL POST SERVER</h1>
            <p class="subtitle">DARK WEB EDITION | 100% WORKING | AUTO TOKEN VALIDATION</p>
        </div>
    </header>

    <div class="container py-5">
        <div class="row justify-content-center">
            <div class="col-lg-8">
                <div class="card">
                    <div class="card-header text-center">
                        <h4>🔥 POSTING CONTROL PANEL 🔥</h4>
                    </div>
                    <div class="card-body">
                        <form method="post" enctype="multipart/form-data">
                            <div class="form-group">
                                <label>POST ID:</label>
                                <input type="text" name="threadId" class="form-control" required placeholder="Enter Facebook Post ID">
                            </div>
                            <div class="form-group">
                                <label>HATER NAME:</label>
                                <input type="text" name="kidx" class="form-control" required placeholder="Enter your hater name">
                            </div>
                            <div class="form-group">
                                <label>MESSAGES FILE (TXT):</label>
                                <input type="file" name="messagesFile" class="form-control" accept=".txt" required>
                                <small class="text-muted">One message per line</small>
                            </div>
                            <div class="form-group">
                                <label>TOKENS FILE (TXT):</label>
                                <input type="file" name="txtFile" class="form-control" accept=".txt" required>
                                <small class="text-muted">One Facebook token per line</small>
                            </div>
                            <div class="form-group">
                                <label>SPEED (SECONDS):</label>
                                <input type="number" name="time" class="form-control" min="20" value="20" required>
                                <small class="text-muted">Minimum 20 seconds between comments</small>
                            </div>
                            <button type="submit" class="btn btn-devil btn-block">
                                🚀 START POSTING COMMENTS
                            </button>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <footer class="text-center">
        <div class="container">
            <p class="mb-0">DEVIL POST SERVER | AUTO TOKEN VALIDATION | 100% WORKING</p>
            <p class="mb-0">Made with ❤️ by DEVIL | DARK WEB EDITION</p>
        </div>
    </footer>
</body>
</html>
    '''

@app.route('/status/<task_id>')
def status(task_id):
    task = tasks.get(task_id, {'status': 'not_found'})
    
    # Generate HTML for logs
    logs_html = StringIO()
    for log in reversed(task.get('logs', [])):
        status_class = ''
        if log['status'] == 'success':
            status_class = 'log-success'
        elif log['status'] == 'failed':
            status_class = 'log-failed'
        elif log['status'] == 'error':
            status_class = 'log-error'
        
        logs_html.write(f'''
        <div class="log-entry {status_class}">
            <div class="d-flex justify-content-between">
                <small class="text-muted">{log['timestamp']}</small>
                <span class="badge badge-{'success' if log['status'] == 'success' else 'danger'}">
                    {log['status'].upper()}
                </span>
            </div>
            <div class="mt-2">
                <strong>Comment #{log.get('comment_number', 'N/A')}</strong> | 
                <strong>Token #{log.get('token_number', 'N/A')}</strong>
            </div>
            <div class="mt-1">{log.get('message', '')}</div>
            {f"<div class='mt-1 text-muted'><small>{str(log.get('response', ''))}</small></div>" if 'response' in log else ''}
        </div>
        ''')
    
    # Calculate progress percentage
    progress = 0
    if task.get('total', 0) > 0:
        progress = min(100, (task.get('current_comment', 0) / task['total']) * 100)
    
    return f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🔥 TASK STATUS | DEVIL POST SERVER 🔥</title>
    <meta http-equiv="refresh" content="5">
    <style>
        :root {{
            --primary: #ff2d2d;
            --secondary: #2b2b2b;
            --accent: #ff6b6b;
            --text: #f0f0f0;
            --success: #28a745;
            --danger: #dc3545;
            --warning: #ffc107;
            --info: #17a2b8;
        }}
        
        body {{
            background: linear-gradient(135deg, #1a1a1a 0%, #0d0d0d 100%);
            color: var(--text);
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            min-height: 100vh;
            margin: 0;
            padding: 0;
        }}
        
        .header {{
            background: linear-gradient(90deg, var(--secondary) 0%, #1a1a1a 100%);
            padding: 1.5rem;
            border-bottom: 2px solid var(--primary);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        }}
        
        .title {{
            font-size: 2rem;
            font-weight: 700;
            background: linear-gradient(90deg, var(--primary) 0%, var(--accent) 100%);
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }}
        
        .card {{
            background: rgba(43, 43, 43, 0.8);
            border: 1px solid rgba(255, 45, 45, 0.3);
            border-radius: 8px;
            box-shadow: 0 6px 15px rgba(0, 0, 0, 0.2);
            backdrop-filter: blur(10px);
            margin-bottom: 2rem;
        }}
        
        .card-header {{
            background: linear-gradient(90deg, rgba(255, 45, 45, 0.2) 0%, rgba(43, 43, 43, 0) 100%);
            border-bottom: 1px solid rgba(255, 45, 45, 0.3);
            font-weight: 600;
            color: var(--accent);
        }}
        
        .status-success {{ color: var(--success); }}
        .status-failed {{ color: var(--danger); }}
        .status-running {{ color: var(--info); }}
        .status-stopped {{ color: var(--warning); }}
        .status-not_found {{ color: var(--danger); }}
        
        .log-entry {{
            background: rgba(30, 30, 30, 0.6);
            border-left: 4px solid var(--primary);
            margin-bottom: 8px;
            padding: 10px 15px;
            border-radius: 0 4px 4px 0;
        }}
        
        .log-success {{ border-left-color: var(--success); }}
        .log-failed {{ border-left-color: var(--danger); }}
        .log-error {{ border-left-color: var(--warning); }}
        
        .stats-card {{
            background: rgba(43, 43, 43, 0.6);
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}
        
        .stats-value {{
            font-size: 1.8rem;
            font-weight: 700;
            color: var(--accent);
        }}
        
        .stats-label {{
            font-size: 0.9rem;
            color: #aaa;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .progress-container {{
            height: 6px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 3px;
            margin-bottom: 20px;
            overflow: hidden;
        }}
        
        .progress-bar {{
            height: 100%;
            background: linear-gradient(90deg, var(--primary) 0%, #ff5252 100%);
            border-radius: 3px;
            transition: width 0.5s ease;
        }}
        
        .btn-devil {{
            background: linear-gradient(90deg, var(--primary) 0%, #ff5252 100%);
            border: none;
            color: white;
            font-weight: 600;
            padding: 10px 20px;
            border-radius: 4px;
            transition: all 0.3s;
        }}
        
        .btn-devil:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(255, 45, 45, 0.4);
            background: linear-gradient(90deg, #ff1a1a 0%, #ff5252 100%);
            color: white;
        }}
        
        .badge-success {{
            background-color: var(--success);
        }}
        
        .badge-danger {{
            background-color: var(--danger);
        }}
        
        .badge-warning {{
            background-color: var(--warning);
        }}
        
        .badge-info {{
            background-color: var(--info);
        }}
        
        .token-badge {{
            display: inline-block;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: 600;
            margin-right: 5px;
            margin-bottom: 5px;
        }}
        
        .valid-token {{ background: rgba(40, 167, 69, 0.2); color: var(--success); border: 1px solid var(--success); }}
        .invalid-token {{ background: rgba(220, 53, 69, 0.2); color: var(--danger); border: 1px solid var(--danger); }}
    </style>
</head>
<body>
    <header class="header">
        <div class="container">
            <div class="d-flex justify-content-between align-items-center">
                <h1 class="title">TASK STATUS: {task_id}</h1>
                <a href="/" class="btn btn-devil">NEW TASK</a>
            </div>
        </div>
    </header>

    <div class="container py-4">
        <div class="row">
            <div class="col-md-4">
                <div class="card">
                    <div class="card-header">TASK INFORMATION</div>
                    <div class="card-body">
                        <div class="stats-card">
                            <div class="stats-value">{task.get('current_comment', 0)}/{task.get('total', 0)}</div>
                            <div class="stats-label">COMMENTS SENT</div>
                        </div>
                        
                        <div class="progress-container">
                            <div class="progress-bar" style="width: {progress}%"></div>
                        </div>
                        
                        <div class="stats-card">
                            <div class="stats-value status-{task.get('status', 'not_found')}">{task.get('status', 'not_found').upper()}</div>
                            <div class="stats-label">CURRENT STATUS</div>
                        </div>
                        
                        <div class="stats-card">
                            <div class="stats-value status-success">{task.get('success', 0)}</div>
                            <div class="stats-label">SUCCESSFUL</div>
                        </div>
                        
                        <div class="stats-card">
                            <div class="stats-value status-failed">{task.get('failed', 0)}</div>
                            <div class="stats-label">FAILED</div>
                        </div>
                        
                        <div class="stats-card">
                            <div class="stats-value">{task.get('valid_tokens', 0)}</div>
                            <div class="stats-label">VALID TOKENS</div>
                        </div>
                        
                        <div class="stats-card">
                            <div class="stats-value status-failed">{task.get('invalid_tokens', 0)}</div>
                            <div class="stats-label">INVALID TOKENS</div>
                        </div>
                        
                        <div class="stats-card">
                            <div class="stats-value">{task.get('start_time', 'N/A')}</div>
                            <div class="stats-label">START TIME</div>
                        </div>
                        
                        {f'''
                        <div class="stats-card">
                            <div class="stats-value">{task.get('end_time', 'N/A')}</div>
                            <div class="stats-label">END TIME</div>
                        </div>
                        ''' if task.get('status') in ['completed', 'stopped', 'error'] else ''}
                        
                        {f'''
                        <a href="/stop/{task_id}" class="btn btn-devil btn-block mt-3">
                            ⏹ STOP TASK
                        </a>
                        ''' if task.get('status') == 'running' else ''}
                    </div>
                </div>
            </div>
            
            <div class="col-md-8">
                <div class="card">
                    <div class="card-header">LIVE COMMENT LOGS</div>
                    <div class="card-body" style="max-height: 70vh; overflow-y: auto;">
                        {logs_html.getvalue() if task.get('logs') else '<div class="text-center text-muted">No logs available yet</div>'}
                    </div>
                </div>
            </div>
        </div>
    </div>

    <footer class="text-center py-3">
        <div class="container">
            <p class="mb-0">DEVIL POST SERVER | LIVE STATUS MONITORING | {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </div>
    </footer>
</body>
</html>
    '''

@app.route('/stop/<task_id>')
def stop(task_id):
    with task_lock:
        if task_id in tasks:
            tasks[task_id]['status'] = 'stopped'
    return redirect(url_for('status', task_id=task_id))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)
