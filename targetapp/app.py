from flask import Flask, request, render_template_string, redirect
import sqlite3

DB_PATH = '/opt/targetapp/target.db'
app = Flask(__name__)

login_page = '''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Internal Target Login</title>
  <style>body{font-family:Arial,sans-serif;background:#eef2ff;color:#0f172a;padding:2rem;}form{max-width:360px;margin:auto;background:#fff;padding:1.5rem;border-radius:8px;box-shadow:0 10px 24px rgba(15,23,42,0.08);}input,button{width:100%;padding:0.75rem;margin:0.5rem 0;border:1px solid #cbd5e1;border-radius:6px;}button{background:#4338ca;color:#fff;border:none;cursor:pointer;}</style>
</head>
<body>
  <h1>Internal Target Login</h1>
  <p>Enter your internal credentials to continue.</p>
  <form method="post" action="/login">
    <input type="text" name="username" placeholder="Username" required>
    <input type="password" name="password" placeholder="Password" required>
    <button type="submit">Login</button>
  </form>
  {% if error %}
  <p style="color:#b91c1c;">{{ error }}</p>
  {% endif %}
</body>
</html>'''

dashboard_page = '''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Target Dashboard</title>
  <style>body{font-family:Arial,sans-serif;background:#f8fafc;color:#111827;padding:2rem;}pre{background:#e2e8f0;padding:1rem;border-radius:8px;overflow-x:auto;}section{max-width:720px;margin:auto;}</style>
</head>
<body>
  <section>
    <h1>Welcome, {{ username }}</h1>
    <p>Your internal dashboard has loaded successfully.</p>
    <h2>Secure Message</h2>
    <pre>{{ flag }}</pre>
  </section>
</body>
</html>'''


def query_flag():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT value FROM flags LIMIT 1")
    row = cur.fetchone()
    conn.close()
    return row[0] if row else 'FLAG_NOT_FOUND'

@app.route('/')
def home():
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
        cur.execute(query)
        row = cur.fetchone()
        conn.close()
        if row:
            return render_template_string(dashboard_page, username=username, flag=query_flag())
        error = 'Invalid credentials'
    return render_template_string(login_page, error=error)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
