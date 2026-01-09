# 작업 방법론 가이드

다른 AI 에이전트가 이 프로젝트에서 작업할 때 참고할 수 있는 작업 방식과 원칙을 정리합니다.

## 작업 프로세스

### 1. 요구사항 분석 및 계획 수립

**단계:**
1. 사용자 요구사항을 명확히 이해
2. 현재 코드베이스 구조 파악
3. 관련 파일들 읽기 및 분석
4. 구현 계획서 작성

**주의사항:**
- 계획서에는 구체적인 구현 방법, 파일 구조, 변경 사항을 명시
- 아키텍처 원칙을 반드시 확인하고 준수
- 라이브러리와 데모 앱의 경계를 명확히 구분

### 2. 아키텍처 검토

**검토 항목:**
- 라이브러리 코드가 `apps/`에 들어가지 않는가?
- 데모 앱은 라이브러리 함수만 호출하는가?
- 비즈니스 로직이 라이브러리에 캡슐화되어 있는가?
- 하위 호환성이 유지되는가?

**검토 방법:**
- 계획서의 각 변경 사항을 라이브러리/데모 앱으로 분류
- 점수 평가 (100점 만점)
- 문제점 발견 시 계획서 수정

### 3. 단계별 구현

**원칙:**
- Phase별로 순차 구현
- 각 Phase 완료 후 검증
- TODO 리스트 활용하여 진행 상황 관리

**구현 순서:**
1. 백엔드 라이브러리 수정 (핵심 로직)
2. 백엔드 서버 수정 (HTTP 인터페이스)
3. 프론트 라이브러리 확장
4. 프론트엔드 앱 통합

### 4. 검증 및 수정

**검증 항목:**
- 린터 에러 확인
- 타입 에러 확인
- 아키텍처 원칙 준수 여부
- 기능 동작 확인

## 아키텍처 원칙

### 라이브러리와 데모 앱의 경계

**라이브러리 (`packages/`)**
- ✅ 모든 비즈니스 로직
- ✅ 유틸리티 함수
- ✅ 핵심 기능
- ✅ 메타데이터 인터페이스 정의

**데모 앱 (`apps/`)**
- ✅ 라이브러리 import 및 호출만
- ✅ UI 표시
- ✅ 예시 데이터
- ❌ 비즈니스 로직 구현 금지
- ❌ 유틸리티 함수 구현 금지

### 설계 원칙

1. **비즈니스 로직 캡슐화**
   - 백엔드: `packages/ogen_stream/`에 모든 로직
   - 프론트: `packages/svelte/`에 모든 로직
   - 서버/앱은 라이브러리 함수 호출만

2. **점진적 개선**
   - 필수 기능부터 구현
   - 나머지는 점진적으로 추가
   - 하위 호환성 유지

3. **메타데이터 우선, 추론은 보조**
   - 메타데이터가 있으면 우선 사용
   - 없으면 기존 추론 방식 유지
   - 하위 호환성 보장

## 파일 수정 가이드

### 백엔드 라이브러리 수정 시

**위치:** `packages/ogen_stream/src/ogen_stream/`

**체크리스트:**
- [ ] 온톨로지 파일(`ogen-core.ttl`) 수정 시 모든 속성의 domain/range 확인
- [ ] 엔진 클래스 수정 시 기존 메서드 시그니처 유지 (하위 호환성)
- [ ] 새로운 메서드는 명확한 docstring 작성
- [ ] 에러 처리는 적절한 예외 타입 사용

**예시:**
```python
# ✅ 좋은 예: 명확한 파라미터, docstring, 에러 처리
def connect_user_data(self, ttl_string: str, base_iri: str = "http://myapp.com/ui/") -> dict:
    """
    초기 연동을 위한 통합 API 함수
    
    Args:
        ttl_string: TTL 형식의 지식 그래프 문자열
        base_iri: 기본 IRI (기본값 제공)
    
    Returns:
        dict: {"status": "success" | "already_connected", "node_count": int, "message": str}
    
    Raises:
        ValueError: TTL 파싱 에러 시
    """
```

### 백엔드 서버 수정 시

**위치:** `apps/server/`

**체크리스트:**
- [ ] 라이브러리 함수만 호출
- [ ] HTTP 에러 처리는 서버에서만 수행
- [ ] 비즈니스 로직은 라이브러리에 위임
- [ ] 코드는 최소화 (약 10줄 내외)

**예시:**
```python
# ✅ 좋은 예: 라이브러리 함수 호출만
@app.post("/api/connect")
async def connect_knowledge_graph(request: ConnectRequest):
    try:
        result = engine.connect_user_data(
            ttl_string=request.ttl_content,
            base_iri=request.base_iri
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 프론트 라이브러리 수정 시

**위치:** `packages/svelte/`

**체크리스트:**
- [ ] TypeScript 타입 정의 명확히
- [ ] export할 인터페이스/타입은 명시
- [ ] 하위 호환성 유지 (기존 API 변경 시 주의)
- [ ] 메타데이터 인터페이스는 라이브러리에 정의

**예시:**
```typescript
// ✅ 좋은 예: 명확한 타입, export
export interface ComponentMetadata {
    type: string;
    label: string;
    // ...
}

export function generateTTLFromDesignSystem(
    components: Record<string, any>,
    metadataMap?: Record<string, ComponentMetadata>, // 선택적 파라미터로 하위 호환성
    // ...
): string {
    // 메타데이터가 있으면 우선 사용, 없으면 추론
}
```

### 프론트엔드 앱 수정 시

**위치:** `apps/front/`

**체크리스트:**
- [ ] 라이브러리 함수만 import 및 호출
- [ ] 비즈니스 로직 구현 금지
- [ ] UI 표시만 담당
- [ ] 예시 데이터는 하드코딩 또는 라이브러리 함수 호출

**예시:**
```typescript
// ✅ 좋은 예: 라이브러리 함수 호출만
import { generateTTLFromDesignSystem } from '@ogen/svelte';
import { designSystem, designSystemMetadata } from '$lib/ds';

const userKnowledgeTTL = generateTTLFromDesignSystem(designSystem, designSystemMetadata);
```

## 코드 작성 규칙

### 1. 명확한 네이밍

- 함수명: 동사로 시작 (`connect`, `load`, `generate`)
- 변수명: 명확한 의미 (`userKnowledgeTTL`, `connectionStatus`)
- 타입명: 명확한 의미 (`ComponentMetadata`, `OgenState`)

### 2. 에러 처리

- 백엔드: 적절한 예외 타입 사용 (`ValueError`, `HTTPException`)
- 프론트: try-catch로 에러 처리, 사용자에게 명확한 메시지 표시

### 3. 주석 및 문서화

- 복잡한 로직은 주석 추가
- 함수는 docstring 작성 (Python) 또는 JSDoc (TypeScript)
- 중요한 결정 사항은 주석으로 설명

### 4. 타입 안정성

- TypeScript: 명시적 타입 정의
- Python: 타입 힌트 사용
- Optional 파라미터는 기본값 제공

## 검증 프로세스

### 구현 후 필수 검증

1. **린터 에러 확인**
   ```bash
   # 수정한 파일들에 대해 린터 실행
   read_lints(['수정한/파일/경로'])
   ```

2. **아키텍처 원칙 확인**
   - 라이브러리 코드가 `apps/`에 없는가?
   - 데모 앱이 라이브러리 함수만 호출하는가?
   - 비즈니스 로직이 라이브러리에 있는가?

3. **하위 호환성 확인**
   - 기존 코드가 여전히 작동하는가?
   - 새로운 기능은 선택적으로 사용 가능한가?

### TODO 관리

- 구현 시작 전 TODO 리스트 생성
- 각 Phase별로 TODO 항목 분리
- 완료된 항목은 즉시 업데이트
- 진행 중인 항목은 하나씩만

## 일반적인 작업 패턴

### 패턴 1: 새 기능 추가

1. 계획서 작성 (요구사항, 구현 방법, 파일 구조)
2. 아키텍처 검토 (라이브러리/데모 앱 경계 확인)
3. 라이브러리 수정 (핵심 로직)
4. 서버/앱 수정 (인터페이스만)
5. 검증 (린터, 아키텍처, 하위 호환성)

### 패턴 2: 기존 기능 확장

1. 현재 구현 파악
2. 확장 방안 계획 (하위 호환성 고려)
3. 선택적 파라미터 추가 또는 새 메서드 추가
4. 기존 코드는 그대로 유지
5. 검증

### 패턴 3: 리팩토링

1. 리팩토링 범위 명확히
2. 아키텍처 원칙 준수 확인
3. 단계별로 진행 (한 번에 너무 많이 변경하지 않음)
4. 각 단계마다 검증

## 주의사항

### 절대 하지 말아야 할 것

1. ❌ `apps/` 폴더에 비즈니스 로직 구현
2. ❌ 라이브러리 코드를 데모 앱에 복사
3. ❌ 기존 API를 깨뜨리는 변경 (하위 호환성 깨기)
4. ❌ 타입 없이 코드 작성
5. ❌ 에러 처리 없이 코드 작성

### 반드시 해야 할 것

1. ✅ 계획서 작성 및 검토
2. ✅ 아키텍처 원칙 확인
3. ✅ 라이브러리/데모 앱 경계 명확히
4. ✅ 하위 호환성 유지
5. ✅ 린터 에러 확인 및 수정
6. ✅ TODO 리스트 관리

## 예시: 실제 작업 흐름

### 예시 1: 새 API 엔드포인트 추가

```
1. 요구사항: "상태 확인 API 추가"
2. 계획서 작성:
   - 라이브러리에 `get_status()` 메서드 추가
   - 서버에 `GET /api/status` 엔드포인트 추가
3. 아키텍처 검토:
   - ✅ 로직은 라이브러리에
   - ✅ 서버는 HTTP 인터페이스만
4. 구현:
   - packages/ogen_stream/engine.py에 get_status() 추가
   - apps/server/main.py에 엔드포인트 추가
5. 검증:
   - 린터 에러 확인
   - 아키텍처 원칙 확인
```

### 예시 2: 메타데이터 추가

```
1. 요구사항: "새 컴포넌트 메타데이터 추가"
2. 계획서 작성:
   - ds.ts에 새 컴포넌트 메타데이터 추가
   - TTL 생성기는 자동으로 처리
3. 아키텍처 검토:
   - ✅ 메타데이터는 데모 앱에 (예시 데이터)
   - ✅ TTL 생성 로직은 라이브러리에
4. 구현:
   - apps/front/src/lib/ds.ts에 메타데이터 추가
5. 검증:
   - TTL 생성 테스트
   - 린터 에러 확인
```

## 요약

### 작업 순서
1. 계획서 작성 → 2. 아키텍처 검토 → 3. 구현 → 4. 검증

### 핵심 원칙
- 라이브러리와 데모 앱의 명확한 경계
- 비즈니스 로직은 라이브러리에
- 하위 호환성 유지
- 점진적 개선

### 검증 필수
- 린터 에러
- 아키텍처 원칙
- 하위 호환성

이 방법론을 따르면 일관성 있고 유지보수 가능한 코드를 작성할 수 있습니다.



