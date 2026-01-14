def agent_route(stage: str) -> str:
    if stage == "LanguageChoiceAgent":
        return "LearningGoalAgent"
    raise ValueError(f"Unknown stage: {stage}")
