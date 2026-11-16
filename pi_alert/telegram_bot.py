"""Gửi tin nhắn và nhận lệnh Telegram qua Bot API (long polling)."""
import requests

API = "https://api.telegram.org/bot{token}/{method}"


class Telegram:
    def __init__(self, token, chat_id, dry_run=False):
        self.token, self.chat_id, self.dry_run = token, str(chat_id), dry_run
        self.offset = None

    def _call(self, method, timeout=20, **params):
        r = requests.post(API.format(token=self.token, method=method), json=params, timeout=timeout)
        r.raise_for_status()
        return r.json()

    def send(self, text, chat_id=None):
        if self.dry_run or not self.token:
            print("\n----- [TELEGRAM] -----\n" + text + "\n----------------------")
            return
        for i in range(0, len(text), 4000):  # giới hạn 4096 ký tự/tin
            self._call("sendMessage", chat_id=chat_id or self.chat_id, text=text[i:i + 4000],
                       parse_mode="HTML", disable_web_page_preview=True)

    def poll_commands(self, timeout=20):
        """Trả về list (chat_id, lệnh). Chỉ chấp nhận lệnh từ TELEGRAM_CHAT_ID đã cấu hình."""
        if self.dry_run or not self.token:
            return []
        params = {"timeout": timeout, "allowed_updates": ["message"]}
        if self.offset is not None:
            params["offset"] = self.offset
        data = self._call("getUpdates", timeout=timeout + 10, **params)
        cmds = []
        for u in data.get("result", []):
            self.offset = u["update_id"] + 1
            msg = u.get("message") or {}
            text = (msg.get("text") or "").strip()
            cid = str(msg.get("chat", {}).get("id", ""))
            if text.startswith("/") and cid == self.chat_id:
                cmds.append((cid, text.split()[0].split("@")[0].lower()))
        return cmds

    def print_chat_ids(self):
        data = self._call("getUpdates", timeout=30)
        seen = set()
        for u in data.get("result", []):
            chat = (u.get("message") or u.get("channel_post") or {}).get("chat", {})
            if chat and chat["id"] not in seen:
                seen.add(chat["id"])
                print(f"chat_id={chat['id']}  ({chat.get('type')}: "
                      f"{chat.get('title') or chat.get('username') or chat.get('first_name')})")
        if not seen:
            print("Chưa thấy tin nhắn nào. Hãy nhắn /start cho bot rồi chạy lại lệnh này.")
