import logging
import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import anyio

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class WhatsAppCloudAPIError(RuntimeError):
    pass


class WhatsAppCloudAPI:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def send_whatsapp_message(self, to: str, message: str) -> dict[str, Any]:
        return await self._send_payload(
            to=to,
            payload={
                "messaging_product": "whatsapp",
                "to": to,
                "type": "text",
                "text": {"body": message},
            },
        )

    async def send_whatsapp_image(self, to: str, image_url: str, caption: str | None = None) -> dict[str, Any]:
        image_payload: dict[str, str] = {"link": image_url}
        if caption:
            image_payload["caption"] = caption
        return await self._send_payload(
            to=to,
            payload={
                "messaging_product": "whatsapp",
                "to": to,
                "type": "image",
                "image": image_payload,
            },
        )

    async def _send_payload(self, to: str, payload: dict[str, Any]) -> dict[str, Any]:
        phone_number_id = self.settings.phone_number_id
        access_token = self.settings.access_token
        if not phone_number_id or not access_token:
            raise WhatsAppCloudAPIError("WhatsApp ACCESS_TOKEN and PHONE_NUMBER_ID must be configured.")

        url = (
            f"https://graph.facebook.com/{self.settings.whatsapp_graph_api_version}/"
            f"{phone_number_id}/messages"
        )
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        return await anyio.to_thread.run_sync(self._post_message, url, headers, payload, to)

    def _post_message(
        self,
        url: str,
        headers: dict[str, str],
        payload: dict[str, Any],
        to: str,
    ) -> dict[str, Any]:
        request = Request(
            url=url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urlopen(request, timeout=10) as response:
                body = response.read().decode("utf-8")
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            logger.error(
                "WhatsApp API rejected message to %s: status=%s body=%s",
                to,
                exc.code,
                body,
            )
            raise WhatsAppCloudAPIError("WhatsApp API rejected outbound message.") from exc
        except URLError as exc:
            logger.error("WhatsApp API request failed for %s: %s", to, exc)
            raise WhatsAppCloudAPIError("WhatsApp API request failed.") from exc

        return json.loads(body) if body else {}


async def sendWhatsAppMessage(to: str, message: str) -> dict[str, Any]:
    return await WhatsAppCloudAPI().send_whatsapp_message(to, message)
