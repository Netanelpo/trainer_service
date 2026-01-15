def test_firestore():
    from firestore_functions import get_config_field
    model = get_config_field("agents", "model")
    assert model == 'gpt-5-mini'


def test_empty(client):
    resp = client.post("/", json={"input": "", "context": {}})

    body = resp.get_json()
    print('BODY', body)
    assert resp.status_code == 200
    assert resp.headers["Access-Control-Allow-Origin"] == "*"

    assert body["output"] == "Please choose your learning language."
    assert body["context"]["stage"] == "LanguageChoiceAgent"
