"""
app/services/intent_analyzer.py

稳健的 IntentAnalyzer 实现：
- FEW-SHOT 示例 JSON 使用双大括号转义，避免 ChatPromptTemplate 将示例 JSON 当作模板变量
- 从 LLM 获取原始文本后再做 safe_load_json + normalize_analysis，再用 Pydantic 校验
- 对 LLM 返回的可能非字符串对象做鲁棒转换，避免 'method' object is not subscriptable 错误
- 在任何异常情况下返回合法的 IntentAnalysisResult（不会抛出到上层）
"""

import json
import re
import logging
from typing import List, Optional, Any

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from app.core.config import settings
from app.schemas.intent import IntentAnalysisResult

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 与 Pydantic schema 保持一致的长度常量（根据你的 schema 设定）
MAX_SHORT_EXPLANATION = 60
MAX_PERSONA_HINT = 120
MAX_REPLY_SEED = 120


def safe_load_json(raw_text: str) -> Optional[dict]:
    """
    尝试从 LLM 返回文本中提取 JSON 对象并解析为 dict。若失败返回 None。
    优先取第一个 { ... } 段进行解析，若失败尝试直接 json.loads。
    """
    if not raw_text:
        return None
    try:
        start = raw_text.index('{')
        end = raw_text.rindex('}') + 1
        json_str = raw_text[start:end]
        return json.loads(json_str)
    except Exception:
        try:
            return json.loads(raw_text)
        except Exception:
            logger.debug("safe_load_json: failed to parse strict JSON, snippet: %s", raw_text[:200])
            return None


def normalize_analysis(raw_obj: dict) -> dict:
    """
    将解析得到的 dict 规整为可被 Pydantic 验证的最低保障结构：
    - 填默认值
    - 强制类型/范围
    - 截断超长字段与移除技术堆栈噪音
    """
    normalized = {}

    # primary_intent
    normalized['primary_intent'] = raw_obj.get('primary_intent') or 'casual_chat'

    # secondary_intents -> 保证为 list
    sec = raw_obj.get('secondary_intents') or []
    if not isinstance(sec, list):
        sec = [sec]
    normalized['secondary_intents'] = sec

    # emotional_state
    normalized['emotional_state'] = raw_obj.get('emotional_state') or 'neutral'

    # emotional_intensity -> 强制整数 1..10
    try:
        val = int(raw_obj.get('emotional_intensity', 3))
    except Exception:
        val = 3
    val = max(1, min(10, val))
    normalized['emotional_intensity'] = val

    # underlying_need
    underlying = raw_obj.get('underlying_need') or raw_obj.get('underlyingNeed') or "unknown"
    underlying = str(underlying)[:100]
    normalized['underlying_need'] = underlying

    # user_receptivity
    normalized['user_receptivity'] = raw_obj.get('user_receptivity') or 'needs_validation_and_comfort'

    # confidence -> float 0.0..1.0
    try:
        conf = float(raw_obj.get('confidence', 0.5))
    except Exception:
        conf = 0.5
    conf = max(0.0, min(1.0, conf))
    normalized['confidence'] = conf

    # short_explanation: 去掉可能的 traceback 并截断
    short = raw_obj.get('short_explanation') or raw_obj.get('explanation') or ""
    if isinstance(short, str):
        # 去掉堆栈或 traceback 段，避免将错误追踪放入短说明
        short = re.sub(r'(?is)traceback.*', '', short)
        short = short.strip()
        if len(short) > MAX_SHORT_EXPLANATION:
            short = short[:MAX_SHORT_EXPLANATION - 3].rstrip() + "..."
    normalized['short_explanation'] = short

    # persona_hint, reply_seed 截断
    normalized['persona_hint'] = (raw_obj.get('persona_hint') or "")[:MAX_PERSONA_HINT]
    normalized['reply_seed'] = (raw_obj.get('reply_seed') or "")[:MAX_REPLY_SEED]

    return normalized


class IntentAnalyzer:
    """
    稳健版 IntentAnalyzer：
    - Prompt -> LLM，仅获取原始文本输出
    - safe_load_json + normalize_analysis -> Pydantic 验证
    - 所有异常统一捕获，返回安全 fallback
    """

    def __init__(self):
        self.llm = ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.DEEPSEEK_API_BASE,
            model_name="deepseek-chat",
            temperature=0.1,
            streaming=False,
        )

        # 用于在 prompt 中生成 format_instructions 示例文本（保留以便传入）
        self.parser = PydanticOutputParser(pydantic_object=IntentAnalysisResult)

        # Prompt（FEW-SHOT 中的示例 JSON 的大括号已用双大括号转义，避免模板变量解析）
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """
            你是一名顶级的心理学家兼沟通分析师。你的客户是一位拥有独特人设的AI伙伴：{ai_partner_persona}。
            任务：读取标注了角色的聊天历史，并对最新用户消息生成结构化的“用户状态情报报告”。**必须只输出 JSON，严格符合下面的格式指令。不要有任何解释。**

            {format_instructions}

            --- FEW-SHOT EXAMPLE ---
            INPUT:
            - CHAT HISTORY: [user] 我明天要面试了，好紧张……
            - LATEST MESSAGE: 我怕表现不好，会被刷掉怎么办？
            - AI PARTNER PERSONA: 一个温柔且鼓励的姐姐

            OUTPUT (this is the format you MUST follow):
            ```json
            {{
                "primary_intent": "emotional_expression",
                "secondary_intents": ["suggestion_seeking"],
                "emotional_state": "anxious",
                "emotional_intensity": 8,
                "underlying_need": "seeks_reassurance_and_confidence_boost",
                "user_receptivity": "needs_validation_and_comfort",
                "confidence": 0.9,
                "short_explanation": "用户表现出对面试的强烈焦虑，并寻求情感支持和实际建议。",
                "persona_hint": "首先要强烈共情她的焦虑，然后用温柔鼓励的语气给她信心，最后可以给一两个小技巧。",
                "reply_seed": "别担心，感到紧张是非常正常的，这说明你很重视这次机会。"
            }}
            ```
            --- END OF EXAMPLE ---
            """),
            ("human", """
            Now, analyze the following real request:
            CHAT HISTORY:
            {chat_history}

            LATEST MESSAGE:
            {user_message}
            """)
        ])

        # 链：只包含 prompt -> llm（不包含 parser）
        self.analyzer_chain = self.prompt | self.llm

    async def analyze(self, user_message: str, chat_history: List[str], ai_partner_persona: str) -> IntentAnalysisResult:
        formatted_history = "\n".join(chat_history[-6:]) or "无历史记录"
        logger.info(f"Analyzing intent for message: '{user_message}' with persona context '{ai_partner_persona}'.")

        try:
            # 调用 LLM，得到原始返回（可能是字符串，也可能是对象）
            raw = await self.analyzer_chain.ainvoke({
                "chat_history": formatted_history,
                "user_message": user_message,
                "ai_partner_persona": ai_partner_persona,
                "format_instructions": self.parser.get_format_instructions(),
            })

            # ---------- 鲁棒地把 raw 转为字符串（优先尝试常见属性） ----------
            def _safe_get_attr(obj: Any, name: str) -> Optional[Any]:
                try:
                    attr = getattr(obj, name)
                except Exception:
                    return None
                # 如果是方法（callable），谨慎尝试调用（若需要参数则跳过）
                if callable(attr):
                    try:
                        return attr()
                    except TypeError:
                        # 方法需要参数，不能调用，返回方法对象供后续 str()
                        return attr
                    except Exception:
                        return None
                return attr

            raw_text: str = ""

            if isinstance(raw, str):
                raw_text = raw
            else:
                # 常见候选属性顺序
                for field in ("text", "content", "message", "data"):
                    candidate = _safe_get_attr(raw, field)
                    if isinstance(candidate, str) and candidate.strip():
                        raw_text = candidate
                        break
                    if candidate is not None:
                        try:
                            s = str(candidate)
                            if s.strip():
                                raw_text = s
                                break
                        except Exception:
                            pass

                # 最后兜底直接 str()
                if not raw_text:
                    try:
                        raw_text = str(raw)
                    except Exception:
                        raw_text = ""

            # 确保为字符串后安全切片/打印
            logger.debug("Raw LLM output (preview): %s", raw_text[:1000])

            # ---------- 解析与规范化 ----------
            parsed = safe_load_json(raw_text)
            if parsed is None:
                logger.warning("LLM output JSON parsing failed. Using fallback normalization from raw text.")
                parsed = {"short_explanation": raw_text[:MAX_SHORT_EXPLANATION]}

            normalized = normalize_analysis(parsed)

            # Pydantic 严格校验（若仍抛异常会被 except 捕获）
            intent_result = IntentAnalysisResult.model_validate(normalized)
            logger.info("Intent analysis successful: %s", intent_result.model_dump_json(indent=2))
            return intent_result

        except Exception as e:
            # 捕获所有异常并返回安全 fallback，避免抛出导致上层 websocket 或请求流程中断
            logger.error("Intent analysis failed: %s", e, exc_info=True)
            err_str = str(e)[: (MAX_SHORT_EXPLANATION - 15)]
            short = f"Analyzer service failed: {err_str}"
            if len(short) > MAX_SHORT_EXPLANATION:
                short = short[:MAX_SHORT_EXPLANATION - 3] + "..."

            return IntentAnalysisResult(
                primary_intent="casual_chat",
                secondary_intents=[],
                emotional_state="neutral",
                emotional_intensity=3,
                underlying_need="无法确定，分析失败",
                user_receptivity="seeks_logical_and_calm_explanation",
                confidence=0.0,
                short_explanation=short,
                persona_hint="使用最安全、最通用的方式回应。",
                reply_seed=None
            )


# 创建全局单例，按需在外部 import 使用
intent_analyzer_service = IntentAnalyzer()
