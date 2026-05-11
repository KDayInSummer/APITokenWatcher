import sys
import time
import threading
from pathlib import Path

# 确保项目根目录在导入路径中
ROOT = Path(__file__).parent.resolve()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import webview
import uvicorn
from backend.main import app

HOST = "127.0.0.1"
PORT = 8765
URL = f"http://{HOST}:{PORT}"


def start_server():
    uvicorn.run(app, host=HOST, port=PORT, log_level="warning")


def main():
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    # 等待服务就绪
    time.sleep(1.5)

    window = webview.create_window(
        title="APITokenWatcher",
        url=URL,
        width=900,
        height=560,
        min_size=(360, 240),
        text_select=True,
    )
    webview.start(debug=False)


if __name__ == "__main__":
    main()
