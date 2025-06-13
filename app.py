from fastapi import FastAPI, UploadFile, File, Form, HTTPException
import os
from google import genai
from dotenv import load_dotenv
from pathlib import Path
from typing import Optional

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

@app.get("/ping")
def ping():
    return {"message": "Server is running"}

@app.post("/validate-api-key")
def validate_api_key(api_key: str):
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-pro-preview-06-05",
            contents=["Hello How are you"]
        )
        if not response or not response.text:
            raise HTTPException(status_code=401, detail="Invalid API key")
        return {"valid": True, "message": "API key is valid"}
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid API key")

@app.post("/analyze-resume")
async def analyze_resume(
    file: UploadFile = File(...),
    job_title: str = Form(...),
    company: str = Form(...),
    api_key: str = Form(...)
):
    try:
        # Create upload directory if it doesn't exist
        save_folder = "uploaded_files"
        Path(save_folder).mkdir(parents=True, exist_ok=True)
        
        # Save the uploaded file
        save_path = Path(save_folder, file.filename)
        with open(save_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Initialize Gemini client with provided API key
        client = genai.Client(api_key=api_key)
        
        # Upload file to Gemini
        myfile = client.files.upload(file=str(save_path))
        
        # Compose job description prompt
        prompt = f"""
Analyze this resume:
Resume: {file.filename}
Job Title: {job_title}
Company: {company}

Rate it out of 10 and provide feedback in 5 lines
        """
        
        # Call Gemini model
        response = client.models.generate_content(
            model="gemini-2.5-pro-preview-06-05",
            contents=[prompt, myfile]
        )
        
        # Clean up: remove the uploaded file
        if save_path.exists():
            save_path.unlink()
            
        return {"response": response.text}
        
    except Exception as e:
        # Clean up in case of error
        if 'save_path' in locals() and save_path.exists():
            save_path.unlink()
        raise HTTPException(status_code=500, detail=str(e)) 
