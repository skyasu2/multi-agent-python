"""
RAG Enhancements Test (Phase 2)

Covers:
1. CitationValidator logic (Regex & LLM checks)
2. Retriever output formatting (Metadata inclusion)
3. Reranker input formatting (Metadata inclusion)
"""

import pytest
from unittest.mock import MagicMock, patch
from rag.validator import CitationValidator

class TestCitationValidator:
    """CitationValidator 테스트"""

    def test_regex_extraction_basic(self):
        """기본 인용 추출 테스트"""
        validator = CitationValidator()
        
        text = "This is a claim [Source 1]. Another claim [Source 2]."
        citations = validator._extract_citations(text)
        assert "Source 1" in citations
        assert "Source 2" in citations
        assert len(citations) == 2

    def test_regex_extraction_with_headers(self):
        """헤더가 포함된 복잡한 인용 추출 테스트"""
        validator = CitationValidator()
        
        text = "Claim with header [Source 1 > Purpose]. Claim with paren [Source 2 (Overview)]."
        citations = validator._extract_citations(text)
        # Validator는 숫자까지만 추출해야 함 "Source 1", "Source 2"
        assert "Source 1" in citations
        assert "Source 2" in citations
        assert "Source 1 > Purpose" not in citations

    def test_valid_source_ids_extraction(self):
        """Context에서 유효한 Source ID 추출 테스트"""
        validator = CitationValidator()
        
        context = """
[Source 1]
Content of source 1...

[Source 2 (Detail)]
Content of source 2...
"""
        valid_sources = validator._extract_valid_source_ids(context)
        assert "Source 1" in valid_sources
        assert "Source 2" in valid_sources
        assert len(valid_sources) == 2

    def test_validate_logic(self):
        """검증 로직 통합 테스트"""
        validator = CitationValidator()
        validator.llm = MagicMock() # LLM 호출 방지
        
        context = "[Source 1]\nDoc 1 content.\n[Source 2]\nDoc 2 content."
        text = "Valid citation [Source 1]. Invalid citation [Source 3]."
        
        # LLM check skip
        result = validator.validate(text, context, check_content=False)
        
        assert result["valid"] is False
        assert any("Source 3" in issue for issue in result["issues"])
        assert "citation_count" in result
        assert result["citation_count"] == 2

class TestRetrieverEnhancement:
    """Retriever 포맷팅 테스트"""

    @patch('rag.retriever.load_vectorstore')
    def test_formatted_context_with_headers(self, mock_load):
        from rag.retriever import Retriever
        
        # Mock Documents
        doc1 = MagicMock()
        doc1.page_content = "Content 1"
        doc1.metadata = {"Header 1": "Introduction", "Header 2": "Goal"}
        
        doc2 = MagicMock()
        doc2.page_content = "Content 2"
        doc2.metadata = {} # No header
        
        mock_store = MagicMock()
        mock_store.max_marginal_relevance_search.return_value = [doc1, doc2]
        mock_load.return_value = mock_store
        
        retriever = Retriever(k=2)
        formatted = retriever.get_formatted_context("query")
        
        # Check output format
        assert "[Source 1 (Introduction > Goal)]" in formatted
        assert "[Source 2]" in formatted
        assert "Content 1" in formatted

class TestRerankerEnhancement:
    """Reranker 입력 포맷팅 테스트"""

    def test_reranker_input_formatting(self):
        """Reranker 입력 쌍 생성 시 헤더 포함 여부 확인"""
        from rag.reranker import rerank_documents
        
        # Mock CrossEncoder
        with patch('rag.reranker._get_cross_encoder') as mock_get_model:
            mock_model = MagicMock()
            # return fake scores
            mock_model.predict.return_value = [0.9, 0.5]
            mock_get_model.return_value = mock_model
            
            doc1 = MagicMock()
            doc1.page_content = "Content 1"
            doc1.metadata = {"Header 1": "Topic"}
            
            doc2 = MagicMock()
            doc2.page_content = "Content 2"
            doc2.metadata = {}
            
            docs = [doc1, doc2]
            
            # Run reranker
            rerank_documents("query", docs, top_k=2)
            
            # Check arguments passed to model.predict
            # pairs = [('query', '[Topic]\nContent 1'), ('query', 'Content 2')]
            call_args = mock_model.predict.call_args[0][0]
            
            assert call_args[0][0] == "query"
            assert "[Topic]" in call_args[0][1]
            assert "Content 1" in call_args[0][1]
            
            assert call_args[1][0] == "query"
            assert "Content 2" in call_args[1][1]
            assert "[Topic]" not in call_args[1][1]
