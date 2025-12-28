# Implementation Plan - Schema-driven UI & Advanced Interrupts

This plan outlines the steps to implement a schema-based UI generation system that automatically creates Streamlit forms from Pydantic models. This fulfills the user's request for "Schema-driven UI automation" and "Generalized Human Interrupts".

## User Review Required

> [!IMPORTANT]
> This change introduces a new module `ui/dynamic_form.py` and generalizes the interrupt handling logic. It moves away from hardcoded UI widgets for inputs towards a fully dynamic approach.

- **Proposed Change**: Replace manual `st.text_input` calls for structured inputs with a unified `render_schema_form(model_class)` function.
- **Benefit**: Ensures UI always matches the data schema, reduces boilerplate, and enables automatic validation.

## Proposed Changes

### 1. UI Layer
#### [NEW] `ui/dynamic_form.py`
- **Function**: `render_pydantic_form(model: Type[BaseModel], key_prefix: str) -> Optional[BaseModel]`
- **Logic**:
    - Iterate over `model.model_fields`.
    - Map types (`str`, `int`, `bool`, `Enum`) to Streamlit widgets.
    - Handle `description` as help text and `title` as labels.
    - Return an instance of the model if submitted, else None.

#### `ui/__init__.py`
- Export `render_pydantic_form`.

### 2. Graph Layer
#### `utils/schemas.py`
- Add `UserInputSchema` (already planned) with diverse fields (text, option, file) to demonstrate the capability.

#### `graph/interrupt_utils.py`
- Update `create_interrupt_payload` to optionally include a `schema` field (JSON schema dict).

### 3. Application Layer
#### `app.py`
- In the interrupt handling block, check if `schema` is present in the payload.
- If present, call `render_pydantic_form`.
- Fallback to `render_option_selector` if only `options` are present.

## Verification Plan

### Automated Tests
- **`tests/test_dynamic_form.py`**:
    - Since we cannot easily test Streamlit UI rendering in unit tests without a complex harness, we will mock `streamlit` methods and verify that the correct widgets are called for a given schema.
    - OR, simply rely on the existing `test_scenarios.py` to verify the *flow* and manually verify the UI. (Given the constraints, we will verify the logic flow).

### Manual Verification
- Run the app (`streamlit run app.py`).
- Trigger an interrupt (e.g., via "Needs more info").
- Verify the form is rendered correctly based on the schema.
