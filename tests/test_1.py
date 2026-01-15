def test_empty(client):
    resp = client.post("/", json={"input": "", "context": {}})

    body = resp.get_json()
    print('BODY', body)
    assert resp.status_code == 200
    assert resp.headers["Access-Control-Allow-Origin"] == "*"

    assert body["output"] == "Please choose your learning language."
    assert body["context"]["language"] is None
    assert body["context"]["stage"] == "LanguageChoiceAgent"
    assert body.get("next") is None


def test_hebrew(client):
    resp = client.post("/", json={"input": "hebrew", "context": {
        "stage": "LanguageChoiceAgent",
    }})

    body = resp.get_json()
    print('BODY', body)
    assert resp.status_code == 200
    assert resp.headers["Access-Control-Allow-Origin"] == "*"

    assert body["context"]["language"] == "Hebrew"
    assert body["context"]["stage"] == "LanguageChoiceAgent"
    assert body["next"] == True


def test_next(client):
    resp = client.post("/", json={"input": "",
                                  "next": True,
                                  "context": {
                                      "stage": "LanguageChoiceAgent",
                                      "language": "Hebrew",
                                  }})

    body = resp.get_json()
    print('BODY', body)
    assert resp.status_code == 200
    assert resp.headers["Access-Control-Allow-Origin"] == "*"

    assert body["context"]["language"] == "Hebrew"
    assert body["context"]["stage"] == "EnglishWordsAgent"
    assert body["next"] == False
