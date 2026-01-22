

def test_start(client):
    words = ['apple', 'banana', 'orange', 'kiwi', 'mango', 'pineapple']
    resp = client.post(
        "/",
        json={
            'action': 'EN_TO_TARGET_START_TRAINING',
            'language': 'Hebrew',
            'input': '',
            'words': words,
            'remaining': words,
        },
    )

    body = resp.get_json()
    print("BODY", body)
    assert resp.status_code == 200
    assert resp.headers["Access-Control-Allow-Origin"] == "*"

    assert body['next_word'] in words
    assert body['next_word'] in body['output']
    assert body['words'] == words
    words.remove(body['next_word'])
    assert body['remaining'] == words
    assert body.get('done_training') is None

def test_wrong_answer(client):
    words = ['apple', 'banana', 'orange', 'kiwi', 'mango', 'pineapple']
    resp = client.post(
        "/",
        json={
            'action': 'EN_TO_TARGET_TRAINING',
            'language': 'Hebrew',
            'input': 'hi',
            'next_word': 'orange',
            'words': words,
            'remaining': words,
        },
    )

    body = resp.get_json()
    print("BODY", body)
    assert resp.status_code == 200
    assert resp.headers["Access-Control-Allow-Origin"] == "*"

    assert body['next_word'] == 'orange'
    assert 'orange' in body['output']
    assert body['words'] == words
    assert body['remaining'] == words
    assert body.get('done_training') is None


def test_correct_answer(client):
    words = ['apple', 'banana', 'orange', 'kiwi', 'mango', 'pineapple']
    resp = client.post(
        "/",
        json={
            'action': 'EN_TO_TARGET_TRAINING',
            'language': 'Hebrew',
            'input': 'תות',
            'next_word': 'strawberry',
            'words': words,
            'remaining': words,
        },
    )

    body = resp.get_json()
    print("BODY", body)
    assert resp.status_code == 200
    assert resp.headers["Access-Control-Allow-Origin"] == "*"

    assert body['next_word'] != 'strawberry'
    assert body['next_word'] in words
    assert body['next_word'] in body['output']
    assert body['words'] == words
    words.remove(body['next_word'])
    assert body['remaining'] == words
    assert body.get('done_training') is None


def test_last_wrong_answer(client):
    words = ['apple', 'banana', 'orange', 'kiwi', 'mango', 'pineapple']
    resp = client.post(
        "/",
        json={
            'action': 'EN_TO_TARGET_LAST_QUESTION',
            'language': 'Hebrew',
            'input': 'hi',
            'next_word': 'strawberry',
            'words': words,
            'remaining': words,
        },
    )

    body = resp.get_json()
    print("BODY", body)
    assert resp.status_code == 200
    assert resp.headers["Access-Control-Allow-Origin"] == "*"

    assert body['next_word'] == 'strawberry'
    assert 'strawberry' in body['output']
    assert body['words'] == words
    assert body['remaining'] == words
    assert body.get('done_training') is None


def test_last_correct_answer(client):
    words = ['apple', 'banana', 'orange', 'kiwi', 'mango', 'pineapple']
    resp = client.post(
        "/",
        json={
            'action': 'EN_TO_TARGET_LAST_QUESTION',
            'language': 'Hebrew',
            'input': 'תות',
            'next_word': 'strawberry',
            'words': words,
            'remaining': words,
        },
    )

    body = resp.get_json()
    print("BODY", body)
    assert resp.status_code == 200
    assert resp.headers["Access-Control-Allow-Origin"] == "*"

    assert body['next_word'] == 'strawberry'
    assert body['words'] == words
    assert body['remaining'] == words
    assert body['done_training'] == True
