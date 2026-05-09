from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, EmailStr, field_validator
from slowapi import Limiter
from slowapi.util import get_remote_address
import sendgrid
from sendgrid.helpers.mail import Mail
import os, html as html_lib

router  = APIRouter()
limiter = Limiter(key_func=get_remote_address)

class ContactForm(BaseModel):
    name: str
    email: EmailStr
    message: str

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        v = v.strip()
        if not v:
            raise ValueError('Name is required')
        if len(v) > 100:
            raise ValueError('Name must be 100 characters or fewer')
        return v

    @field_validator('message')
    @classmethod
    def validate_message(cls, v):
        v = v.strip()
        if not v:
            raise ValueError('Message is required')
        if len(v) > 2000:
            raise ValueError('Message must be 2000 characters or fewer')
        return v

@router.post("")
@limiter.limit("5/hour")
async def send_contact(request: Request, form: ContactForm):
    api_key    = os.getenv("SENDGRID_API_KEY")
    from_email = os.getenv("CONTACT_FROM_EMAIL", "kartikkale03@gmail.com")
    to_email   = os.getenv("CONTACT_TO_EMAIL",   "kartikkale03@gmail.com")

    if not api_key:
        print(f"[DEV] {form.name} <{form.email}>: {form.message}")
        return {"success": True, "message": "Dev mode — no email sent"}

    safe_name    = html_lib.escape(form.name)
    safe_email   = html_lib.escape(form.email)
    safe_message = html_lib.escape(form.message)

    msg = Mail(
        from_email=from_email,
        to_emails=to_email,
        subject=f"Portfolio Contact: {safe_name}",
        html_content=f"""
        <h2>New portfolio message</h2>
        <p><strong>Name:</strong> {safe_name}</p>
        <p><strong>Email:</strong> <a href="mailto:{safe_email}">{safe_email}</a></p>
        <p><strong>Message:</strong></p>
        <blockquote style="border-left:3px solid #7dd3fc;padding-left:12px;color:#555;white-space:pre-wrap">
          {safe_message}
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
