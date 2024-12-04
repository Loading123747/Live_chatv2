from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, send, emit
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'your_secret_key'
socketio = SocketIO(app)

# Store bans in memory
banned_users = {}

# Login route
@app.route('/')
def login():
    return render_template('login.html')

@app.route('/handle_login', methods=['POST'])
def handle_login():
    username = request.form['username']
    password = request.form['password']

    # Owner credentials
    if username == 'owner123' and password == 'password':
        session['user_role'] = 'owner'
        session['username'] = username
        return redirect(url_for('chat'))
    elif username and not password:  # Guest Login
        session['user_role'] = 'guest'
        session['username'] = username
        return redirect(url_for('chat'))
    else:
        return "Invalid credentials. Try again!"

@app.route('/chat')
def chat():
    if 'username' in session:
        username = session['username']
        if banned_users.get(username) and banned_users[username] > datetime.now():
            return f"You are banned until {banned_users[username]}"
        role = session.get('user_role', 'guest')
        return render_template('chat.html', username=username, role=role)
    return redirect(url_for('login'))

# Ban functionality
@socketio.on('ban_user')
def ban_user(data):
    if session.get('user_role') == 'owner':
        user_to_ban = data['username']
        ban_duration = int(data['duration'])  # in minutes
        banned_users[user_to_ban] = datetime.now() + timedelta(minutes=ban_duration)
        emit('user_banned', {'username': user_to_ban}, broadcast=True)

# Handle messages
@socketio.on('message')
def handle_message(data):
    if 'username' in session:
        username = session['username']
        if not banned_users.get(username) or banned_users[username] < datetime.now():
            send(f"{username}: {data if data.strip() else ''}", broadcast=True)

if __name__ == '__main__':
    socketio.run(app, debug=True)
