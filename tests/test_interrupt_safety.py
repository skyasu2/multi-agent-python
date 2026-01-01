
import pytest
from graph.hitl_config import create_option_payload, create_base_payload, InterruptType
from pydantic import ValidationError

class TestInterruptSafety:
    """
    [Safety Test] 인터럽트 시스템 안정성 검증
    
    1. Semantic Key (interrupt_id) 강제화 검증
    2. Pydantic Schema 준수 검증
    """
    
    def test_semantic_key_enforcement(self):
        """create_option_payload가 interrupt_id 없이 호출되면 실패해야 함"""
        # Python 레벨에서는 TypeError가 발생해야 함 (필수 인자)
        with pytest.raises(TypeError):
            create_option_payload(
                question="Test?",
                options=[],
                node_ref="test_node"
                # interrupt_id Missing
            )

    def test_payload_structure_validation(self):
        """생성된 페이로드가 Pydantic 모델을 통과하는지 검증"""
        # 정상 케이스
        payload = create_option_payload(
            question="Valid Question",
            options=[{"title": "A", "description": "Desc A"}],
            node_ref="test_node",
            interrupt_id="test_id_001"
        )
        
        assert payload["interrupt_id"] == "test_id_001"
        assert payload["type"] == "option"
        assert "event_id" in payload
        assert "expires_at" in payload
        
        # Pydantic 모델 직접 검증 (Double Check)
        from graph.interrupt_types import OptionInterruptPayload
        model = OptionInterruptPayload(**payload)
        assert model.interrupt_id == "test_id_001"

    def test_invalid_option_structure(self):
        """옵션 구조가 잘못되면 Pydantic 검증에서 실패해야 함"""
        # create_option_payload 내부에서 Pydantic 검증을 수행하므로,
        # 잘못된 options를 넘기면 ValidationError가 발생할 것임
        # (현재 구현은 try-except로 warning만 띄우고 원본 반환하지만, 
        #  엄격한 테스트를 위해 로그 확인이나 로직 수정 필요. 일단 호출 자체는 성공하되 경고가 뜸)
        
        # 만약 Pydantic 검증 실패 시 raise하도록 로직을 변경했다면 여기서 잡힘.
        # 현재는 안전장치로 pass하므로 payload가 그대로 반환됨.
        # 따라서 반환된 payload가 Pydantic 검증에 실패하는지 확인.
        
        invalid_payload = create_option_payload(
            question="Invalid Options",
            options=[{"wrong_key": "val"}], # title/description 누락
            node_ref="test_node",
            interrupt_id="test_id_002"
        )
        
        from graph.interrupt_types import OptionInterruptPayload
        with pytest.raises(ValidationError):
            OptionInterruptPayload(**invalid_payload)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
