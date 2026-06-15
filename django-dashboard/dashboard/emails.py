from django.conf import settings
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To


def send_instant_usage_invoice_email(user_email: str, org_name: str, project_id: str, cost: str = "$2.00") -> bool:
    message = Mail(
        from_email=Email("billing@yourstartupdomain.com", "AI Patch-Bot Billing"),
        to_emails=To(user_email),
        subject=f"Usage Invoice: Code Remediation Run Complete [{project_id}]",
        html_content=f"""
        <div style="font-family: sans-serif; max-width: 600px; color: #334155; padding: 20px; border: 1px solid #e2e8f0; border-radius: 8px;">
            <h2 style="color: #0e7490; margin-bottom: 4px;">AI Patch-Bot Ledger Update</h2>
            <p style="font-size: 14px; color: #64748b; margin-top: 0;">Autonomous Processing Completed Successfully</p>
            <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 20px 0;"/>
            <p>Hello team <strong>{org_name}</strong>,</p>
            <p>Our sandboxed core system has successfully analyzed, patched, and verified your repository payload code changes.</p>

            <div style="background-color: #f8fafc; padding: 15px; border-radius: 6px; margin: 20px 0; font-family: monospace; font-size: 13px;">
                <strong>Execution Context:</strong> {project_id}<br/>
                <strong>Status Metric:</strong> Passed & Triggered PR<br/>
                <strong>Unit Transaction Cost:</strong> {cost} USD
            </div>

            <p style="font-size: 12px; color: #94a3b8;">
                This transaction has been automatically applied to your Stripe enterprise file profile under your metered plan parameters. No further action is required.
            </p>
        </div>
        """,
    )

    try:
        sg_client = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg_client.send(message)
        return response.status_code == 202
    except Exception as network_error:
        print(f"SendGrid delivery channel pipeline failure: {network_error}")
        return False
