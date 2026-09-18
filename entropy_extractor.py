
import os
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF


class HybridEntropyExtractor:
    def __init__(self, hash_algo=None):
        self.hash_algo = hash_algo or hashes.SHA512()

    def extract(
        self,
        quantum_bytes: bytes,
        length: int,
        info: bytes = b"hybrid-qrng-pipeline-v1",
        os_salt_len: int = 64,
    ) -> bytes:
        
        salt = os.urandom(os_salt_len)
        hkdf = HKDF(
            algorithm=self.hash_algo,
            length=length,
            salt=salt,
            info=info,
        )
        return hkdf.derive(quantum_bytes)
