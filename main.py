from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_socketio import SocketIO, send, emit
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'
socketio = SocketIO(app)

# Store bans in memory
banned_users = {}

# Route for login page
@app.route('/')
def login():
    return render_template('login.html')

# Handle login
@app.route('/handle_login', methods=['POST'])
def handle_login():
    username = request.form['username']
    password = request.form.get('password', '')  # Use .get() to avoid KeyError

    # Owner credentials
    if username == 'owner123' and password == 'password':
        session['user_role'] = 'owner'
        return redirect(url_for('owner_setup'))
    elif username and not password:  # Guest Login (password is omitted)
        session['user_role'] = 'guest'
        session['username'] = username
        return redirect(url_for('chat'))
    else:
        return "Invalid credentials. Try again!"

# Owner setup page
@app.route('/owner_setup')
def owner_setup():
    if session.get('user_role') == 'owner':
        return render_template('owner_setup.html')
    return redirect(url_for('login'))

@app.route('/setup_owner', methods=['POST'])
def setup_owner():
    username = request.form['username']
    session['username'] = username
    return redirect(url_for('chat'))

# Chat page
@app.route('/chat')
def chat():
    if 'username' in session:
        username = session['username']
        if banned_users.get(username) and banned_users[username] > datetime.now():
            return "You are banned until " + str(banned_users[username])
        return render_template('chat.html', username=username, role=session['user_role'])
    return redirect(url_for('login'))

# Ban functionality
@socketio.on('ban_user')
def ban_user(data):
    if session.get('user_role') == 'owner':
        user_to_ban = data['username']
        ban_duration = int(data['duration'])  # in minutes
        banned_users[user_to_ban] = datetime.now() + timedelta(minutes=ban_duration)
        emit('user_banned', {'username': user_to_ban}, broadcast=True)

# Chat messages
@socketio.on('message')
def handle_message(data):
    if 'username' in session:
        username = session['username']
        if not banned_users.get(username) or banned_users[username] < datetime.now():
            send(f"{username}: {data}", broadcast=True)

if __name__ == '__main__':
    socketio.run(app, debug=True)
