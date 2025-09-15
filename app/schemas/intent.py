from pydantic import BaseModel, Field
from typing import Literal, List, Optional

# --- 以下定义完全来自你的方案文档 ---

IntentType = Literal[
    "information_seeking", "problem_solving", "emotional_expression",
    "casual_chat", "suggestion_seeking"
]

EmotionalStateType = Literal["joyful", "sad", "anxious", "angry", "surprised", "neutral"]

ReceptivityType = Literal[
    "needs_validation_and_comfort",
    "seeks_logical_and_calm_explanation",
    "open_to_humor_and_lightheartedness",
    "desires_shared_joy_and_excitement"
]

class IntentAnalysisResult(BaseModel):
    """
    定义了意图分析的结构化输出，作为一份“描述性情报”。
    该模型是 IntentAnalyzer 和 Persona 层之间的核心契约。
    """
    primary_intent: IntentType = Field(
        ...,
        description="识别出的用户最主要的核心意图。"
    )
    secondary_intents: List[IntentType] = Field(
        default_factory=list,
        description="识别出的次要意图列表，以处理复杂或混合的用户输入。"
    )
    emotional_state: EmotionalStateType = Field(
        ...,
        description="判断的用户当前最可能的情绪状态。"
    )
    emotional_intensity: int = Field(
        ...,
        ge=1,
        le=10,
        description="情绪的强度等级，从1（轻微）到10（强烈）。"
    )
    underlying_need: str = Field(
        ...,
        max_length=100,
        description="洞察用户消息背后更深层次的、可能未言明的需求。"
    )
    user_receptivity: ReceptivityType = Field(
        ...,
        description="评估用户当前最容易接受哪种沟通方式。"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="分析器对本次分析结果的置信度评分，用于后续的决策判断。"
    )
    short_explanation: Optional[str] = Field(
        None,
        max_length=100,
        description="对分析结果的简短文字说明，尤其是在低置信度时解释原因。"
    )
    persona_hint: Optional[str] = Field(
        None,
        max_length=120,
        description="给 Persona 层提供的一个风格或内容上的具体提示。"
    )
    reply_seed: Optional[str] = Field(
        None,
        max_length=120,
        description="建议的一个回复开头或核心句子，Persona 层可以围绕它进行构建。"
    )