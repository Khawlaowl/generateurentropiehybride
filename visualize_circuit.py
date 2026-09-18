"""
visualize_circuit.py
=====================
Visualise le circuit H + mesure du QRNG en LOCAL, sans compte IBM Quantum,
sans instance, sans connexion internet. Équivalent des panneaux du
Composer (schéma, Q-sphere/Bloch, histogramme de probabilités).

Usage :
    pip install qiskit matplotlib pylatexenc
    python3 visualize_circuit.py
"""
from qiskit import QuantumCircuit, transpile
from qiskit.providers.basic_provider import BasicSimulator
from qiskit.quantum_info import Statevector
from qiskit.visualization import plot_histogram, plot_bloch_multivector, plot_state_qsphere
import matplotlib.pyplot as plt

N_QUBITS = 4

# --------------------------------------------------------------------- #
# 1. Construire le circuit (H sur chaque qubit), SANS mesure pour l'instant
# --------------------------------------------------------------------- #
qc_superposition = QuantumCircuit(N_QUBITS, N_QUBITS)
qc_superposition.h(range(N_QUBITS))

# --------------------------------------------------------------------- #
# 2. État quantique AVANT mesure (équivalent Q-sphere / Bloch du Composer)
#    Doit être calculé sur le circuit SANS mesure : une fois mesuré,
#    l'état "collapse" et il n'y a plus de superposition à visualiser.
# --------------------------------------------------------------------- #
statevector = Statevector.from_instruction(qc_superposition)

fig_bloch = plot_bloch_multivector(statevector)
fig_bloch.savefig("bloch_sphere.png", bbox_inches="tight")
print("Sphères de Bloch -> bloch_sphere.png")

fig_qsphere = plot_state_qsphere(statevector)
fig_qsphere.savefig("q_sphere.png", bbox_inches="tight")
print("Q-sphere -> q_sphere.png")

# --------------------------------------------------------------------- #
# 3. Circuit COMPLET (H + mesure) : c'est celui-ci qu'on dessine et exécute
# --------------------------------------------------------------------- #
qc = qc_superposition.copy()
qc.measure(range(N_QUBITS), range(N_QUBITS))

# Schéma du circuit complet, mesures incluses (comme la vue du Composer)
fig_circuit = qc.draw("mpl")
fig_circuit.savefig("circuit_diagram.png", bbox_inches="tight")
print("Schéma du circuit -> circuit_diagram.png")

simulator = BasicSimulator()
compiled = transpile(qc, simulator)
job = simulator.run(compiled, shots=1024)
counts = job.result().get_counts()

fig_hist = plot_histogram(counts)
fig_hist.savefig("probabilities_histogram.png", bbox_inches="tight")
print("Histogramme des probabilités -> probabilities_histogram.png")

print("\nRésultats bruts (1024 shots) :")
for outcome, count in sorted(counts.items()):
    print(f"  {outcome} : {count}")

plt.show()  # ouvre les fenêtres si tu es en local (pas dans un notebook headless)
