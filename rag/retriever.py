"""
PlanCraft Agent - RAG Retriever 모듈

벡터스토어에서 쿼리와 관련된 문서를 검색하는 기능을 제공합니다.
LangGraph 워크플로우의 retrieve 노드에서 사용됩니다.

주요 기능:
    - 유사도 기반 문서 검색 (MMR)
    - Cross-Encoder Reranking (정확도 향상)
    - 검색 결과 포맷팅

사용 예시:
    from rag.retriever import Retriever

    # 기본 검색 (MMR only)
    retriever = Retriever(k=3)
    docs = retriever.get_relevant_documents("기획서 작성법")

    # Reranking 활성화 (정확도 향상)
    retriever = Retriever(k=3, use_reranker=True)
    docs = retriever.get_relevant_documents("기획서 작성법")
"""

from rag.vectorstore import load_vectorstore


class Retriever:
    """
    RAG 검색을 수행하는 클래스

    FAISS 벡터스토어에서 쿼리와 유사한 문서를 검색합니다.
    Cross-Encoder Reranking을 통해 정확도를 향상시킬 수 있습니다.

    Attributes:
        vectorstore: FAISS 벡터스토어 인스턴스
        k: 최종 반환할 문서 수
        use_reranker: Cross-Encoder Reranking 사용 여부
        fetch_k_multiplier: Reranking 시 초기 검색 배수 (k * multiplier)

    Example:
        >>> retriever = Retriever(k=3, use_reranker=True)
        >>> docs = retriever.get_relevant_documents("기획서 구조")
        >>> for doc in docs:
        ...     print(doc.page_content[:50])
    """

    def __init__(self, k: int = 3, use_reranker: bool = False, fetch_k_multiplier: int = 4):
        """
        Retriever를 초기화합니다.

        Args:
            k: 최종 반환할 상위 문서 수 (기본값: 3)
            use_reranker: Cross-Encoder Reranking 사용 여부 (기본값: False)
            fetch_k_multiplier: Reranking 시 초기 검색 배수 (기본값: 4)

        Note:
            - use_reranker=True: 더 많은 후보를 검색 후 Reranking으로 정확도 향상
            - use_reranker=False: MMR 검색만 사용 (빠름, 다양성 중심)
        """
        self.vectorstore = load_vectorstore()
        self.k = k
        self.use_reranker = use_reranker
        self.fetch_k_multiplier = fetch_k_multiplier

    def get_relevant_documents(self, query: str) -> list:
        """
        쿼리와 관련된 문서를 검색합니다.

        use_reranker=True일 경우:
            1. MMR로 더 많은 후보 검색 (k * fetch_k_multiplier)
            2. Cross-Encoder로 Reranking
            3. 상위 k개 반환

        use_reranker=False일 경우:
            1. MMR로 k개 검색 (다양성 중심)

        Args:
            query: 검색 쿼리 문자열

        Returns:
            list: Document 객체 리스트
                - 각 Document는 page_content와 metadata를 포함
                - use_reranker=True 시 metadata에 rerank_score 포함

        Example:
            >>> docs = retriever.get_relevant_documents("목표 섹션 작성법")
            >>> print(docs[0].page_content)
        """
        if not self.vectorstore:
            return []

        if self.use_reranker:
            # [Reranking Mode] 더 많은 후보를 검색 후 Cross-Encoder로 재정렬
            from rag.reranker import rerank_documents

            # 1단계: MMR로 후보군 확보 (k * multiplier개)
            fetch_k = self.k * self.fetch_k_multiplier
            candidates = self.vectorstore.max_marginal_relevance_search(
                query,
                k=fetch_k,
                fetch_k=fetch_k * 2,
                lambda_mult=0.7  # 유사도 중심 (Reranker가 정확도 보정)
            )

            # 2단계: Cross-Encoder Reranking
            docs = rerank_documents(query, candidates, top_k=self.k)
            return docs
        else:
            # [MMR Mode] 다양성 중심 검색 (기본 동작)
            docs = self.vectorstore.max_marginal_relevance_search(
                query,
                k=self.k,
                fetch_k=self.k * self.fetch_k_multiplier,
                lambda_mult=0.6  # 다양성 가중치 (0.5=균형, 1.0=유사도중심)
            )
            return docs
    
    # [REMOVED] get_relevant_documents_with_score
    # 기존 코드에서 사용되지 않으며, 현재 MMR 검색(get_relevant_documents)이 더 효과적이므로 제거함.
    # 추후 점수 기반 필터링이 필요할 경우 vectorstore.similarity_search_with_score 활용하여 재구현 권장.


    def get_formatted_context(self, query: str) -> str:
        """
        쿼리와 관련된 문서를 검색하여 포맷된 문자열로 반환합니다.
        
        여러 문서의 내용을 하나의 문자열로 결합합니다.
        프롬프트에 컨텍스트로 삽입할 때 사용합니다.
        
        Args:
            query: 검색 쿼리 문자열
        
        Returns:
            str: 검색된 문서들의 내용을 결합한 문자열
        
        Example:
            >>> context = retriever.get_formatted_context("기획서 배경")
            >>> prompt = f"참고 자료:\\n{context}\\n\\n질문: ..."
        """
        docs = self.get_relevant_documents(query)
        
        if not docs:
            return ""
        
        # 각 문서 내용을 구분자로 연결
        return "\n\n---\n\n".join([d.page_content for d in docs])
