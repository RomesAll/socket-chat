import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pydantic import SecretStr
from app.data_layer.exceptions import EmailSendError


class EmailSender:
    """Класс для отправки email уведомлений"""
    def __init__(self, smtp_server: str, port: int, sender_email: str, password: SecretStr):
        self.smtp_server = smtp_server
        self.port = port
        self.sender_email = sender_email
        self.password = password

    def send_accept_code(self, to: str, code: str):
        """Отправка кода подтверждения"""
        self._send(to, f'Код: {code}', 'Отправка кода подтверждения для доступа к мессенджеру')

    def _send(self, to: str, message: str, sub: str):
        """Подключение к SMTP серверу и отправка сообщения"""
        msg = MIMEMultipart()
        msg['From'] = self.sender_email
        msg['To'] = to
        msg['Subject'] = sub
        mime_type = 'plain'
        msg.attach(MIMEText(message, mime_type, 'utf-8'))
        # Подключаемся к SMTP-серверу и отправляем письмо
        try:
            if self.port == 465:
                # SSL подключение
                with smtplib.SMTP_SSL(self.smtp_server, self.port) as server:
                    server.login(self.sender_email, self.password.get_secret_value())
                    server.send_message(msg)
            else:
                # TLS подключение (порт 587 и другие)
                with smtplib.SMTP(self.smtp_server, self.port) as server:
                    server.starttls()
                    server.login(self.sender_email, self.password.get_secret_value())
                    server.send_message(msg)
        except Exception as e:
            raise EmailSendError(to, str(e))