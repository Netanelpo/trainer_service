def get_agent_name(action: str) -> str:
    if action == "SET_WORDS":
        return "EnglishWordsAgent"
    # if action == "LanguageChoiceAgent":
    #     return "EnglishWordsAgent"
    # elif action == "EnglishWordsAgent":
    #     return "FromEnglishTranslatorAgent"
    # elif action == "FromEnglishTranslatorAgent":
    #     return "ToEnglishTranslatorAgent"
    # elif action == "ToEnglishTranslatorAgent":
    #     return "ReviewerAgent"
    raise ValueError(f"Unknown action: {action}")
