import os
import threading
import logging
from flask import Flask, jsonify, render_template_string
from dotenv import load_dotenv
import schedule
import time

from db import init_db
from pushover import send_pushover
from engine import SignalEngine
from sources.reddit_trump import RedditTrumpSource
from sources.wscn_lives import WSCNLivesSource

load_dotenv()
init_db()

# --- Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)

app = Flask(__name__)
engine = SignalEngine()

# Register sources
engine.register(RedditTrumpSource())
engine.register(WSCNLivesSource())

# --- Landing page ---
INDEX_HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SignalX — 多源信号聚合推送</title>
<script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-950 text-gray-100 min-h-screen flex items-center justify-center p-4">
<div class="max-w-lg w-full text-center space-y-8">
  <!-- Logo / Brand -->
  <div>
    <h1 class="text-5xl font-bold tracking-tight">
      <span class="text-cyan-400">Signal</span><span class="text-white">X</span>
    </h1>
    <p class="text-gray-400 mt-3 text-lg">
      多源信号聚合，实时推送特朗普相关动态
    </p>
  </div>

  <!-- Sources -->
  <div class="bg-gray-900 rounded-xl p-6 text-left space-y-3">
    <h2 class="text-sm font-semibold text-gray-500 uppercase tracking-wider">监控来源</h2>
    <div class="flex items-center gap-3 text-sm">
      <span class="w-2 h-2 bg-orange-500 rounded-full animate-pulse"></span>
      <span>Reddit r/trump — 社群动态</span>
    </div>
    <div class="flex items-center gap-3 text-sm">
      <span class="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></span>
      <span>华尔街见闻 — 实时快讯（特朗普/Trump/川普）</span>
    </div>
  </div>

  <!-- How it works -->
  <div class="bg-gray-900 rounded-xl p-6 text-left space-y-4">
    <h2 class="text-sm font-semibold text-gray-500 uppercase tracking-wider">两步激活</h2>
    <div class="flex gap-4 items-start">
      <div class="bg-cyan-500/20 text-cyan-400 rounded-full w-8 h-8 flex items-center justify-center font-bold shrink-0">1</div>
      <div>
        <p class="font-medium">下载 Pushover</p>
        <p class="text-sm text-gray-400 mt-1">
          在 <a href="https://pushover.net" class="text-cyan-400 underline" target="_blank">pushover.net</a> 注册并下载 App（iOS / Android，一次性购买 $4.99）
        </p>
      </div>
    </div>
    <div class="flex gap-4 items-start">
      <div class="bg-cyan-500/20 text-cyan-400 rounded-full w-8 h-8 flex items-center justify-center font-bold shrink-0">2</div>
      <div>
        <p class="font-medium">加入通知群组</p>
        <p class="text-sm text-gray-400 mt-1">
          点击下方按钮加入 SignalX 推送群组，即可开始接收实时提醒
        </p>
      </div>
    </div>
  </div>

  <!-- CTA -->
  <a href="{{ invite_link }}"
     class="block w-full bg-cyan-500 hover:bg-cyan-400 text-gray-950 font-bold py-4 rounded-xl text-lg transition-colors">
    🔔 激活实时推送
  </a>

  <p class="text-xs text-gray-600">
    每 30 秒轮询 · 发现即推送 · 不遗漏重要信号
  </p>
</div>
</body>
</html>"""


@app.route("/")
def index():
    invite_link = os.getenv("INVITE_LINK", "#")
    return render_template_string(INDEX_HTML, invite_link=invite_link)


@app.route("/test_push")
def test_push():
    result = send_pushover(
        message="Hello from SignalX! If you see this, push notifications are working.",
        title="SignalX Test",
    )
    return jsonify(result)


@app.route("/check")
def check():
    """Manually trigger all sources."""
    results = {}
    for source in engine._sources:
        results[source.source_id] = engine.run_source(source.source_id)
    return jsonify(results)


@app.route("/status")
def status():
    """Return engine status."""
    return jsonify({
        "total_pushed": engine.total_pushed,
        "sources": {
            sid: {
                "last_check": dt.isoformat() if dt else None,
            }
            for sid, dt in engine.last_check.items()
        },
    })


# --- Background scheduler (30-second polling) ---
def _run_scheduler():
    schedule.every(30).seconds.do(engine.run_all)
    logging.info("Scheduler started: polling every 30 seconds")
    while True:
        schedule.run_pending()
        time.sleep(1)


_scheduler_thread = threading.Thread(target=_run_scheduler, daemon=True)
_scheduler_thread.start()

# --- Main ---
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
