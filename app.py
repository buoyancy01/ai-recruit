import os, uvicorn
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import google.generativeai as genai
import odoorpc

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "*")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health():
    return {"status": "ok"}

@app.post("/upload-cv/")
async def upload_cv(file: UploadFile = File(...)):
    content = await file.read()
    text = model.generate_content([
        "Extract structured candidate data (name, email, skills, experience) from this CV:",
        {"mime_type": file.content_type, "data": content}
    ]).text
    return {"raw_text": text}

@app.post("/apply/")
def apply(job_id: int = Form(...), name: str = Form(...), email: str = Form(...)):
    odoo = odoorpc.ODOO(host=os.getenv("ODOO_URL").replace("https://", ""),
                        protocol="jsonrpcs", port=443)
    odoo.login(os.getenv("ODOO_DB"), os.getenv("ODOO_USERNAME"), os.getenv("ODOO_PASSWORD"))
    applicant_id = odoo.env["hr.applicant"].create({
        "name": f"{name} – {email}",
        "job_id": job_id,
        "email_from": email,
        "stage_id": odoo.env["hr.recruitment.stage"].search([("name", "=", "New")])[0]
    })
    return {"applicant_id": applicant_id}

# Serve the tiny React build at /interview/{id}
@app.get("/interview/{applicant_id}", response_class=HTMLResponse)
def interview_page(applicant_id: int):
    return f"""
    <!doctype html>
    <html>
      <head><title>AI Interview</title></head>
      <body>
        <h1>Interview for applicant {applicant_id}</h1>
        <p>AI questions will appear here (plug in Gemini Live API).</p>
      </body>
    </html>
    """

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)