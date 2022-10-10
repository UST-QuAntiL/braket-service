from braket.circuits import Circuit, Observable
from braket.circuits.result_types import Sample


def get_circuit(param1):
    circuit = Circuit()
    circuit.h(0)
    circuit.cnot(0, 1)
    circuit.rx(0, param1)
    circuit.add_result_type(Sample(Observable.Z()), 0)
    circuit.add_result_type(Sample(Observable.Z()), 1)
    return circuit



