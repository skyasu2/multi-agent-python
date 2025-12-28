# Task: Schema-driven UI & Advanced Interrupts Implementation

## Goal
Implement a fully schema-driven UI generation system and generalized human interrupt pattern to maximize automation, consistency, and testability, as requested by the user.

## Todo List
- [ ] **Implement Schema-driven UI Generator (`ui/dynamic_form.py`)** <!-- id: 0 -->
    - Create a utility function `render_form_from_schema(pydantic_model)` that dynamically generates Streamlit widgets based on Pydantic field types (str, int, bool, Enum, etc.).
    - Support validation and default values from the schema.
- [ ] **Enhance Interrupt Utilities (`graph/interrupt_utils.py`)** <!-- id: 1 -->
    - Generalize `create_interrupt_payload` to support any Pydantic model schema for user input (not just options).
    - Add `UserInputSchema` to `utils/schemas.py`.
- [ ] **Update App Integration (`app.py`)** <!-- id: 2 -->
    - Integrate the dynamic form generator into the main UI loop to handle general `interrupt` payloads with schemas.
    - Replace/Extend `render_option_selector` to use this generalized system.
- [ ] **Cleanup Documentation** <!-- id: 3 -->
    - Remove `docs/EXPERT_REVIEW.md` and `docs/FINAL_ARCHITECTURE_ANALYSIS.md`.
    - Update `docs/INTERNAL_PLAN.md` to reflect the completed improvements.
- [ ] **Verify with Tests** <!-- id: 4 -->
    - Add a test case in `tests/test_scenarios.py` for the schema-driven input flow.

## Implementation Details
1.  **Schema-driven UI**: Inspect Pydantic fields using `.model_fields` or `.model_json_schema()`. Map types to `st.text_input`, `st.number_input`, `st.checkbox`, `st.selectbox` (for Enums/Options).
2.  **Generalized Node**: Create a generic `human_input_node` in the graph that can carry any schema request.
