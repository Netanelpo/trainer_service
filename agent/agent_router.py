def agent_route(stage: str) -> str:
    if stage == "LanguageChoiceAgent":
        return "EnglishWordsAgent"
        # return "LearningGoalAgent"
    elif stage == "EnglishWordsAgent":
        return "FromEnglishTranslatorAgent"
    elif stage == "FromEnglishTranslatorAgent":
        return "ToEnglishTranslatorAgent"
    elif stage == "ToEnglishTranslatorAgent":
        return "ReviewerAgent"
    raise ValueError(f"Unknown stage: {stage}")
