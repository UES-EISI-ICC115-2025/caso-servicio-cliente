from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import EventType
from dotenv import load_dotenv, find_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from email.mime.application import MIMEApplication
from datetime import datetime

# Cargar variables de entorno desde un archivo .env (si existe)
dotenv_path = find_dotenv()
print(f"Cargando variables de entorno desde: {dotenv_path}")
if dotenv_path:
    load_dotenv(dotenv_path)
else:
    # fallback: intenta cargar .env desde el directorio de trabajo actual
    load_dotenv()

class ActionSendEmail(Action):
    def name(self) -> Text:
        return "action_send_email"

    # Adjuntar contrato falso en PDF
    def _escape_pdf_text(s: str) -> str:
        s = s or ""
        return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    def _minimal_pdf_from_lines(lines: List[str]) -> bytes:
        header = b"%PDF-1.4\n"
        objects = []

        # Build text stream
        y = 760  # start near top of page
        stream_lines: List[str] = []
        for line in lines:
            esc = ActionSendEmail._escape_pdf_text(line)
            stream_lines.append(f"BT /F1 12 Tf 72 {y} Td ({esc}) Tj ET\n")
            y -= 18
        stream_data = "".join(stream_lines).encode("latin-1", errors="ignore")
        length = len(stream_data)

        # Objects
        obj1 = b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        obj2 = b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        obj3 = (
            b"3 0 obj\n"
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>\n"
            b"endobj\n"
        )
        obj4 = (
            f"4 0 obj\n<< /Length {length} >>\nstream\n".encode("latin-1")
            + stream_data +
            b"endstream\nendobj\n"
        )
        obj5 = b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"

        objects.extend([obj1, obj2, obj3, obj4, obj5])

        # Concatenate and compute xref
        content = bytearray()
        content += header
        xref_positions = [0]  # object 0 is free
        for obj in objects:
            xref_positions.append(len(content))
            content += obj

        xref_start = len(content)
        xref = ["xref\n0 6\n"]
        xref.append("0000000000 65535 f \n")
        for pos in xref_positions[1:]:
            xref.append(f"{pos:010} 00000 n \n")
        content += "".join(xref).encode("latin-1")

        trailer = (
            b"trailer << /Size 6 /Root 1 0 R >>\n"
            + f"startxref\n{xref_start}\n%%EOF\n".encode("latin-1")
        )
        content += trailer
        return bytes(content)
    
    def generate_fake_contract_pdf(
        nombre: str,
        apellido: str,
        dui: str,
        direccion: str,
        telefono: str,
        fecha_creacion: str,
        plan: str,
        monto_mensual: str,
    ) -> bytes:
        full_name = f"{(nombre or '').strip()} {(apellido or '').strip()}".strip()
        header = "CONTRATO DE PRESTACION DE SERVICIOS"
        subheader = "*** DOCUMENTO DE PRUEBA - SIN VALIDEZ LEGAL ***"
        lines: List[str] = [
            header,
            subheader,
            "=" * 60,
            "",
            "DATOS DEL CLIENTE:",
            f"  Nombre completo: {full_name or 'No especificado'}",
            f"  DUI: {dui or 'No especificado'}",
            f"  Telefono: {telefono or 'No especificado'}",
            f"  Direccion: {direccion or 'No especificado'}",
            "",
            "DETALLES DEL SERVICIO:",
        ]

        if plan and monto_mensual:
            lines.append(f"  Plan contratado: {plan}")
            lines.append(f"  Inversion mensual: ${monto_mensual}")
        elif plan:
            lines.append(f"  Plan contratado: {plan}")
        elif monto_mensual:
            lines.append(f"  Inversion mensual: ${monto_mensual}")

        lines += [
            f"  Fecha de solicitud: {fecha_creacion or ''}",
            "",
            "=" * 60,
            "CLAUSULAS PRINCIPALES:",
            "",
            "1. NATURALEZA DEL DOCUMENTO",
            "   Este es un contrato de demostracion generado",
            "   automaticamente con fines educativos y de prueba.",
            "   NO posee validez legal alguna.",
            "",
            "2. PROPOSITO",
            "   La informacion contenida es solo para ilustrar",
            "   el funcionamiento del sistema automatizado.",
            "",
            "3. AVISO IMPORTANTE",
            "   Para un contrato real, contacte a nuestro",
            "   departamento legal y de atencion al cliente.",
            "",
            "=" * 60,
            "",
            "Gracias por su preferencia.",
            "Este documento fue generado automaticamente."
        ]
        return ActionSendEmail._minimal_pdf_from_lines(lines)

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:

        # Obtener información del cliente desde los slots
        email_destinatario = tracker.get_slot("email")
        nombre = tracker.get_slot("nombre")
        apellido = tracker.get_slot("apellido")
        nombre_producto = tracker.get_slot("nombre_producto")
        precio_producto = tracker.get_slot("precio_producto")
        dui = tracker.get_slot("dui")
        telefono = tracker.get_slot("telefono")
        direccion = tracker.get_slot("direccion")

        # Validar que tengamos el email del destinatario
        if not email_destinatario:
            dispatcher.utter_message(text="No tengo un correo electrónico registrado para enviar la confirmación.")
            return []

        # Configuración de Gmail desde variables de entorno
        gmail_user = os.getenv("GMAIL_USER")
        gmail_password = os.getenv("GMAIL_APP_PASSWORD")  # Usar App Password, no la contraseña regular

        if not gmail_user or not gmail_password:
            print("ERROR: Credenciales de Gmail no configuradas en variables de entorno")
            dispatcher.utter_message(text="Lo siento, no puedo enviar el correo en este momento. Configuración incompleta.")
            return []

        try:

            # Generar PDF con datos disponibles
            fecha_creacion = datetime.now().strftime("%Y-%m-%d %H:%M")
            pdf_bytes = ActionSendEmail.generate_fake_contract_pdf(
                nombre=nombre,
                apellido=apellido,
                dui=dui,
                direccion=direccion,
                telefono=telefono,
                fecha_creacion=fecha_creacion,
                plan=nombre_producto,
                monto_mensual=precio_producto,
            )

            # Crear MIMEMultipart y adjuntar el PDF
            msg = MIMEMultipart()
            attachment = MIMEApplication(pdf_bytes, _subtype="pdf")
            safe_last = (apellido or "").strip().replace(" ", "_") or "Cliente"
            safe_first = (nombre or "").strip().replace(" ", "_") or ""
            filename = f"Contrato_{safe_last}_{safe_first}.pdf".strip("_")
            attachment.add_header('Content-Disposition', 'attachment', filename=filename)
            msg.attach(attachment)
            # Cuerpo del correo
            body = f"""

         CONFIRMACIÓN DE SOLICITUD DE SERVICIO               
                    (DOCUMENTO DE PRUEBA)                     

Estimado/a {nombre or ''} {apellido or ''},

Le confirmamos la recepción de su solicitud de contratación:

DETALLES DE SU SOLICITUD:

    📦 Plan seleccionado:  {nombre_producto or 'No especificado'}
    💰 Inversión mensual:  ${precio_producto or 'No especificado'}
    📧 Correo electrónico: {email_destinatario}
    📱 Teléfono:           {telefono or 'No especificado'}
    🏠 Dirección:          {direccion or 'No especificado'}

Nuestro equipo se pondrá en contacto con usted en las próximas
24-48 horas para coordinar la instalación y activación del servicio.

Encontrará adjunto un contrato preliminar con los detalles de su
solicitud.

⚠️  IMPORTANTE: Este es un mensaje de PRUEBA generado por un
    sistema automatizado. La información contenida es únicamente
    para fines de demostración y no tiene validez legal.

¿Tiene preguntas? Contáctenos:
  • Email: {gmail_user}
  • Teléfono: +503 1234-5678

Gracias por su confianza.

Atentamente,
Equipo de Atención al Cliente
            """

            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            msg['From'] = gmail_user
            msg['To'] = email_destinatario
            msg['Subject'] = "Confirmación de Solicitud de Servicio"

            # Conectar y enviar
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(gmail_user, gmail_password)
            print("Login exitoso.")
            # server.send_message(msg)
            # server.quit()
            # Envío del correo
            text = msg.as_string()
            server.sendmail(gmail_user, email_destinatario, text)
            print(f"Correo enviado exitosamente a {email_destinatario}")
            dispatcher.utter_message(text=f"He enviado un correo de confirmación a {email_destinatario}.")
            print(f"Email enviado exitosamente a {email_destinatario}")

        except Exception as e:
            print(f"ERROR al enviar email: {e}")
            dispatcher.utter_message(text="Lo siento, hubo un problema al enviar el correo de confirmación.")

        finally:
            if 'server' in locals():
                server.quit()
                print("Conexión cerrada.")
        return []
