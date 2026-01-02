from typing import Any

from auraframes.api.baseApi import BaseApi


# TODO: Test
class NotificationAPI(BaseApi):
    def get_notification_settings(self) -> Any:
        json_response = self._client.get("f/notifications/settings/")

        return json_response

    def update_notification(self, update_settings: Any) -> Any:
        json_response = self._client.post(
            "/notifications/update_setting", data=update_settings
        )

        return json_response
