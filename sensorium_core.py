# sensorium_core.py
from typing import Dict, Any, Optional, List

# Default value for unknown input
UNKNOWN_INPUT_PLACEHOLDER: str = "no_discernible_input"
# Confidence adjustment factors
BASE_CONFIDENCE: float = 0.50
CONFIDENCE_PER_ACTIVE_MODALITY: float = 0.10
MAX_CONFIDENCE: float = 0.95 # Cap confidence to avoid over-assurance from simple fusion

def integrate_sensorium(
    text_input: Optional[str] = None,
    audio_input: Optional[str] = None, # Assuming audio is pre-processed to text or features
    vision_input: Optional[str] = None # Assuming vision is pre-processed to text or features
) -> Dict[str, Any]:
    """
    Integrates multimodal inputs into a unified sensorium structure.
    This version assumes inputs are already processed into a somewhat comparable format (e.g., string descriptors).

    Args:
        text_input (Optional[str]): Processed text input.
        audio_input (Optional[str]): Processed audio input/features.
        vision_input (Optional[str]): Processed visual input/features.

    Returns:
        Dict[str, Any]: A dictionary representing the fused sensorium data, including:
            - "raw_fused" (str): The primary fused representation of the input.
            - "active_modalities" (List[str]): List of modalities that provided input.
            - "modality_weights" (Dict[str, float]): Calculated weights for each active modality.
            - "fusion_confidence" (float): Confidence score for the fused representation.
            - "detailed_inputs" (Dict[str, Optional[str]]): Original inputs provided.
    """

    modalities_data: Dict[str, Optional[str]] = {
        "text": text_input,
        "audio": audio_input,
        "vision": vision_input
    }

    active_modalities: List[str] = [k for k, v in modalities_data.items() if v is not None and v.strip() != ""]
    
    modality_weights: Dict[str, float] = {}
    if active_modalities:
        # Simple equal weighting, could be more sophisticated (e.g., based on reliability)
        weight_per_modality = round(1.0 / len(active_modalities), 3)
        modality_weights = {modality: weight_per_modality for modality in active_modalities}


    # Fusion strategy: Prioritize text, then audio, then vision if available.
    # This is a simplistic fusion; more advanced methods would involve feature-level fusion or weighted averaging.
    fused_representation: str = UNKNOWN_INPUT_PLACEHOLDER
    if text_input and text_input.strip():
        fused_representation = text_input
    elif audio_input and audio_input.strip(): # Assuming audio can be represented as a string
        fused_representation = f"[Audio] {audio_input}"
    elif vision_input and vision_input.strip(): # Assuming vision can be represented as a string
        fused_representation = f"[Vision] {vision_input}"
    
    # Calculate confidence: base + bonus per active modality, capped.
    num_active_modalities = len(active_modalities)
    confidence_score = BASE_CONFIDENCE + (num_active_modalities * CONFIDENCE_PER_ACTIVE_MODALITY)
    fusion_confidence = round(min(confidence_score, MAX_CONFIDENCE), 3)

    # If no active modalities, confidence should be very low.
    if not active_modalities:
        fusion_confidence = 0.1 # Minimal confidence for unknown input

    sensorium_output = {
        "raw_fused": fused_representation, # <--- ИЗМЕНЕНО ЗДЕСЬ (было "raw_fused_representation")
        "active_modalities": active_modalities,
        "modality_weights": modality_weights,
        "fusion_confidence": fusion_confidence,
        "detailed_inputs": modalities_data # Store the original inputs for traceability
    }

    return sensorium_output