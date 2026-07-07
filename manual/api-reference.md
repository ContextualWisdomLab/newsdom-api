# 사용 방법 및 API 레퍼런스

FastAPI 서버를 실행하고, 스캔된 신문 PDF를 업로드하여 기사 DOM 트리 형태의 Canonical JSON 데이터를 파싱하는 방법을 안내합니다.

## 1. 서버 실행하기

가상환경을 활성화한 상태에서, `uv run uvicorn`으로 API 서버(`src/newsdom_api/main.py`)를 구동합니다.

```bash
# 개발 시 핫-리로딩(--reload) 모드 사용
uv run uvicorn --app-dir src newsdom_api.main:app --reload
```

## 2. 인터랙티브 웹 UI

FastAPI는 OpenAPI 기반의 대화형 API 문서를 자동으로 생성합니다.
웹 브라우저를 열고 다음 주소에 접속하면 시각적인 환경에서 바로 API를 테스트할 수 있습니다.

- **Swagger UI**: `http://127.0.0.1:8000/docs`
- **ReDoc**: `http://127.0.0.1:8000/redoc`

해당 페이지에서 **`/parse`** 버튼을 클릭한 후, `Try it out` 기능을 통해 파일을 직접 첨부하고 결과물을 테스트해 볼 수 있습니다.

---

## 3. API 엔드포인트 세부 설명

### `POST /parse`

스캔된 일본어 신문 PDF 문서를 업로드 받아, 요청별 임시 디렉토리에 저장한 뒤 `mineru` 파이프라인을 실행하고 변환 결과를 기사 단위 DOM 구조가 담긴 JSON 형태로 반환합니다. 업로드된 PDF와 MinerU 산출물은 응답 후 정리됩니다.

#### 요청 매개변수 (Request Body)
- **`file`** (`UploadFile`, 필수): 변환할 PDF 바이너리 파일 데이터 (`multipart/form-data`)

#### cURL 테스트 예제

```bash
# 로컬 테스트 (sample.pdf를 /parse 엔드포인트로 전송)
curl -X 'POST' \
  'http://127.0.0.1:8000/parse' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=@sample.pdf;type=application/pdf'
```

#### Python 클라이언트 예제 (requests)

프론트엔드나 타 백엔드 서버에서 NewsDOM API를 호출하는 일반적인 패턴입니다.

```python
import requests

url = "http://127.0.0.1:8000/parse"
file_path = "sample_newspaper.pdf"

with open(file_path, "rb") as f:
    files = {"file": ("sample_newspaper.pdf", f, "application/pdf")}
    response = requests.post(url, files=files)

if response.status_code == 200:
    dom_json = response.json()
    print(f"문서 ID: {dom_json['document_id']}")
    # 첫 번째 페이지의 첫 기사 제목 출력
    print(f"헤드라인: {dom_json['pages'][0]['articles'][0]['headline']}")
else:
    print(f"에러 발생: {response.status_code}, {response.text}")
```

#### 실패 응답 계약

- `503 Service Unavailable`: `MinerU runtime unavailable`
  - `mineru` 실행 파일을 찾을 수 없거나 실행 자체가 실패했을 때 반환됩니다.
- `502 Bad Gateway`: `MinerU output was incomplete`
  - MinerU 프로세스는 종료되었지만 필수 JSON 산출물이 없거나 불완전할 때 반환됩니다.

서버는 내부 `stdout`/`stderr`를 그대로 노출하지 않고 위의 고정된 상세 메시지로만 `/parse` 실패를 응답합니다.

---

### 응답(Response) JSON 스키마 (`src/newsdom_api/schemas.py`)

파싱 성공 시 반환되는 DOM 형태의 `ParseResponse` 객체 구조입니다.

```json
{
  "document_id": "string (고유 문서 식별자)",
  "pages": [
    {
      "page_number": 1,
      "width": 800.5,
      "height": 1200.0,
      "articles": [
        {
          "article_id": "article-1",
          "headline": "신문 헤드라인 제목 (text_level=1 또는 role=section_headings 기반)",
          "bbox": {
            "x0": 10.0, "y0": 20.0, "x1": 400.0, "y1": 150.0
          },
          "body_blocks": [
            "첫 번째 단락의 본문입니다.",
            "두 번째 단락이 이어집니다."
          ],
          "images": [
            {
              "path": "extracted_images/page1_img1.jpg",
              "bbox": {
                "x0": 120.0,
                "y0": 320.0,
                "x1": 420.0,
                "y1": 560.0
              },
              "captions": [
                {
                  "text": "사진 캡션 내용입니다. (image_caption 블록 연결)",
                  "bbox": {
                    "x0": 120.0,
                    "y0": 565.0,
                    "x1": 420.0,
                    "y1": 620.0
                  }
                }
              ]
            }
          ],
          "captions": []
        }
      ],
      "ads": [
        "광고 문구 또는 배너 텍스트 (type=ad 또는 role=ad)"
      ],
      "headers": [
        "2026년 4월 9일 목요일 조간 (role=header)"
      ]
    }
  ],
  "quality": {
    "status": "success",
    "parser": "mineru",
    "warnings": [
      "Page 1: 일부 레이아웃이 겹침"
    ]
  }
}
```

#### 스키마 주요 노드 설명
1. **`BoundingBox` (`bbox`)**: 요소가 위치한 직사각형 영역 `(x0, y0, x1, y1)`. 신문 지면 상에서의 절대적 물리 좌표를 나타냅니다.
2. **`PageNode`**: 단일 신문 지면입니다. 여러 개의 기사(`articles`)와 광고(`ads`), 상단 헤더 정보(`headers`)를 포함합니다.
3. **`ArticleNode`**: 가장 핵심적인 DOM 요소로, 제목(`headline`), 문단 블록 배열(`body_blocks`), 기사에 속한 이미지 목록(`images`), 기사 내 독립된 사진 설명(`captions`)으로 구성됩니다.
4. **`ParseQuality`**: 변환 결과를 검증하기 위한 상태, 사용된 파서 엔진 정보(`mineru`), 주의해야할 품질 문제(`warnings`) 등의 메타데이터를 갖습니다.

---

### `GET /health`

API 서버의 작동 여부를 검사하는 경량 상태 체크 엔드포인트입니다. 로드밸런서나 컨테이너/오케스트레이션 프로브에서 프로세스 응답 여부를 확인할 때 사용합니다. 이 응답은 애플리케이션이 요청을 받고 있음을 보여주지만, MinerU 기반 `/parse` 전체 경로를 보증하지는 않습니다.

#### 요청 / 응답

```bash
curl http://127.0.0.1:8000/health
```

```json
{
  "status": "ok"
}
```
