from email.header import decode_header
from openai import OpenAI
from dotenv import load_dotenv
import imaplib, email, time, json, os, utils

load_dotenv()

EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")
HOST = os.getenv("HOST")

def procesar_correo(mail_id, imap):
    status, msg_data = imap.fetch(mail_id, "(RFC822)")
    
    for response_part in msg_data:
        if isinstance(response_part, tuple):
            msg = email.message_from_bytes(response_part[1])

            subject, encoding = decode_header(msg["Subject"])[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding if encoding else "utf-8")

            from_ = msg.get("From")

            email_data = {
                "subject": subject,
                "from": from_,
                "body": ""
            }

            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        try:
                            body = part.get_payload(decode=True).decode('utf-8')
                        except UnicodeDecodeError:
                            try:
                                body = part.get_payload(decode=True).decode('latin-1')  # Probar otra codificación
                            except UnicodeDecodeError:
                                body = part.get_payload(decode=True).decode('utf-8', errors='replace')  # Reemplazar caracteres no decodificables
                        email_data["body"] = body
            else:
                try:
                    body = msg.get_payload(decode=True).decode('utf-8')
                except UnicodeDecodeError:
                    try:
                        body = msg.get_payload(decode=True).decode('latin-1')
                    except UnicodeDecodeError:
                        body = msg.get_payload(decode=True).decode('utf-8', errors='replace')
                email_data["body"] = body

            print(f"Nuevo correo de: {from_}")
            print(f"Asunto: {subject}")

            with open('emails.json', 'a', encoding='utf-8') as f:
                json.dump(email_data, f, ensure_ascii=False, indent=4)
                f.write('\n')
            
            JUMO_ASSISTANT_ID = os.getenv("JUMO_ASSISTANT_ID")
            OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
            openai_client = OpenAI(api_key=OPENAI_API_KEY)
            
            thread = openai_client.beta.threads.create()
            ans = utils.submit_message(email_data["body"], thread.id, JUMO_ASSISTANT_ID)
            utils.send_mail(from_, f"Reply {subject}", ans)

imap = imaplib.IMAP4_SSL(HOST)
try:
    imap.login(EMAIL, PASSWORD)
except imaplib.IMAP4.error as e:
    print(f"Error de IMAP: {e}")
    exit()
except Exception as e:
    print(f"Error inesperado: {e}")
    exit()

imap.select("inbox")

try:
    while True:
        print("Escuchando nuevos correos...")
        time.sleep(2)
        status, response = imap.search(None, 'UNSEEN')

        if status == 'OK':
            for mail_id in response[0].split():
                procesar_correo(mail_id, imap)

        time.sleep(10)
finally:
    imap.close()
    imap.logout()
