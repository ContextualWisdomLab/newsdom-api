# Skill: fix-mypy-type-narrowing-and-subprocess-strings

# Fixing Mypy Type Narrowing and Subprocess Strings

## Overview
This skill provides specific remediation patterns for common Python type-checking (`mypy`) errors encountered during development, specifically around type narrowing (`isinstance`) and `subprocess` output decoding. 

## When to Use
- You encounter `mypy` errors such as `Incompatible types in assignment (expression has type "Any | None", variable has type "int")`.
- You encounter `mypy` errors such as `Argument "stdout" to ... has incompatible type "bytes | str"; expected "str | None"`.
- You are handling `dict.get()` values that return optional or union types.
- You are handling exceptions from the `subprocess` module like `TimeoutExpired` or `CalledProcessError`.

## Patterns

### Pattern 1: Type Narrowing for `dict.get()`
When retrieving a value from a generic dictionary (`dict[str, Any]`), `dict.get()` returns `Any | None`. If you try to assign this directly to a strongly typed variable or use it as a dictionary key for a strictly typed dictionary (like `dict[int, ...]`), `mypy` will complain.

**Symptom:**
```python
src/newsdom_api/dom_builder.py:225: error: Incompatible types in assignment (expression has type "Any | None", variable has type "int") [assignment]
```

**Anti-Pattern:**
```python
page_idx = block.get("page_idx")
# Reusing `page_idx` implicitly makes mypy confused about its type in later scopes
normalized_page_idx = page_idx if isinstance(page_idx, int) else 0
blocks_by_page_idx.setdefault(normalized_page_idx, []).append(block)
```

**Remediation:**
Use a separate variable name for the raw value, and explicitly narrow its type using `isinstance()`. This prevents scope pollution of variables and ensures mypy properly infers the type.

```python
raw_page_idx = block.get("page_idx")
normalized_page_idx: int = raw_page_idx if isinstance(raw_page_idx, int) else 0
blocks_by_page_idx.setdefault(normalized_page_idx, []).append(block)
```

### Pattern 2: Subprocess Output Decoding
The `subprocess.run` command can return stdout/stderr as either `bytes` or `str` depending on whether `text=True` (or `universal_newlines=True`) was passed. However, the exception classes `subprocess.TimeoutExpired` and `subprocess.CalledProcessError` define their `stdout` and `stderr` attributes as `bytes | str | None` in the standard library stubs. If you pass these attributes to a function or exception that expects `str | None`, mypy will fail.

**Symptom:**
```python
src/newsdom_api/mineru_runner.py:74: error: Argument "stdout" to "MineruRuntimeUnavailableError" has incompatible type "bytes | str"; expected "str | None" [arg-type]
```

**Anti-Pattern:**
```python
except subprocess.TimeoutExpired as exc:
    raise MineruRuntimeUnavailableError(
        stdout=exc.stdout if exc.stdout else "",
    ) from exc
```

**Remediation:**
Explicitly decode the value if it is `bytes`, otherwise use it as `str`. This guarantees a string is passed downstream and satisfies mypy's type checker.

```python
except subprocess.TimeoutExpired as exc:
    stdout_str = exc.stdout.decode("utf-8", "replace") if isinstance(exc.stdout, bytes) else exc.stdout
    raise MineruRuntimeUnavailableError(
        stdout=stdout_str or "",
    ) from exc
```

## Checklist
- [ ] If dealing with `mypy` errors involving `Any | None`, did you introduce a temporary variable and an `isinstance` check?
- [ ] If dealing with `subprocess` output, did you explicitly check `isinstance(exc.stdout, bytes)` and decode it?
- [ ] Did you run `uvx mypy` to confirm the error is fully resolved?
- [ ] Did you run `pytest` to ensure your explicit type conversions did not break runtime logic?