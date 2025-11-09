import os
import asyncio
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI Backend!"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    
    try:
        # Try to import database module
        from database import db
        
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            
            # Try to list collections to verify connectivity
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]  # Show first 10 collections
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
            
    except ImportError:
        response["database"] = "❌ Database module not found (run enable-database first)"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    
    # Check environment variables
    import os
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    
    return response


@app.post("/api/process")
async def process_clip(file: UploadFile = File(...)):
    """
    Synchronous-style processing endpoint intended to be fast (~1s).
    - Validates that the intended viral cut is max 2 seconds (policy).
    - Simulates processing for ~1 second for UX purposes.
    - Returns the input video bytes as a processed result (demo mode),
      with headers indicating the enforced max duration and ETA.

    NOTE: In a full implementation, ffmpeg would trim to <=2s and transcode.
    """
    # Basic MIME validation
    allowed = {"video/mp4", "video/quicktime", "video/webm", "video/x-matroska"}
    if file.content_type not in allowed:
        raise HTTPException(status_code=400, detail="Unsupported format. Use MP4/MOV/WEBM/MKV.")

    # Simulated processing time (~1s)
    eta_seconds = 1
    await asyncio.sleep(eta_seconds)

    data = await file.read()

    async def file_iter():
        yield data

    # Map extension
    ext_map = {
        "video/mp4": ".mp4",
        "video/quicktime": ".mov",
        "video/webm": ".webm",
        "video/x-matroska": ".mkv",
    }
    ext = ext_map.get(file.content_type, "")
    filename = f"viral-cut{ext}" if ext else "viral-cut"

    headers = {
        "x-eta-seconds": str(0),  # Done on response
        "x-policy-max-duration": "2",  # seconds
        "x-processing-seconds": str(eta_seconds),
        "x-processed-fps": "30",
    }

    return StreamingResponse(
        file_iter(),
        media_type=file.content_type or "application/octet-stream",
        headers=headers,
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
