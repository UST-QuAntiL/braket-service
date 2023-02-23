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
import urllib
from urllib import request, error
import tempfile
import os, sys, shutil
from importlib import reload

import numpy as np
from braket.circuits import Circuit, Observable
from flask_restful import abort
from braket.ir.jaqcd import Program
from urllib3 import HTTPResponse

from app import app


def prepare_code_from_data(data, input_params):
    """Get implementation code from data. Set input parameters into implementation. Return circuit."""
    temp_dir = tempfile.mkdtemp()
    with open(os.path.join(temp_dir, "__init__.py"), "w") as f:
        f.write("")
    with open(os.path.join(temp_dir, "downloaded_code.py"), "w") as f:
        f.write(data)
    sys.path.append(temp_dir)
    try:
        import downloaded_code

        # deletes every attribute from downloaded_code, except __name__, because importlib.reload
        # doesn't reset the module's global variables
        for attr in dir(downloaded_code):
            if attr != "__name__":
                delattr(downloaded_code, attr)

        reload(downloaded_code)
        if 'get_circuit' in dir(downloaded_code):
            circuit = downloaded_code.get_circuit(**input_params)
        elif 'qc' in dir(downloaded_code):
            circuit = downloaded_code.qc
        elif 'p' in dir(downloaded_code):
            circuit = downloaded_code.p
        elif 'c' in dir(downloaded_code):
            circuit = downloaded_code.c
    finally:
        sys.path.remove(temp_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)
    if not circuit:
        raise ValueError
    return circuit


def prepare_code_from_url(url, input_params, bearer_token: str = ""):
    """Get implementation code from URL. Set input parameters into implementation. Return circuit."""
    try:
        impl = _download_code(url, bearer_token)
    except (error.HTTPError, error.URLError):
        return None

    circuit = prepare_code_from_data(impl, input_params)
    return circuit


def prepare_code_from_braket_ir(braket_ir):
    ir = Program.parse_raw(braket_ir)
    instructions = ir.instructions
    circuit = Circuit()
    # adding of instructions
    for inst in instructions:
        # Get instruction by name. This is possible since braket and braket ir use identical names for all gates.
        instcall = getattr(circuit, f"{inst.type}")
        args = []
        kwargs = {}
        # Special cases for gates that interact with matrices, since they have special target syntax
        if hasattr(inst, "matrices"):
            matrices = inst.matrices.copy()
            reformed_matrices = []
            for matrix in matrices:
                for row in matrix:
                    for i in range(len(row)):
                        row[i] = np.complex(row[i][0], row[i][1])
                reformed_matrices.append(np.array(matrix))
            args.append(inst.targets)
            kwargs["matrices"] = reformed_matrices
        elif hasattr(inst, "matrix"):
            matrix = inst.matrix.copy()
            for row in matrix:
                for i in range(len(row)):
                    row[i] = np.complex(row[i][0], row[i][1])
            kwargs["matrix"] = np.array(matrix)
            kwargs["targets"] = inst.targets
        else:
            # Adding of parameters to args and kwargs respectively
            if hasattr(inst, "control"):
                args.append(inst.control)
            elif hasattr(inst, "controls"):
                for control in inst.controls:
                    args.append(control)

            if hasattr(inst, "target"):
                args.append(inst.target)
            elif hasattr(inst, "targets"):
                for target in inst.targets:
                    args.append(target)

            if hasattr(inst, "angle"):
                args.append(inst.angle)

            if hasattr(inst, "probability"):
                kwargs["probability"] = inst.probability

            if hasattr(inst, "gamma"):
                kwargs["gamma"] = inst.gamma

        # Calls function using args and kwargs
        instcall(*args, **kwargs)

    # Get measurement operations from IR
    results = ir.results

    # Adding of resulttypes
    for result in results:
        # Isolated cases for statevector and densitymatrix,
        # since they don't have matching names in both representations
        if result.type == "statevector":
            circuit.state_vector()
        elif result.type == "densitymatrix":
            circuit.density_matrix(target=result.targets)
        else:
            # Get operation
            instcall = getattr(circuit, f"{result.type}")
            kwargs = {}
            # Adding of parameters to kwargs
            if hasattr(result, "observable"):
                obscall = getattr(Observable, f"{(str(result.observable[0])).upper()}")
                kwargs["observable"] = obscall()
            if hasattr(result, "states"):
                kwargs["states"] = result.states
            if hasattr(result, "targets"):
                kwargs["target"] = result.targets

            # Calls function with arguments
            instcall(**kwargs)
    return circuit


def prepare_code_from_braket_ir_url(url, bearer_token: str = ""):
    """Get implementation code from URL. Set input parameters into implementation. Return circuit."""
    try:
        impl = _download_code(url, bearer_token)
    except (error.HTTPError, error.URLError):
        return None

    return prepare_code_from_braket_ir(impl)


def _download_code(url: str, bearer_token: str = "") -> str:
    req = request.Request(url)

    if urllib.parse.urlparse(url).netloc == "platform.planqk.de":
        if bearer_token == "":
            app.logger.error("No bearer token specified, download from the PlanQK platform will fail.")

            abort(401)
        elif bearer_token.startswith("Bearer"):
            app.logger.error("The bearer token MUST NOT start with \"Bearer\".")

            abort(401)

        req.add_header("Authorization", "Bearer " + bearer_token)

    try:
        res: HTTPResponse = request.urlopen(req)
    except Exception as e:
        app.logger.error("Could not open url: " + str(e))

        if str(e).find("401") != -1:
            abort(401)

    if res.getcode() == 200 and urllib.parse.urlparse(url).netloc == "platform.planqk.de":
        app.logger.info("Request to platform.planqk.de was executed successfully.")

    if res.getcode() == 401:
        abort(401)

    return res.read().decode("utf-8")
