# 🧠 PlanCraft Multi-Agent Architecture

> LangGraph StateGraph 기반 Multi-Agent 워크플로우 구성도

---

## 📊 1. 전체 시스템 아키텍처

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#4493f8', 'primaryTextColor': '#fff', 'lineColor': '#58a6ff'}}}%%

graph TB
    subgraph UI["🖥️ Frontend Layer"]
        STREAMLIT[Streamlit UI<br/>사용자 인터페이스]
    end
    
    subgraph API["🔌 API Layer"]
        FASTAPI[FastAPI Server<br/>REST API v1]
    end
    
    subgraph ORCHESTRATOR["🧠 Orchestration Layer"]
        LANGGRAPH[LangGraph StateGraph<br/>워크플로우 엔진]
    end
    
    subgraph AGENTS["🤖 Agent Layer"]
        direction LR
        ANALYZER[🔍 Analyzer]
        STRUCTURER[📐 Structurer]
        WRITER[✍️ Writer]
        REVIEWER[🔎 Reviewer]
        REFINER[✨ Refiner]
        FORMATTER[📄 Formatter]
    end
    
    subgraph SPECIALISTS["🎯 Specialist Layer"]
        direction LR
        MARKET[📈 Market]
        BM[💼 BM]
        RISK[⚠️ Risk]
        TECH[🛠️ Tech]
        CONTENT[📝 Content]
    end
    
    subgraph EXTERNAL["🌐 External Services"]
        direction LR
        AOAI[Azure OpenAI<br/>GPT-4o]
        TAVILY[Tavily<br/>Web Search]
        FAISS[FAISS<br/>Vector Store]
        LANGSMITH[LangSmith<br/>Tracing]
    end
    
    STREAMLIT <-->|HTTP| FASTAPI
    FASTAPI <--> LANGGRAPH
    LANGGRAPH --> AGENTS
    WRITER --> SPECIALISTS
    SPECIALISTS --> WRITER
    AGENTS --> EXTERNAL
    
    style STREAMLIT fill:#ff4b4b,color:#fff
    style FASTAPI fill:#009688,color:#fff
    style LANGGRAPH fill:#8957e5,color:#fff
```

---

## 📊 2. 워크플로우 상세 (Workflow Graph)

```mermaid
%%{init: {'theme': 'base'}}%%

flowchart TD
    START([🚀 START]) --> CONTEXT
    
    subgraph CONTEXT["📚 Context Gathering"]
        RAG[retrieve_context<br/>FAISS RAG]
        WEB[fetch_web_context<br/>Tavily Search]
        RAG --> WEB
    end
    
    CONTEXT --> ANALYZE[🔍 Analyzer<br/>요구사항 분석]
    
    ANALYZE -->|need_more_info| HITL
    ANALYZE -->|is_general| GENERAL[💬 일반 응답]
    ANALYZE -->|ready| STRUCTURE
    
    subgraph HITL["💬 Human-in-the-Loop"]
        OPTION[option_pause_node<br/>interrupt & wait]
    end
    
    HITL -->|user_response| ANALYZE
    GENERAL --> END_NODE
    
    STRUCTURE[📐 Structurer<br/>목차 설계] --> WRITE
    
    subgraph QA_LOOP["🔄 Quality Assurance Loop"]
        WRITE[✍️ Writer<br/>콘텐츠 작성]
        REVIEW[🔎 Reviewer<br/>품질 평가]
        REFINE[✨ Refiner<br/>피드백 개선]
        
        WRITE --> REVIEW
        REVIEW -->|score<9| REFINE
        REFINE --> STRUCTURE
    end
    
    REVIEW -->|score≥9 PASS| FORMAT[📄 Formatter<br/>최종 문서]
    REVIEW -->|FAIL| ANALYZE
    
    FORMAT --> END_NODE([🏁 END])
    
    style START fill:#3fb950,color:#fff
    style END_NODE fill:#f85149,color:#fff
    style HITL fill:#db61a2,color:#fff
    style QA_LOOP fill:#21262d,color:#fff
```

---

## 📊 3. Agent 협업 구조

```mermaid
%%{init: {'theme': 'base'}}%%

graph LR
    subgraph INPUT["📥 Input"]
        USER[👤 User Input]
    end
    
    subgraph CORE_AGENTS["🤖 Core Agents"]
        A1[🔍 Analyzer]
        A2[📐 Structurer]
        A3[✍️ Writer]
        A4[🔎 Reviewer]
        A5[✨ Refiner]
        A6[📄 Formatter]
    end
    
    subgraph SPECIALISTS["🎯 Specialist Squad"]
        S1[📈 Market Agent<br/>TAM/SAM/SOM 분석]
        S2[💼 BM Agent<br/>수익 모델 설계]
        S3[⚠️ Risk Agent<br/>리스크 평가]
        S4[🛠️ Tech Agent<br/>기술 스택 설계]
        S5[📝 Content Agent<br/>마케팅 전략]
    end
    
    subgraph OUTPUT["📤 Output"]
        PLAN[📋 기획서]
    end
    
    USER --> A1
    A1 --> A2
    A2 --> A3
    A3 --> S1 & S2 & S3 & S4 & S5
    S1 & S2 & S3 & S4 & S5 --> A3
    A3 --> A4
    A4 -->|REVISE| A5
    A5 --> A2
    A4 -->|PASS| A6
    A6 --> PLAN
    
    style A1 fill:#d29922,color:#fff
    style A4 fill:#58a6ff,color:#fff
    style PLAN fill:#3fb950,color:#fff
```

---

## 📊 4. Supervisor + Specialist 패턴

```mermaid
%%{init: {'theme': 'base'}}%%

graph TB
    SUPERVISOR[🎖️ Supervisor<br/>Plan-and-Execute]
    
    SUPERVISOR -->|"1. 시장 분석 필요"| MARKET[📈 Market Agent]
    SUPERVISOR -->|"2. 수익 모델 필요"| BM[💼 BM Agent]
    SUPERVISOR -->|"3. 리스크 필요"| RISK[⚠️ Risk Agent]
    SUPERVISOR -->|"4. 기술 설계 필요"| TECH[🛠️ Tech Agent]
    SUPERVISOR -->|"5. 콘텐츠 전략 필요"| CONTENT[📝 Content Agent]
    
    MARKET -->|결과| MERGE[📦 Result Merger]
    BM -->|결과| MERGE
    RISK -->|결과| MERGE
    TECH -->|결과| MERGE
    CONTENT -->|결과| MERGE
    
    MERGE --> WRITER[✍️ Writer<br/>통합 작성]
    
    style SUPERVISOR fill:#8957e5,color:#fff
    style MERGE fill:#3fb950,color:#fff
```

---

## 📊 5. Human-in-the-Loop (HITL) 흐름

```mermaid
%%{init: {'theme': 'base'}}%%

sequenceDiagram
    participant U as 👤 User
    participant A as 🔍 Analyzer
    participant H as 💬 HITL Node
    participant W as ✍️ Writer
    
    U->>A: "AI 앱 만들어줘"
    A->>A: 분석 (모호함 감지)
    A->>H: interrupt(options)
    H-->>U: "어떤 방향으로 진행할까요?"
    Note over H: ⏸️ 워크플로우 일시정지
    
    U->>H: resume(선택: "헬스케어 AI")
    H->>A: 선택 결과 전달
    A->>A: 재분석 (명확해짐)
    A->>W: 기획서 작성 진행
    W-->>U: 📋 완성된 기획서
```

---

## 📊 6. 품질 루프 (QA Loop) 상태 전이

```mermaid
%%{init: {'theme': 'base'}}%%

stateDiagram-v2
    [*] --> Writing: 구조 설계 완료
    
    Writing --> Reviewing: 초안 작성 완료
    
    Reviewing --> Formatting: score≥9 & PASS
    Reviewing --> Refining: 5≤score<9
    Reviewing --> Analyzing: score<5 | FAIL
    
    Refining --> Writing: 개선 전략 수립
    
    Formatting --> [*]: 최종 문서 생성
    
    Analyzing --> Writing: 재분석 완료
    
    note right of Reviewing
        최대 3회 반복
        (무한 루프 방지)
    end note
```

---

## 📊 7. PlanCraftState 데이터 흐름

```mermaid
%%{init: {'theme': 'base'}}%%

flowchart LR
    subgraph Input
        UI[user_input]
        FILE[file_content]
    end
    
    subgraph Context
        RAG[rag_context]
        WEB[web_context<br/>web_sources]
    end
    
    subgraph Analysis
        ANA[analysis<br/>AnalysisResult]
        STR[structure<br/>StructureResult]
    end
    
    subgraph Draft
        DFT[draft<br/>DraftResult]
        REV[review<br/>JudgeResult]
    end
    
    subgraph Output
        FINAL[final_output<br/>Markdown]
    end
    
    UI & FILE --> Context
    Context --> Analysis
    Analysis --> Draft
    Draft --> Output
    
    style FINAL fill:#3fb950,color:#fff
```

---

## � 8. 서비스 플로우 (End-to-End Flow)

### 8.1 전체 요청-응답 흐름 (Flow Chart)

```mermaid
%%{init: {'theme': 'base'}}%%

flowchart TB
    subgraph USER["👤 사용자"]
        INPUT[/"💬 기획서 요청 입력"/]
        OUTPUT[/"📋 최종 기획서 확인"/]
    end
    
    subgraph UI["🖥️ Streamlit UI"]
        CHAT[채팅 인터페이스]
        PROGRESS[진행률 표시]
        RENDER[마크다운 렌더링]
    end
    
    subgraph API["🔌 FastAPI Backend"]
        ENDPOINT["/api/v1/workflow/run"]
        STATUS["/api/v1/workflow/status"]
        RESUME["/api/v1/workflow/resume"]
    end
    
    subgraph WORKFLOW["🧠 LangGraph Workflow"]
        INIT[State 초기화]
        
        subgraph CONTEXT["📚 Context 수집"]
            RAG_SEARCH[FAISS RAG 검색<br/>내부 가이드라인]
            WEB_SEARCH[Tavily 웹 검색<br/>실시간 시장 데이터]
        end
        
        ANALYZE[🔍 요구사항 분석]
        
        HITL_CHECK{추가 정보<br/>필요?}
        HITL_PAUSE[⏸️ interrupt<br/>사용자 대기]
        
        STRUCTURE[📐 목차 설계]
        
        subgraph SPECIALIST["🎯 전문가 분석"]
            MARKET_A[시장 분석]
            BM_A[수익 모델]
            RISK_A[리스크]
            TECH_A[기술 설계]
        end
        
        WRITE[✍️ 콘텐츠 작성]
        REVIEW[🔎 품질 검토]
        
        REVIEW_CHECK{품질 OK?}
        REFINE[✨ 개선]
        
        FORMAT[📄 최종 포맷팅]
    end
    
    subgraph LLM["🤖 Azure OpenAI"]
        GPT4O[GPT-4o / GPT-4o-mini]
    end
    
    %% Flow
    INPUT --> CHAT
    CHAT --> ENDPOINT
    ENDPOINT --> INIT
    
    INIT --> RAG_SEARCH
    RAG_SEARCH --> WEB_SEARCH
    WEB_SEARCH --> ANALYZE
    
    ANALYZE --> HITL_CHECK
    HITL_CHECK -->|Yes| HITL_PAUSE
    HITL_PAUSE -->|resume| RESUME
    RESUME --> ANALYZE
    HITL_CHECK -->|No| STRUCTURE
    
    STRUCTURE --> SPECIALIST
    MARKET_A & BM_A & RISK_A & TECH_A --> WRITE
    
    WRITE --> REVIEW
    REVIEW --> REVIEW_CHECK
    REVIEW_CHECK -->|score<9| REFINE
    REFINE --> STRUCTURE
    REVIEW_CHECK -->|score≥9| FORMAT
    
    FORMAT --> STATUS
    STATUS --> PROGRESS
    PROGRESS --> RENDER
    RENDER --> OUTPUT
    
    ANALYZE & STRUCTURE & WRITE & REVIEW --> GPT4O
    GPT4O --> ANALYZE & STRUCTURE & WRITE & REVIEW
    
    style INPUT fill:#58a6ff,color:#fff
    style OUTPUT fill:#3fb950,color:#fff
    style HITL_PAUSE fill:#db61a2,color:#fff
    style GPT4O fill:#8957e5,color:#fff
```

### 8.2 서비스 플로우 시퀀스 (Sequence Diagram)

```mermaid
%%{init: {'theme': 'base'}}%%
sequenceDiagram
    autonumber

    participant U as 👤 User
    participant UI as 🖥️ Streamlit UI
    participant API as 🔌 FastAPI
    participant LG as 🧠 LangGraph
    participant RAG as 📚 FAISS RAG
    participant WEB as 🌐 Tavily
    participant SUP as � Supervisor
    participant S as 🎯 Specialists
    participant LLM as 🤖 Azure OpenAI

    %% ===== Request Start =====
    U->>UI: 기획서 생성 요청
    UI->>API: POST /workflow/run
    API->>LG: 워크플로우 실행

    %% ===== Context Collection =====
    LG->>RAG: 내부 문서 검색
    LG->>WEB: 웹 검색
    RAG-->>LG: RAG Context
    WEB-->>LG: Web Context

    %% ===== Analysis =====
    LG->>LLM: 요구사항 분석
    LLM-->>LG: 분석 결과

    %% ===== HITL Check =====
    LG->>LG: 추가 정보 필요 여부 판단
    alt 추가 정보 필요
        LG-->>API: interrupt 발생
        API-->>UI: 상태 스트리밍 (SSE)
        UI-->>U: 추가 정보 요청
        U->>UI: 정보 입력
        UI->>API: POST /workflow/resume
        API->>LG: resume
    end

    %% ===== Structuring =====
    LG->>LLM: 목차 설계
    LLM-->>LG: 구조화 결과

    %% ===== Specialist Analysis =====
    LG->>SUP: Specialist 실행 요청
    par 병렬 분석
        SUP->>S: Market 분석
        SUP->>S: BM 설계
        SUP->>S: Risk 분석
        SUP->>S: Tech 설계
    end
    S-->>SUP: 분석 결과
    SUP-->>LG: 통합 결과 전달

    %% ===== Writing =====
    LG->>LLM: 콘텐츠 작성
    LLM-->>LG: 초안 생성

    %% ===== Review Loop =====
    LG->>LLM: 품질 검토
    LLM-->>LG: 리뷰 점수

    alt 점수 미달 (score < 9)
        LG->>LLM: 개선 요청
        LLM-->>LG: 개선 결과
        LG->>LLM: 구조 재조정
        LLM-->>LG: 수정된 구조
    else 점수 통과 (score ≥ 9)
        LG->>LLM: 최종 포맷팅
        LLM-->>LG: 완성 문서
    end

    %% ===== Result Streaming =====
    LG-->>API: 실행 상태 / 결과
    API-->>UI: SSE 스트리밍
    UI-->>U: 실시간 진행 상태 표시
    UI-->>U: 최종 기획서 출력
```

---

## �📋 Agent 역할 정리

| Agent | 역할 | 입력 | 출력 |
|-------|------|------|------|
| **Analyzer** | 사용자 요구사항 분석 | user_input | AnalysisResult |
| **Structurer** | 기획서 목차 설계 | analysis | StructureResult |
| **Writer** | 섹션별 콘텐츠 작성 | structure + context | DraftResult |
| **Reviewer** | 품질 평가 (PASS/REVISE/FAIL) | draft | JudgeResult |
| **Refiner** | 피드백 기반 개선 | draft + review | Refined Structure |
| **Formatter** | 최종 마크다운 생성 | draft | final_output |

| Specialist | 전문 분야 |
|------------|----------|
| **Market Agent** | 시장 규모 (TAM/SAM/SOM), 경쟁사 분석 |
| **BM Agent** | 수익 모델, 가격 정책, BEP 분석 |
| **Risk Agent** | 법적/기술적/운영 리스크, SWOT |
| **Tech Agent** | 기술 스택, 시스템 아키텍처 |
| **Content Agent** | 마케팅 전략, 브랜딩, User Journey |

---

*Generated by PlanCraft Multi-Agent System*
