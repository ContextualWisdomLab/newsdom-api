with open('src/newsdom_api/dom_builder.py', 'r') as f:
    content = f.read()

new_func = '''def _html_safe_text(value: Any) -> str:
    """Normalize OCR text for safe downstream HTML rendering."""
    if not value:
        return ""
    # ⚡ Bolt: Fast path for str to avoid expensive str() cast
    text = value if type(value) is str else str(value)
    text = text.strip()
    if not text:
        return ""
    # ⚡ Bolt: Explicit 'in' checks are faster than regex allocation and overhead
    if (
        "&" not in text
        and "<" not in text
        and ">" not in text
        and '"' not in text
        and "'" not in text
    ):
        return text
    return html_escape(text)'''

old_func = '''def _html_safe_text(value: Any) -> str:
    """Normalize OCR text for safe downstream HTML rendering."""
    if not value:
        return ""
    # ⚡ Bolt: Fast path for str to avoid expensive str() cast
    text = value if type(value) is str else str(value)
    text = text.strip()
    # ⚡ Bolt: Explicit 'in' checks are faster than regex allocation and overhead
    if (
        "&" not in text
        and "<" not in text
        and ">" not in text
        and '"' not in text
        and "'" not in text
    ):
        return text
    return html_escape(text)'''

content = content.replace(old_func, new_func)

new_coerce_bbox = '''def _coerce_bbox_coordinate(value: Any) -> float | None:
    """Convert a bounded, finite bounding-box coordinate into a float."""

    v_type = type(value)
    if v_type is float:
        pass
    elif v_type is bool or value is None:
        return None
    else:
        try:
            value = float(value)
        except (TypeError, ValueError, OverflowError):
            return None

    if not isfinite(value) or value < 0 or value > MAX_BBOX_COORDINATE:
        return None

    return value'''

old_coerce_bbox = '''def _coerce_bbox_coordinate(value: Any) -> float | None:
    """Convert a bounded, finite bounding-box coordinate into a float."""

    if type(value) is bool:
        return None

    try:
        coordinate = value if type(value) is float else float(value)
    except (TypeError, ValueError, OverflowError):
        return None

    if not isfinite(coordinate):
        return None

    if coordinate < 0 or coordinate > MAX_BBOX_COORDINATE:
        return None

    return coordinate'''

content = content.replace(old_coerce_bbox, new_coerce_bbox)


with open('src/newsdom_api/dom_builder.py', 'w') as f:
    f.write(content)
