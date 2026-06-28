import pytest
from app.modules.context.validator import PromptValidator
from app.modules.logger.exceptions import PromptValidationError


class TestPromptValidator:
    @pytest.fixture
    def validator(self):
        return PromptValidator(max_tokens=500)

    def test_valid_prompt(self, validator):
        content = """
## Identidad y Bio
Soy un asistente.

## Límites
No digo cosas malas.

## Instrucciones Técnicas
Sé natural.
"""
        # Should not raise
        validator.validate(content)

    def test_empty_prompt(self, validator):
        with pytest.raises(PromptValidationError, match="empty"):
            validator.validate("")

    def test_missing_sections(self, validator):
        with pytest.raises(PromptValidationError, match="Missing"):
            validator.validate("Solo un mensaje simple sin secciones requeridas.")

    def test_too_long_prompt(self, validator):
        content = "## Identidad\n" + "a" * 5000  # Way too long
        with pytest.raises(PromptValidationError, match="too long"):
            validator.validate(content)

    def test_missing_identity(self, validator):
        content = "## Límites\nTodo bien.\n## Instrucciones Técnicas\nSé natural."
        with pytest.raises(PromptValidationError):
            validator.validate(content)
