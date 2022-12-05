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

import boto3
from braket.circuits import Circuit, Noise
from braket.devices import LocalSimulator
from braket.aws import AwsDevice
from braket.tasks import QuantumTask
from botocore.config import Config


def get_backend(qpu, client = None):
    """Get backend."""
    if qpu.lower() == "local-simulator":
        return LocalSimulator("braket_dm")
    elif client:
        try:
            return client.get_device(qpu)
        except ValueError:
            return None

def set_up_client(access_key, secret_access_key, region):
    custom_config = Config(
        region_name=region,
    )
    braket_client = boto3.client('braket', aws_access_key_id=access_key, aws_secret_access_key=secret_access_key,
                                config=custom_config)
    s3_client = boto3.client('s3', aws_access_key_id=access_key, aws_secret_access_key=secret_access_key,
                            config=custom_config)

    s3_response = s3_client.s3client.list_buckets
    bucket_available = False
    for bucket in s3_response["Buckets"]:
        if bucket["Name"] == "braket-service-bucket":
            bucket_available = True
    if not bucket_available:
        s3_client.create_bucket(Bucket="braket-service-bucket")
    return braket_client, s3_client


def execute_job(circuit: Circuit, shots, qpu, clients = None):
    """Execute and Simulate Job on simulator and return results"""
    if qpu.lower() == "local-simulator":
        return execute_locally(circuit, shots)
    elif clients:
        return execute_remotely(circuit, shots, qpu, clients)
    return None


def execute_locally(circuit: Circuit, shots):
    backend = LocalSimulator("braket_dm")
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


def execute_remotely(circuit: Circuit, shots, qpu, clients):
    client = clients[0]
    s3_client = clients[1]
    response = client.search_devices(filters=[{
        "name": "deviceArn",
        "values": [qpu]
    }])
    if len(response["devices"]) == 0:
        print("No device found with that arn")
        return None
    kwargs = {
        "action": {circuit.to_ir()},
        "device": {qpu},
        "deviceParameters": '{"braketSchemaHeader": {"name": "braket.device_schema.simulators.gate_model_simulator_device_parameters", "version": "1"}, "paradigmParameters": {"braketSchemaHeader": {"name": "braket.device_schema.gate_model_parameters", "version": "1"}, "qubitCount":' + str(
            len(circuit.qubits)) + '}"',
        "outputS3Bucket": "braket-service-bucket",
        "outputS3KeyPrefix": "braket-service",
        "shots": shots
    }
    response = client.create_quantum_task(**kwargs)
    task_arn = response["quantumTaskArn"]
    response = client.get_quantum_task(quantumTaskArn=task_arn)
    while response["status"] != "FINISHED":
        if response["status"] == "FAILED" or response["status"] == "CANCELLED":
            return None
        sleep(3)
        response = client.get_quantum_task(quantumTaskArn=task_arn)
    print("execution finished")
    with open('results.txt', 'wb') as f:
        s3_client.download_fileobj("braket-service-bucket", "braket-service", f)
