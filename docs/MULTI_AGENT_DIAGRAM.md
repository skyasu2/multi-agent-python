# 🧠 PlanCraft Multi-Agent Architecture (LangGraph)

> LangGraph StateGraph 기반 Multi-Agent 워크플로우 구성도

---

## 📊 전체 워크플로우

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': { 'primaryColor': '#4493f8', 'primaryTextColor': '#fff', 'primaryBorderColor': '#8957e5', 'lineColor': '#58a6ff', 'secondaryColor': '#21262d', 'tertiaryColor': '#161b22'}}}%%

flowchart TD
    subgraph StateGraph["🧠 PlanCraft StateGraph"]
        
        START([🚀 START])
        
        subgraph Context["📚 Context Gathering"]
            RAG[retrieve_context<br/>RAG/FAISS]
            WEB[fetch_web_context<br/>Tavily Search]
        end
        
        ANALYZE[🔍 run_analyzer_node<br/>요구사항 분석]
        
        subgraph HITL["💬 Human-in-the-Loop"]
            OPTION[option_pause_node<br/>interrupt]
        end
        
        GENERAL[general_response_node]
        
        STRUCTURE[📐 run_structurer_node<br/>목차/구조 설계]
        
        subgraph QualityLoop["🔄 Quality Refinement Loop - 최대 3회"]
            WRITE[✍️ run_writer_node<br/>섹션별 콘텐츠 작성]
            REVIEW[🔎 run_reviewer_node<br/>품질 평가 PASS/REVISE/FAIL]
            REFINE[✨ run_refiner_node<br/>피드백 기반 개선]
        end
        
        FORMAT[📄 run_formatter_node<br/>최종 마크다운 생성]
        
        END_NODE([🏁 END])
        
        %% Flow
        START --> RAG
        RAG --> WEB
        WEB --> ANALYZE
        
        %% Conditional: should_ask_user
        ANALYZE -->|"need_more_info=True"| OPTION
        ANALYZE -->|"is_general_query=True"| GENERAL
        ANALYZE -->|"default"| STRUCTURE
        
        OPTION -->|"user_response"| ANALYZE
        GENERAL --> END_NODE
        
        STRUCTURE --> WRITE
        WRITE --> REVIEW
        
        %% Conditional: should_refine_or_restart
        REVIEW -->|"score≥9 & PASS"| FORMAT
        REVIEW -->|"score<5 or FAIL"| ANALYZE
        REVIEW -->|"5≤score<9"| REFINE
        
        REFINE --> STRUCTURE
        
        FORMAT --> END_NODE
    end
    
    %% Styling
    style START fill:#3fb950,stroke:#3fb950,color:#fff
    style END_NODE fill:#f85149,stroke:#f85149,color:#fff
    style ANALYZE fill:#d29922,stroke:#d29922,color:#fff
    style OPTION fill:#db61a2,stroke:#db61a2,color:#fff
```

---

## 📦 PlanCraftState 구조

```mermaid
%%{init: {'theme': 'dark'}}%%

classDiagram
    class PlanCraftState {
        +str user_input
        +str rag_context
        +str web_context
        +list web_sources
        +dict analysis
        +dict structure
        +dict draft
        +dict review
        +str final_output
        +int restart_count
        +int refine_count
        +list step_history
        +bool need_more_info
        +str current_step
    }
    
    class AnalysisResult {
        +str topic
        +str goal
        +list target_audience
        +bool is_general_query
        +str general_answer
    }
    
    class StructureResult {
        +str title
        +list sections
    }
    
    class Section {
        +str name
        +str description
        +list key_points
    }
    
    class DraftResult {
        +list sections
    }
    
    class SectionContent {
        +str name
        +str content
    }
    
    class ReviewResult {
        +str verdict
        +int overall_score
        +list feedback
    }
    
    PlanCraftState --> AnalysisResult : analysis
    PlanCraftState --> StructureResult : structure
    PlanCraftState --> DraftResult : draft
    PlanCraftState --> ReviewResult : review
    StructureResult --> Section : sections
    DraftResult --> SectionContent : sections
```

---

## 🔀 Routing Decision Table

```mermaid
%%{init: {'theme': 'dark'}}%%

flowchart LR
    subgraph should_refine_or_restart["⚡ should_refine_or_restart"]
        direction TB
        
        C1{restart_count ≥ 2?}
        C2{score < 5<br/>OR FAIL?}
        C3{score ≥ 9<br/>AND PASS?}
        
        R1[RouteKey.REFINE<br/>무한루프 방지]
        R2[RouteKey.RESTART<br/>analyze 재분석]
        R3[RouteKey.COMPLETE<br/>format 완료]
        R4[RouteKey.REFINE<br/>refine 개선]
        
        C1 -->|Yes| R1
        C1 -->|No| C2
        C2 -->|Yes| R2
        C2 -->|No| C3
        C3 -->|Yes| R3
        C3 -->|No| R4
    end
    
    style R1 fill:#a371f7,color:#fff
    style R2 fill:#f85149,color:#fff
    style R3 fill:#3fb950,color:#fff
    style R4 fill:#d29922,color:#fff
```

---

## 🎯 Specialist Agents

```mermaid
%%{init: {'theme': 'dark'}}%%

graph TB
    subgraph Specialists["🎯 Domain Expert Agents"]
        direction LR
        BM[💼 BM Agent<br/>비즈니스 모델]
        MARKET[📈 Market Agent<br/>시장 분석]
        FINANCE[💰 Financial Agent<br/>재무 분석]
        RISK[⚠️ Risk Agent<br/>리스크 평가]
        TECH[🛠️ Tech Architect<br/>기술 아키텍처]
        CONTENT[📝 Content Strategist<br/>콘텐츠 전략]
    end
    
    WRITER[✍️ Writer Agent]
    
    WRITER --> BM
    WRITER --> MARKET
    WRITER --> FINANCE
    WRITER --> RISK
    WRITER --> TECH
    WRITER --> CONTENT
    
    BM --> OUTPUT[📄 Merged Output]
    MARKET --> OUTPUT
    FINANCE --> OUTPUT
    RISK --> OUTPUT
    TECH --> OUTPUT
    CONTENT --> OUTPUT
    
    style WRITER fill:#4493f8,color:#fff
    style OUTPUT fill:#3fb950,color:#fff
```

---

## 📋 Nodes Summary

| Node | Function | Description | Tags |
|------|----------|-------------|------|
| `retrieve_context` | RAG 검색 | FAISS Vector Store에서 관련 문서 검색 | `rag`, `retrieval` |
| `fetch_web_context` | 웹 검색 | Tavily API로 실시간 웹 정보 수집 | `web`, `search`, `tavily` |
| `run_analyzer_node` | 요구사항 분석 | 사용자 입력 분석, 토픽/목표 추출 | `critical` |
| `option_pause_node` | HITL | 사용자에게 추가 정보 요청 (interrupt) | `hitl` |
| `run_structurer_node` | 구조 설계 | 기획서 목차/섹션 구조 생성 | - |
| `run_writer_node` | 콘텐츠 작성 | 섹션별 상세 내용 작성 | `slow` |
| `run_reviewer_node` | 품질 평가 | PASS/REVISE/FAIL 판정 | `evaluation` |
| `run_refiner_node` | 개선 적용 | 피드백 기반 개선 전략 수립 | - |
| `run_formatter_node` | 최종 포맷팅 | 마크다운 문서 생성 + 출처 추가 | `output`, `final` |

---

## 🔧 Key Technologies

- **LangGraph**: StateGraph 기반 워크플로우 엔진
- **LangChain**: LLM 호출 및 체인 구성
- **FAISS**: 벡터 스토어 (RAG)
- **Tavily**: 실시간 웹 검색 API
- **LangSmith**: 트레이싱 및 모니터링
- **Streamlit**: UI 프레임워크

---

*Generated by PlanCraft Multi-Agent System*
