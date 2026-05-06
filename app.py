#!/usr/bin/env python3
"""
VM2 - Vulnerable Flask App
Intentionally vulnerable to command injection for demo purposes.
"""

from flask import Flask, request, render_template
import subprocess

app = Flask(__name__, template_folder="/opt/templates")


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/ping", methods=["GET", "POST"])
def ping():
    output = ""
    target = ""

    if request.method == "POST":
        target = request.form.get("target", "")

        # !! INTENTIONALLY VULNERABLE — never do this in production !!
        # Input is passed directly to the shell without sanitization.
        # An attacker can inject commands using ; | & etc.
        try:
            result = subprocess.run(
                f"ping -c 2 {target}",
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            output = result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            output = "Request timed out."
        except Exception as e:
            output = str(e)

    return render_template("ping.html", output=output, target=target)


if __name__ == "__main__":
    # Bind to all interfaces so the attacker (10.0.0.10) can reach it
    app.run(host="0.0.0.0", port=80, debug=False)
