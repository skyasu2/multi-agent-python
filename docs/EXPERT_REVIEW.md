# Expert Code Review & Improvement Plan

본 문서는 전문가 코드 리뷰(2025-12-28) 결과를 바탕으로 PlanCraft Agent의 아키텍처 강점을 정리하고, 향후 구체적인 개선 로드맵을 정의합니다.

## 1. 아키텍처 강점 (Strengths)

### ✅ 완성도 높은 백엔드 설계
*   **SRP & Modularity**: LangGraph의 노드/엣지/조건 분기를 활용하여 각 에이전트(Analyzer, Structurer 등)의 역할을 명확히 분리.
*   **Immutable State Management**: Pydantic 모델과 `model_copy(update=...)` 패턴을 사용하여 상태 변이의 추적성과 안전성 보장.
*   **Robust Error Handling**: Structured Output 자동 매핑 및 실패 시 Fallback 로직, Cross-field Validation 적용.
*   **Observability**: LangSmith 연동 및 단계별 파일 로깅 시스템 구축으로 디버깅 및 트레이싱 용이.
*   **Advanced Features**: Sub-graph 패턴, RAG/Web Search 분리, Human-in-the-loop 준비 등 엔터프라이즈급 확장성 확보.

---

## 2. 개선 로드맵 (Improvement Roadmap)

### Phase 1: Frontend-Backend Sync (현재 진행 중)
프론트엔드와 백엔드 간의 상태 동기화 및 가시성 확보에 집중합니다.
- [x] **Dev Tools Visualization**: `app.py` 내 LangGraph 워크플로우 시각화 (Mermaid).
- [x] **Smart UI Components**: 진행 상태(Status Callback), 결과 메트릭(Tooltip), Metric 가독성 개선.
- [ ] **State Inspector**: 현재 State JSON 및 히스토리를 UI에서 직접 조회.

### Phase 2: Advanced Interaction & Automation (단기 목표)
사용자 경험(UX)을 고도화하고 개발 생산성을 높이는 자동화를 도입합니다.
- [ ] **Dynamic Forms**: Pydantic 스키마(InputState/OutputState) 기반 UI 폼 자동 생성 (예: 설정 변경 폼).
- [ ] **Interactive Interrupts**: AI의 `interrupt` 신호를 감지하여 모달/입력창을 자동 팝업하고 `Resume` 처리.
- [ ] **Error Visibility**: 백엔드 에러(Exception)를 UI에 친화적인 메시지 및 복구 옵션으로 노출.

### Phase 3: Time-Travel & Collaboration (중장기 목표)
LangGraph의 강력한 체크포인팅 기능을 활용하여 고급 기능을 구현합니다.
- [ ] **Timeline Debugger**: 실행 이력(Checkpoint)을 타임라인으로 시각화하고 특정 시점으로 `Rollback` 또는 `Branching`.
- [ ] **Multi-Session History**: DB 연동을 통해 세션 영속화 및 과거 기획서 탐색 기능 강화.
- [ ] **Collaborative Features**: 다중 사용자간 기획서 공유 및 공동 개선.

---

## 3. Action Items (Immediate)

1.  **리뷰 문서화**: 본 `DOCS/EXPERT_REVIEW.md` 생성 및 저장.
2.  **스키마 기반 폼 검토**: `app.py`의 `render_refinement_ui` 등을 스키마 기반으로 리팩토링 가능성 확인.
3.  **에러 전파 로직 강화**: `graph/workflow.py`의 에러 상태가 `app.py` UI에 더 명확히 전달되도록 로직 점검.

*Documented by PlanCraft Team based on Expert Review.*
