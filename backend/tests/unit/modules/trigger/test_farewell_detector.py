import pytest
from app.modules.trigger.farewell_detector import is_farewell


class TestFarewellDetector:
    @pytest.mark.parametrize("text", [
        "adios",
        "adiós",
        "hasta luego",
        "hasta mañana",
        "nos vemos",
        "chao",
        "chau",
        "me voy",
        "buenas noches",
        "que descanses",
        "cuídate",
        "cuidate",
        "bye",
        "goodbye",
        "see you",
        "take care",
        "me voy a dormir",
        "tengo que irme",
    ])
    def test_farewell_keywords(self, text):
        assert is_farewell(text) is True

    @pytest.mark.parametrize("text", [
        "hola como estas",
        "no digo adios todavia",
        "adiosfera",
        "me gusta la canción",
        "que tal",
        "buenos días",
        "",
    ])
    def test_not_farewell(self, text):
        assert is_farewell(text) is False

    def test_empty_string(self):
        assert is_farewell("") is False

    def test_none(self):
        assert is_farewell(None) is False

    def test_case_insensitive(self):
        assert is_farewell("ADIOS") is True
        assert is_farewell("ByE") is True

    def test_with_punctuation(self):
        assert is_farewell("adios!") is True
        assert is_farewell("hasta luego...") is True

    def test_with_surrounding_text(self):
        assert is_farewell("bueno, nos vemos luego") is True
        assert is_farewell("me voy a comer, chao") is True
