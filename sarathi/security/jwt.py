import base64
import hashlib
import hmac
import json
import time
from typing import Dict, Any, Optional

class JWTManager:
    def __init__(self, secret_key: str, algorithm: str = "HS256", default_ttl: float = 3600.0):
        self.secret_key = secret_key.encode('utf-8')
        self.algorithm = algorithm
        self.default_ttl = default_ttl

    def _base64url_encode(self, data: bytes) -> str:
        return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')

    def _base64url_decode(self, data: str) -> bytes:
        padding = '=' * (4 - (len(data) % 4))
        return base64.urlsafe_b64decode((data + padding).encode('utf-8'))

    def encode(self, payload: Dict[str, Any], ttl: Optional[float] = None) -> str:
        header = {"alg": self.algorithm, "typ": "JWT"}
        now = time.time()
        effective_ttl = ttl if ttl is not None else self.default_ttl

        claims = dict(payload)
        claims.setdefault("iat", int(now))
        claims.setdefault("exp", int(now + effective_ttl))

        header_b64 = self._base64url_encode(json.dumps(header, separators=(',', ':')).encode('utf-8'))
        payload_b64 = self._base64url_encode(json.dumps(claims, separators=(',', ':')).encode('utf-8'))

        signing_input = f"{header_b64}.{payload_b64}".encode('utf-8')
        signature = hmac.new(self.secret_key, signing_input, hashlib.sha256).digest()
        sig_b64 = self._base64url_encode(signature)

        return f"{header_b64}.{payload_b64}.{sig_b64}"

    def decode(self, token: str) -> Dict[str, Any]:
        parts = token.split('.')
        if len(parts) != 3:
            raise ValueError("Invalid JWT format")

        header_b64, payload_b64, sig_b64 = parts
        signing_input = f"{header_b64}.{payload_b64}".encode('utf-8')
        expected_sig = hmac.new(self.secret_key, signing_input, hashlib.sha256).digest()
        actual_sig = self._base64url_decode(sig_b64)

        if not hmac.compare_digest(expected_sig, actual_sig):
            raise ValueError("Invalid signature")

        payload = json.loads(self._base64url_decode(payload_b64).decode('utf-8'))
        if "exp" in payload and time.time() > payload["exp"]:
            raise ValueError("Token has expired")

        return payload
