import smtplib
from email.mime.text import MIMEText

from dotenv import load_dotenv
import os

from jinja2 import Environment, FileSystemLoader

load_dotenv()

# load credentials for the email that is sending the jobs
EMAIL = os.getenv("EMAIL_ADDR")
PASSWORD = os.getenv("EMAIL_PASSWORD")


def render_email_template(jobs):
    env = Environment(loader=FileSystemLoader("."))
    template = env.get_template("email_template.html") # custom email template
    return template.render(jobs=jobs, count=len(jobs))


def send_email(jobs, recipients):
    email_content = render_email_template(jobs)
    companies = set(job["company"] for job in jobs) # get the company names that have job postings
    subject = f"New Job Postings from {', '.join(companies)}"
    # limit the number of characters in the title
    subject = subject[:100] + "..." if len(subject) > 100 else subject

    # in case the user wants to email to multiple recipients
    for recipient in recipients:
        msg = MIMEText(email_content, "html")
        msg["Subject"] = subject
        msg["From"] = EMAIL
        msg["To"] = recipient
        
        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(EMAIL, PASSWORD)
                server.sendmail(EMAIL, recipient, msg.as_string())
            print(f"Email sent successfully to {recipient}.")
        except Exception as e:
            print(f"Failed to send email: {e}")
            raise e
