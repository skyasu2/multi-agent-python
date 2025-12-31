# Pydantic v2 마이그레이션 가이드

> PlanCraft Agent의 Pydantic v1 → v2 마이그레이션 전략 및 체크리스트

## 현재 상태

| 항목 | 상태 |
|------|------|
| **Pydantic 버전** | v2.x (LangChain 0.3+ 호환) |
| **호환성 레이어** | `ensure_dict()` 패턴 적용 |
| **영향 범위** | 6개 Agent, Interrupt Types |

## ensure_dict 패턴 (핵심)

### 배경
LangChain/LangGraph의 `with_structured_output()`은 Pydantic 모델 또는 dict를 반환합니다.
Pydantic v1과 v2에서 dict 변환 방식이 다르므로, 일관된 패턴이 필요합니다.

### 구현 위치
```
graph/state.py → ensure_dict()
```

### 코드
```python
def ensure_dict(obj: Any) -> Dict[str, Any]:
    """
    Pydantic 모델 또는 dict를 항상 dict로 변환

    Pydantic v1/v2 호환성을 위한 유틸리티
    - v1: .dict() 메서드
    - v2: .model_dump() 메서드
    """
    if obj is None:
        return {}

    if isinstance(obj, dict):
        return obj

    # Pydantic v2
    if hasattr(obj, "model_dump"):
        return obj.model_dump()

    # Pydantic v1 (fallback)
    if hasattr(obj, "dict"):
        return obj.dict()

    # 기타 객체
    return dict(obj) if hasattr(obj, "__iter__") else {"value": obj}
```

### 사용 예시
```python
from graph.state import ensure_dict

# 모든 Agent에서 LLM 결과 처리
result = llm.invoke(messages)
result_dict = ensure_dict(result)  # 항상 dict 보장

return update_state(state, analysis=result_dict)
```

## Pydantic v1 vs v2 주요 차이점

| 기능 | Pydantic v1 | Pydantic v2 |
|------|-------------|-------------|
| Dict 변환 | `.dict()` | `.model_dump()` |
| JSON 변환 | `.json()` | `.model_dump_json()` |
| Schema | `.schema()` | `.model_json_schema()` |
| Validation | `@validator` | `@field_validator` |
| Config | `class Config:` | `model_config = ConfigDict()` |

## 마이그레이션 체크리스트

### Phase 1: 호환성 레이어 (현재 완료)
- [x] `ensure_dict()` 유틸리티 생성
- [x] 모든 Agent에 `ensure_dict()` 적용
- [x] CI에서 Pydantic 버전 체크 추가

### Phase 2: 코드 정리 (선택적)
- [ ] `.dict()` 호출을 `.model_dump()`로 교체
- [ ] `@validator`를 `@field_validator`로 교체
- [ ] `class Config:`를 `model_config`로 교체

### Phase 3: 타입 강화 (선택적)
- [ ] `TypedDict` → Pydantic `BaseModel` 전환 검토
- [ ] Strict mode 활성화 검토

## 영향받는 파일

### 필수 수정 완료
| 파일 | ensure_dict 적용 |
|------|-----------------|
| `agents/analyzer_agent.py` | O |
| `agents/structurer_agent.py` | O |
| `agents/writer_agent.py` | O |
| `agents/reviewer_agent.py` | O |
| `agents/refiner_agent.py` | O |
| `agents/formatter_agent.py` | O |
| `graph/subgraphs.py` | O |

### Interrupt Types (Pydantic 모델)
```
graph/interrupt_types.py
```

InterruptPayload 클래스들은 이미 Pydantic v2 호환:
```python
from pydantic import BaseModel, Field

class InterruptPayload(BaseModel):
    interrupt_type: str
    message: str
    # ...

    model_config = {"extra": "allow"}  # v2 스타일
```

## CI 버전 체크

`.github/workflows/ci.yml`에서 자동 검증:

```yaml
- name: Check dependency versions
  run: |
    python -c "
    RECOMMENDED_VERSIONS = {
        'pydantic': ('2.0.0', '3.0.0'),  # v2.x 권장
    }
    # 버전 검증 로직...
    "
```

## 트러블슈팅

### 문제: AttributeError: 'dict' object has no attribute 'model_dump'

**원인**: 이미 dict인 객체에 `.model_dump()` 호출

**해결**: `ensure_dict()` 사용
```python
# Bad
result = llm.invoke(messages)
data = result.model_dump()  # dict일 경우 에러

# Good
result = llm.invoke(messages)
data = ensure_dict(result)  # 항상 안전
```

### 문제: ValidationError in Pydantic v2

**원인**: v2의 엄격한 타입 검증

**해결**: `model_config`에서 완화
```python
class MyModel(BaseModel):
    model_config = ConfigDict(
        strict=False,  # 타입 강제 변환 허용
        extra="allow"  # 추가 필드 허용
    )
```

## 버전 호환성 매트릭스

| Python | Pydantic | LangChain | LangGraph | 상태 |
|--------|----------|-----------|-----------|------|
| 3.10 | 2.0-2.9 | 0.3.x | 0.2.x | 테스트됨 |
| 3.11 | 2.0-2.9 | 0.3.x | 0.2.x | 권장 |
| 3.12 | 2.0-2.9 | 0.3.x | 0.2.x | 테스트됨 |

## 참고 자료

- [Pydantic v2 Migration Guide](https://docs.pydantic.dev/latest/migration/)
- [LangChain Pydantic Compatibility](https://python.langchain.com/docs/guides/pydantic_compatibility)
- [PlanCraft ensure_dict 구현](../graph/state.py)

---

**Last Updated**: 2025-12-31
