import cv2
import logging
import math
import os
import urllib.request
import mediapipe as mp
from core.models import ImageRecord
from core.config import AppConfig

logger = logging.getLogger(__name__)

# Ensure FaceLandmarker model is downloaded
model_path = 'face_landmarker.task'
if not os.path.exists(model_path):
    logger.info("Downloading MediaPipe Face Landmarker model...")
    url = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"
    try:
        urllib.request.urlretrieve(url, model_path)
    except Exception as e:
        logger.error(f"Failed to download Face Landmarker model: {e}")

try:
    BaseOptions = mp.tasks.BaseOptions
    FaceLandmarker = mp.tasks.vision.FaceLandmarker
    FaceLandmarkerOptions = mp.tasks.vision.FaceLandmarkerOptions
    VisionRunningMode = mp.tasks.vision.RunningMode
    
    options = FaceLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=model_path),
        running_mode=VisionRunningMode.IMAGE,
        num_faces=5,
        output_face_blendshapes=True
    )
    landmarker = FaceLandmarker.create_from_options(options)
except Exception as e:
    logger.error(f"Failed to initialize MediaPipe Face Landmarker: {e}")
    landmarker = None



def analyze_blendshapes(blendshapes_categories):
    scores = {c.category_name: c.score for c in blendshapes_categories}
    
    # Eye state
    blink_l = scores.get('eyeBlinkLeft', 0.0)
    blink_r = scores.get('eyeBlinkRight', 0.0)
    
    if blink_l > 0.6 and blink_r > 0.6:
        eye_state = "Both Eyes Closed"
        eye_score = (blink_l + blink_r) / 2
    elif blink_l > 0.6 or blink_r > 0.6:
        eye_state = "One Eye Closed"
        eye_score = max(blink_l, blink_r)
    elif blink_l > 0.2 or blink_r > 0.2:
        eye_state = "Mid Blink"
        eye_score = max(blink_l, blink_r)
    else:
        eye_state = "Open"
        eye_score = 1.0 - max(blink_l, blink_r)
        
    # Expression
    smile_l = scores.get('mouthSmileLeft', 0.0)
    smile_r = scores.get('mouthSmileRight', 0.0)
    jaw_open = scores.get('jawOpen', 0.0)
    
    smile_score = (smile_l + smile_r) / 2
    
    if smile_score > 0.5 and jaw_open > 0.3:
        expr_type = "Laughing"
        expr_conf = (smile_score + jaw_open) / 2
    elif smile_score > 0.4:
        expr_type = "Smile"
        expr_conf = smile_score
    elif jaw_open > 0.3:
        expr_type = "Mouth Open"
        expr_conf = jaw_open
    else:
        expr_type = "Neutral"
        expr_conf = 1.0 - max(smile_score, jaw_open)
        
    return eye_state, eye_score, expr_type, expr_conf

def process_face_eye(record: ImageRecord) -> ImageRecord:
    if not record.preview_path or not landmarker:
        return record
        
    try:
        img_h, img_w = record.preview_height, record.preview_width
        
        if hasattr(record, 'image_bgr') and record.image_bgr is not None:
            img_rgb = cv2.cvtColor(record.image_bgr, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_rgb)
        else:
            mp_image = mp.Image.create_from_file(record.preview_path)
        
        results = landmarker.detect(mp_image)
        
        record.face_count = 0
        record.face_boxes = []
        
        if results.face_landmarks:
            record.face_count = len(results.face_landmarks)
            record.number_of_faces = len(results.face_landmarks)
            
            best_area = 0.0
            best_box = None
            primary_face_idx = -1
            
            gray_img = record.image_gray if hasattr(record, 'image_gray') and record.image_gray is not None else cv2.imread(record.preview_path, cv2.IMREAD_GRAYSCALE)
            
            for idx, face_landmarks in enumerate(results.face_landmarks):
                x_min = min([lm.x for lm in face_landmarks]) * img_w
                y_min = min([lm.y for lm in face_landmarks]) * img_h
                x_max = max([lm.x for lm in face_landmarks]) * img_w
                y_max = max([lm.y for lm in face_landmarks]) * img_h
                
                padding_x = (x_max - x_min) * 0.1
                padding_y = (y_max - y_min) * 0.1
                x1 = max(0, int(x_min - padding_x))
                y1 = max(0, int(y_min - padding_y * 1.5))
                x2 = min(img_w, int(x_max + padding_x))
                y2 = min(img_h, int(y_max + padding_y * 0.5))
                
                area = (x2 - x1) * (y2 - y1)
                area_pct = (area / (img_w * img_h)) * 100 if img_w*img_h > 0 else 0
                
                landmarks_list = [{"x": lm.x, "y": lm.y, "z": lm.z} for lm in face_landmarks]
                
                eye_state, eye_score, expr_type, expr_conf = "Unknown", 0.0, "Unknown", 0.0
                if results.face_blendshapes and idx < len(results.face_blendshapes):
                    blendshapes = results.face_blendshapes[idx]
                    eye_state, eye_score, expr_type, expr_conf = analyze_blendshapes(blendshapes)
                
                record.face_boxes.append({
                    "x1": x1, "y1": y1, "x2": x2, "y2": y2,
                    "confidence": 0.99,
                    "area_pct": area_pct,
                    "ear": 0.0,
                    "landmarks": landmarks_list,
                    "eye_state": eye_state,
                    "eye_score": eye_score,
                    "expression_type": expr_type,
                    "expression_confidence": expr_conf
                })
                
                if area > best_area:
                    best_area = area
                    best_box = (x1, y1, x2, y2)
                    primary_face_idx = idx
                    
            record.face_confidence = 0.99
            record.primary_face_index = primary_face_idx
            record.largest_face_ratio = (best_area / (img_w * img_h)) if img_w*img_h > 0 else 0.0
            
            if primary_face_idx != -1:
                primary_face = record.face_boxes[primary_face_idx]
                record.eye_state = primary_face["eye_state"]
                record.eye_state_score = primary_face["eye_score"]
                record.expression_type = primary_face["expression_type"]
                record.expression_confidence = primary_face["expression_confidence"]
                
                # We can deduce Face Quality / Visibility broadly from box size
                # Since MediaPipe caught it, it's fairly visible. Let's make a simple heuristic.
                if record.largest_face_ratio > 0.05:
                    record.face_quality_score = 100.0
                    record.face_visibility_score = 100.0
                elif record.largest_face_ratio > 0.01:
                    record.face_quality_score = 80.0
                    record.face_visibility_score = 90.0
                else:
                    record.face_quality_score = 50.0
                    record.face_visibility_score = 60.0
            
            # Legacy EAR threshold logic removed.
                
            if best_box is not None and gray_img is not None:
                x1, y1, x2, y2 = best_box
                roi = gray_img[y1:y2, x1:x2]
                if roi.size > 0:
                    record.face_sharpness = float(cv2.Laplacian(roi, cv2.CV_64F).var())
                    
        else:
            record.face_confidence = 0.0
            
    except Exception as e:
        logger.error(f"Module 'FaceEyeAnalysis' failed on '{record.filename}'. Reason: {str(e)}. Action: Skipping face/eye analysis.")
        
    return record

def face_eye_analysis_module():
    def _module(record: ImageRecord) -> ImageRecord:
        return process_face_eye(record)
    _module.__name__ = "FaceEyeAnalysis"
    return _module

