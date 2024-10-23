# server.py
from fastapi import FastAPI, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import shutil
import os
from typing import Optional
from main import process_audio, parse_instructions  # importing from your existing script

app = FastAPI()

# Enable CORS for your React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Update with your React app's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create temporary directory for uploads if it doesn't exist
os.makedirs("temp", exist_ok=True)

@app.post("/process-audio")
async def process_audio_endpoint(
    file: UploadFile,
    instructions: Optional[str] = Form(None)
):
    try:
        # Save the uploaded file temporarily
        temp_path = f"temp/{file.filename}"
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Parse instructions and process audio
        operations = parse_instructions(instructions) if instructions else None
        process_audio(temp_path, operations)
        
        # Get the most recent processed file
        processed_dir = 'processed'
        processed_files = [f for f in os.listdir(processed_dir) if f.endswith('.mp3')]
        if not processed_files:
            return {"error": "No processed file found"}
            
        latest_file = max([os.path.join(processed_dir, f) for f in processed_files], 
                         key=os.path.getctime)
        
        # Return the processed file
        return FileResponse(
            latest_file,
            media_type='audio/mpeg',
            filename=os.path.basename(latest_file)
        )
        
    except Exception as e:
        return {"error": str(e)}
    
    finally:
        # Cleanup temporary file
        if os.path.exists(temp_path):
            os.remove(temp_path)

# Optional: endpoint to check if server is running
@app.get("/health")
async def health_check():
    return {"status": "ok"}