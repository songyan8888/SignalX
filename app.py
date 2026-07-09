import os
import threading
import logging
from flask import Flask, jsonify, render_template_string, request
from dotenv import load_dotenv
import schedule
import time

from db import init_db
from pushover import send_pushover
from engine import SignalEngine
# from sources.reddit_trump import RedditTrumpSource  # disabled
from sources.wscn_lives import WSCNLivesSource

load_dotenv()
init_db()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)

app = Flask(__name__)
engine = SignalEngine()

# engine.register(RedditTrumpSource())  # disabled
engine.register(WSCNLivesSource())

# --- Landing page ---
INDEX_HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SignalX — 特朗普动态实时推送</title>
<script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-950 text-gray-100 min-h-screen flex items-center justify-center p-4">
<div class="max-w-lg w-full space-y-8">
  <!-- Brand -->
  <div class="text-center">
    <h1 class="text-5xl font-bold tracking-tight">
      <span class="text-cyan-400">Signal</span><span class="text-white">X</span>
    </h1>
    <p class="text-gray-400 mt-3 text-lg">
      特朗普动态，实时推送到你手机
    </p>
  </div>

  <!-- Step 1 -->
  <div class="bg-gray-900 rounded-xl p-6 space-y-4">
    <div class="flex gap-4 items-start">
      <div class="bg-cyan-500/20 text-cyan-400 rounded-full w-8 h-8 flex items-center justify-center font-bold shrink-0">1</div>
      <div>
        <p class="font-medium text-white">下载 Pushover</p>
        <p class="text-sm text-gray-400 mt-1">
          前往 <a href="https://pushover.net" class="text-cyan-400 underline" target="_blank">pushover.net</a> 注册账号，
          在手机 App Store 搜索 <strong>Pushover</strong> 下载（一次性购买 $4.99）
        </p>
      </div>
    </div>

    <!-- Step 2 -->
    <div class="flex gap-4 items-start">
      <div class="bg-cyan-500/20 text-cyan-400 rounded-full w-8 h-8 flex items-center justify-center font-bold shrink-0">2</div>
      <div>
        <p class="font-medium text-white">获取你的 User Key</p>
        <p class="text-sm text-gray-400 mt-1">
          登录 <a href="https://pushover.net" class="text-cyan-400 underline" target="_blank">pushover.net</a>，
          首页就能看到 <span class="text-yellow-400 font-mono">Your User Key</span>，复制下来
        </p>
      </div>
    </div>

    <!-- Step 3 -->
    <div class="flex gap-4 items-start">
      <div class="bg-cyan-500/20 text-cyan-400 rounded-full w-8 h-8 flex items-center justify-center font-bold shrink-0">3</div>
      <div>
        <p class="font-medium text-white">粘贴激活</p>
        <p class="text-sm text-gray-400 mt-1">
          把你的 User Key 粘贴到下方，点击激活即可
        </p>
      </div>
    </div>
  </div>

  <!-- Activation Form -->
  <div class="bg-gray-900 rounded-xl p-6 space-y-4">
    <input type="text" id="userkey" placeholder="粘贴你的 Pushover User Key（30位字符）"
           class="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-cyan-400 text-sm">
    <button onclick="activate()"
            class="w-full bg-cyan-500 hover:bg-cyan-400 text-gray-950 font-bold py-4 rounded-xl text-lg transition-colors">
      🔔 激活实时推送
    </button>
    <p id="msg" class="text-sm text-center hidden"></p>
  </div>

  <p class="text-xs text-gray-600 text-center">
    华尔街见闻 · 每 30 秒轮询 · 特朗普相关快讯 · 即时推送
  </p>
</div>

<script>
async function activate() {
  const key = document.getElementById('userkey').value.trim();
  const btn = document.querySelector('button');
  const msg = document.getElementById('msg');

  if (!key) { msg.className = 'text-sm text-center text-red-400'; msg.innerText = '请填写 User Key'; msg.classList.remove('hidden'); return; }

  btn.disabled = true; btn.innerText = '提交中...';
  msg.className = 'text-sm text-center text-gray-400'; msg.innerText = '正在验证...'; msg.classList.remove('hidden');

  try {
    const resp = await fetch('/activate', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({user_key: key})
    });
    const data = await resp.json();
    if (data.status === 'ok') {
      msg.className = 'text-sm text-center text-green-400';
      msg.innerText = data.message;
    } else {
      msg.className = 'text-sm text-center text-red-400';
      msg.innerText = data.message;
    }
  } catch (e) {
    msg.className = 'text-sm text-center text-red-400';
    msg.innerText = '网络错误，请稍后重试';
  }
  btn.disabled = false; btn.innerText = '🔔 激活实时推送';
}
</script>
</body>
</html>"""


@app.route("/")
def index():
    return render_template_string(INDEX_HTML)


@app.route("/activate", methods=["POST"])
def activate():
    """User submits their Pushover User Key to subscribe."""
    data = request.get_json(silent=True) or {}
    user_key = (data.get("user_key") or "").strip()

    if not user_key or len(user_key) != 30:
        return jsonify({"status": "error", "message": "User Key 格式不正确，应为30位字符"})

    # Notify admin (you) to manually add this user to the group
    send_pushover(
        message=f"New subscriber User Key:\n{user_key}",
        title="SignalX — 新用户订阅",
    )

    return jsonify({
        "status": "ok",
        "message": "激活请求已收到！我们会在几分钟内将你加入推送群组，请留意 Pushover 通知。",
    })


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
            sid: {"last_check": dt.isoformat() if dt else None}
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
