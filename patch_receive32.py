import fastapi
import newsdom_api.main as main_mod

from starlette.datastructures import UploadFile

def custom_getattr(obj, name, default=None):
    if name == "size" and isinstance(obj, UploadFile):
        return 100
    try:
        return getattr(obj, name)
    except AttributeError:
        if default is not None:
            return default
        raise

import builtins
print(isinstance(UploadFile(filename="t", file=None), UploadFile))
