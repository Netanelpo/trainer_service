words = ['apple', 'banana', 'orange', 'kiwi', 'mango', 'pineapple']


def test_start(client):
    resp = client.post(
        "/",
        json={
            'action': 'EN_TO_TARGET_TRAINING',
            'language': 'Hebrew',
            'input': '',
            'words': words,
        },
    )

    body = resp.get_json()
    print("BODY", body)
    assert resp.status_code == 200
    assert resp.headers["Access-Control-Allow-Origin"] == "*"
    assert body['next_word'] in words


def test_wrong_answer(client):
    resp = client.post(
        "/",
        json={
            'action': 'EN_TO_TARGET_TRAINING',
            'language': 'Hebrew',
            'input': 'hi',
            'next_word': 'orange',
            'words': words,
        },
    )

    body = resp.get_json()
    print("BODY", body)
    assert resp.status_code == 200
    assert resp.headers["Access-Control-Allow-Origin"] == "*"
    assert body['next_word'] == 'orange'


def test_correct_answer(client):
    resp = client.post(
        "/",
        json={
            'action': 'EN_TO_TARGET_TRAINING',
            'language': 'Hebrew',
            'input': 'תפוז',
            'next_word': 'orange',
            'words': words,
        },
    )

    body = resp.get_json()
    print("BODY", body)
    assert resp.status_code == 200
    assert resp.headers["Access-Control-Allow-Origin"] == "*"
    assert body['next_word'] != 'orange'
    assert body['next_word'] in words

# def test_no_input(client):
#     resp = client.post(
#         "/",
#         json={
#             'action': 'SET_WORDS',
#             'language': 'Hebrew',
#         },
#     )
#
#     body = resp.get_json()
#     print("BODY", body)
#     assert resp.status_code == 400
#     assert resp.headers["Access-Control-Allow-Origin"] == "*"
#
#     assert body == {'error': "input is required."}
#
#
# def test_no_action(client):
#     resp = client.post(
#         "/",
#         json={
#             'input': 'hi',
#             'action': '',
#             'language': 'Hebrew',
#         },
#     )
#
#     body = resp.get_json()
#     print("BODY", body)
#     assert resp.status_code == 400
#     assert resp.headers["Access-Control-Allow-Origin"] == "*"
#
#     assert body == {'error': "action is required."}
#
#
# def test_no_language(client):
#     resp = client.post(
#         "/",
#         json={
#             'input': 'hi',
#             'action': 'SET_WORDS',
#             'language': '',
#         },
#     )
#
#     body = resp.get_json()
#     print("BODY", body)
#     assert resp.status_code == 400
#     assert resp.headers["Access-Control-Allow-Origin"] == "*"
#
#     assert body == {'error': "language is required."}
#
#
# def test_words_empty(client):
#     resp = client.post(
#         "/",
#         json={
#             'input': 'hi',
#             'action': 'SET_WORDS',
#             'language': 'Hebrew',
#         },
#     )
#
#     body = resp.get_json()
#     print("BODY", body)
#     assert resp.status_code == 200
#     assert resp.headers["Access-Control-Allow-Origin"] == "*"
#     assert body["output"]
#     assert not body.get("words")
#
#
# def test_words(client):
#     resp = client.post(
#         "/",
#         json={
#             'input': 'apple, sleep, go, dance',
#             'action': 'SET_WORDS',
#             'language': 'Hebrew',
#         },
#     )
#
#     body = resp.get_json()
#     print("BODY", body)
#     assert resp.status_code == 200
#     assert resp.headers["Access-Control-Allow-Origin"] == "*"
#     assert body["output"]
#     assert set(body["words"]) == {"apple", "sleep", "go", "dance"}
