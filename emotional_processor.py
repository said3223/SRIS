# emotional_processor.py
import logging
from typing import Dict, Any

from logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

def evaluate_emotion(perception_struct: Dict[str, Any], chosen_hypothesis: str) -> Dict[str, Any]:
    """
    Evaluates or determines an emotional state based on perception and chosen hypothesis.

    Args:
        perception_struct: The structured perception data. This might include
                           sentiment, recognized entities, themes, etc.
                           (Output from perception_analysis.py)
        chosen_hypothesis: The hypothesis that the system has currently chosen
                           as most plausible or relevant.

    Returns:
        A dictionary representing the agent's current emotional state.
        Example: {"valence": 0.0, "arousal": 0.0, "dominant_emotion": "neutral"}
                 Valence: positive/negative (-1.0 to 1.0)
                 Arousal: intensity/energy (0.0 to 1.0)
    """
    logger.info("\n[EMOTIONAL PROCESSOR INPUT]")
    logger.info(f"Perception Sentiment: {perception_struct.get('sentiment', 'unknown')}")
    logger.info(f"Chosen Hypothesis: {chosen_hypothesis[:100]}...")

    valence = 0.0  # Default to neutral
    arousal = 0.1  # Default to low arousal
    dominant_emotion = "neutral"

    # Simple rule-based emotional evaluation (can be greatly expanded)
    perception_sentiment = perception_struct.get('sentiment', 'neutral').lower()
    perception_intent = perception_struct.get('intent', 'unknown').lower()

    if "threat" in chosen_hypothesis.lower() or "danger" in chosen_hypothesis.lower():
        dominant_emotion = "fear"
        valence = -0.7
        arousal = 0.8
    elif perception_sentiment == "negative":
        dominant_emotion = "sadness" # or "frustration" depending on other cues
        valence = -0.5
        arousal = 0.4
        if "help" in perception_intent or "warn" in perception_intent:
            dominant_emotion = "concern"
            valence = -0.3
            arousal = 0.6
    elif perception_sentiment == "positive":
        dominant_emotion = "joy" # or "contentment"
        valence = 0.6
        arousal = 0.5
        if "congratulations" in chosen_hypothesis.lower() or "success" in chosen_hypothesis.lower():
            dominant_emotion = "excitement"
            valence = 0.8
            arousal = 0.7
    elif "curiosity" in chosen_hypothesis.lower() or "explore" in chosen_hypothesis.lower():
        dominant_emotion = "curiosity"
        valence = 0.3
        arousal = 0.6

    # You could integrate an LLM here as well to infer emotion from text,
    # or use more sophisticated models based on the perception_struct.
    # For example:
    # prompt = f"Given the perception with sentiment '{perception_sentiment}' and the hypothesis '{chosen_hypothesis}',
    # what is the likely emotional state (valence, arousal, dominant emotion label)?"
    # llm_response = query_ollama_mistral(prompt)
    # ... then parse llm_response ...

    emotion_state = {
        "valence": round(valence, 2),
        "arousal": round(arousal, 2),
        "dominant_emotion": dominant_emotion,
        "details": f"Based on sentiment: {perception_sentiment} and hypothesis content."
    }

    logger.info(f"Evaluated Emotion State: {emotion_state}")
    return emotion_state

# Example usage (can be uncommented for quick testing of this module)
# if __name__ == '__main__':
#     sample_perception_positive = {
#         "sentiment": "positive",
#         "intent": "inform",
#         "summary": "User is happy about the good news."
#     }
#     sample_hypothesis_positive = "The project was a great success and everyone is celebrating."
#     emotion1 = evaluate_emotion(sample_perception_positive, sample_hypothesis_positive)
#     print(f"Emotion 1: {emotion1}")

#     sample_perception_negative_threat = {
#         "sentiment": "negative",
#         "intent": "warn",
#         "summary": "User reports a dangerous situation."
#     }
#     sample_hypothesis_negative_threat = "There is an immediate threat to safety; evacuation required."
#     emotion2 = evaluate_emotion(sample_perception_negative_threat, sample_hypothesis_negative_threat)
#     print(f"Emotion 2: {emotion2}")

#     sample_perception_neutral = {
#         "sentiment": "neutral",
#         "intent": "describe",
#         "summary": "The object is blue."
#     }
#     sample_hypothesis_neutral = "The object under observation is blue and has a metallic sheen."
#     emotion3 = evaluate_emotion(sample_perception_neutral, sample_hypothesis_neutral)
#     print(f"Emotion 3: {emotion3}")