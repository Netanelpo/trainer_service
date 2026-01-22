import dataclasses
import random
from typing import List, Optional

from agents.run_context import RunContextWrapper
from agents.tool import function_tool


@dataclasses.dataclass
class AgentContext:
    """Context passed to the agent and instructions."""
    input_text: str
    action: str
    language: str
    words: List[str] = dataclasses.field(default_factory=list)
    remaining: List[str] = dataclasses.field(default_factory=list)
    next_word: Optional[str] = None
    done_training: Optional[bool] = None


@function_tool
def set_words(context: RunContextWrapper[AgentContext], words: List[str]) -> str:
    """
    Save the list of English words the student wants to learn.
    """
    print("set_words")
    cleaned_words = [str(w).strip().lower() for w in words if w]

    if not cleaned_words:
        return "Error: No valid words provided."

    # Update the context state so it's returned to the client
    context.context.words = cleaned_words
    context.context.remaining = cleaned_words

    return f"Successfully saved {len(cleaned_words)} words."


@function_tool
def pick_next_word(context: RunContextWrapper[AgentContext]) -> str:
    """
    Selects a random word from the existing word list in the context
    and removes it from the remaining list.
    """
    print("pick_next_word")
    current_words = context.context.remaining

    valid_words = [w for w in current_words if w]
    if not valid_words:
        return "Error: Word list is empty in the current context."

    selection = random.choice(valid_words)

    # Remove the chosen word from remaining (one occurrence)
    try:
        current_words.remove(selection)
    except ValueError:
        pass  # in case it's not found for some reason

    # Update state
    print(selection)
    context.context.next_word = selection
    return f"Next word selected: {selection}"


@function_tool
def done_training(context: RunContextWrapper[AgentContext]) -> str:
    """
    Marks the current learning session as finished.
    """
    print("done_training")
    context.context.done_training = True
    return "Training Finished"
