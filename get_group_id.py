"""臨時 webhook server，用來取得 LINE 群組 Group ID。"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json


class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length))

        for event in body.get("events", []):
            source = event.get("source", {})
            source_type = source.get("type")
            if source_type == "group":
                group_id = source.get("groupId")
                print(f"\n{'='*60}")
                print(f"找到 Group ID: {group_id}")
                print(f"{'='*60}")
                print(f"\n請把這個 ID 填入 .env 的 LINE_GROUP_ID")
            elif source_type == "user":
                print(f"\n收到個人訊息 (userId: {source.get('userId')})")
                print("請在「群組」中傳訊息，不是個人聊天")
            else:
                print(f"\n收到事件: type={source_type}, source={source}")

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"status":"ok"}')

    def log_message(self, format, *args):
        pass  # 靜音 HTTP log


print("Webhook server 啟動在 port 8765 ...")
print("等待群組訊息中... (在群組裡傳任意訊息)")
print("按 Ctrl+C 結束\n")
HTTPServer(("", 8765), WebhookHandler).serve_forever()
