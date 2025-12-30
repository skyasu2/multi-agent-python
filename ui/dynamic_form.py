"""
Dynamic Form Generator

Pydantic 모델 스키마를 기반으로 Streamlit UI를 동적으로 생성합니다.
이를 통해 새로운 입력 요구사항이 생길 때마다 UI 코드를 수정할 필요 없이 스키마만 정의하면 됩니다.
"""

import streamlit as st
from pydantic import BaseModel
from typing import Type, Optional, Any, get_origin, get_args
from enum import Enum

def render_pydantic_form(
    model: Type[BaseModel], 
    key_prefix: str = "dynamic_form",
    defaults: dict = None
) -> Optional[dict]:
    """
    Pydantic 모델 스키마를 기반으로 Streamlit 위젯을 렌더링하고,
    사용자가 제출하면 입력 데이터를 반환합니다.
    
    Args:
        model: 입력받을 데이터의 Pydantic 모델 클래스
        key_prefix: 위젯 키 충돌 방지를 위한 접두사
        defaults: 초기값 딕셔너리 (Optional)
        
    Returns:
        Optional[dict]: 제출 버튼 클릭 시 입력 데이터 dict, 아니면 None
    """
    if defaults is None:
        defaults = {}
        
    # 상태 관리를 위해 폼 데이터를 세션 스테이트 임시 저장소에 연결 가능하지만,
    # 여기서는 간단히 즉시 렌더링 방식을 사용합니다.
    
    with st.container(border=True):
        if model.__doc__:
            st.caption(f"📝 {model.__doc__.strip().splitlines()[0]}")
            
        form_inputs = {}
        
        # 모델의 필드를 순회하며 위젯 생성
        for name, field in model.model_fields.items():
            # 라벨 및 헬프 텍스트 설정
            label = field.title or name.replace("_", " ").title()
            help_text = field.description or ""
            
            # 기본값 결정
            default_val = defaults.get(name)
            if default_val is None:
                if field.default is not ...:
                    default_val = field.default
            
            # 타입 검사 및 위젯 선택
            field_type = field.annotation
            origin = get_origin(field_type)
            args = get_args(field_type)
            
            widget_key = f"{key_prefix}_{name}"
            
            # 1. Enum 처리 (Selectbox)
            if isinstance(field_type, type) and issubclass(field_type, Enum):
                options = [e.value for e in field_type]
                idx = 0
                if default_val in options:
                    idx = options.index(default_val)
                form_inputs[name] = st.selectbox(
                    label, options, index=idx, help=help_text, key=widget_key
                )
                
            # 2. Boolean 처리 (Checkbox)
            elif field_type is bool:
                form_inputs[name] = st.checkbox(
                    label, value=bool(default_val or False), help=help_text, key=widget_key
                )
                
            # 3. Integer 처리 (Number Input)
            elif field_type is int:
                form_inputs[name] = st.number_input(
                    label, value=int(default_val or 0), step=1, help=help_text, key=widget_key
                )
                
            # 4. String 처리 (Text Area / Text Input)
            elif field_type is str:
                # 긴 텍스트 판별 (description 등을 통해 힌트를 줄 수 있음)
                if "내용" in label or "description" in name or "feedback" in name:
                    form_inputs[name] = st.text_area(
                        label, value=str(default_val or ""), help=help_text, key=widget_key
                    )
                else:
                    form_inputs[name] = st.text_input(
                        label, value=str(default_val or ""), help=help_text, key=widget_key
                    )
            
            # 5. List[str] 처리 (Multiselect) - 단순 예시
            elif origin is list and args and args[0] is str:
                form_inputs[name] = st.multiselect(
                    label, options=[], default=default_val or [], help=help_text + " (직접 입력 가능)", key=widget_key
                )
                # 주의: options가 없으면 선택 불가하므로, 
                # 실제로는 Field의 json_schema_extra 등을 통해 옵션을 전달받아야 함.
            
            # 그 외 타입은 문자열로 처리 (Fallback)
            else:
                form_inputs[name] = st.text_input(
                    label, value=str(default_val or ""), help=f"{help_text} ({field_type})", key=widget_key
                )

        st.markdown("---")
        if st.button("입력 완료", key=f"{key_prefix}_submit", use_container_width=True, type="primary"):
            return form_inputs
            
    return None
