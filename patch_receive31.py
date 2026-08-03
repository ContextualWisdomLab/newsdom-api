from fastapi import UploadFile
import io
u = UploadFile(filename="test.txt", file=io.BytesIO(b"abc"))
print(getattr(u, "size", None))
