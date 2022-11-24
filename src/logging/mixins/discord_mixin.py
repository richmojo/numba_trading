from discord_webhook import DiscordWebhook
from threading import Thread
import time


class DiscordMixin:
    def send_discord_errors(self, message):
        send_thread = Thread(target=self._send, args=(self.discord_errors_url, message,))
        send_thread.start()

    def send_discord_logs(self, message):
        send_thread = Thread(target=self._send, args=(self.discord_logs_url, message,))
        send_thread.start()

    def send_discord_trades(self, message):
        send_thread = Thread(target=self._send, args=(self.discord_trades_url, message,))
        send_thread.start()

    def _send(self, url, message):
        try:
            webhook = DiscordWebhook(url=url, content=message, timeout=10)
            webhook.execute()
            time.sleep(.1)
        except Exception as e:
            print(e)