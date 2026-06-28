from typing import List, Dict


class PromptBuilder:
    """Builds the message payload for OpenAI API."""

    def __init__(self, max_history: int = 20):
        self.max_history = max_history

    def build_messages(
        self,
        system_prompt: str,
        history: List[Dict[str, str]],
        new_message: str,
    ) -> List[Dict[str, str]]:
        """
        Build the complete messages array for OpenAI.

        Args:
            system_prompt: The system-level instruction.
            history: Previous conversation messages.
            new_message: The new user message.

        Returns:
            Ordered list of messages for the API.
        """
        messages = [{"role": "system", "content": system_prompt}]

        # Truncate history if needed
        if len(history) > self.max_history:
            history = history[-self.max_history:]

        messages.extend(history)
        messages.append({"role": "user", "content": new_message})

        return messages
