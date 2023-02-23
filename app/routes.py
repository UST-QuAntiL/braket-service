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
import braket.circuits

from app import app, braket_handler, implementation_handler, db, parameters
from app.request_schemas import ExecutionRequestSchema, ExecutionRequest, TranspilationRequestSchema, \
    TranspilationRequest
from app.response_schemas import ExecutionResponseSchema, ExecutionResponse, ResultResponseSchema, ResultResponse, \
    TranspilationResponseSchema, TranspilationResponse
from app.result_model import Result
from flask import jsonify, abort, request, Response
import logging
import json
from flask_smorest import Blueprint
import base64
import traceback


blp = Blueprint(
    "routes",
    __name__,
    url_prefix="/braket-service/api/v1.0/",
    description="All Braket-Service endpoints",
)


@blp.route("/transpile", methods=["POST"])
@blp.arguments(
    TranspilationRequestSchema,
    example={
        "impl-url": "https://raw.githubusercontent.com/UST-QuAntiL/braket-service/main/Sample%20Implementations/circuit_braket_ir.json",
        "impl-language": "Braket-IR"
    }
)
@blp.response(200, TranspilationResponseSchema)
def transpile_circuit(json: TranspilationRequest):
    """Get implementation from URL. Pass input into implementation. Generate and transpile circuit
    and return depth and width."""
    if not json:
        abort(400)
    qpu_name = json.get('qpu_name', "")
    impl_language = json.get('impl_language', '')
    input_params = json.get('input_params', "")
    impl_url = json.get('impl_url', "")
    impl_data = json.get('impl_data', "")
    bearer_token = json.get("bearer_token", "")
    app.logger.info("The input params are:" + str(input_params))
    if input_params != "":
        input_params = parameters.ParameterDictionary(input_params)
    # adapt if real backends are available
    token = ''
    # if 'token' in input_params:
    #     token = input_params['token']
    # elif 'token' in request.json:
    #     token = request.json.get('token')
    # else:
    #     abort(400)

    if impl_url:
        if impl_language.lower() == 'braket-ir':
            short_impl_name = 'no name'
            circuit = implementation_handler.prepare_code_from_braket_ir_url(impl_url, bearer_token)
        else:
            short_impl_name = "untitled"
            try:
                circuit = implementation_handler.prepare_code_from_url(impl_url, input_params, bearer_token)
            except ValueError:
                abort(400)

    elif impl_data:
        # Add padding is added for decoding
        app.logger.info(impl_data)
        impl_data = base64.b64decode(impl_data.encode() + b'=' * (-len(impl_data) % 4)).decode()

        short_impl_name = 'no short name'
        if impl_language.lower() == 'braket-ir':
            circuit = implementation_handler.prepare_code_from_braket_ir(impl_data)
        else:
            try:
                circuit = implementation_handler.prepare_code_from_data(impl_data, input_params)
            except ValueError:
                abort(400)
    else:
        abort(400)



    try:
        # transpile circuit (currently only local sim is supported, so no transpilation is done)

        if not qpu_name.lower == "local-simulator":
            # TODO: Do actual transpilation if ever possible
            pass

        # count number of gates and multi qubit gates by iterating over all operations
        number_of_multi_qubit_gates = 0

        total_number_of_gates = 0
        for instruction in circuit.instructions:
            if issubclass(type(instruction.operator), braket.circuits.gate.Gate):
                total_number_of_gates += 1
                if len(instruction.target) > 1:
                    number_of_multi_qubit_gates += 1

        # width: the amount of qubits
        width = len(circuit.qubits)

        # gate_depth: the longest subsequence of compiled instructions where adjacent instructions share resources
        depth = circuit.depth

        # multi_qubit_gate_depth not available in braket
        multi_qubit_gate_depth = -1

        # count number of single qubit gates
        number_of_single_qubit_gates = total_number_of_gates - number_of_multi_qubit_gates

        # in braket measurement operations are saved separately from gates as result types
        number_of_measurement_operations = len(circuit.result_types)

        # count total number of all operations including gates and measurement operations
        total_number_of_operations = total_number_of_gates + number_of_measurement_operations
    except NotImplementedError:
        app.logger.info(f"QPU {qpu_name} is not supported!")
        abort(400)
    except Exception:
        app.logger.info(f"Transpile {short_impl_name} for {qpu_name}.")
        app.logger.info(traceback.format_exc())
        return jsonify({'error': 'transpilation failed'}), 200

    app.logger.info(f"Transpile {short_impl_name} for {qpu_name}: "
                    f"w={width}, "
                    f"d={depth}, "
                    f"total number of operations={total_number_of_operations}, "
                    f"number of single qubit gates={number_of_single_qubit_gates}, "
                    f"number of multi qubit gates={number_of_multi_qubit_gates}, "
                    f"number of measurement operations={number_of_measurement_operations}, "
                    f"multi qubit gate depth={multi_qubit_gate_depth}")

    return TranspilationResponse(depth, multi_qubit_gate_depth, width, total_number_of_operations,
                                number_of_single_qubit_gates, number_of_multi_qubit_gates,
                                number_of_measurement_operations, circuit.to_ir().json(indent=4))





@blp.route("/execute", methods=["POST"])
@blp.arguments(
    ExecutionRequestSchema,
    example={
    "impl-url": "https://raw.githubusercontent.com/UST-QuAntiL/braket-service/main/Sample%20Implementations/circuit_braket.py",
    "impl-language": "Braket",
    "qpu-name": "local-simulator",
    "shots": 1024,
    "input-params": {
        "param1": {
                "rawValue": "2",
                "type": "Integer"
                }
        }
    }
)
@blp.response(202, ExecutionResponseSchema)
def execute_circuit(json: ExecutionRequest):
    """Put execution job in queue. Return location of the later result."""
    if not json or not json.get('qpu_name'):
        abort(400)
    qpu_name = json.get('qpu_name')
    impl_language = json.get('impl_language', '')
    impl_url = json.get('impl_url')
    bearer_token = json.get("bearer_token", "")
    impl_data = json.get('impl_data')
    braket_ir = json.get('braket_ir', "")
    input_params = json.get('input_params', "")
    if input_params != "":
        input_params = parameters.ParameterDictionary(input_params)
    shots = json.get('shots', 1024)
    if 'token' in input_params:
        token = input_params['token']
        input_params = {}
    elif json.get('token'):
        token = json.get('token')
    else:
        token = ""

    app.logger.info(f"ir {braket_ir}")

    job = app.execute_queue.enqueue('app.tasks.execute', impl_url=impl_url, impl_data=impl_data,
                                    impl_language=impl_language, braket_ir=braket_ir, qpu_name=qpu_name,
                                    token=token, input_params=input_params, shots=shots, bearer_token=bearer_token)
    result = Result(id=job.get_id(), backend=qpu_name, shots=shots)
    db.session.add(result)
    db.session.commit()

    logging.info('Returning HTTP response to client...')
    content_location = '/braket-service/api/v1.0/results/' + result.id
    response = ExecutionResponse(content_location)
    response.status_code = 202
    response.headers.set('Location', content_location)
    return response


@app.route('/braket-service/api/v1.0/calculate-calibration-matrix', methods=['POST'])
def calculate_calibration_matrix():
    """Put calibration matrix calculation job in queue. Return location of the later result."""
    abort(404)


@blp.route("/results/<string:result_id>", methods=["GET"])
@blp.response(200, ResultResponseSchema)
def get_result(result_id):
    """Return result when it is available."""
    result = Result.query.get(str(result_id).strip())
    if result.complete:
        result_histogram = json.loads(result.result)
        response = ResultResponse(result.id, result.complete, result_histogram, result.backend, result.shots)
    else:
        response = ResultResponse(result.id, result.complete)
    return response


@blp.route("/version", methods=["GET"])
@blp.response(200)
def version():
    """Return current version number."""
    return jsonify({'version': '1.0'})


