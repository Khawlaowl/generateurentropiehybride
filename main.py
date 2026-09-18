
import os
import sys
import math

from qrng_source import QuantumEntropySource
from entropy_extractor import HybridEntropyExtractor
from key_generator import (
    generate_ed25519_ssh_keypair,
    generate_x25519_keypair,
    generate_rsa_keypair_from_entropy,
    build_self_signed_certificate,
)
from cryptography.hazmat.primitives import serialization

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")


def monobit_frequency_test(bits: str) -> float:
    """Test statistique NIST SP 800-22 simplifié (test monobit).
    Renvoie une p-value : une valeur proche de 1 indique un flux
    compatible avec un aléa uniforme ; une valeur proche de 0 indique
    un biais statistique significatif (test d'ALERTE, pas une preuve
    de sécurité cryptographique à lui seul)."""
    n = len(bits)
    s = sum(1 if b == "1" else -1 for b in bits)
    s_obs = abs(s) / math.sqrt(n)
    # fonction d'erreur complémentaire
    p_value = math.erfc(s_obs / math.sqrt(2))
    return p_value


def banner(title: str):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # ---------------------------------------------------------------- #
    banner("ÉTAPE 1 — Source Quantique (QRNG)")
    qsource = QuantumEntropySource(backend="auto")
    print(f"Backend actif : {qsource.mode}")
    if qsource.mode == "fallback":
        print(
            "ATTENTION : Qiskit n'est pas installé dans cet environnement.\n"
            "Le flux est généré via os.urandom (même loi Bernoulli(0.5),\n"
            "mais sans passer par un simulateur d'état quantique).\n"
            "Sur votre poste : pip install qiskit  ->  bascule automatique."
        )

    n_test_bits = 2048
    bits = qsource.generate_bits(n_test_bits)
    p_value = monobit_frequency_test(bits)
    print(f"Échantillon : {n_test_bits} bits générés")
    print(f"Test monobit (NIST SP800-22, simplifié) : p-value = {p_value:.4f}")
    print("  -> échantillon jugé", "ACCEPTABLE" if p_value > 0.01 else "SUSPECT (biaisé)")

    # Entropie brute utilisée pour les clés (indépendante de l'échantillon de test)
    quantum_bytes_for_keys = qsource.generate_bytes(64)  # 512 bits d'IKM

    # ---------------------------------------------------------------- #
    banner("ÉTAPE 2 — Pipeline de Durcissement (HKDF-SHA512)")
    extractor = HybridEntropyExtractor()

    seed_ssh = extractor.extract(quantum_bytes_for_keys, length=32, info=b"ssh-ed25519")
    seed_vpn = extractor.extract(quantum_bytes_for_keys, length=32, info=b"vpn-x25519")
    seed_rsa = extractor.extract(quantum_bytes_for_keys, length=64, info=b"rsa-2048")
    print("3 graines dérivées (domain-separated) : ssh (32o), vpn (32o), rsa (64o)")

    # ---------------------------------------------------------------- #
    banner("ÉTAPE 3 — Application Cyber Concrète")

    # --- SSH Ed25519 ---
    priv_ssh, priv_pem, pub_ssh = generate_ed25519_ssh_keypair(seed_ssh)
    with open(os.path.join(OUTPUT_DIR, "id_ed25519_server"), "wb") as f:
        f.write(priv_pem)
    with open(os.path.join(OUTPUT_DIR, "id_ed25519_server.pub"), "wb") as f:
        f.write(pub_ssh)
    print("[SSH]  Clé Ed25519 générée -> output/id_ed25519_server(.pub)")

    # --- VPN X25519 ---
    priv_vpn, pub_vpn = generate_x25519_keypair(seed_vpn)
    priv_vpn_raw = priv_vpn.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    pub_vpn_raw = pub_vpn.public_bytes(
        encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw
    )
    import base64
    with open(os.path.join(OUTPUT_DIR, "serverx25519_private.key"), "w") as f:
        f.write(base64.b64encode(priv_vpn_raw).decode())
    with open(os.path.join(OUTPUT_DIR, "serverx25519_public.key"), "w") as f:
        f.write(base64.b64encode(pub_vpn_raw).decode())
    print("[VPN]  Paire X25519 générée -> output/serverx25519_{private,public}.key")

    # --- RSA + certificat X.509 ---
    print("[RSA]  Génération de p, q via HMAC-DRBG (peut prendre quelques secondes)...")
    priv_rsa = generate_rsa_keypair_from_entropy(seed_rsa, key_size=2048)
    rsa_pem = priv_rsa.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    with open(os.path.join(OUTPUT_DIR, "rsa_private_key.pem"), "wb") as f:
        f.write(rsa_pem)
    print("[RSA]  Clé RSA-2048 générée -> output/rsa_private_key.pem")

    cert = build_self_signed_certificate(priv_rsa, common_name="corp-vpn.example.com")
    cert_pem = cert.public_bytes(serialization.Encoding.PEM)
    with open(os.path.join(OUTPUT_DIR, "certificate.pem"), "wb") as f:
        f.write(cert_pem)
    print("[X.509] Certificat auto-signé -> output/certificate.pem")

    banner("TERMINÉ")
    print(f"Tous les artefacts sont dans : {OUTPUT_DIR}/")


if __name__ == "__main__":
    sys.exit(main())
