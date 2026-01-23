"""
Multi-Agent Collaboration 테스트

1. Co-authoring Loop (LLM 기반 합의 감지)
2. Dynamic Q&A (Writer ↔ Specialist 동적 질의응답)

실행:
    pytest tests/test_multi_agent_collab.py -v
"""

import pytest
from unittest.mock import patch, MagicMock
from pydantic import ValidationError


# =============================================================================
# Schema Tests
# =============================================================================

class TestConsensusResultSchema:
    """ConsensusResult 스키마 테스트"""

    def test_valid_consensus_result(self):
        """정상적인 합의 결과 생성"""
        from utils.schemas import ConsensusResult

        result = ConsensusResult(
            consensus_reached=True,
            confidence=0.85,
            agreed_items=["시장 분석 보강", "BEP 계산 추가"],
            unresolved_items=[],
            reasoning="Reviewer가 Writer의 개선 계획에 동의함",
            suggested_next_action="finalize"
        )

        assert result.consensus_reached is True
        assert result.confidence == 0.85
        assert len(result.agreed_items) == 2

    def test_confidence_bounds(self):
        """신뢰도 범위 검증 (0.0 ~ 1.0)"""
        from utils.schemas import ConsensusResult

        # 유효 범위
        result = ConsensusResult(consensus_reached=False, confidence=0.5)
        assert result.confidence == 0.5

        # 범위 초과 시 ValidationError
        with pytest.raises(ValidationError):
            ConsensusResult(consensus_reached=True, confidence=1.5)

        with pytest.raises(ValidationError):
            ConsensusResult(consensus_reached=True, confidence=-0.1)





# =============================================================================
# Discussion Consensus Tests (Mock LLM)
# =============================================================================

class TestConsensusDetection:
    """LLM 기반 합의 감지 테스트"""

    @patch('utils.llm.get_llm')
    def test_llm_consensus_reached(self, mock_get_llm):
        """LLM이 합의 완료로 판정한 경우"""
        from graph.subgraphs import _check_consensus_node
        from utils.schemas import ConsensusResult

        # Mock LLM 응답 설정
        mock_llm = MagicMock()
        mock_consensus_result = ConsensusResult(
            consensus_reached=True,
            confidence=0.9,
            agreed_items=["시장 분석 보강", "경쟁사 3개 추가"],
            unresolved_items=[],
            reasoning="양측이 개선 방향에 합의함"
        )
        mock_llm.with_structured_output.return_value.invoke.return_value = mock_consensus_result
        mock_get_llm.return_value = mock_llm

        # 테스트 State
        state = {
            "discussion_round": 1,
            "discussion_messages": [
                {"role": "reviewer", "content": "시장 분석이 부족합니다", "round": 0},
                {"role": "writer", "content": "경쟁사 3개를 추가하겠습니다", "round": 0},
                {"role": "reviewer", "content": "좋습니다. 진행하세요", "round": 1},
            ]
        }

        result = _check_consensus_node(state)

        assert result.get("consensus_reached") is True
        assert len(result.get("agreed_action_items", [])) >= 1

    @patch('utils.llm.get_llm')
    def test_llm_consensus_not_reached(self, mock_get_llm):
        """LLM이 합의 미완료로 판정한 경우"""
        from graph.subgraphs import _check_consensus_node
        from utils.schemas import ConsensusResult

        # Mock LLM 응답 설정
        mock_llm = MagicMock()
        mock_consensus_result = ConsensusResult(
            consensus_reached=False,
            confidence=0.8,
            agreed_items=[],
            unresolved_items=["재무 계획 구체화 필요"],
            reasoning="Writer가 아직 구체적인 방안을 제시하지 않음"
        )
        mock_llm.with_structured_output.return_value.invoke.return_value = mock_consensus_result
        mock_get_llm.return_value = mock_llm

        state = {
            "discussion_round": 0,
            "discussion_messages": [
                {"role": "reviewer", "content": "재무 계획이 불명확합니다", "round": 0},
                {"role": "writer", "content": "검토해 보겠습니다", "round": 0},
            ]
        }

        result = _check_consensus_node(state)

        assert result.get("consensus_reached") is False

    @patch('utils.llm.get_llm')
    def test_max_rounds_force_consensus(self, mock_get_llm):
        """최대 라운드 도달 시 강제 합의"""
        from graph.subgraphs import _check_consensus_node
        from utils.schemas import ConsensusResult

        # Mock LLM 응답 설정 (합의 미완료로 반환)
        mock_llm = MagicMock()
        mock_consensus_result = ConsensusResult(
            consensus_reached=False,
            confidence=0.5,
            agreed_items=[],
            unresolved_items=["미해결"]
        )
        mock_llm.with_structured_output.return_value.invoke.return_value = mock_consensus_result
        mock_get_llm.return_value = mock_llm

        # DISCUSSION_MAX_ROUNDS(5) 이상으로 설정
        state = {
            "discussion_round": 4,  # 다음 라운드가 5가 됨 (max_rounds 도달)
            "discussion_messages": [
                {"role": "reviewer", "content": "아직 부족합니다", "round": 4},
                {"role": "writer", "content": "개선하겠습니다", "round": 4},
            ]
        }

        result = _check_consensus_node(state)

        # 최대 라운드에서 강제 합의
        assert result.get("consensus_reached") is True


# =============================================================================
# Workflow Integration Tests
# =============================================================================

class TestWorkflowIntegration:
    """워크플로우 통합 테스트"""

    def test_workflow_imports(self):
        """워크플로우 임포트 테스트"""
        from graph.workflow import (
            create_workflow,
            RouteKey,
        )

        assert RouteKey.RETRY == "retry"


# =============================================================================
# Prompt Tests
# =============================================================================

class TestDiscussionPrompts:
    """Discussion 프롬프트 테스트"""

    def test_consensus_prompts_exist(self):
        """합의 판정 프롬프트 존재 확인"""
        from prompts.discussion_prompt import (
            CONSENSUS_JUDGE_SYSTEM_PROMPT,
            CONSENSUS_JUDGE_USER_PROMPT,
        )

        assert "합의 판정" in CONSENSUS_JUDGE_SYSTEM_PROMPT
        assert "{discussion_history}" in CONSENSUS_JUDGE_USER_PROMPT


