from newsdom_api.dom_builder import _coerce_page_number

print(_coerce_page_number([1, 2, 3]))
try:
    int([1, 2, 3])
except Exception as e:
    print(f"Exception type: {type(e)}")
