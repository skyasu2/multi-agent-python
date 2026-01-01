
from agents.writer import run
from graph.state import PlanCraftState
from utils.schemas import AnalysisResult
from unittest.mock import MagicMock, patch

def test_writer_prompt_formatting():
    # Mock State
    state = PlanCraftState(
        user_input="Test Input",
        analysis={"topic": "Test", "user_constraints": ["Must use Python", "No Cloud"]},
        structure={"sections": []},
        rag_context="RAG",
        web_context="Web",
        web_urls=["http://test.com"]
    )
    
    # Mock LLM and file logger
    with patch("agents.writer.get_llm") as mock_get_llm, \
         patch("agents.writer.get_file_logger") as mock_logger:
             
        mock_llm_instance = MagicMock()
        mock_get_llm.return_value = mock_llm_instance
        
        # Invoke run
        # We expect it to TRY invoking the LLM. 
        # If formatting failed, it would return error state BEFORE invoking LLM.
        
        result = run(state)
        
        if result.get("error") and "프롬프트 포맷 오류" in result["error"]:
            print(f"FAILED: {result['error']}")
        else:
            print("SUCCESS: Prompt formatting passed.")

if __name__ == "__main__":
    test_writer_prompt_formatting()
