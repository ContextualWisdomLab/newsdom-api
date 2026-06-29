## 2025-02-14 - Fix Insecure File Upload via Missing Magic Byte Check
**Vulnerability:** The `/parse` endpoint verified file types exclusively using the `Content-Type` header, omitting payload inspection. This allowed bypassing checks by supplying malicious payloads with an `application/pdf` header.
**Learning:** Checking headers is insufficient; APIs consuming binary data must validate content via magic bytes (e.g., `b"%PDF-"`) and structural parsing before processing.
**Prevention:** Always inspect magic bytes for binary upload endpoints and reject structurally invalid payloads before handing data to downstream parsers.

## 2024-06-25 - Prevent DoS from unbounded file read
**Vulnerability:** The `/parse` API reads the entire uploaded PDF into memory using `await file.read()`. If an attacker uploads a massive file, it can cause an Out-Of-Memory (OOM) error, leading to Denial of Service (DoS).
**Learning:** FastAPI `UploadFile.read()` loads the entire file into memory unless limited. Even if it's spooled to disk by FastAPI initially, calling `.read()` buffers it fully into memory. Since this goes to MinerU which might process it for a while, large files cause severe memory exhaustion.
**Prevention:** Implement an application-level file size limit during the upload read process using `file.size`.

## 2025-02-14 - 500 내부 에러 시 보안 헤더 누락 및 스택 트레이스 노출 방지
**Vulnerability:** 요청 처리 중 처리되지 않은 예외(Unhandled exceptions)가 발생할 경우 FastAPI의 기본 예외 처리기로 넘어가면서, 사용자 정의 보안 헤더 미들웨어가 우회되어 500 내부 서버 에러 응답에 필수 보안 헤더(`X-Content-Type-Options`, `X-Frame-Options`, `Content-Security-Policy` 등)가 누락되는 취약점이 있었습니다.
**Learning:** `await call_next(request)`를 호출한 후 응답을 수정하는 미들웨어 함수는 오류 응답에도 헤더가 반드시 주입되도록 예외를 명시적으로 처리해야 합니다. 그렇지 않으면 FastAPI의 기본 예외 처리기가 미들웨어의 반환 경로를 우회할 수 있습니다. 동시에 관찰 가능성(observability)을 위해 예외를 삼키지 않고 로깅해야 합니다.
**Prevention:** 보안이 중요한 미들웨어 내에서 `call_next`를 `try...except Exception` 블록으로 감싸서 처리되지 않은 에러를 잡고, `logging.exception()`을 호출해 오류를 기록한 후, 스택 트레이스 유출을 방지하는 안전한 제네릭 에러 응답 객체(JSONResponse)를 명시적으로 생성하여 보안 헤더를 주입한 뒤 반환하도록 합니다.
