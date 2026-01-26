import os, json, re, datetime, asyncio, base64
import requests
from bs4 import BeautifulSoup
from telegram import Bot
from telegram.constants import ParseMode
from urllib.parse import urlparse, urlunparse, quote

# ================== CONFIG ==================
BOT_TOKEN = os.getenv("BOT_TOKEN")
TARGET_CHAT = os.getenv("TARGET_CHAT")

SOURCES = [
    "https://t.me/s/BestProxyTel1",
    "https://t.me/s/ch_v2ryng_support",
    "https://t.me/s/Proxymelimon",
    "https://t.me/s/nitruStore",
    "https://t.me/s/NETMelliAnti",
]

STATE_FILE = "last_messages.json"
MAX_LEN = 3800
CONFIG_NAME = "اتصال پایدار | configs_freeiran"
# ===========================================

HEADER = (
    "╔════════════════════╗\n"
    "🔥 CONFIG DROP 🔥\n"
    "╚════════════════════╝\n\n"
    "🛡 کانفیگ‌های پایدار و امن\n"
    "⚡ کپی با یک کلیک\n\n"
)

def footer(ts):
    return (
        "\n\n╔════════════════════╗\n"
        f"⏱ {ts}\n"
        "📡 @configs_freeiran\n"
        "╚════════════════════╝"
    )

# ---------- State ----------
def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False)

# ---------- Fetch ----------
def fetch_channel(url):
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    posts = soup.select("div.tgme_widget_message")
    messages = []

    for p in posts:
        mid = p.get("data-post")
        if not mid:
            continue
        text = p.get_text("\n", strip=True)
        messages.append((mid, text))

    return messages  # جدید → قدیم

# ---------- Extract ----------
def extract_configs(text):
    pattern = r'(vmess://[^\s]+|vless://[^\s]+|trojan://[^\s]+|ss://[^\s]+|ssr://[^\s]+)'
    return re.findall(pattern, text)

# ---------- Validate ----------
def is_valid_vmess(cfg):
    try:
        raw = cfg.replace("vmess://", "")
        data = json.loads(base64.b64decode(raw + "===").decode())
        return all(k in data for k in ("add", "port", "id"))
    except:
        return False

def is_valid_link(cfg):
    try:
        p = urlparse(cfg)
        return p.hostname is not None and p.port is not None
    except:
        return False

def is_valid_ss(cfg):
    try:
        raw = cfg.split("://", 1)[1].split("#", 1)[0]
        base64.b64decode(raw + "===")
        return True
    except:
        return False

def is_config_valid(cfg):
    if cfg.startswith("vmess://"):
        return is_valid_vmess(cfg)
    elif cfg.startswith(("vless://", "trojan://")):
        return is_valid_link(cfg)
    elif cfg.startswith(("ss://", "ssr://")):
        return is_valid_ss(cfg)
    return False

# ---------- Rename ----------
def rename_vmess(cfg, name):
    try:
        raw = cfg.replace("vmess://", "")
        data = json.loads(base64.b64decode(raw + "===").decode())
        data["ps"] = name
        new_raw = base64.b64encode(
            json.dumps(data, ensure_ascii=False).encode()
        ).decode()
        return "vmess://" + new_raw
    except:
        return cfg

def rename_by_fragment(cfg, name):
    try:
        p = urlparse(cfg)
        return urlunparse(p._replace(fragment=quote(name)))
    except:
        return cfg

def rename_config(cfg):
    if cfg.startswith("vmess://"):
        return rename_vmess(cfg, CONFIG_NAME)
    else:
        return rename_by_fragment(cfg, CONFIG_NAME)

# ---------- Build Messages ----------
def build_messages(configs):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    messages = []

    cur = HEADER + "<blockquote><code>"

    for cfg in configs:
        cfg = rename_config(cfg)
        piece = cfg + "\n"

        if len(cur) + len(piece) + len("</code></blockquote>") + len(footer(now)) > MAX_LEN:
            cur = cur.rstrip("\n") + "</code></blockquote>" + footer(now)
            messages.append(cur)
            cur = HEADER + "<blockquote><code>" + piece
        else:
            cur += piece

    if cur.strip() != HEADER.strip() + "<blockquote><code>":
        cur = cur.rstrip("\n") + "</code></blockquote>" + footer(now)
        messages.append(cur)

    return messages

# ---------- Main ----------
async def main():
    bot = Bot(BOT_TOKEN)
    state = load_state()
    all_new_configs = []

    for src in SOURCES:
        last = state.get(src)
        msgs = fetch_channel(src)

        for mid, text in msgs:
            if last and mid <= last:
                break

            for cfg in extract_configs(text):
                if is_config_valid(cfg):
                    all_new_configs.append(cfg)

        if msgs:
            state[src] = msgs[0][0]

    if not all_new_configs:
        print("📭 پیام جدیدی نیست")
        save_state(state)
        return

    messages = build_messages(all_new_configs)

    for m in messages:
        await bot.send_message(
            chat_id=TARGET_CHAT,
            text=m,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
        await asyncio.sleep(1)

    save_state(state)
    print(f"✅ ارسال شد | تعداد پیام: {len(messages)}")

if __name__ == "__main__":
    asyncio.run(main())
