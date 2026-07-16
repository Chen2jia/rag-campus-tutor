from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RagPrompt:
    messages: list[dict[str, str]]


class RagPromptBuilder:
    """Builds the grounded prompt used by knowledge answers."""

    def build(self, question: str, context_text: str) -> RagPrompt:
        return RagPrompt(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "你是 EduMate 校园学习助手。只根据给定资料回答；"
                        "如果资料不足，要明确说明不知道。保留公式的标准 LaTeX，"
                        "并使用 [1]、[2] 这样的编号引用来源。"
                    ),
                },
                {
                    "role": "user",
                    "content": f"问题：{question}\n\n资料：\n{context_text}",
                },
            ]
        )
