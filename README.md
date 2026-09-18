🔐 Projet perso : un générateur d'entropie hybride pour sécuriser des infrastructures SSH/VPN

La faille la plus sous-estimée en cybersécurité n'est souvent pas l'algorithme de chiffrement lui-même, mais la qualité de l'aléa utilisé pour générer les clés. Un générateur prévisible = une porte dérobée gratuite pour un attaquant.

J'ai conçu et implémenté un pipeline en 3 étapes :

1️⃣ Source quantique (Qiskit) — circuit à portes de Hadamard simulant la superposition quantique, mesuré pour produire un flux de bits
2️⃣ Durcissement (HKDF-SHA512) — mélange de cette entropie avec le bruit natif du système d'exploitation (os.urandom), pour une défense en profondeur même si une source est compromise
3️⃣ Application concrète — génération automatique de clés Ed25519 (SSH), X25519 (VPN) et RSA-2048 + certificat X.509, puis déploiement réel dans un tunnel WireGuard monté entre deux VMs

Techs utilisées : Python, Qiskit, cryptography, HKDF/RFC 5869, WireGuard, VirtualBox.

Ce projet m'a permis d'approfondir à la fois les fondamentaux de la mécanique quantique appliquée (superposition, règle de Born) et les briques concrètes d'une infrastructure réseau sécurisée, de la théorie jusqu'au tunnel chiffré fonctionnel.
