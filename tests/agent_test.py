import os
import pytest
from dotenv import load_dotenv
load_dotenv()

import agent

pytestmark = pytest.mark.asyncio


@pytest.fixture(scope="session", autouse=True)
def require_api_key():
    """
    Fail fast if API key is missing.
    """
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY is not set")


async def test_extracts_english_words_basic():
    text = "Hello, World! 123"

    result = await agent.run_agent_once(text)

    assert result == ["hello", "world"]


async def test_removes_numbers_and_punctuation():
    text = "This!!! is 99% a testcase."

    result = await agent.run_agent_once(text)

    assert result == ["this", "is", "a", "testcase"]


async def test_ignores_non_english_words():
    text = "Hello שלום привет world"

    result = await agent.run_agent_once(text)

    assert result == ["hello", "world"]


async def test_lowercases_all_words():
    text = "MiXeD CaSe WORDS"

    result = await agent.run_agent_once(text)

    assert result == ["mixed", "case", "words"]


async def test_memory_is_preserved_between_calls():
    """
    Ensures previous_response_id is used
    (we can't see it directly, but this verifies no crash
    and stable continuation behavior).
    """

    first = await agent.run_agent_once("Hello World")
    second = await agent.run_agent_once("Again!")

    assert first == ["hello", "world"]
    assert second == ["again"]


async def test_empty_or_symbol_only_input():
    text = "!!! 123 ###"

    result = await agent.run_agent_once(text)

    assert result == []


async def test_longer_sentence():
    text = """
    This is a longer sentence, with commas, dots...
    and NEWLINES, plus numbers 42 and symbols $#@!
    """

    result = await agent.run_agent_once(text)

    assert result == [
        "this",
        "is",
        "a",
        "longer",
        "sentence",
        "with",
        "commas",
        "dots",
        "and",
        "newlines",
        "plus",
        "numbers",
        "and",
        "symbols",
    ]
