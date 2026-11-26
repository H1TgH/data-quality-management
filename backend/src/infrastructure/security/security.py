from cryptography.fernet import Fernet

from settings import settings


class Security:
    def __init__(
        self,
        secret_key: str
    ):
        self.fernet = Fernet(secret_key.encode("utf-8"))

    def encrypt(
        self,
        data: str
    ) -> str:
        data_bytes = data.encode("utf-8")
        encrypted_bytes = self.fernet.encrypt(data_bytes)
        return encrypted_bytes.decode("utf-8")

    def decrypt(
        self,
        encrypted_data: str
    ) -> str:
        encrypted_bytes = encrypted_data.encode("utf-8")
        encrypted_bytes = self.fernet.decrypt(encrypted_bytes)
        return encrypted_bytes.decode("utf-8")


security_instance = Security(settings.security.secret_key.get_secret_value())
