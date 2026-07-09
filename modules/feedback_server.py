import os
import json
import logging
from pathlib import Path
from datetime import datetime
import pandas as pd

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

logger = logging.getLogger(__name__)

app = FastAPI(title="Local AI Culling Feedback Server")

# We will mount static directories later inside the run_server function
# to ensure we use the correct dynamic output_dir path.

class FeedbackRecord(BaseModel):
    filename: str
    ai_classification: str
    photographer_decision: str
    override_direction: str = None
    reason_category: str = None
    additional_notes: str = None
    classification_score: float
    review_time_ms: float = 0.0

_OUTPUT_DIR = None

def get_severity(ai: str, human: str) -> str:
    if ai == human:
        return "None"
    if human == "SKIPPED":
        return "None"
    if (ai == "KEEP" and human == "REJECT") or (ai == "REJECT" and human == "KEEP"):
        return "Major"
    return "Minor"

@app.get("/api/images")
def get_images():
    global _OUTPUT_DIR
    if not _OUTPUT_DIR:
        return JSONResponse({"error": "Output dir not set"}, status_code=500)
        
    validation_csv = Path(_OUTPUT_DIR) / "manual_validation.csv"
    feedback_csv = Path(_OUTPUT_DIR) / "photographer_feedback.csv"
    
    if not validation_csv.exists():
        return JSONResponse({"error": "manual_validation.csv not found"}, status_code=404)
        
    df = pd.read_csv(validation_csv)
    
    # Filter out already reviewed
    reviewed_set = set()
    if feedback_csv.exists():
        feedback_df = pd.read_csv(feedback_csv)
        if "filename" in feedback_df.columns:
            reviewed_set = set(feedback_df["filename"].tolist())
            
    total_images = len(df)
    total_reviewed = len(reviewed_set)
            
    # Filter remaining
    df_remaining = df[~df["filename"].isin(reviewed_set)]
    
    # Convert to list of dicts safely handling NaNs
    import json
    images = json.loads(df_remaining.to_json(orient="records"))
    
    return {
        "images": images,
        "total": total_images,
        "completed": total_reviewed,
        "remaining": len(images)
    }

@app.post("/api/feedback")
def post_feedback(feedback: FeedbackRecord):
    global _OUTPUT_DIR
    feedback_csv = Path(_OUTPUT_DIR) / "photographer_feedback.csv"
    
    severity = get_severity(feedback.ai_classification, feedback.photographer_decision)
    
    record = {
        "filename": feedback.filename,
        "ai_classification": feedback.ai_classification,
        "photographer_decision": feedback.photographer_decision,
        "override_direction": feedback.override_direction or "",
        "reason_category": feedback.reason_category or "",
        "additional_notes": feedback.additional_notes or "",
        "classification_score": feedback.classification_score,
        "review_time_ms": feedback.review_time_ms,
        "disagreement_severity": severity,
        "timestamp": datetime.now().isoformat()
    }
    
    df_new = pd.DataFrame([record])
    if not feedback_csv.exists():
        df_new.to_csv(feedback_csv, index=False)
    else:
        try:
            df_existing = pd.read_csv(feedback_csv)
            if "override_direction" not in df_existing.columns:
                df_existing["override_direction"] = "Legacy"
            if "review_time_ms" not in df_existing.columns:
                df_existing["review_time_ms"] = 0.0
                
            df_combined = pd.concat([df_existing, df_new], ignore_index=True)
            df_combined.to_csv(feedback_csv, index=False)
        except Exception:
            # If CSV is totally broken due to previous failed append, rewrite cleanly
            df_new.to_csv(feedback_csv, mode='a', header=False, index=False)
        
    update_summary()
    return {"status": "success"}

def update_summary():
    global _OUTPUT_DIR
    feedback_csv = Path(_OUTPUT_DIR) / "photographer_feedback.csv"
    summary_csv = Path(_OUTPUT_DIR) / "feedback_summary.csv"
    
    if not feedback_csv.exists():
        return
        
    df = pd.read_csv(feedback_csv)
    
    total_reviewed = len(df)
    total_skipped = len(df[df["photographer_decision"] == "SKIPPED"])
    
    df_judged = df[df["photographer_decision"] != "SKIPPED"]
    
    major_disagreements = len(df_judged[df_judged["disagreement_severity"] == "Major"])
    minor_disagreements = len(df_judged[df_judged["disagreement_severity"] == "Minor"])
    agreements = len(df_judged[df_judged["disagreement_severity"] == "None"])
    
    agreement_rate = (agreements / len(df_judged) * 100) if len(df_judged) > 0 else 0.0
    
    # Calculate estimated time saved
    avg_review_time = df_judged["review_time_ms"].mean() if "review_time_ms" in df_judged.columns else 0.0
    agreed_rejects = len(df_judged[(df_judged["ai_classification"] == "REJECT") & (df_judged["photographer_decision"] == "REJECT")])
    time_saved_ms = agreed_rejects * avg_review_time
    time_saved_sec = time_saved_ms / 1000.0
    
    reason_counts = df_judged["reason_category"].value_counts().to_dict()
    
    # Save a simple flat summary
    summary_data = {
        "Total Reviewed": total_reviewed,
        "Total Skipped": total_skipped,
        "Agreement Rate (%)": round(agreement_rate, 2),
        "Major Disagreements": major_disagreements,
        "Minor Disagreements": minor_disagreements,
        "Estimated Time Saved (s)": round(time_saved_sec, 1)
    }
    
    for reason, count in reason_counts.items():
        if pd.isna(reason) or not str(reason).strip():
            continue
        summary_data[f"Reason: {reason}"] = count
        
    summary_df = pd.DataFrame([summary_data])
    summary_df.to_csv(summary_csv, index=False)

@app.get("/api/stats")
def get_stats():
    global _OUTPUT_DIR
    if not _OUTPUT_DIR:
        return JSONResponse({"error": "Output dir not set"}, status_code=500)
        
    summary_csv = Path(_OUTPUT_DIR) / "feedback_summary.csv"
    if not summary_csv.exists():
        return {"stats": {}}
        
    df = pd.read_csv(summary_csv)
    return {"stats": df.to_dict(orient="records")[0]}

@app.get("/api/inspector/{filename}")
def get_inspector_metadata(filename: str):
    global _OUTPUT_DIR
    if not _OUTPUT_DIR:
        return JSONResponse({"error": "Output dir not set"}, status_code=500)
        
    metadata_json = Path(_OUTPUT_DIR) / "metadata" / f"{filename}.json"
    if not metadata_json.exists():
        return JSONResponse({"error": "Metadata not found for this image"}, status_code=404)
        
    try:
        with open(metadata_json, "r") as f:
            data = json.load(f)
        return data
    except Exception as e:
        logger.error(f"Failed to read metadata for {filename}: {e}")
        return JSONResponse({"error": "Failed to read metadata"}, status_code=500)

@app.get("/api/image/{filename}")
def serve_image(filename: str):
    global _OUTPUT_DIR
    if not _OUTPUT_DIR:
        return JSONResponse({"error": "Output dir not set"}, status_code=500)
        
    # 1. Try lightweight previews
    preview_path = Path(_OUTPUT_DIR) / "previews" / filename
    if preview_path.exists():
        return FileResponse(preview_path)
        
    # 2. Try visual export folders (if --profile was used)
    for folder in ["keep_preview", "review_preview", "reject_preview"]:
        path = Path(_OUTPUT_DIR) / folder / filename
        if path.exists():
            return FileResponse(path)
            
    # 3. Try hardlinked final export folders
    for folder in ["KEEP", "REVIEW", "REJECT"]:
        path = Path(_OUTPUT_DIR) / folder / filename
        if path.exists():
            return FileResponse(path)
            
    return JSONResponse({"error": "Image not found"}, status_code=404)

@app.get("/")
def serve_index():
    # Serve index.html directly
    html_path = Path(__file__).parent.parent / "templates" / "index.html"
    if html_path.exists():
        return HTMLResponse(content=html_path.read_text(encoding='utf-8'))
    return HTMLResponse(content="<h1>Templates not found</h1>", status_code=404)

def run_server(output_dir: Path, port: int = 8000):
    global _OUTPUT_DIR
    _OUTPUT_DIR = output_dir
    
    # Mount previews statically from visual export folders
    for folder in ["keep_preview", "review_preview", "reject_preview"]:
        folder_path = output_dir / folder
        if folder_path.exists():
            app.mount(f"/{folder}", StaticFiles(directory=str(folder_path)), name=folder)
        else:
            logger.warning(f"Preview directory {folder_path} not found.")
        
    logger.info(f"Starting feedback server on http://localhost:{port}")
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="error")
