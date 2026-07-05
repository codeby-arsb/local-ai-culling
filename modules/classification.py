import math
import logging
from typing import List
from core.models import ImageRecord
from core.config import AppConfig

logger = logging.getLogger(__name__)

def calculate_confidence(classification: str, score: float, is_burst_safety_net: bool) -> float:
    if not AppConfig.get("modules.confidence_engine", False):
        return None
        
    midpoint_keep = AppConfig.get("confidence.midpoint_keep", 60.0)
    midpoint_reject = AppConfig.get("confidence.midpoint_reject", 40.0)
    steepness = AppConfig.get("confidence.steepness", 0.11)
    burst_cap = AppConfig.get("confidence.burst_cap", 55.0)
    
    if classification == "KEEP":
        distance = score - midpoint_keep
    elif classification == "REJECT":
        distance = midpoint_reject - score
    elif classification == "REVIEW":
        if is_burst_safety_net:
            distance = score - midpoint_keep
        else:
            distance = min(abs(score - midpoint_keep), abs(score - midpoint_reject))
    else:
        distance = 0
            
    conf = 1.0 / (1.0 + math.exp(-steepness * distance))
    
    if classification == "REVIEW" and is_burst_safety_net:
        conf = min(conf, burst_cap / 100.0)
        
    return round(conf * 100.0, 1)

def classify_records(records: List[ImageRecord]) -> List[ImageRecord]:
    """
    Evaluates absolute mathematical metrics and burst indicators to assign
    a KEEP, REVIEW, or REJECT status to each photo.
    """
    logger.info("Starting Phase 5B: Rule-Based Classification...")
    
    counts = {"KEEP": 0, "REVIEW": 0, "REJECT": 0}
    
    for r in records:
        # 1. Base Mathematical Score
        score = 0.0
        
        ss = r.subject_sharpness or 0.0
        score += min(ss, 150) * 0.3
        
        sv = r.subject_visibility_score or 0.0
        score += sv * 30
        
        fc = r.face_confidence or 0.0
        score += fc * 15
        
        fs = r.face_sharpness or 0.0
        score += min(fs, 100) * 0.1
        
        ln = r.luminance_noise or 0.0
        score -= ln * 3.0
        
        ue = r.underexposure_score or 0.0
        score -= min(ue, 50) * 0.2
        
        reasons = []
        
        # Expression Intelligence Penalty
        is_severe_eye_closure = False
        if AppConfig.get("modules.expression_intelligence", True):
            expr_penalty = 0.0
            
            # Eye State Penalty
            if r.eye_state == "Both Eyes Closed":
                expr_penalty += 15.0
            elif r.eye_state == "One Eye Closed":
                expr_penalty += 10.0
            elif r.eye_state == "Mid Blink":
                expr_penalty += 20.0
                
            # Expression Type Penalty
            if r.expression_type == "Unknown":
                expr_penalty += 2.0
            elif r.expression_type == "Mouth Open":
                # Mouth awkwardly open -> small penalty
                expr_penalty += 5.0
                
            # Face Visibility Penalty
            if r.face_visibility_score is not None:
                if r.face_visibility_score < 70.0:
                    expr_penalty += 10.0
                elif r.face_visibility_score < 90.0:
                    expr_penalty += 5.0
                    
            if r.face_count == 0 or r.face_count is None:
                # If expecting faces but none found, it's covered by face_confidence=0. 
                pass
                
            score -= expr_penalty
            if expr_penalty > 10.0:
                reasons.append("Poor Expression / Visibility")
                
            # Legacy Demotion Rule (keep for now, updated to use new eye_state)
            dominant_subject = (r.subject_count == 1 and (r.subject_area_percentage or 0.0) > 10.0)
            large_face = (r.largest_face_ratio or 0.0) > 0.02
            if dominant_subject and large_face and r.eye_state in ["Both Eyes Closed", "Mid Blink"]:
                is_severe_eye_closure = True
        
        # Editability Engine Penalty
        if r.editability_score is not None:
            # Excellent editability -> 0 penalty. Poor -> larger penalty.
            editability_deficit = max(0.0, 85.0 - r.editability_score)
            edit_penalty = (editability_deficit ** 1.2) * 0.15
            score -= edit_penalty
            if edit_penalty > 5.0 and r.recovery_failure_reason:
                reasons.append(f"Poor Editability ({r.recovery_failure_reason})")
        
        r.classification_score = score
        
        # 2. Rule-Based Explanations (Tags)
        if ss > 80: reasons.append("High Subject Sharpness")
        if ss < 25: reasons.append("Low Subject Sharpness")
        if sv > 0.6: reasons.append("Strong Subject Visibility")
        if sv < 0.2: reasons.append("Poor Subject Visibility")
        if ln > 4.0: reasons.append("Elevated Noise")
        if r.is_best_frame: reasons.append("Strongest Frame in Burst (or Standalone)")
        else: reasons.append("Non-Best Frame in Burst")
        
        # 3. Decision Matrix
        classification = "REVIEW" # Default fallback
        is_burst_safety_net = False
        
        # --- REJECT RULES ---
        if score < 40.0 or ss < 10.0:
            classification = "REJECT"
            
        # --- KEEP RULES ---
        elif score >= 60.0 and ss > 30.0:
            if r.is_best_frame:
                if is_severe_eye_closure:
                    classification = "REVIEW"
                    reasons.append("Demoted to REVIEW: Severe Eye Closure")
                else:
                    classification = "KEEP"
            else:
                # Strong score, but lost the burst battle -> REVIEW safety net
                classification = "REVIEW"
                is_burst_safety_net = True
                
        # Everything between 40 and 60 (or strong non-best) remains REVIEW
        
        r.classification = classification
        r.classification_reasons = reasons
        
        # 4. Confidence Engine
        r.confidence_score = calculate_confidence(classification, score, is_burst_safety_net)
        
        counts[classification] += 1
        
    logger.info(f"Classification complete. KEEP: {counts['KEEP']}, REVIEW: {counts['REVIEW']}, REJECT: {counts['REJECT']}")
    return records
