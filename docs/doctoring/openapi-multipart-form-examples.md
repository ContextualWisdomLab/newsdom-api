# OpenAPI multipart form examples

## Scope

This note records the standards boundary for the `/parse` endpoint's `language` and `mode` examples.

NewsDOM uses FastAPI's generated OpenAPI 3.1 document as its primary developer-facing interface. The examples are documentation annotations only: they do not change the runtime defaults, validation, authentication, accepted MinerU aliases, or multipart serialization.

## Decision

The form declarations use the plural `examples` metadata:

```python
Form(description="...", examples=["ch"])
Form(description="...", examples=["auto"])
```

OpenAPI 3.1 Schema Objects align with JSON Schema Draft 2020-12. The OpenAPI specification retains the singular Schema Object `example` field for compatibility but deprecates it in favor of the JSON Schema `examples` keyword. FastAPI's current documentation likewise recommends plural examples for OpenAPI 3.1 output.

The regression test follows the `/parse` multipart request body's local `$ref` and verifies the emitted component properties. Testing generated output prevents source-level metadata that is silently dropped or relocated by a framework upgrade from being treated as shipped developer experience.

## File-upload boundary

The PR does not add a synthetic filename example. Browser security prevents documentation UIs from pre-populating a user's local file picker, and a string such as `document.pdf` could imply an executable upload that Swagger UI cannot provide. The file field retains its required status, binary schema, and description.

## Compatibility and upgrade rule

A FastAPI, Pydantic, or OpenAPI-version upgrade must preserve:

- `/parse` as `multipart/form-data`;
- required binary `file` input;
- optional `language` and `mode` fields;
- `examples: ["ch"]` and `examples: ["auto"]` on the resolved property schemas;
- existing defaults and validation behavior; and
- authenticated parser semantics.

Any generated-schema movement requires an explicit test update that proves equivalent public output rather than matching a hard-coded component name.

## APA 7th references

FastAPI. (2026). *Declare request example data*. https://fastapi.tiangolo.com/tutorial/schema-extra-example/

OpenAPI Initiative. (2024). *OpenAPI specification v3.1.1*. https://spec.openapis.org/oas/v3.1.1.html
