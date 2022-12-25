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

from app import app, braket_handler, implementation_handler, db, parameters
from app.request_schemas import ExecutionRequestSchema, ExecutionRequest
from app.response_schemas import ExecutionResponseSchema, ExecutionResponse, ResultResponseSchema, ResultResponse
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


@app.route('/braket-service/api/v1.0/transpile', methods=['POST'])
def transpile_circuit():
    """Get implementation from URL. Pass input into implementation. Generate and transpile circuit
    and return depth and width."""

    # braket does not support compilation of circuits before execution
    abort(Response("The Braket Service does not support transpilation", 404))


@blp.route("/execute", methods=["POST"])
@blp.arguments(
    ExecutionRequestSchema,
    example={
    "impl_url": "https://raw.githubusercontent.com/UST-QuAntiL/braket-service/main/Sample%20Implementations/circuit_braket.py",
    "impl_language": "Braket",
    "qpu_name": "local-simulator",
    "shots": 1024,
    "input_params": {
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


