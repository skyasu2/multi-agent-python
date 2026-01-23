"""
PlanCraft Agent - RAG Reranker 모듈

Cross-Encoder를 사용하여 검색 결과의 순위를 재조정합니다.
초기 검색(MMR/유사도) 후 정확도를 높이기 위해 사용됩니다.

주요 기능:
    - Cross-Encoder 기반 Reranking
    - 상위 k개 문서 재정렬
    - Lazy Loading (첫 호출 시 모델 로드)

사용 예시:
    from rag.reranker import rerank_documents

    # 검색 결과 Reranking
    reranked = rerank_documents(query, docs, top_k=3)
"""

from typing import Any, List, Optional, Tuple
from functools import lru_cache

# =============================================================================
# 모델 설정
# =============================================================================
# 경량 Cross-Encoder 모델 (한국어/영어 혼용에 적합)
# - ms-marco-MiniLM-L-6-v2: 빠르고 정확한 균형
# - ms-marco-MiniLM-L-12-v2: 더 정확하지만 느림
DEFAULT_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"


@lru_cache(maxsize=1)
def _get_cross_encoder(model_name: str = DEFAULT_MODEL):
    """
    Cross-Encoder 모델을 Lazy Loading합니다.

    lru_cache로 모델을 캐싱하여 재로딩을 방지합니다.

    Args:
        model_name: HuggingFace 모델 이름

    Returns:
        CrossEncoder 인스턴스 또는 None (로드 실패 시)
    """
    try:
        from sentence_transformers import CrossEncoder
        print(f"[Reranker] Loading Cross-Encoder: {model_name}")
        model = CrossEncoder(model_name)
        print("[Reranker] Model loaded successfully")
        return model
    except ImportError:
        print("[WARN] sentence-transformers not installed. Reranking disabled.")
        return None
    except Exception as e:
        print(f"[WARN] Failed to load Cross-Encoder: {e}")
        return None


def rerank_documents(
    query: str,
    documents: List,
    top_k: int = 3,
    model_name: str = DEFAULT_MODEL,
    score_threshold: float = 0.0
) -> List:
    """
    Cross-Encoder를 사용하여 문서 순위를 재조정합니다.

    Args:
        query: 검색 쿼리
        documents: LangChain Document 리스트 (page_content 필수)
        top_k: 반환할 상위 문서 수
        model_name: Cross-Encoder 모델 이름
        score_threshold: 최소 점수 임계값 (이하 필터링)

    Returns:
        List: 재정렬된 Document 리스트 (상위 top_k개)

    Example:
        >>> from rag.retriever import Retriever
        >>> from rag.reranker import rerank_documents
        >>>
        >>> retriever = Retriever(k=10)  # 더 많이 검색
        >>> docs = retriever.get_relevant_documents("기획서 작성법")
        >>> reranked = rerank_documents("기획서 작성법", docs, top_k=3)
    """
    if not documents:
        return []

    # Cross-Encoder 로드
    model = _get_cross_encoder(model_name)

    if model is None:
        # 모델 로드 실패 시 원본 반환 (Fallback)
        return documents[:top_k]

    # Query-Document 쌍 생성
    pairs = []
    for doc in documents:
        # 헤더 메타데이터가 있으면 본문 앞에 추가하여 문맥 보강
        content = doc.page_content
        headers = []
        if "Header 1" in doc.metadata: headers.append(doc.metadata["Header 1"])
        if "Header 2" in doc.metadata: headers.append(doc.metadata["Header 2"])
        if "Header 3" in doc.metadata: headers.append(doc.metadata["Header 3"])
        
        if headers:
            header_text = " > ".join(headers)
            content = f"[{header_text}]\n{content}"
            
        pairs.append((query, content))

    # 점수 계산
    try:
        scores = model.predict(pairs)
    except Exception as e:
        print(f"[WARN] Reranking failed: {e}")
        return documents[:top_k]

    # (점수, 문서) 튜플 생성 및 정렬
    scored_docs = list(zip(scores, documents))
    scored_docs.sort(key=lambda x: x[0], reverse=True)

    # 점수 임계값 필터링 및 상위 k개 추출
    result = []
    for score, doc in scored_docs[:top_k]:
        if score >= score_threshold:
            # 메타데이터에 rerank_score 추가 (디버깅용)
            doc.metadata["rerank_score"] = float(score)
            result.append(doc)

    return result


def rerank_with_scores(
    query: str,
    documents: List,
    model_name: str = DEFAULT_MODEL
) -> List[Tuple[float, Any]]:
    """
    문서와 점수를 함께 반환합니다.

    Args:
        query: 검색 쿼리
        documents: Document 리스트
        model_name: Cross-Encoder 모델 이름

    Returns:
        List[Tuple[float, Document]]: (점수, 문서) 튜플 리스트 (내림차순)
    """
    if not documents:
        return []

    model = _get_cross_encoder(model_name)

    if model is None:
        # Fallback: 기본 점수 0.5 부여
        return [(0.5, doc) for doc in documents]

    pairs = [(query, doc.page_content) for doc in documents]

    try:
        scores = model.predict(pairs)
    except Exception as e:
        print(f"[WARN] Reranking failed: {e}")
        return [(0.5, doc) for doc in documents]

    scored_docs = list(zip(scores, documents))
    scored_docs.sort(key=lambda x: x[0], reverse=True)

    return scored_docs
