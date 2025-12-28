Ogen: Ontology-based Generative UI

## 설치

### 사전 요구사항
- Python 3.11 이상
- Node.js (pnpm 사용)
- [uv](https://github.com/astral-sh/uv) (Python 패키지 관리자)
- [pnpm](https://pnpm.io/) (Node.js 패키지 관리자)

### Python 의존성 설치
```bash
uv sync
```

### Node.js 의존성 설치
```bash
pnpm install
```

### 환경 변수 설정
```bash
# apps/server/.env 파일 생성
echo "OPENAI_API_KEY=your-api-key-here" > apps/server/.env
```

## 실행

### 전체 앱 실행 (권장)
```bash
./start.sh
```

백엔드(포트 8000)와 프론트엔드(포트 5173)가 동시에 실행됩니다.

### 개별 실행

**백엔드만 실행:**
```bash
cd apps/server
uv run uvicorn main:app --reload
```

**프론트엔드만 실행:**
```bash
cd apps/front
pnpm dev
```

## 접속 주소
- 프론트엔드: http://localhost:5173
- 백엔드 API: http://localhost:8000
