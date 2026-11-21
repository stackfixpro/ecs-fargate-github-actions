import socket

from flask import Flask

app = Flask(__name__)

# Change this to "v2", commit, and watch GitHub Actions put it live on ECS.
VERSION = "v1"


@app.get("/")
def home():
    return f"""<!doctype html>
<html>
  <head>
    <title>StackFix Pro on ECS</title>
    <style>
      body {{ font-family: system-ui, sans-serif; background: #0f172a; color: #e2e8f0;
              display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }}
      .card {{ text-align: center; }}
      h1 {{ font-size: 48px; margin: 0 0 16px; }}
      .version {{ font-size: 32px; color: #22c55e; }}
      .host {{ font-size: 20px; color: #94a3b8; margin-top: 12px; }}
    </style>
  </head>
  <body>
    <div class="card">
      <h1>Hello from AWS ECS Fargate</h1>
      <div class="version">Version: {VERSION}</div>
      <div class="host">Served by task: {socket.gethostname()}</div>
    </div>
  </body>
</html>"""


@app.get("/health")
def health():
    # The load balancer calls this every few seconds. 200 = healthy.
    return {"status": "ok"}
