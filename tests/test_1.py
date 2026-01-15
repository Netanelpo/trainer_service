def test_initial_load(client):
    """
    1) Initial load

    Given no context
    When client posts {"input":"", "context":{}}
    Then response is 200 + CORS header
    And context.stage == "LanguageChoiceAgent"
    And context.language is None
    And next is not present / not true
    """
    resp = client.post("/", json={"input": "", "context": {}})

    body = resp.get_json()
    print("BODY", body)
    assert resp.status_code == 200
    assert resp.headers["Access-Control-Allow-Origin"] == "*"

    assert body["output"] == "Please choose your learning language."
    assert body["context"]["language"] is None
    assert body["context"]["stage"] == "LanguageChoiceAgent"
    assert body.get("next") is None


def test_choose_language_enables_next(client):
    """
    2) Choose language -> Next enabled

    Given LanguageChoiceAgent and language not chosen
    When client posts {"input":"Hebrew", "context":{"stage":"LanguageChoiceAgent","language":None}}
    Then context.language == "Hebrew"
    And next == True
    """
    resp = client.post(
        "/",
        json={"input": "Hebrew", "context": {"stage": "LanguageChoiceAgent", "language": None}},
    )

    body = resp.get_json()
    print("BODY", body)
    assert resp.status_code == 200
    assert resp.headers["Access-Control-Allow-Origin"] == "*"

    assert body["context"]["stage"] == "LanguageChoiceAgent"
    assert body["context"]["language"] == "Hebrew"
    assert body.get("next") is True
    assert isinstance(body["output"], str)


def test_next_from_language_choice_moves_to_english_words_agent(client):
    """
    3) Clicking Next -> moves to EnglishWordsAgent

    Given language already chosen
    When client posts {"input":"", "context":{"stage":"LanguageChoiceAgent","language":"Hebrew"}, "next":true}
    Then context.stage == "EnglishWordsAgent"
    And next is not true (disabled until words are provided)
    """
    resp = client.post(
        "/",
        json={
            "input": "",
            "context": {"stage": "LanguageChoiceAgent", "language": "Hebrew"},
            "next": True,
        },
    )

    body = resp.get_json()
    print("BODY", body)
    assert resp.status_code == 200
    assert resp.headers["Access-Control-Allow-Origin"] == "*"

    assert body["context"]["stage"] == "EnglishWordsAgent"
    assert body.get("next") is not True
    assert isinstance(body["output"], str)


def test_english_words_agent_requires_explicit_words(client):
    """
    4) EnglishWordsAgent: user didn't type explicit words -> Next disabled

    Given EnglishWordsAgent
    When client posts a topic/description instead of a word list
    Then stage stays EnglishWordsAgent
    And next is not true
    """
    resp = client.post(
        "/",
        json={
            "input": "I want to learn business words",
            "context": {"stage": "EnglishWordsAgent", "language": "Hebrew"},
        },
    )

    body = resp.get_json()
    print("BODY", body)
    assert resp.status_code == 200
    assert resp.headers["Access-Control-Allow-Origin"] == "*"

    assert body["context"]["stage"] == "EnglishWordsAgent"
    assert body.get("next") is not True
    assert isinstance(body["output"], str)
    assert len(body["output"]) > 0


def test_english_words_agent_accepts_word_list_enables_next(client):
    """
    5) EnglishWordsAgent: explicit word list -> Next enabled

    Given EnglishWordsAgent
    When client posts "engineer, brave"
    Then context.words contains the extracted lowercase words
    And next == True
    """
    resp = client.post(
        "/",
        json={
            "input": "engineer, brave",
            "context": {"stage": "EnglishWordsAgent", "language": "Hebrew"},
        },
    )

    body = resp.get_json()
    print("BODY", body)
    assert resp.status_code == 200
    assert resp.headers["Access-Control-Allow-Origin"] == "*"

    assert body["context"]["stage"] == "EnglishWordsAgent"
    assert body.get("next") is True

    words = body["context"].get("words")
    assert isinstance(words, list)
    assert "engineer" in words
    assert "brave" in words
    assert all(isinstance(w, str) and w == w.lower() for w in words)


def test_next_starts_training_sets_next_word(client):
    """
    6) Clicking Next after words -> starts FromEnglishTranslatorAgent and sets next_word

    Given EnglishWordsAgent with words already stored in context
    When client posts {"next":true}
    Then stage becomes FromEnglishTranslatorAgent
    And context.next_word exists and is one of context.words
    And output includes that English word
    """
    resp = client.post(
        "/",
        json={
            "input": "",
            "context": {
                "stage": "EnglishWordsAgent",
                "language": "Hebrew",
                "words": ["engineer", "brave"],
            },
            "next": True,
        },
    )

    body = resp.get_json()
    print("BODY", body)
    assert resp.status_code == 200
    assert resp.headers["Access-Control-Allow-Origin"] == "*"

    assert body["context"]["stage"] == "FromEnglishTranslatorAgent"

    asked = body["context"].get("next_word")
    assert isinstance(asked, str)
    assert asked in body["context"]["words"]
    assert asked in body["output"]


def test_from_english_translator_idontknow_keeps_same_next_word(client):
    """
    7) FromEnglishTranslatorAgent: "לא יודע" keeps the same next_word and re-asks it

    Given FromEnglishTranslatorAgent with next_word == "engineer"
    When client posts "לא יודע"
    Then next_word remains "engineer"
    And stage stays FromEnglishTranslatorAgent
    And output includes "engineer"
    """
    resp = client.post(
        "/",
        json={
            "input": "לא יודע",
            "context": {
                "stage": "FromEnglishTranslatorAgent",
                "language": "Hebrew",
                "words": ["engineer", "brave"],
                "next_word": "engineer",
            },
        },
    )

    body = resp.get_json()
    print("BODY", body)
    assert resp.status_code == 200
    assert resp.headers["Access-Control-Allow-Origin"] == "*"

    assert body["context"]["stage"] == "FromEnglishTranslatorAgent"
    assert body["context"].get("next_word") == "engineer"
    assert "engineer" in body["output"]


def test_restart_with_full_context_resets_to_language_choice(client):
    """
    8) Restart (server-side safety)

    Given the client sends a full (later-stage) context
    When client posts {"input":"", "context": <full_context>}
    Then response resets to LanguageChoiceAgent
    And context.language is None
    And next is not present / not true
    """
    resp = client.post(
        "/",
        json={"input": "",
              "context": {
                  "stage": "FromEnglishTranslatorAgent",
                  "language": "Hebrew",
                  "words": ["engineer", "brave"],
                  "next_word": "engineer",
              }})

    body = resp.get_json()
    print("BODY", body)
    assert resp.status_code == 200
    assert resp.headers["Access-Control-Allow-Origin"] == "*"

    assert body["output"] == "Please choose your learning language."
    assert body["context"]["stage"] == "LanguageChoiceAgent"
    assert body["context"]["language"] is None
    assert body.get("next") is None
