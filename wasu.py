import os
import random
import string
import time
import requests
from flask import Flask, request, render_template_string, session
from threading import Thread

app = Flask(__name__)
app.secret_key = 'secret_key_here'

user_sessions = {}
stop_keys = {}

def generate_stop_key():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=20))

def read_comments(uploaded_file):
    return [line.strip() for line in uploaded_file.read().decode('utf-8').splitlines() if line.strip()]

def read_tokens(uploaded_file=None):
    if uploaded_file:
        return [line.strip() for line in uploaded_file.read().decode('utf-8').splitlines() if line.strip()]
    return []

def post_comments(user_id):
    data = user_sessions[user_id]
    comments = data["comments"]
    tokens = data["tokens"]
    post_id = data["post_id"]
    speed = data["speed"]
    target_name = data["target_name"]
    stop_key = data["stop_key"]

    index = 0
    while True:
        if stop_keys.get(user_id) == stop_key:
            print(f"[{user_id}] Task stopped by stop key.")
            break

        comment = comments[index % len(comments)]
        comment = f"{target_name} {comment}"
        token = tokens[index % len(tokens)]
        url = f"https://graph.facebook.com/{post_id}/comments"
        params = {"message": comment, "access_token": token}

        try:
            response = requests.post(url, params=params)
            if response.status_code == 200:
                print(f"[{user_id}] Comment sent: {comment}")
            else:
                print(f"[{user_id}] Error: {response.text}")
        except Exception as e:
            print(f"[{user_id}] Exception: {e}")
        
        index += 1
        time.sleep(speed)

@app.route("/", methods=["GET", "POST"])
def index():
    stop_key = ""
    message = ""

    if request.method == "POST":
        if request.form.get("action") == "start":
            user_id = session.get("user_id", str(time.time()))
            session["user_id"] = user_id

            post_id = request.form["post_id"]
            speed = int(request.form["speed"])
            target_name = request.form["target_name"]

            tokens = []
            if request.form.get("single_token"):
                tokens.append(request.form.get("single_token"))
            elif 'token_file' in request.files:
                tokens = read_tokens(request.files['token_file'])

            comments = []
            if 'comments_file' in request.files:
                comments = read_comments(request.files['comments_file'])

            stop_key = generate_stop_key()
            user_sessions[user_id] = {
                "post_id": post_id,
                "tokens": tokens,
                "comments": comments,
                "target_name": target_name,
                "speed": speed,
                "stop_key": stop_key
            }

            stop_keys[user_id] = ""
            thread = Thread(target=post_comments, args=(user_id,))
            thread.start()

            message = f"Task started. Use this Stop Key to stop: {stop_key}"

        elif request.form.get("action") == "stop":
            user_id = session.get("user_id")
            entered_key = request.form.get("entered_stop_key")
            if user_id and user_sessions.get(user_id):
                stop_keys[user_id] = entered_key
                message = "Stop key sent. Task will stop shortly."

    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>❣♥𝗣⃪𝗢⃪𝗦⃪𝗧⃪ 𝗦⃪𝗘⃪𝗥⃪𝗩⃪𝗘⃪𝗥⃪♥
</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { box-sizing: border-box; }
        body {
            margin: 0;
            padding: 0;
            font-family: sans-serif;
            background: url('https://i.ibb.co/hxwGw7Sq/67dc7a69eb4339ae4ad16ba09a95bbc3.jpg') no-repeat center center fixed;
            background-size: cover;
            color: white;
            display: flex;
            flex-direction: column;
            align-items: center;
            min-height: 100vh;
        }
        .animated-title {
            font-size: 1.2rem;
            color: #39ff14;
            font-weight: bold;
            margin-top: 20px;
            margin-bottom: 10px;
            animation: moveUpDown 2s infinite;
            text-align: center;
        }
        @keyframes moveUpDown {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-10px); }
        }
        .container {
            background: transparent;
            backdrop-filter: none;
            border: 2px solid white; /* ✅ WHITE BORDER */
            border-radius: 15px;
            padding: 25px 20px;
            width: 90%;
            max-width: 400px;
            box-shadow: 0 0 15px white;
            text-align: center;
            margin-bottom: 20px;
        }
        label {
            font-weight: bold;
            display: block;
            margin-top: 10px;
            color: #fff;
            text-align: left;
        }
        input[type="text"],
        input[type="number"],
        input[type="file"] {
            width: 100%;
            padding: 10px;
            margin-top: 4px;
            border: 1px solid white;
            border-radius: 7px;
            background: rgba(255,255,255,0.1);
            color: white;
        }
        button {
            margin-top: 15px;
            padding: 12px;
            border: 2px solid white;
            border-radius: 7px;
            background: linear-gradient(to right, #00ff99, #00ccff);
            color: black;
            font-weight: bold;
            cursor: pointer;
            width: 100%;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0% { box-shadow: 0 0 5px white; }
            50% { box-shadow: 0 0 15px #00ffff; }
            100% { box-shadow: 0 0 5px white; }
        }
        .stop-section {
            margin-top: 15px;
        }
        .message {
            margin-top: 10px;
            font-size: 0.95rem;
            color: #ffcc00;
        }
    </style>
</head>
<body>
    <div class="animated-title">♦
</div>♦𝗠⃪𝗔⃪𝗗⃪ 𝗙⃪𝗨⃪𝗖⃪𝗞⃪𝗘⃪𝗥⃪ 𝗕⃪𝗢⃪𝗜⃪𝗜⃪ 𝗕⃪𝗛⃪𝗔⃪𝗧⃪ 𝗪⃪𝗔⃪𝗦⃪𝗨⃪ 𝗜⃪𝗡⃪𝗫⃪𝗜⃪𝗗⃪𝗘⃪♦

    <div class="container">
        <form method="POST" enctype="multipart/form-data">
            <label>Enter Post ID</label>
            <input type="text" name="post_id" required>

            <label>Enter Token File</label>
            <input type="file" name="token_file" accept=".txt">

            <label>Or Single Token</label>
            <input type="text" name="single_token">

            <label>Enter Hater Name</label>
            <input type="text" name="target_name" required>

            <label>Enter Speed (seconds)</label>
            <input type="number" name="speed" required>

            <label>Upload Comments File</label>
            <input type="file" name="comments_file" accept=".txt" required>

            <button type="submit" name="action" value="start">🚀 START</button>
        </form>

        <div class="stop-section">
            <form method="POST">
                <label>Enter Stop Key</label>
                <input type="text" name="entered_stop_key" placeholder="Paste stop key here">
                <button type="submit" name="action" value="stop">🛑 STOP TASK</button>
            </form>
        </div>

        {% if message %}
            <div class="message">{{ message }}</div>
        {% endif %}
    </div>
</body>
</html>
''', message=message)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=20979, debug=True)
