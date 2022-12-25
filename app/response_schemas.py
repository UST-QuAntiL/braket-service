import marshmallow as ma
from flask import Response


class ExecutionResponse(Response):
    def __init__(self, location):
        super().__init__()
        self.location = location

    def to_json(self):
        json_response = {'Location': self.location}
        return json_response


class ResultResponse:
    def __init__(self, id, complete, result = None, backend = None, shots = None):
        self.id = id
        self.complete = complete
        self.result = result
        self.backend = backend
        self.shots = shots

    def to_json(self):
        if self.result and self.backend and self.shots:
            return {'id': self.id, 'complete': self.complete, 'result': self.result,
                            'backend': self.backend, 'shots': self.shots}
        else:
            return {'id': self.id, 'complete': self.complete}


class ExecutionResponseSchema(ma.Schema):
    location = ma.fields.String()


class ResultResponseSchema(ma.Schema):
    id = ma.fields.UUID()
    complete = ma.fields.Boolean()
    result = ma.fields.Mapping()
    backend = ma.fields.String()
    shots = ma.fields.Integer()