# OpenAPI multipart form examples

## Decision

NewsDOM publishes the optional `/parse` form fields with FastAPI's plural
`examples` parameter:

```python
Form(examples=["ch"])
Form(examples=["auto"])
```

The generated Schema Objects must contain `examples: ["ch"]` and
`examples: ["auto"]` and must not contain the legacy singular `example`
field. The required PDF upload remains a binary string schema and does not
publish a filename example.

## Buyer outcome

An API consumer opening Swagger UI or reading `/openapi.json` can identify one
valid language family and one valid parsing mode without guessing values or
consulting source code. Defaults and examples intentionally agree so the first
request is representative of actual runtime behavior.

## Standards and framework basis

FastAPI currently emits OpenAPI 3.1.0. Its request-parameter reference defines
`examples` as a list of field examples and marks singular `example` as
deprecated for OpenAPI 3.1 / JSON Schema 2020-12. OpenAPI 3.1.1 likewise
identifies the Schema Object's plural JSON Schema `examples` array as the
preferred form and retains singular `example` only for compatibility.

OpenAPI 3.2.0, published on September 19, 2025, is the latest published OAS at
the time of this decision. NewsDOM does not claim to emit 3.2.0: changing the
framework-generated dialect is a separate compatibility project. This slice
uses the non-deprecated metadata form supported by both the current runtime
and the newer standard.

JSON Schema Draft 2020-12 defines `examples` as a metadata annotation whose
value is an array and recommends that its values validate against the
associated schema.

## File-upload boundary

A browser cannot pre-populate a user's local file picker from an OpenAPI string
example. Publishing `document.pdf` as though it were an executable upload would
misrepresent browser behavior. The contract therefore verifies only that the
file property remains required and is represented as either the current
`format: binary` form or the JSON Schema content-media representation used by a
future compatible FastAPI release.

## Verification contract

`tests/test_openapi_contract.py` resolves the multipart request body's local
JSON Pointer and verifies:

- the document reports an OpenAPI 3.1 patch version;
- the request body and `file` property remain required;
- the upload is a binary string under an accepted 3.1 representation;
- `language` and `mode` defaults remain `ch` and `auto`;
- plural example arrays contain exactly those values;
- deprecated singular example metadata is absent.

This is generated-contract evidence. It does not by itself prove how every
third-party documentation renderer chooses to display JSON Schema annotations;
representative rendered Swagger UI checks remain release evidence.

## References

FastAPI. (n.d.). *Request parameters*. Retrieved August 16, 2026, from
https://fastapi.tiangolo.com/reference/parameters/

JSON Schema. (2022). *JSON Schema validation: A vocabulary for structural
validation of JSON (Draft 2020-12)*.
https://json-schema.org/draft/2020-12/json-schema-validation

OpenAPI Initiative. (n.d.). *OpenAPI specification (Version 3.1.1)*. Retrieved
August 16, 2026, from https://spec.openapis.org/oas/v3.1.1.html

OpenAPI Initiative. (2025, September 19). *OpenAPI specification (Version
3.2.0)*. https://spec.openapis.org/oas/v3.2.0.html
