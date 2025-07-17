import os
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
import odoorpc  # lightweight Odoo XML-RPC client

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class JobApplyPayload(BaseModel):
    job_id: int
    name: str
    email: str

@app.get("/")
def health():
    return {"status": "ok"}

@app.post("/upload-cv/")
async def upload_cv(file: UploadFile):
    content = await file.read()
    text = model.generate_content([
        "Extract structured candidate data (name, email, skills, experience years) from this CV:",
        {"mime_type": file.content_type, "data": content}
    ]).text
    return {"raw_text": text}

@app.post("/jobs/{job_id}/apply")
def apply(job_id: int, payload: JobApplyPayload):
    odoo = odoorpc.ODOO(host=os.getenv("ODOO_URL").replace("https://", ""),
                        protocol="jsonrpcs", port=443)
    odoo.login(os.getenv("ODOO_DB"),
               os.getenv("ODOO_USERNAME"),
               os.getenv("ODOO_PASSWORD"))
    applicant_id = odoo.env["hr.applicant"].create({
        "name": f"{payload.name} – {payload.email}",
        "job_id": job_id,
        "email_from": payload.email,
        "stage_id": odoo.env["hr.recruitment.stage"].search([("name", "=", "New")])[0]
    })
    return {"applicant_id": applicant_id}

@app.post("/workflow/start")
def start_workflow(job_id: int):
    # TODO: background job to scan & score all "New" applicants
    return {"msg": "Workflow started"}
