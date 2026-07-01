# NewsDOM API 개요 및 아키텍처

[![OpenSSF Scorecard](https://api.securityscorecards.dev/projects/github.com/Seongho-Bae/newsdom-api/badge)](https://securityscorecards.dev/viewer/?uri=github.com/Seongho-Bae/newsdom-api)

**NewsDOM API**는 스캔된 일본어 신문 PDF 문서를 분석하여, 웹 브라우저의 DOM(Document Object Model)과 유사한 기사(Article) 단위의 트리 구조로 파싱해주는 API 서비스입니다.

과거의 신문 이미지는 단순 텍스트 추출(OCR)만으로는 다단 레이아웃이나 이미지/캡션, 기사별 흐름을 파악하기 매우 어렵습니다. 본 프로젝트는 딥러닝 기반 레이아웃 분석 도구인 **MinerU**를 백엔드로 사용하여 이 문제를 해결합니다.

---

## ⚙️ 시스템 내부 아키텍처 (Under the Hood)

사용자가 API를 통해 PDF 파일을 업로드하면, NewsDOM 내부에서는 다음의 세 단계를 거쳐 데이터를 처리합니다:

### 1. 서비스 래퍼 레이어 (`src/newsdom_api/service.py`)
FastAPI 엔드포인트(`/parse`)가 `UploadFile`로 전달받은 바이너리 데이터를 임시 디렉토리(Temporary Directory)에 저장한 후, 파이프라인 러너를 호출합니다.

### 2. MinerU 파이프라인 러너 (`src/newsdom_api/mineru_runner.py`)
저장된 PDF를 대상으로 Python `subprocess` 모듈을 이용해 **MinerU CLI**를 백그라운드에서 실행합니다. 실제 내부적으로 실행되는 명령어는 다음과 같습니다:

```bash
mineru -p <업로드된_PDF> -o <임시출력경로> -b pipeline -m ocr -l japan
```
> *참고: 일본어 신문 처리에 최적화하기 위해 `-l japan` (Language: Japanese) 옵션과 OCR 파이프라인 모드가 하드코딩되어 있습니다.*

명령어 실행이 완료되면 러너는 생성된 출력 폴더(OCR 하위 폴더)를 뒤져 `*_content_list.json` 파일과 `*_model.json` 결과물을 메모리로 로드합니다.

### 3. DOM 빌더 (`src/newsdom_api/dom_builder.py`)
MinerU가 뱉어낸 선형적인(Linear) 블록 리스트(`content_list.json`)를 순회하면서 논리적인 트리 형태의 **`ParseResponse` (Canonical JSON)**로 재구성합니다.
- `role == "header"` 이면 상단 머릿말로(`PageNode.headers`) 분류
- `type == "ad"` 또는 `role == "ad"` 이면 지면 광고(`PageNode.ads`)로 분류
- `text_level == 1` 이거나 `role == "section_headings"`인 경우 새로운 기사의 시작(Headline)으로 인식하여 새 `ArticleNode`를 생성
- 이후 등장하는 일반 텍스트는 해당 기사의 `body_blocks` 배열에 추가
- `type == "image"` 이면 `ImageNode`를 생성하고 포함된 캡션 배열을 파싱하여 기사에 종속시킴

이러한 세밀한 내부 변환 과정을 통해 단순한 OCR 텍스트 덤프가 아닌, 프론트엔드에서 즉시 렌더링이 가능한 **구조화된 DOM 데이터**가 최종 반환됩니다.

---

👉 **[설치 가이드](installation.md)**를 읽고 직접 환경을 구성해 보세요.