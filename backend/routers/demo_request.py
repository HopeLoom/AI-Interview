import sendgrid
from fastapi import APIRouter, HTTPException
from globals import config, main_logger
from pydantic import BaseModel
from sendgrid.helpers.mail import Mail

router = APIRouter()
SENDGRID_API_KEY = config.email.api_key
RECIPIENTS = config.email.recipients
FROM_EMAIL = config.email.from_email

if not SENDGRID_API_KEY:
    raise RuntimeError("SENDGRID_API_KEY not set in environment variables")


class DemoRequest(BaseModel):
    firstName: str
    lastName: str
    email: str
    company: str
    jobTitle: str
    message: str | None = None


@router.post("/api/demo-request")
async def handle_demo_request_api(data: DemoRequest):
    try:
        print("Received demo request:", data)
        return await handle_demo_request(data, logger=main_logger)
    except Exception as e:
        print("Email sending failed:", e)
        raise HTTPException(status_code=500, detail="Failed to send email")


async def handle_demo_request(data: DemoRequest, logger):
    try:
        print("handle demo request:", data)
        print("key is:", SENDGRID_API_KEY)
        print("recipients are:", RECIPIENTS)
        print("from email is:", FROM_EMAIL)

        content = f"""
        Name: {data.firstName} {data.lastName}
        Email: {data.email}
        Company: {data.company}
        Job Title: {data.jobTitle}
        Message: {data.message or "N/A"}
        """

        message = Mail(
            from_email=FROM_EMAIL,
            to_emails=RECIPIENTS,
            subject="New Demo Request from HopeLoom",
            plain_text_content=content,
        )
        sg = sendgrid.SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        logger.info(f"SendGrid response code: {response.status_code}")
        logger.info(f"SendGrid response body: {response.body}")
        logger.info(f"SendGrid response headers: {response.headers}")

        if response.status_code != 202:
            raise HTTPException(status_code=500, detail="SendGrid rejected the email")

        return {"message": "Demo request received"}
    except Exception as e:
        logger.error(f"Email sending failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to send email")
