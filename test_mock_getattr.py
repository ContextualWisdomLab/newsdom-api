from fastapi import UploadFile
import io
import builtins
import time

original_getattr = getattr

def custom_getattr(obj, name, default=None):
    if name == "size" and isinstance(obj, UploadFile):
        return 1000
    try:
        return original_getattr(obj, name)
    except AttributeError:
        if default is not None:
            return default
        raise

builtins.getattr = custom_getattr

u = UploadFile(filename="test", file=io.BytesIO(b"abc"))
print(getattr(u, "size"))
print(getattr(u, "filename"))
