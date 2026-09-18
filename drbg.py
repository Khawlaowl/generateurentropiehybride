"""
drbg.py
=======
HMAC-DRBG minimal (inspiré de NIST SP 800-90A, non certifié / usage
pédagogique) : transforme une graine unique (la sortie de
HybridEntropyExtractor) en un flux pseudo-aléatoire arbitrairement long.

Utilisé par key_generator.py pour la recherche des nombres premiers RSA,
car la génération de clé RSA "standard" (cryptography/OpenSSL) ne permet
pas d'injecter directement notre propre entropie hybride : OpenSSL pioche
dans son propre RNG interne. En pilotant nous-mêmes la recherche de
premiers avec ce DRBG, la totalité de la clé RSA dérive bien de la
graine hybride quantique+OS.
"""
import hmac
import hashlib


class HmacDrbg:
    def __init__(self, seed: bytes, personalization: bytes = b""):
        self._k = b"\x00" * 64
        self._v = b"\x01" * 64
        self._update(seed + personalization)

    def _hmac(self, key: bytes, data: bytes) -> bytes:
        return hmac.new(key, data, hashlib.sha512).digest()

    def _update(self, data: bytes = b"") -> None:
        self._k = self._hmac(self._k, self._v + b"\x00" + data)
        self._v = self._hmac(self._k, self._v)
        if data:
            self._k = self._hmac(self._k, self._v + b"\x01" + data)
            self._v = self._hmac(self._k, self._v)

    def generate(self, n_bytes: int) -> bytes:
        out = b""
        while len(out) < n_bytes:
            self._v = self._hmac(self._k, self._v)
            out += self._v
        self._update()  # backtracking resistance
        return out[:n_bytes]
