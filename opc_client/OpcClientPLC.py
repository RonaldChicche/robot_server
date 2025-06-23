from opcua import Client, ua
from typing import Optional


class OpcUaClient(Client):
    def __init__(self, endpoint: str, username: Optional[str] = None, password: Optional[str] = None):
        super().__init__(endpoint)
        if username and password:
            self.set_user(username)
            self.set_password(password)

        self.conection_id = None
        self.subscription_id = None
        self.sub_handles = []
        self.is_connected = False