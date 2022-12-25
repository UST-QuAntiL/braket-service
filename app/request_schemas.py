import marshmallow as ma
from marshmallow import pre_load, ValidationError
import numpy as np


class ExecutionRequest:
    def __init__(self, qpu_name, impl_language, impl_url, transpiled_cirq_json, impl_data, bearer_token, shots, input_params):
        self.qpu_name = qpu_name
        self.impl_language = impl_language
        self.impl_url = impl_url
        self.impl_data = impl_data
        self.transpiled_cirq_json = transpiled_cirq_json
        self.bearer_token = bearer_token
        self.shots = shots
        self.input_params = input_params


class ResultRequest:
    def __init__(self, result_id):
        self.result_id = result_id


class ExecutionRequestSchema(ma.Schema):
    qpu_name = ma.fields.String()
    impl_language = ma.fields.String()
    impl_url = ma.fields.String()
    impl_data = ma.fields.String()
    transpiled_cirq_json = ma.fields.String()
    bearer_token = ma.fields.String()
    shots = ma.fields.Integer()
    input_params = ma.fields.Mapping()


class ResultRequestSchema(ma.Schema):
    result_id = ma.fields.String()
