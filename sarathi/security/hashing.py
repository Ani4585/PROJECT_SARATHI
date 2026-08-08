import hashlib
import hmac
import os

def constant_time_compare(val1: str, val2: str) -> bool:
    return hmac.compare_digest(val1.encode('utf-8'), val2.encode('utf-8'))

class PasswordHasher:
    def __init__(self, iterations: int = 10_000, hash_name: str = "sha256"):
        self.iterations = iterations
        self.hash_name = hash_name

    def hash_password(self, password: str) -> str:
        salt = os.urandom(16)
        key = hashlib.pbkdf2_hmac(self.hash_name, password.encode('utf-8'), salt, self.iterations)
        return f"pbkdf2_{self.hash_name}${self.iterations}${salt.hex()}${key.hex()}"

    def verify_password(self, password: str, hashed: str) -> bool:
        try:
            parts = hashed.split('$')
            if len(parts) != 4 or not parts[0].startswith("pbkdf2_"):
                return False
            _, iterations_str, salt_hex, key_hex = parts
            iterations = int(iterations_str)
            salt = bytes.fromhex(salt_hex)
            expected_key = bytes.fromhex(key_hex)
            actual_key = hashlib.pbkdf2_hmac(self.hash_name, password.encode('utf-8'), salt, iterations)
            return hmac.compare_digest(expected_key, actual_key)
        except Exception:
            return False
