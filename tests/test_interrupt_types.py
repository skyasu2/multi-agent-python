"""
인터럽트 타입 시스템 테스트

graph/interrupt_types.py 모듈의 단위 테스트입니다.
"""

import pytest
from graph.interrupt_types import (
    InterruptType,
    InterruptFactory,
    ResumeHandler,
    BaseInterruptPayload,
    OptionInterruptPayload,
    FormInterruptPayload,
    ConfirmInterruptPayload,
    ApprovalInterruptPayload,
    InterruptOption,
)


# =============================================================================
# InterruptType Enum 테스트
# =============================================================================

class TestInterruptType:
    """InterruptType Enum 테스트"""

    def test_enum_values(self):
        """Enum 값들이 올바른지 확인"""
        assert InterruptType.OPTION.value == "option"
        assert InterruptType.FORM.value == "form"
        assert InterruptType.CONFIRM.value == "confirm"
        assert InterruptType.APPROVAL.value == "approval"

    def test_string_conversion(self):
        """Enum이 문자열로 변환되는지 확인"""
        assert str(InterruptType.OPTION) == "InterruptType.OPTION"
        assert InterruptType.OPTION == "option"  # str 상속으로 비교 가능


# =============================================================================
# OptionInterruptPayload 테스트
# =============================================================================

class TestOptionInterruptPayload:
    """옵션 인터럽트 페이로드 테스트"""

    def test_create_basic(self):
        """기본 옵션 페이로드 생성"""
        payload = OptionInterruptPayload(
            question="선택하세요",
            options=[InterruptOption(title="A", description="옵션 A")]
        )
        assert payload.type == InterruptType.OPTION
        assert payload.question == "선택하세요"
        assert len(payload.options) == 1

    def test_empty_options_fallback(self):
        """빈 옵션 시 기본값 생성"""
        payload = OptionInterruptPayload(question="선택하세요", options=[])
        assert len(payload.options) == 1
        assert payload.options[0].title == "계속 진행"

    def test_to_dict(self):
        """딕셔너리 변환 확인"""
        payload = OptionInterruptPayload(
            question="선택하세요",
            options=[InterruptOption(title="A", description="옵션 A")]
        )
        result = payload.to_dict()
        assert result["type"] == "option"
        assert result["question"] == "선택하세요"
        assert isinstance(result["options"], list)

    def test_validate_response_with_selected(self):
        """선택된 옵션 응답 검증"""
        payload = OptionInterruptPayload(
            question="선택하세요",
            options=[InterruptOption(title="A", description="옵션 A")]
        )
        assert payload.validate_response({"selected_option": {"title": "A"}})

    def test_validate_response_with_text(self):
        """직접 입력 응답 검증"""
        payload = OptionInterruptPayload(
            question="선택하세요",
            options=[InterruptOption(title="A", description="옵션 A")],
            allow_custom=True
        )
        assert payload.validate_response({"text_input": "직접 입력"})

    def test_validate_response_empty(self):
        """빈 응답 검증 실패"""
        payload = OptionInterruptPayload(
            question="선택하세요",
            options=[InterruptOption(title="A", description="옵션 A")]
        )
        assert not payload.validate_response({})


# =============================================================================
# FormInterruptPayload 테스트
# =============================================================================

class TestFormInterruptPayload:
    """폼 인터럽트 페이로드 테스트"""

    def test_create_basic(self):
        """기본 폼 페이로드 생성"""
        payload = FormInterruptPayload(
            question="정보를 입력하세요",
            input_schema_name="UserInputSchema",
            required_fields=["name", "email"]
        )
        assert payload.type == InterruptType.FORM
        assert payload.input_schema_name == "UserInputSchema"

    def test_validate_response_with_required_fields(self):
        """필수 필드 포함 응답 검증"""
        payload = FormInterruptPayload(
            question="정보를 입력하세요",
            input_schema_name="UserInputSchema",
            required_fields=["name", "email"]
        )
        assert payload.validate_response({"name": "홍길동", "email": "test@test.com"})

    def test_validate_response_missing_required(self):
        """필수 필드 누락 응답 검증 실패"""
        payload = FormInterruptPayload(
            question="정보를 입력하세요",
            input_schema_name="UserInputSchema",
            required_fields=["name", "email"]
        )
        assert not payload.validate_response({"name": "홍길동"})


# =============================================================================
# ConfirmInterruptPayload 테스트
# =============================================================================

class TestConfirmInterruptPayload:
    """확인 인터럽트 페이로드 테스트"""

    def test_create_basic(self):
        """기본 확인 페이로드 생성"""
        payload = ConfirmInterruptPayload(question="진행하시겠습니까?")
        assert payload.type == InterruptType.CONFIRM
        assert payload.confirm_text == "예"
        assert payload.cancel_text == "아니오"

    def test_validate_response_confirmed(self):
        """확인 응답 검증"""
        payload = ConfirmInterruptPayload(question="진행하시겠습니까?")
        assert payload.validate_response({"confirmed": True})
        assert payload.validate_response({"confirmed": False})

    def test_validate_response_missing(self):
        """확인 값 누락 검증 실패"""
        payload = ConfirmInterruptPayload(question="진행하시겠습니까?")
        assert not payload.validate_response({})


# =============================================================================
# ApprovalInterruptPayload 테스트
# =============================================================================

class TestApprovalInterruptPayload:
    """승인 인터럽트 페이로드 테스트"""

    def test_create_basic(self):
        """기본 승인 페이로드 생성"""
        payload = ApprovalInterruptPayload(
            question="승인하시겠습니까?",
            role="팀장"
        )
        assert payload.type == InterruptType.APPROVAL
        assert payload.role == "팀장"
        assert len(payload.options) == 2

    def test_is_approved_true(self):
        """승인 판정 확인"""
        payload = ApprovalInterruptPayload(question="승인?", role="팀장")
        assert payload.is_approved({"approved": True})
        assert payload.is_approved({"selected_option": {"value": "approve"}})

    def test_is_approved_false(self):
        """반려 판정 확인"""
        payload = ApprovalInterruptPayload(question="승인?", role="팀장")
        assert not payload.is_approved({"approved": False})
        assert not payload.is_approved({"selected_option": {"value": "reject"}})


# =============================================================================
# InterruptFactory 테스트
# =============================================================================

class TestInterruptFactory:
    """인터럽트 팩토리 테스트"""

    def test_create_option(self):
        """옵션 타입 생성"""
        payload = InterruptFactory.create(
            InterruptType.OPTION,
            question="선택하세요",
            options=[InterruptOption(title="A", description="옵션 A")]
        )
        assert isinstance(payload, OptionInterruptPayload)

    def test_create_from_string(self):
        """문자열로 타입 생성"""
        payload = InterruptFactory.create(
            "option",
            question="선택하세요",
            options=[InterruptOption(title="A", description="옵션 A")]
        )
        assert isinstance(payload, OptionInterruptPayload)

    def test_create_form(self):
        """폼 타입 생성"""
        payload = InterruptFactory.create(
            InterruptType.FORM,
            question="입력하세요",
            input_schema_name="TestSchema"
        )
        assert isinstance(payload, FormInterruptPayload)

    def test_create_confirm(self):
        """확인 타입 생성"""
        payload = InterruptFactory.create(
            InterruptType.CONFIRM,
            question="진행하시겠습니까?"
        )
        assert isinstance(payload, ConfirmInterruptPayload)

    def test_create_approval(self):
        """승인 타입 생성"""
        payload = InterruptFactory.create(
            InterruptType.APPROVAL,
            question="승인하시겠습니까?",
            role="팀장"
        )
        assert isinstance(payload, ApprovalInterruptPayload)

    def test_create_invalid_type(self):
        """잘못된 타입 예외 발생"""
        with pytest.raises(ValueError):
            InterruptFactory.create("invalid_type", question="테스트")


# =============================================================================
# ResumeHandler 테스트
# =============================================================================

class TestResumeHandler:
    """응답 핸들러 테스트"""

    def test_handle_option(self):
        """옵션 응답 처리"""
        result = ResumeHandler.handle(
            InterruptType.OPTION,
            {"selected_option": {"title": "A"}}
        )
        assert result["action"] == "option_selected"
        assert result["selected_option"]["title"] == "A"

    def test_handle_confirm(self):
        """확인 응답 처리"""
        result = ResumeHandler.handle(
            InterruptType.CONFIRM,
            {"confirmed": True}
        )
        assert result["action"] == "confirmed"
        assert result["confirmed"] is True

    def test_handle_approval_approved(self):
        """승인 응답 처리"""
        result = ResumeHandler.handle(
            InterruptType.APPROVAL,
            {"selected_option": {"value": "approve"}}
        )
        assert result["action"] == "approved"
        assert result["approved"] is True

    def test_handle_approval_rejected(self):
        """반려 응답 처리"""
        result = ResumeHandler.handle(
            InterruptType.APPROVAL,
            {"selected_option": {"value": "reject"}, "rejection_reason": "수정 필요"}
        )
        assert result["action"] == "rejected"
        assert result["approved"] is False
        assert result["rejection_reason"] == "수정 필요"


# =============================================================================
# 통합 테스트
# =============================================================================

class TestIntegration:
    """통합 테스트"""

    def test_full_option_flow(self):
        """옵션 인터럽트 전체 흐름"""
        # 1. 페이로드 생성
        payload = InterruptFactory.create(
            InterruptType.OPTION,
            question="방향을 선택하세요",
            options=[
                InterruptOption(title="A", description="방향 A"),
                InterruptOption(title="B", description="방향 B"),
            ]
        )

        # 2. 딕셔너리로 변환 (interrupt() 전달용)
        payload_dict = payload.to_dict()
        assert payload_dict["type"] == "option"

        # 3. 사용자 응답 시뮬레이션
        user_response = {"selected_option": {"title": "A", "description": "방향 A"}}

        # 4. 응답 검증
        assert payload.validate_response(user_response)

        # 5. 응답 처리
        result = ResumeHandler.handle(InterruptType.OPTION, user_response)
        assert result["selected_option"]["title"] == "A"

    def test_full_approval_flow(self):
        """승인 인터럽트 전체 흐름"""
        # 1. 페이로드 생성
        payload = InterruptFactory.create(
            InterruptType.APPROVAL,
            question="이 기획서를 승인하시겠습니까?",
            role="팀장"
        )

        # 2. 딕셔너리로 변환
        payload_dict = payload.to_dict()
        assert payload_dict["role"] == "팀장"

        # 3. 승인 응답 시뮬레이션
        approve_response = {"selected_option": {"value": "approve"}}
        assert payload.validate_response(approve_response)
        assert payload.is_approved(approve_response)

        # 4. 반려 응답 시뮬레이션
        reject_response = {"selected_option": {"value": "reject"}, "rejection_reason": "근거 부족"}
        assert payload.validate_response(reject_response)
        assert not payload.is_approved(reject_response)
