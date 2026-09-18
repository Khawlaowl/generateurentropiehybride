
import datetime

from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ed25519, x25519
from cryptography.hazmat.primitives.asymmetric.rsa import (
    RSAPrivateNumbers,
    RSAPublicNumbers,
    rsa_crt_dmp1,
    rsa_crt_dmq1,
    rsa_crt_iqmp,
)
from sympy import nextprime

from drbg import HmacDrbg


# --------------------------------------------------------------------- #
# SSH (Ed25519)
# --------------------------------------------------------------------- #
def generate_ed25519_ssh_keypair(seed32: bytes):
    """32 octets d'entropie hybride -> clé privée Ed25519 (format OpenSSH)."""
    if len(seed32) != 32:
        raise ValueError("Ed25519 nécessite exactement 32 octets de graine.")
    priv = ed25519.Ed25519PrivateKey.from_private_bytes(seed32)
    pub = priv.public_key()
    priv_pem = priv.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.OpenSSH,
        encryption_algorithm=serialization.NoEncryption(),
    )
    pub_ssh = pub.public_bytes(
        encoding=serialization.Encoding.OpenSSH,
        format=serialization.PublicFormat.OpenSSH,
    )
    return priv, priv_pem, pub_ssh


# --------------------------------------------------------------------- #
# VPN (X25519 — échange de clés type WireGuard)
# --------------------------------------------------------------------- #
def generate_x25519_keypair(seed32: bytes):
    if len(seed32) != 32:
        raise ValueError("X25519 nécessite exactement 32 octets de graine.")
    priv = x25519.X25519PrivateKey.from_private_bytes(seed32)
    return priv, priv.public_key()


# --------------------------------------------------------------------- #
# RSA — nombres premiers pilotés par le DRBG hybride
# --------------------------------------------------------------------- #
def _drbg_random_odd_int(drbg: HmacDrbg, bit_length: int) -> int:
    n_bytes = bit_length // 8
    raw = bytearray(drbg.generate(n_bytes))
    raw[0] |= 0x80  # garantit la taille en bits exacte
    raw[-1] |= 1    # impair
    return int.from_bytes(bytes(raw), "big")


def _drbg_generate_prime(drbg: HmacDrbg, bit_length: int) -> int:
    candidate = _drbg_random_odd_int(drbg, bit_length)
    return nextprime(candidate)


def generate_rsa_keypair_from_entropy(seed: bytes, key_size: int = 2048):
    """Clé RSA dont p et q proviennent d'un HMAC-DRBG réamorcé avec la
    graine hybride (quantique simulé + os.urandom), au lieu du RNG
    interne d'OpenSSL utilisé par défaut par `rsa.generate_private_key`.
    """
    drbg = HmacDrbg(seed, personalization=b"rsa-keygen-v1")
    half = key_size // 2

    p = _drbg_generate_prime(drbg, half)
    q = _drbg_generate_prime(drbg, half)
    while q == p:
        q = _drbg_generate_prime(drbg, half)

    n = p * q
    e = 65537
    phi = (p - 1) * (q - 1)
    d = pow(e, -1, phi)

    dmp1 = rsa_crt_dmp1(d, p)
    dmq1 = rsa_crt_dmq1(d, q)
    iqmp = rsa_crt_iqmp(p, q)

    priv_numbers = RSAPrivateNumbers(
        p=p, q=q, d=d, dmp1=dmp1, dmq1=dmq1, iqmp=iqmp,
        public_numbers=RSAPublicNumbers(e=e, n=n),
    )
    return priv_numbers.private_key()


# --------------------------------------------------------------------- #
# Certificat X.509 auto-signé (HTTPS / VPN)
# --------------------------------------------------------------------- #
def build_self_signed_certificate(private_key, common_name="corp-vpn.example.com", days_valid=365):
    subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, "MA"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Quantum-Enhanced Entropy Pipeline"),
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
        ]
    )
    now = datetime.datetime.now(datetime.timezone.utc)
    builder = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(minutes=5))
        .not_valid_after(now + datetime.timedelta(days=days_valid))
        .add_extension(x509.SubjectAlternativeName([x509.DNSName(common_name)]), critical=False)
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
    )
    if isinstance(private_key, ed25519.Ed25519PrivateKey):
        cert = builder.sign(private_key, algorithm=None)
    else:
        cert = builder.sign(private_key, algorithm=hashes.SHA512())
    return cert
