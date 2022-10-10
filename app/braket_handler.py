# ******************************************************************************
#  Copyright (c) 2021 University of Stuttgart
#
#  See the NOTICE file(s) distributed with this work for additional
#  information regarding copyright ownership.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
# ******************************************************************************
from time import sleep

from braket.circuits import Circuit, Noise
from braket.devices import LocalSimulator
from braket.aws import AwsDevice
from braket.tasks import QuantumTask


def get_backend(qpu):
    """Get backend."""
    if qpu.lower() == "local-simulator":
        return LocalSimulator("braket_dm")
    else:
        try:
            return AwsDevice(qpu)
        except ValueError:
            return None


def delete_token():
    """Delete account."""
    pass


def execute_job(circuit: Circuit, shots, backend):
    """Execute and Simulate Job on simulator and return results"""
    if isinstance(backend, LocalSimulator):
        noise = Noise.Depolarizing(probability=0.1)
        circuit.apply_gate_noise(noise)
        circuit.apply_readout_noise(noise)
        circuit.apply_initialization_noise(noise)
    task = backend.run(circuit, shots=shots)
    status = task.state()
    while not status == "COMPLETED":
        if status == "FAILED" or status == "CANCELLED":
            print("The execution failed or was cancelled.")
            return None
        print("The task is still running")
        status = task.state()
    result = task.result()
    return result.measurement_counts
