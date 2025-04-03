from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from backend import PrescriptionBackend
from pydantic import BaseModel
import json
import uvicorn
import os

app = FastAPI()
backend = PrescriptionBackend()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    text: str

@app.post("/transcribe_stream")
async def transcribe_stream(audio: UploadFile = File(...)):
    try:
        result = await backend.process_transcription_request(audio) 
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat(request: ChatRequest = Body(...)): 
    try:
        response = await backend.process_chat_request(request.text)  
        if "error" in response:
            raise HTTPException(status_code=400, detail=response["error"])
        return response["response"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/save_prescription")
async def save_prescription(prescription: str = Form(...)):
    try:
        prescription_data = json.loads(prescription)
        result = await backend.save_prescription_data(prescription_data) 
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000)) 
    uvicorn.run(app, host="0.0.0.0", port=port)
