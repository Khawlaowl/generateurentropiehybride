"""
entropy_extractor.py
=====================
Étape 2 de l'architecture : le Pipeline de Durcissement.

Le flux "quantique" (simulé, cf. qrng_source.py) est mélangé avec une
source de bruit indépendante du système d'exploitation (os.urandom,
adossé à /dev/urandom sous Linux / getrandom(2)) via HKDF (RFC 5869)
instancié avec SHA-512.

Pourquoi HKDF plutôt qu'un simple SHA-512(a || b) :
  - HKDF-Extract "aplatit" une source d'entropie potentiellement
    biaisée (IKM = nos bits quantiques) en une clé pseudo-aléatoire
    uniforme, en utilisant le sel (salt = bruit OS) comme clé HMAC.
  - HKDF-Expand permet de dériver autant d'octets de sortie que
    nécessaire (ex: 32 pour Ed25519, 256 pour RSA-2048) tout en
    conservant une séparation de domaine via le paramètre `info`
    (deux appels avec des `info` différents ne collisionnent jamais).
  - C'est la construction standard recommandée par la NIST SP 800-56C
    pour combiner plusieurs sources d'entropie hétérogènes.
"""
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
        """
        quantum_bytes : IKM issu du QRNG (simulé)
        length        : nombre d'octets de sortie désirés
        info          : étiquette de contexte (domain separation)
        os_salt_len   : taille en octets du sel os.urandom
        """
        salt = os.urandom(os_salt_len)
        hkdf = HKDF(
            algorithm=self.hash_algo,
            length=length,
            salt=salt,
            info=info,
        )
        return hkdf.derive(quantum_bytes)
