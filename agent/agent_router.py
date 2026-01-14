def agent_route(stage: str) -> str:
    if stage == "LanguageChoiceAgent":
        return "EnglishWordsAgent"
        # return "LearningGoalAgent"
    raise ValueError(f"Unknown stage: {stage}")
