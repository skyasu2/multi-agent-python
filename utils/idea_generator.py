
import random
from utils.llm import get_llm
from utils.schemas import CreativeIdeaList
from utils.prompt_examples import WEB_APP_POOL, NON_IT_POOL

SYSTEM_PROMPT = """
당신은 실리콘밸리의 유니콘 스타트업 액셀러레이터입니다.
현재 시장에는 없지만 기술적으로 실현 가능하고, 사람들이 "와우"할 만한 혁신적인 앱/웹 서비스 아이디어를 제안해야 합니다.

조건:
1. 흔한 아이디어(예: 단순 쇼핑몰, 투두리스트)는 절대 제외하세요.
2. AI, 블록체인, O2O, 핀테크 등 최신 기술을 접목하세요.
3. '제목'은 이모지를 포함해 직관적이고 매력적으로 지으세요.
4. '설명'은 이 에이전트에게 그대로 기획 요청을 보낼 수 있도록 구체적인 프롬프트 형태여야 합니다. (예: "~하는 서비스를 기획해줘")
"""

def generate_creative_ideas(count: int = 3) -> list:
    """
    LLM을 사용하여 창의적인 아이디어를 생성합니다.
    생성 실패 시 정적 예제 풀(WEB_APP_POOL + NON_IT_POOL)에서 랜덤 추출하여 Fallback합니다.
    
    Returns:
        List[Tuple[str, str]]: [(제목, 프롬프트), ...] 형식의 리스트
    """
    try:
        # LLM 호출
        llm = get_llm(temperature=0.9).with_structured_output(CreativeIdeaList)
        
        user_msg = f"기발하고 혁신적인 스타트업 아이디어 {count}개를 제안해줘. 한국어로 작성해."
        
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg}
        ]
        
        result = llm.invoke(messages)
        
        if not result or not result.ideas:
            raise ValueError("Empty result from LLM")
            
        ideas = [(idea.title, idea.description) for idea in result.ideas]
        
        # 목록이 부족하면 Static에서 채움 (희박함)
        if len(ideas) < count:
            fallback = random.sample(WEB_APP_POOL + NON_IT_POOL, count - len(ideas))
            ideas.extend(fallback)
            
        return ideas[:count]

    except Exception as e:
        print(f"[WARN] 아이디어 생성 실패 (Fallback 작동): {e}")
        # Fallback: 정적 풀에서 랜덤 추출
        full_pool = WEB_APP_POOL + NON_IT_POOL
        return random.sample(full_pool, min(count, len(full_pool)))
