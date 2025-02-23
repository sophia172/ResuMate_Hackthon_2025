from fastapi import FastAPI, HTTPException, Form, UploadFile, File, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict
import uvicorn
from datetime import datetime
import os

# Initialize FastAPI app
app = FastAPI(title="User Profile API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this to restrict allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Create storage directory if it doesn't exist
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

hr_agent = None

class ChatRequest(BaseModel):
    message: str

@app.post("/chat/")
async def chat_endpoint(request: ChatRequest) -> Dict[str, str]:
    try:
        user_message = request.message.strip()
        if not user_message:
            raise HTTPException(status_code=400, detail="Message cannot be empty")

        global hr_agent
        if hr_agent:
            return_response = hr_agent(user_message)
        else:
            return_response = "Please initialise your profile first by providing github username,LinkedIn profile link, and the job description url"

        # Example bot response (Replace with actual logic)
        # bot_response = f"🤖 Echo: {user_message}"
        return {"message": return_response}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")


@app.post("/chat/audio/")
async def process_audio(audio: UploadFile = File(...)):
    """
    Receives an uploaded audio file, transcribes it, and returns the text.
    """
    try:
        # Generate timestamped filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_extension = os.path.splitext(audio.filename)[-1] or ".webm"
        filename = f"{timestamp}_recording{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, filename)

        # Save the file
        with open(file_path, "wb") as buffer:
            buffer.write(await audio.read())

        # Read the saved file to return it as response
        with open(file_path, "rb") as audio_file:
            audio_data = audio_file.read()

        # return {"message": "Audio saved successfully",
        #         "file_path": file_path,
        #         "audioResponse":audio,
        #         "content-type":"audio/webm"}

        return Response(content=audio_data, media_type="audio/mpeg")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing audio: {str(e)}")


@app.get("/")
async def root():
    return {"message": "Welcome to the User Profile API"}


@app.post("/user-profile/")
async def user_profile(
        github_link: str = Form(...),
        linkedin_link: str = Form(...),
        resume: Optional[UploadFile] = File(None),
        job_description: str = Form(...)

):
    try:
        # Create user profile record
        user_profile = {
            "github_link": github_link,
            "linkedin_link": linkedin_link,
            "job_description": job_description,
            "resume_path": None
        }

        # Handle resume upload if provided
        if resume:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            resume_filename = f"{timestamp}_resume_{resume.filename}"
            resume_filepath = os.path.join(UPLOAD_DIR, resume_filename)

            with open(resume_filepath, "wb") as buffer:
                content = await resume.read()
                buffer.write(content)

            user_profile["resume_path"] = resume_filepath

        # global hr_agent
        # hr_agent = HrAgent(user_profile=user_profile)
        # response = hr_agent("Generate CV")
        # print("response: ", response)
        cv_response = "John Doe\nSoftware Engineer\n123 Main Street\nCity, State 12345\n\nPROFESSIONAL SUMMARY\n-------------------\nDetail-oriented software engineer with 5 years of experience\n\nWORK EXPERIENCE\n--------------\nSenior Developer | Tech Company\n2020 - Present\n• Led development team\n• Managed projects\n\nEDUCATION\n---------\nBS Computer Science\nState University, 2019"
        return {
            "message": "CV created successfully",
            "cv": cv_response
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)