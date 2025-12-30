# BOOTCAMP_ALIGNMENT_GUIDE.md
# AI Bootcamp Final Project – Development Alignment Guide

## 0. 문서 목적 (Purpose)

이 문서는 본 프로젝트가 **AI Bootcamp 최종 과제 요구사항과 평가 기준에 부합하는지**를
개발 단계에서 지속적으로 검증하기 위한 **기준선(Alignment Baseline)** 이다.

본 문서는:
- 기능 추가 여부 판단
- 설계 변경 시 정당성 검증
- 과도한 기술 사용 방지
- "구현은 되었으나 평가 기준과 무관한 요소" 식별

을 목적으로 하며,
**개발을 수행하는 AI Agent는 항상 이 문서를 최우선 기준으로 참조해야 한다.**

---

## 1. 최상위 원칙 (Non-Negotiable Principles)

### P1. End-to-End Agent 서비스여야 한다
- 단일 기능 데모 ❌
- Prompt → Agent 동작 → 결과 생성 → 사용자 인터페이스까지 연결 ⭕
- 실제 사용 시나리오가 설명 가능해야 함

### P2. Multi-Agent 구조는 필수
- 단일 Agent 구조는 인정되지 않음
- 역할 분리가 명확해야 함 (예: Analyzer / Writer / Reviewer 등)
- Agent 간 호출 흐름이 구조적으로 표현되어야 함 (Graph / Router / Supervisor 등)

### P3. "많이 쓰는 것"이 아니라 "왜 썼는지"가 중요
- 모든 기술을 쓰는 것은 목표가 아님
- 선택된 기술은 반드시 **문제 해결과 직접 연결**되어야 함

---

## 2. 필수 기술 요소 – 충족 기준

### 2.1 Prompt Engineering

#### 필수 충족 조건
- 역할 기반 프롬프트(Role Prompt) 존재
- 입력이 달라져도 출력 품질이 유지되도록 구조화됨
- Few-shot / 예시 / 규칙 중 최소 1개 이상 명확히 사용

#### 실패 판정 기준
- 단일 시스템 프롬프트 + 사용자 입력만 사용
- 프롬프트가 코드 내부에 하드코딩되어 설명 불가
- "그냥 잘 나오길 기대"하는 형태

---

### 2.2 LangChain / LangGraph 기반 Agent

#### 필수 충족 조건
- LangChain 또는 LangGraph를 사용한 Agent 구조
- Agent 간 책임이 분리되어 있음 (SRP 준수)
- 상태(State) 또는 실행 흐름이 코드 구조상 드러남

#### 권장 (가점)
- LangGraph StateGraph 사용
- Conditional Edge / Loop / Refine 구조
- Structured Output 기반 안정성 확보

#### 실패 판정 기준
- 단순 chain.invoke() 반복
- Agent 이름만 있고 실제 역할 분리가 없음

---

### 2.3 RAG (Retrieval-Augmented Generation)

#### 필수 충족 조건
- 외부 지식 소스 존재 (문서, 파일, 데이터 등)
- Retrieval 과정이 코드/구조상 명확
- "모델 지식"이 아닌 "검색된 정보"를 기반으로 응답

#### 허용 범위
- FAISS / Chroma 등 Vector DB
- 파일 기반 RAG
- 단순하지만 실제 의미 있는 데이터면 충분

#### 실패 판정 기준
- RAG가 있다고 주장하나 실제로는 사용되지 않음
- 검색 결과를 무시하고 LLM이 독자적으로 답변

---

### 2.4 서비스 패키징 (UI / 실행 구조)

#### 필수 충족 조건
- 사용자가 직접 실행 가능한 인터페이스 존재
- Streamlit / Web UI / CLI 등 형태는 자유
- "이 Agent는 이렇게 사용한다"가 명확

#### 실패 판정 기준
- 코드만 있고 실행 방법이 불명확
- notebook 단위 실험 수준

---

## 3. 선택 요소 (Advanced Option) – 사용 판단 기준

### 3.1 Structured Output / Function Calling

#### 사용 권장 조건
- Agent 간 데이터 전달이 많을 때
- Refine / Review / Loop 구조가 있을 때

#### 사용하지 않아도 되는 경우
- 단순 단방향 생성 Agent

---

### 3.2 MCP (Model Context Protocol)

#### 사용 정당성 기준
- 파일 시스템 / 외부 도구 / 시스템 접근이 실제 필요할 때
- "Agent가 할 수 있는 일의 범위를 확장"하는 역할일 때

#### 감점 위험
- 단순히 기술 나열용 MCP
- 실제 Agent 동작과 연결되지 않음

---

### 3.3 A2A (Agent-to-Agent)

#### 사용 정당성 기준
- Agent 간 협업 개념이 명확할 때
- Supervisor / Orchestrator 패턴이 설명 가능할 때

#### 주의
- 단순 호출 체인은 A2A로 인정되지 않을 수 있음

---

## 4. 개발 중 AI Agent를 위한 Self-Check 질문

개발 AI는 기능 추가/변경 시 아래 질문에 답할 수 있어야 한다:

1. 이 변경은 **어떤 과제 요구사항과 직접 연결되는가?**
2. 평가자가 봤을 때 "왜 필요했는지" 설명 가능한가?
3. 기존 구조 대비 복잡도만 증가시키지 않았는가?
4. 제거해도 과제 점수에 영향이 없는 요소는 아닌가?

→ 위 질문 중 2개 이상에 명확히 답하지 못하면 **추가 구현 금지**

---

## 5. 최종 판단 기준 (Decision Rule)

- ✅ 과제 기준 충족 + 설명 가능 → 유지
- ⚠️ 기술적으로 훌륭하나 과제 무관 → 문서/발표용으로만 유지
- ❌ 과제 기준과 무관 + 설명 불가 → 제거 대상

---

## 6. 이 문서의 우선순위

본 문서는:
- 코드 리뷰 기준
- Refiner Agent 판단 기준
- 기능 추가/삭제 결정 기준

으로 사용되며,
**개발 편의성·개인 취향보다 항상 우선한다.**
