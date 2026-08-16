# PageNode OpenAPI example contract

## Decision

The optional page-geometry and repeated text-block fields in `PageNode` publish
examples through Pydantic's plural `Field(examples=[...])` metadata.

Scalar fields use scalar example values:

```python
width: float | None = Field(default=None, examples=[595.28])
height: float | None = Field(default=None, examples=[841.89])
```

List-valued fields use arrays as the individual example values, so the metadata
array is intentionally nested:

```python
headers: list[str] = Field(
    default_factory=list,
    examples=[["Quarterly report", "2026 Q2"]],
)
```

The generated Schema Object must expose `examples`, not the legacy singular
`example` property. Every first example must also be accepted by the actual
Pydantic field contract.

## Buyer outcome

API consumers can inspect the generated response schema and immediately see:

- the coordinate scale used by a realistic PDF page;
- that advertisements, headers, footers, and visible page numbers are arrays of
  strings rather than one concatenated string; and
- representative multi-value output without consulting source code.

The examples deliberately use domain-neutral report language rather than the
newspaper-specific wording retained by older generated branches.

## Standards and framework basis

Pydantic v2 identifies `examples` as a field-level JSON Schema customization
parameter. Its official example shows `Field(examples=[...])` producing the
plural JSON Schema `examples` array.

JSON Schema Draft 2020-12 defines `examples` as annotation metadata whose value
is an array. Each example should be a value valid under the associated schema;
therefore an example for `list[str]` is itself an array, while an example for a
numeric field is a number.

NewsDOM currently emits OpenAPI 3.1 through FastAPI. OpenAPI 3.1 aligns its
Schema Object with JSON Schema 2020-12 and retains the singular `example`
property only for compatibility. The latest published OpenAPI 3.2 specification
continues to use JSON Schema vocabulary, but changing NewsDOM's emitted dialect
is a separate framework-compatibility project.

## Verification contract

`tests/test_pagenode_openapi_schema.py` obtains `PageNode.model_json_schema()`
and proves for each affected field that:

- the exact plural example array is present;
- singular `example` metadata is absent; and
- the first example is accepted by an actual `PageNode` instance.

This test verifies generated schema and runtime type compatibility. It does not
claim that every OpenAPI renderer displays annotation metadata identically.
Representative Swagger UI rendering remains separate release evidence.

## Change boundary

This documentation-only response-contract enhancement does not change PDF
parsing, response serialization, authentication, upload handling, MinerU
execution, database objects, dependencies, or lockfiles. Examples are annotations
and do not become runtime defaults.

## References

JSON Schema. (2022). *JSON Schema validation: A vocabulary for structural
validation of JSON (Draft 2020-12)*.
https://json-schema.org/draft/2020-12/json-schema-validation

OpenAPI Initiative. (n.d.). *OpenAPI specification (Version 3.1.1)*. Retrieved
August 16, 2026, from https://spec.openapis.org/oas/v3.1.1.html

OpenAPI Initiative. (2025, September 19). *OpenAPI specification (Version
3.2.0)*. https://spec.openapis.org/oas/v3.2.0.html

Pydantic Services Inc. (n.d.). *JSON schema: Field-level customization*.
Retrieved August 16, 2026, from
https://docs.pydantic.dev/latest/concepts/json_schema/
