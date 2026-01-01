"""
HITL Enhancements Verification Tests

Verifies Phase 6 enhancements:
1. State Snapshots in Interrupt Payloads
2. UI/UX Hints for High Retry Counts
3. Task-level Audit Trail in Resume History
"""

import pytest
from unittest.mock import MagicMock
from graph.state import create_initial_state, update_state
from graph.interrupt_utils import create_option_interrupt, handle_user_response
from graph.hitl_config import create_base_payload, InterruptType

class TestHITLEnhancements:
    
    @pytest.fixture
    def base_state(self):
        return create_initial_state(
            user_input="Initial Input",
            thread_id="test_thread_enhancements"
        )

    def test_snapshot_in_payload(self, base_state):
        """Verify that create_option_interrupt includes a state snapshot."""
        # Setup state
        state = update_state(
            base_state,
            current_step="analyze",
            option_question="Choose option",
            options=[{"title": "A", "description": "Opt A"}]
        )
        
        # Create Payload
        payload = create_option_interrupt(state, interrupt_id="test_snapshot_01")
        
        # Verify Snapshot
        assert "snapshot" in payload
        assert payload["snapshot"]["user_input"] == "Initial Input"
        assert payload["snapshot"]["current_step"] == "analyze"
        assert payload["snapshot"]["retry_count"] == 0

    def test_hint_generation_high_retry(self, base_state):
        """Verify that a hint is automatically added when retry_count >= 2."""
        # Setup state with high retry count
        state = update_state(
            base_state,
            retry_count=2,
            option_question="Retry Question",
            options=[{"title": "A", "description": "Opt A"}]
        )
        
        # Create Payload
        payload = create_option_interrupt(state, interrupt_id="test_hint_01")
        
        # Verify Hint
        assert "hint" in payload
        assert payload["hint"] == "입력에 어려움이 있으신가요? 도움말을 확인해보세요."

    def test_hint_generation_low_retry(self, base_state):
        """Verify that no hint is added when retry_count < 2."""
        state = update_state(base_state, retry_count=1)
        payload = create_option_interrupt(state, interrupt_id="test_hint_02")
        assert payload.get("hint") is None

    def test_audit_trail_in_resume_history(self, base_state):
        """Verify that handle_user_response records audit trail in step_history."""
        # Setup initial state with a mock last_interrupt
        last_interrupt = {
            "interrupt_id": "test_audit_id",
            "node_ref": "test_node",
            "event_id": "evt_12345",
            "type": "option"
        }
        state = update_state(
            base_state, 
            last_interrupt=last_interrupt,
            current_step="write"
        )
        
        # Simulate User Response
        response = {"selected_option": {"title": "Approved", "value": "ok"}}
        new_state = handle_user_response(state, response)
        
        # Verify Audit Trail
        history = new_state.get("step_history", [])
        assert len(history) > 0
        last_item = history[-1]
        
        assert "audit_trail" in last_item
        audit = last_item["audit_trail"]
        assert audit["task_step"] == "write"
        assert audit["interrupt_id"] == "test_audit_id"
        assert audit["node_ref"] == "test_node"
        assert audit["event_id"] == "evt_12345"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
