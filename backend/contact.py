from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, EmailStr
from slowapi import Limiter
from slowapi.util import get_remote_address
import sendgrid
from sendgrid.helpers.mail import Mail
import os

router  = APIRouter()
limiter = Limiter(key_func=get_remote_address)

class ContactForm(BaseModel):
    name: str
    email: EmailStr
    message: str

@router.post("")
@limiter.limit("5/hour")
async def send_contact(request: Request, form: ContactForm):
    api_key    = os.getenv("SENDGRID_API_KEY")
    from_email = os.getenv("CONTACT_FROM_EMAIL", "kartikkale03@gmail.com")
    to_email   = os.getenv("CONTACT_TO_EMAIL",   "kartikkale03@gmail.com")

    if not api_key:
        print(f"[DEV] {form.name} <{form.email}>: {form.message}")
        return {"success": True, "message": "Dev mode — no email sent"}

    msg = Mail(
        from_email=from_email,
        to_emails=to_email,
        subject=f"Portfolio Contact: {form.name}",
        html_content=f"""
        <h2>New portfolio message</h2>
        <p><strong>Name:</strong> {form.name}</p>
        <p><strong>Email:</strong> <a href="mailto:{form.email}">{form.email}</a></p>
        <p><strong>Message:</strong></p>
        <blockquote style="border-left:3px solid #7dd3fc;padding-left:12px;color:#555">
          {form.message}
        </blockquote>
        """,
    )
    try:
        sg = sendgrid.SendGridAPIClient(api_key=api_key)
        resp = sg.send(msg)
        if resp.status_code not in (200, 202):
            raise HTTPException(status_code=500, detail="Email send failed")
        return {"success": True, "message": "Message sent!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
