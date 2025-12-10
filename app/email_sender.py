"""
Módulo para enviar correos de bienvenida con credenciales.

Usa Jinja2 para renderizar templates HTML y Microsoft Graph API para enviar correos.
"""

from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from loguru import logger
from app.config import get_settings
from app.graph_api import GraphAPIClient

settings = get_settings()


class EmailSender:
    """
    Envía correos de bienvenida con credenciales a usuarios nuevos.

    Usa templates Jinja2 para el contenido HTML y Microsoft Graph API para enviar.
    """

    def __init__(self, graph_client: GraphAPIClient):
        """
        Inicializa el EmailSender.

        Args:
            graph_client: Cliente autenticado de Microsoft Graph API
        """
        self.graph_client = graph_client
        self.template_dir = Path(__file__).parent.parent / "templates"
        self.env = Environment(loader=FileSystemLoader(self.template_dir))

    def render_welcome_email(self, user_data: dict) -> str:
        """
        Renderiza el template de bienvenida con los datos del usuario.

        Args:
            user_data: Diccionario con datos del usuario:
                - full_name: Nombres completos
                - full_last_name: Apellidos completos
                - institutional_email: Email institucional
                - password_generated: Contraseña de Office 365
                - identification_id: Número de documento
                - (password de AppConnecto viene de settings)

        Returns:
            HTML renderizado como string

        Example:
            >>> html = sender.render_welcome_email({
            ...     "full_name": "Juan",
            ...     "full_last_name": "Perez",
            ...     "institutional_email": "juan.perez@ecr.edu.co",
            ...     "password_generated": "Abc123xyz!",
            ...     "identification_id": "1234567890"
            ... })
        """
        template = self.env.get_template("welcome_email.html")
        return template.render(
            nombre=f"{user_data['full_name']} {user_data['full_last_name']}",
            email_institucional=user_data['institutional_email'],
            password_office365=user_data.get('password_generated', 'No disponible'),
            identification_id=user_data['identification_id'],
            password_appconnecto=settings.appconnecto_default_password
        )

    async def send_welcome_email(self, user_data: dict) -> dict:
        """
        Envía correo de bienvenida a un usuario.

        Args:
            user_data: Diccionario con datos del usuario (debe incluir email_personal)

        Returns:
            Diccionario con resultado:
                - status: "sent" o "failed"
                - email: Email del destinatario
                - name: Nombre completo del usuario
                - error: Mensaje de error (si falló)

        Example:
            >>> result = await sender.send_welcome_email(user_data)
            >>> if result["status"] == "sent":
            ...     print(f"Correo enviado a {result['name']} ({result['email']})")
        """
        email_personal = user_data.get('email_personal')
        full_name = f"{user_data['full_name']} {user_data['full_last_name']}"

        try:
            html = self.render_welcome_email(user_data)
            success = await self.graph_client.send_email(
                to_email=email_personal,
                subject=settings.email_subject_welcome,
                body_html=html
            )

            if success:
                logger.info(f"✅ Correo enviado a: {full_name} ({email_personal})")
                return {"status": "sent", "email": email_personal, "name": full_name}
            else:
                logger.error(f"❌ Error enviando correo a: {full_name} ({email_personal})")
                return {"status": "failed", "email": email_personal, "name": full_name, "error": "Error desconocido"}

        except Exception as e:
            logger.error(f"❌ Error enviando correo a {full_name} ({email_personal}): {e}")
            return {"status": "failed", "email": email_personal, "name": full_name, "error": str(e)}

    async def send_welcome_emails(self, users: list[dict]) -> dict:
        """
        Envía correos a múltiples usuarios.

        Args:
            users: Lista de diccionarios con datos de usuarios

        Returns:
            Diccionario con estadísticas:
                - sent: Lista de dicts con email y name de usuarios enviados exitosamente
                - failed: Lista de dicts con email, name y error
                - total: Total de usuarios procesados

        Example:
            >>> results = await sender.send_welcome_emails(users_list)
            >>> print(f"Enviados: {len(results['sent'])}")
            >>> for user in results['sent']:
            ...     print(f"  - {user['name']} ({user['email']})")
        """
        sent = []
        failed = []

        logger.info(f"📧 Enviando {len(users)} correos de bienvenida...")

        for i, user in enumerate(users, 1):
            logger.info(f"[{i}/{len(users)}] Enviando a: {user.get('email_personal')}")

            result = await self.send_welcome_email(user)

            if result["status"] == "sent":
                sent.append({"email": result["email"], "name": result["name"]})
            else:
                failed.append({"email": result["email"], "name": result["name"], "error": result.get("error")})

        return {
            "sent": sent,
            "failed": failed,
            "total": len(users)
        }
