from typing import Any

from app.models.conversation_message import ConversationMessage


class ContextResolver:
    FOLLOW_UP_PHRASES = {
        "why",
        "why?",
        "explain",
        "explain it",
        "tell me why",
        "how",
        "how?",
        "show more",
        "tell me more",
        "what do you mean",
        "how can i improve it",
        "how can i reduce it",
        "compare it",
    }

    def resolve(
        self,
        question: str,
        last_assistant_message: ConversationMessage | None,
    ) -> str:
        clean_question = question.strip().lower()

        if last_assistant_message is None:
            return question

        if not self._is_follow_up(clean_question):
            return question

        previous_intent = last_assistant_message.intent
        previous_data = last_assistant_message.data or {}

        if previous_intent == "CARD_RECOMMENDATION":
            return self._resolve_card_follow_up(
                question=question,
                data=previous_data,
            )

        if previous_intent in {
            "FINANCIAL_DNA",
            "FINANCIAL_DNA_EXPLANATION",
        }:
            return self._resolve_dna_follow_up(
                question=question,
                data=previous_data,
            )

        if previous_intent in {
            "SPENDING_INSIGHTS",
            "TOP_CATEGORY",
            "CATEGORY_SPEND",
        }:
            return self._resolve_spending_follow_up(
                question=question,
                data=previous_data,
            )

        if previous_intent == "AI_COACH":
            return (
                "Explain the previous financial coaching recommendation "
                "in more detail."
            )

        if previous_intent == "SPENDING_PREDICTION":
            return (
                "Explain my spending prediction and tell me how "
                "I can reduce next month's spending."
            )
        if self._is_card_comparison_follow_up(question):
             return "Compare the recommended card with the second best card"

        return question

    def _is_follow_up(self, clean_question: str) -> bool:
        if clean_question in self.FOLLOW_UP_PHRASES:
            return True

        follow_up_starts = (
            "why ",
            "how ",
            "explain ",
            "tell me more",
            "show more",
            "what about",
            "can you compare",
        )

        return clean_question.startswith(follow_up_starts)

    @staticmethod
    def _resolve_card_follow_up(
        question: str,
        data: dict[str, Any],
    ) -> str:
        card_name = ContextResolver._find_card_name(data)

        if "compare" in question.lower():
            if card_name:
                return (
                    f"Compare {card_name} with the other available "
                    "Deutsche Bank cards."
                )

            return "Compare my recommended card with other cards."

        if card_name:
            return f"Why did you recommend {card_name}?"

        return "Why did you recommend this card?"

    @staticmethod
    def _resolve_dna_follow_up(
        question: str,
        data: dict[str, Any],
    ) -> str:
        personality = (
            data.get("primary_personality")
            or data.get("personality")
        )

        if "improve" in question.lower():
            if personality:
                return (
                    f"How can I improve my financial habits as "
                    f"a {personality}?"
                )

            return "How can I improve my Financial DNA?"

        if personality:
            return f"Why is my Financial DNA {personality}?"

        return "Explain my Financial DNA."

    @staticmethod
    def _resolve_spending_follow_up(
        question: str,
        data: dict[str, Any],
    ) -> str:
        category = (
            data.get("top_category")
            or data.get("category")
        )

        if "reduce" in question.lower():
            if category:
                return (
                    f"How can I reduce my spending on {category}?"
                )

            return "How can I reduce my spending?"

        if category:
            return f"Explain why {category} is my highest spending category."

        return "Explain my spending insights in more detail."

    @staticmethod
    def _find_card_name(data: dict[str, Any]) -> str | None:
        direct_name = (
            data.get("recommended_card")
            or data.get("card_name")
            or data.get("name")
        )

        if direct_name:
            return str(direct_name)

        best_card = data.get("best_card")

        if isinstance(best_card, dict):
            return (
                best_card.get("name")
                or best_card.get("card_name")
            )

        return None
    def _is_card_comparison_follow_up(self, question: str) -> bool:
        normalized = question.strip().lower()

        phrases = [
            "compare it with the second one",
            "compare it with second one",
            "compare with the second one",
            "compare with second",
            "compare the second one",
            "what about the second one",
            "compare them",
        ]

        return any(phrase in normalized for phrase in phrases)