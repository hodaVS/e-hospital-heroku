import os
from openai import AsyncOpenAI  
import json
import logging
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from dotenv import load_dotenv


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()


class DiagnosisInformation(BaseModel):
    Diagnosis: Optional[str] = None
    Medicine: Optional[str] = None

class MedicationDetails(BaseModel):
    Dose: Optional[str] = None
    DoseUnit: Optional[str] = None
    DoseRoute: Optional[str] = None
    Frequency: Optional[str] = None
    FrequencyDuration: Optional[str] = None
    FrequencyUnit: Optional[str] = None
    Quantity: Optional[str] = None
    QuantityUnit: Optional[str] = None
    Refill: Optional[str] = None
    Pharmacy: Optional[str] = None

class Prescription(BaseModel):
    DiagnosisInformation: DiagnosisInformation
    MedicationDetails: MedicationDetails
    Description: Optional[str] = None

class PrescriptionResponse(BaseModel):
    Prescriptions: List[Prescription]

class PrescriptionBackend:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.system_prompt = """You are a helpful assistant that generates prescriptions. Always return the prescription in the following JSON format: (Warn doctor in Description if you suspect any drug conflicts). If any information is missing, use 'None' as the value for that field.
        {
            "Prescriptions": [
                {
                    "DiagnosisInformation": { "Diagnosis": "<diagnosis>", "Medicine": "<medicine>" },
                    "MedicationDetails": {
                        "Dose": "<dose>",
                        "DoseUnit": "<dose unit>",
                        "DoseRoute": "<dose route>",
                        "Frequency": "<frequency>",
                        "FrequencyDuration": "<frequency duration>",
                        "FrequencyUnit": "<frequency unit>",
                        "Quantity": "<quantity>",
                        "QuantityUnit": "<quantity unit>",
                        "Refill": "<refill>",
                        "Pharmacy": "<pharmacy>"
                    },
                    "Description": "<description>"
                }
            ]
        }"""

    async def transcribe_audio(self, file_path: str) -> str:
        try:
            with open(file_path, "rb") as audio_file:
                transcript = await self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
            return transcript.text
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            raise

    async def generate_prescription(self, user_input: str) -> PrescriptionResponse:
        try:
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_input}
            ]
    
            completion = await self.client.chat.completions.create(
                model="gpt-4",  
                messages=messages,
                max_tokens=500,
                temperature=0.1
            )
    
            response_content = completion.choices[0].message.content
            logger.info(f"Raw OpenAI response: {response_content}")  
            if isinstance(response_content, str):

                response_content = response_content.replace('1-2', '"1-2"')  #
                prescription_data = json.loads(response_content)
            else:
                prescription_data = response_content
    
            return self._validate_prescription(prescription_data)
    
        except Exception as e:
            logger.error(f"Prescription generation failed: {str(e)}")
            return self._get_default_response()

    def _validate_prescription(self, data: Dict[str, Any]) -> PrescriptionResponse:
        """Ensure the prescription has all required fields with defaults"""
        if "Prescriptions" not in data:
            data["Prescriptions"] = []

        for prescription in data["Prescriptions"]:
            prescription.setdefault("DiagnosisInformation", {})
            prescription.setdefault("MedicationDetails", {})
            prescription.setdefault("Description", None)

         
            for field in MedicationDetails.__fields__:
                prescription["MedicationDetails"].setdefault(field, None)

        return PrescriptionResponse(**data)

    def _get_default_response(self) -> PrescriptionResponse:
        """Return a safe default response on failure"""
        return PrescriptionResponse(
            Prescriptions=[
                Prescription(
                    DiagnosisInformation=DiagnosisInformation(),
                    MedicationDetails=MedicationDetails(),
                    Description="Please try again with proper prescription content."
                )
            ]
        )

    async def process_transcription_request(self, audio_file) -> Dict[str, Any]:
        logs = []
        try:

            temp_path = "temp_audio.wav"
            with open(temp_path, "wb") as buffer:
                buffer.write(await audio_file.read())
            logs.append("Audio file saved temporarily")

      
            user_input = await self.transcribe_audio(temp_path)
            logs.append(f"Transcribed text: {user_input}")

      
            prescription = await self.generate_prescription(user_input)
            logs.append("Prescription generated successfully")

         
            os.remove(temp_path)
            logs.append("Temporary file removed")

            return {
                "response": prescription.dict(),
                "transcript": user_input,
                "logs": logs
            }

        except Exception as e:
            logger.error(f"Audio processing failed: {str(e)}")
            return {
                "error": "Audio processing failed",
                "details": str(e),
                "logs": logs
            }

    async def process_chat_request(self, user_input: str) -> Dict[str, Any]:
        if not user_input:
            return {"error": "No text provided"}
        try:
            prescription = await self.generate_prescription(user_input)
            return {"response": prescription.dict()}
        except Exception as e:
            logger.error(f"Chat processing failed: {str(e)}")
            return {"response": self._get_default_response().dict()}

    async def save_prescription_data(self, prescription_data: Dict[str, Any]) -> Dict[str, Any]:
        if not prescription_data or 'prescription' not in prescription_data:
            logger.error("No prescription data provided")
            return {"error": "No prescription data provided"}

        try:
            save_file = "/data/prescriptions_dataset.json" if os.getenv("RENDER") else "prescriptions_dataset.json"

            prescriptions = []
            if os.path.exists(save_file):
                with open(save_file, 'r') as f:
                    try:
                        prescriptions = json.load(f)
                    except json.JSONDecodeError:
                        prescriptions = []


            from datetime import datetime
            prescription_entry = {
                "prescription": prescription_data['prescription'],
                "timestamp": datetime.now().isoformat()
            }
            prescriptions.append(prescription_entry)


            with open(save_file, 'w') as f:
                json.dump(prescriptions, f, indent=2)

            logger.info("Prescription saved successfully")
            return {"message": "Prescription saved successfully"}

        except Exception as e:
            logger.error(f"Failed to save prescription: {str(e)}")
            return {"error": "Failed to save prescription", "details": str(e)}
