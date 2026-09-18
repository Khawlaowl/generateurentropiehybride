
import os
import math

CHUNK_SIZE = 8  # BasicSimulator utilise un état de taille 2**n_qubits


class QuantumEntropySource:
    def __init__(self, backend: str = "auto"):
        self.mode = None
        self._QuantumCircuit = None
        self._transpile = None
        self._simulator = None

        if backend in ("auto", "qiskit"):
            try:
                from qiskit import QuantumCircuit, transpile
                from qiskit.providers.basic_provider import BasicSimulator

                self._QuantumCircuit = QuantumCircuit
                self._transpile = transpile
                self._simulator = BasicSimulator()
                self.mode = "qiskit"
            except ImportError:
                if backend == "qiskit":
                    raise RuntimeError(
                        "Backend 'qiskit' demandé explicitement mais Qiskit "
                        "n'est pas installé. Faites : pip install qiskit"
                    )

        if self.mode is None:
            self.mode = "fallback"

    # ------------------------------------------------------------------ #
    def _generate_chunk_qiskit(self, n_qubits: int) -> str:
        qc = self._QuantumCircuit(n_qubits, n_qubits)
        qc.h(range(n_qubits))
        qc.measure(range(n_qubits), range(n_qubits))
        compiled = self._transpile(qc, self._simulator)
        job = self._simulator.run(compiled, shots=1)
        counts = job.result().get_counts()
        bitstring = next(iter(counts))  # une seule shot -> une seule clé
        return bitstring.replace(" ", "")

    def _generate_chunk_fallback(self, n_qubits: int) -> str:
        raw = os.urandom(math.ceil(n_qubits / 8))
        bits = "".join(f"{byte:08b}" for byte in raw)
        return bits[:n_qubits]

    # ------------------------------------------------------------------ #
    def generate_bits(self, n_bits: int) -> str:
        """Retourne une chaîne de n_bits caractères '0'/'1'."""
        chunks = []
        remaining = n_bits
        while remaining > 0:
            n = min(CHUNK_SIZE, remaining)
            if self.mode == "qiskit":
                chunks.append(self._generate_chunk_qiskit(n))
            else:
                chunks.append(self._generate_chunk_fallback(n))
            remaining -= n
        return "".join(chunks)

    def generate_bytes(self, n_bytes: int) -> bytes:
        bits = self.generate_bits(n_bytes * 8)
        return int(bits, 2).to_bytes(n_bytes, "big")
