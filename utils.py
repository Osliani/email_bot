from dotenv import load_dotenv
from openai import OpenAI
import os, time, json
import smtplib, os
from email.message import EmailMessage

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")
HOST = os.getenv("HOST")

def show_json(obj):
    print(json.loads(obj.model_dump_json()))
    
def wait_on_run(run, thread_id):
    while run.status == "queued" or run.status == "in_progress":
        run = client.beta.threads.runs.retrieve(
            thread_id = thread_id,
            run_id = run.id,
        )
        time.sleep(0.5)
    return run

def pretty_print(messages):
    print("# Messages")
    for m in messages:
        print(f"{m.role}: {m.content[0].text.value}")
    print()
    
def add_message(message, thread_id):
    message_object = client.beta.threads.messages.create (
        thread_id = thread_id, 
        role = "user", 
        content = message
    )
    return message_object

def add_assistant(assistant_id, thread_id):
    run = client.beta.threads.runs.create (
        thread_id = thread_id,
        assistant_id = assistant_id,
    )
    return run

def get_response(thread_id, message_object):
    response = client.beta.threads.messages.list(thread_id=thread_id, order="asc", after=message_object.id)
    ans = ""
    for r in response:
        ans += f"{r.content[0].text.value}\n"

    return ans

def submit_message(message:str, thread_id, assistant_id):
    message_object = add_message(message, thread_id)
    run = add_assistant(assistant_id, thread_id)
    run = wait_on_run(run, thread_id)
    
    if run.status == 'completed':
        return get_response(thread_id, message_object)

def send_mail(to, subject, message):
    email = EmailMessage()
    email["from"] = EMAIL
    email["to"] = to
    email["subject"] = subject
    email.set_content(message)

    with smtplib.SMTP(HOST, port = 587) as smtp:
        smtp.starttls()
        smtp.login(EMAIL, PASSWORD)
        smtp.sendmail(EMAIL, to, email.as_string())
        
    print("Correo enviado!")