import platform
import httpx
from plyer import notification

SYSTEM = platform.system()


def send_webhook(url: str, message: str) -> bool:
    try:
        resp = httpx.post(url, json={"text": message}, timeout=10)
        return resp.status_code < 400
    except Exception:
        return False


def send_desktop_notification(title: str, message: str):
    try:
        notification.notify(
            title=title,
            message=message,
            app_name="APITokenWatcher",
            timeout=10,
        )
    except Exception:
        pass


def notify_alert(alert_type: str, message: str, webhook_url: str | None = None):
    send_desktop_notification(f"APITokenWatcher 告警: {alert_type}", message)
    if webhook_url:
        send_webhook(webhook_url, message)
