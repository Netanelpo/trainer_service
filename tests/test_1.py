def test_firestore():
    from firestore_functions import get_config_field
    model = get_config_field("agents", "model")
    assert model == 'gpt-5-mini'
