#!/usr/bin/env python3
"""
VM3 - Internal Secret App
This app is only reachable from the internal network (192.168.100.0/24).
The attacker must pivot through VM2 to access it.
"""

from flask import Flask, render_template

app = Flask(__name__, template_folder="/opt/internal-templates")


@app.route("/")
def index():
    return render_template("secret.html")


if __name__ == "__main__":
    # Only bind to the internal interface
    app.run(host="0.0.0.0", port=8080, debug=False)
