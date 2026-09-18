# Quantum-Enhanced Entropy Pipeline for Corporate VPN/SSH

Pipeline d'entropie hybride : QRNG simulé (Qiskit) → durcissement HKDF-SHA512
(mélange avec `os.urandom`) → génération de clés SSH (Ed25519), VPN (X25519)
et RSA-2048 + certificat X.509 auto-signé.

## Architecture

```
qrng_source.py        Étape 1 — circuit H + mesure (Qiskit ou repli os.urandom)
entropy_extractor.py  Étape 2 — HKDF-SHA512(IKM=bits quantiques, salt=os.urandom)
drbg.py                HMAC-DRBG utilisé pour piloter la recherche des premiers RSA
key_generator.py      Étape 3 — clés SSH / VPN / RSA + certificat X.509
main.py                Orchestrateur + test statistique monobit
```

## Installation

```bash
pip install qiskit cryptography sympy
```

## Exécution

```bash
python3 main.py
```

Les artefacts sont écrits dans `output/` :
`id_ed25519_server(.pub)`, `vpn_x25519_{private,public}.key`,
`rsa_private_key.pem`, `certificate.pem`.

## Point important : mode Qiskit vs mode de repli

`qrng_source.py` essaie d'abord d'utiliser Qiskit (`BasicSimulator`,
fourni avec `qiskit` — pas besoin de `qiskit-aer`). **Dans cet
environnement d'exécution sandbox, Qiskit n'a pas pu être installé
(pas d'accès réseau)**, donc le pipeline a tourné avec le backend de
repli : même loi de probabilité (Bernoulli 0.5 indépendants par bit)
mais l'aléa vient alors de `os.urandom` et non d'un état quantique
simulé. Sur votre machine, un simple `pip install qiskit` fait
basculer automatiquement sur le vrai circuit Qiskit — aucune autre
modification n'est nécessaire.

## Ce que le projet démontre (et ses limites, à assumer dans un rapport)

- **Ce que fait réellement un simulateur Qiskit** : `AerSimulator` /
  `BasicSimulator` sont des simulateurs *classiques* d'un état
  quantique — l'échantillonnage final du résultat de mesure repose
  lui-même sur le générateur pseudo-aléatoire classique de la machine
  hôte, pas sur du bruit physique quantique. C'est un point à souligner
  dans votre rapport : la « pureté quantique » ici est *simulée*, pas
  physique (contrairement à un vrai QRNG matériel, ex. ID Quantique).
- **Pourquoi mélanger avec `os.urandom` a du sens quand même** :
  combiner deux sources indépendantes (même toutes deux classiques
  in fine) via une construction extract-and-expand (HKDF) est une
  pratique standard de *defense in depth* — si l'une des deux sources
  est un jour compromise ou biaisée, la sortie reste robuste tant que
  l'autre ne l'est pas. C'est le même principe que les mélangeurs
  d'entropie utilisés dans les noyaux Linux modernes.
- **RSA** : contrairement à Ed25519/X25519 (où la clé privée est
  directement les 32 octets d'entropie), la génération RSA "standard"
  via OpenSSL ne permet pas d'injecter une graine externe — d'où le
  DRBG maison (`drbg.py`) qui pilote la recherche des nombres premiers
  p et q. C'est un choix pédagogique pour garder la traçabilité
  entropie → clé de bout en bout ; en production, utilisez plutôt les
  mécanismes de ré-ensemencement natifs de la CSPRNG du système
  (`RAND_add`/`getrandom`) plutôt qu'un DRBG non audité.
- **Le test monobit** (`main.py`) est une version très simplifiée d'un
  des tests de la suite NIST SP 800-22. Il ne prouve rien à lui seul
  sur la qualité cryptographique du flux — pour une validation
  sérieuse, faites tourner la suite NIST complète ou `dieharder` sur
  un échantillon de plusieurs mégaoctets.

## Pour aller plus loin

- Remplacer le repli par un vrai périphérique QRNG matériel si
  disponible (ex. via un flux série), en gardant la même interface
  `QuantumEntropySource.generate_bytes()`.
- Ajouter la suite de tests NIST SP 800-22 complète sur un grand
  échantillon avant de faire confiance au flux en production.
- Faire tourner `main.py` en tant que service qui ré-alimente
  périodiquement `/dev/random` du serveur SSH/VPN (`rngd`-like) plutôt
  que de ne générer qu'un jeu de clés ponctuel.
