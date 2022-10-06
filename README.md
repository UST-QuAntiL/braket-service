# braket-service

This service takes a Braket implementation as data or via an URL and returns either compiled circuit properties and the transpiled Quil String (Transpilation Request) or its results (Execution Request) depending on the input data and selected backend.


[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

## Setup
* Clone repository:
```
git clone https://github.com/KuhnMn/braket-service.git
```

* Start containers:
```
docker-compose pull
docker-compose up
```

Now the braket-service is available on http://localhost:5018/.

## After implementation changes
* Update container:
```
docker build -t kuhnmx/braket-service:latest
docker push kuhnmx/braket-service:latest
```

* Start containers:
```
docker-compose pull
docker-compose up
```

## Transpilation Request
Send implementation and QPU information to the API to get properties of the transpiled circuit and the transpiled Braket-JSON circuit itself.
*Note*: Currently, the Braket package is used for local simulation. Thus, no real backends are accessible.
Inputs are currently also not supported.

`POST /braket-service/api/v1.0/transpile`

#### Transpilation via data
```
{  
    "impl-data": "BASE64-ENCODED-IMPLEMENTATION",
    "impl-language": "Braket",
    "qpu-name": "NAME-OF-QPU",
    "input-params": {
    }
}
```

## Execution Request
Send implementation, input, and QPU information to the API to execute your circuit and get the result.
*Note*: Currently, the Braket package is used for local simulation. Thus, no real backends are accessible.
Inputs are currently also not supported.

`POST /braket-service/api/v1.0/execute`  


#### Execution via URL
```
{  
    "impl-url": "URL-OF-IMPLEMENTATION",,
    "impl-language": "Braket/Braket-IR",
    "qpu-name": "NAME-OF-QPU",
    "input-params": {
        "PARAM-NAME-1": {
                "rawValue": "YOUR-VALUE-1",
                "type": "Integer"
            },
            "PARAM-NAME-2": {
                "rawValue": "YOUR-VALUE-2",
                "type": "String"
            },
            ...
    }
}
```

#### Execution via data
```
{  
    "impl-data": "BASE64-ENCODED-IMPLEMENTATION",
    "impl-language": "Braket/Braket-IR",
    "qpu-name": "NAME-OF-QPU",
    "input-params": {
     "PARAM-NAME-1": {
                "rawValue": "YOUR-VALUE-1",
                "type": "Integer"
            },
            "PARAM-NAME-2": {
                "rawValue": "YOUR-VALUE-2",
                "type": "String"
            },
            ...
    }
}
```
#### Execution via Braket-IR String
Note that the IRs JSON has to be sent in form of a single string.
```
{  
    "braket_ir": "BRAKET-IR-STRING",
    "qpu-name": "NAME-OF-QPU"
}
```

Returns a content location for the result. Access it via `GET`.

## Sample Implementations for Transpilation and Execution
Sample implementations can be found [here](https://github.com/UST-QuAntiL/nisq-analyzer-content/tree/master/compiler-selection/Shor) and under the folder 'Sample Implementations'.
Please use the raw GitHub URL as `impl-url` value (see [example](https://raw.githubusercontent.com/UST-QuAntiL/nisq-analyzer-content/master/compiler-selection/Shor/shor-fix-15-quil.quil)).

## Haftungsausschluss

Dies ist ein Forschungsprototyp.
Die Haftung für entgangenen Gewinn, Produktionsausfall, Betriebsunterbrechung, entgangene Nutzungen, Verlust von Daten und Informationen, Finanzierungsaufwendungen sowie sonstige Vermögens- und Folgeschäden ist, außer in Fällen von grober Fahrlässigkeit, Vorsatz und Personenschäden, ausgeschlossen.

## Disclaimer of Warranty

Unless required by applicable law or agreed to in writing, Licensor provides the Work (and each Contributor provides its Contributions) on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied, including, without limitation, any warranties or conditions of TITLE, NON-INFRINGEMENT, MERCHANTABILITY, or FITNESS FOR A PARTICULAR PURPOSE.
You are solely responsible for determining the appropriateness of using or redistributing the Work and assume any risks associated with Your exercise of permissions under this License.
