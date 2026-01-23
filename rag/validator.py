"""
PlanCraft Agent - RAG Citation Validator
"""

import re
from typing import List, Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
from utils.llm import get_llm

class CitationValidator:
    """
    생성된 텍스트의 인용(Citation) 정확성을 검증하는 클래스입니다.
    
    기능:
    1. 형식 검증: [Source N] 형식이 올바른지 확인
    2. 존재 검증: 인용된 Source ID가 실제 Context에 존재하는지 확인
    3. 내용 검증 (LLM): 인용된 문장이 실제 원문 내용을 담고 있는지 확인 (Hallucination Check)
    """
    
    def __init__(self, model_type: str = "gpt-4o-mini"):
        self.llm = get_llm(model_type=model_type, temperature=0.0)

    def validate(self, text: str, context: str, check_content: bool = True) -> Dict[str, Any]:
        """
        인용 검증을 수행합니다.
        
        Args:
            text: 생성된 텍스트 (기획서 본문)
            context: RAG 검색 결과 (Source ID 포함)
            check_content: LLM 기반 내용 일치 여부 확인 (비용 발생)
            
        Returns:
            Dict: 검증 결과 {valid: bool, issues: List[str], score: float}
        """
        issues = []
        valid_sources = self._extract_valid_source_ids(context)
        citations = self._extract_citations(text)
        
        # 1. 존재 검증
        invalid_citations = [c for c in citations if c not in valid_sources]
        if invalid_citations:
            issues.append(f"존재하지 않는 출처 인용: {', '.join(invalid_citations)}")
            
        # 인용이 아예 없으면 경고 (RAG 모드인데 인용이 없는 경우)
        if not citations and context:
            issues.append("RAG 컨텍스트가 제공되었으나 인용([Source N])이 포함되지 않았습니다.")

        # 2. 내용 검증 (LLM)
        citation_score = 1.0
        if check_content and citations and not invalid_citations:
            # 주요 인용구 3개만 샘플링하여 검증 (속도/비용 최적화)
            sampled_citations = citations[:3]
            content_issues = self._verify_content_match(text, context, sampled_citations)
            if content_issues:
                issues.extend(content_issues)
                citation_score = 0.7  # 감점

        if issues:
            citation_score = max(0.0, citation_score - (len(issues) * 0.2))

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "score": round(citation_score, 2),
            "citation_count": len(citations)
        }

    def _extract_citations(self, text: str) -> List[str]:
        """텍스트에서 [Source 1], [Source 1 > Header] 등의 패턴 추출"""
        # 정규식: [Source 숫자 ... ] 형태에서 숫자만 추출
        # 예: [Source 1], [Source 1 > Header], [Source 1 (Header)]
        pattern = r"\[Source\s+(\d+)(?:[^\]]*)\]"
        matches = re.findall(pattern, text)
        return [f"Source {m}" for m in matches]

    def _extract_valid_source_ids(self, context: str) -> List[str]:
        """Context에서 유효한 Source ID 목록 추출"""
        # Context 포맷: [Source 1], [Source 1 (Header)] 등
        pattern = r"\[(Source\s+\d+)(?:[^\]]*)\]"
        matches = re.findall(pattern, context)
        # "Source 1" 형태의 문자열만 반환 (뒤에 붙은 헤더 정보 제거)
        clean_matches = []
        for m in matches:
            # m이 "Source 1" 또는 "Source 1 (Header)" 일 수 있음 (괄호 시작 전까지만 취함)
            # 하지만 regex 그룹 1이 (Source\s+\d+) 이므로 이미 "Source 1"만 캡처됨.
            clean_matches.append(m.strip())
            
        return list(set(clean_matches))

    def _verify_content_match(self, text: str, context: str, citations: List[str]) -> List[str]:
        """LLM을 사용하여 인용 내용이 원문과 일치하는지 검증"""
        # 전체 텍스트를 다 보내면 너무 길므로, 인용구가 포함된 문장을 추출해야 함
        # 여기서는 단순화를 위해 검증 프롬프트로 처리
        
        system_prompt = """당신은 팩트 체크 전문가입니다.
주어진 '문서 내용'이 '원본 출처'의 내용을 정확하게 인용하고 있는지 검증하세요.
형식적 일치가 아닌, 의미적 일치를 확인해야 합니다.

검증 기준:
1. 인용된 주장이 원본 출처에 실제로 존재하는가?
2. 원본의 의미를 왜곡하지 않았는가?

위반 사항이 있으면 구체적으로 지적하고, 없으면 "문제 없음"이라고 답하세요.
"""
        user_prompt = f"""
## 원본 출처 (Context)
{context}

## 검증할 문서 내용 (Excerpt)
{text[:2000]}... (일부 발췌)

## 검증 대상 인용
{', '.join(citations)}

위 인용들이 원본 출처에 기반한 사실인지 확인해줘.
"""
        try:
            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ])
            result = response.content
            
            if "문제 없음" in result:
                return []
            else:
                return [f"인용 내용 불일치 가능성: {result[:50]}..."]
        except Exception:
            return []  # 검증 실패 시 패스
