from msal import ConfidentialClientApplication
import aiohttp
from loguru import logger
from typing import Dict, Optional
from app.config import get_settings

settings = get_settings()


class GraphAPIClient:
    """Cliente para Microsoft Graph API"""
    
    def __init__(self):
        self.tenant_id = settings.azure_tenant_id
        self.client_id = settings.azure_client_id
        self.client_secret = settings.azure_client_secret

        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.scope = ["https://graph.microsoft.com/.default"]

        self.app = ConfidentialClientApplication(
            client_id=self.client_id,
            client_credential=self.client_secret,
            authority=self.authority
        )

        self._token: Optional[str] = None
        self._group_cache: dict[str, str] = {}  # nombre_grupo -> group_id
    
    def get_token(self) -> str:
        """Obtener access token de Azure AD"""
        result = self.app.acquire_token_for_client(scopes=self.scope)
        
        if "access_token" in result:
            logger.debug("✅ Token obtenido exitosamente")
            self._token = result["access_token"]
            return self._token
        else:
            error = result.get("error_description", "Unknown error")
            logger.error(f"❌ Error obteniendo token: {error}")
            raise Exception(f"Error de autenticación: {error}")
    
    async def list_users(self, limit: int = 10) -> Dict:
        """Listar usuarios de Office 365 (para testing)"""
        token = self.get_token()

        headers = {"Authorization": f"Bearer {token}"}

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://graph.microsoft.com/v1.0/users?$top={limit}",
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Error Graph API: {error_text}")
                    return {"error": error_text}

    async def get_all_user_emails(self, domain: str = "ecr.edu.co") -> set[str]:
        """
        Obtiene todos los emails del dominio desde Office 365.

        Args:
            domain: Dominio a filtrar (default: ecr.edu.co)

        Returns:
            Set de emails en minúsculas del dominio especificado
        """
        logger.info(f"Obteniendo emails existentes de Office 365 para dominio @{domain}...")

        token = self.get_token()
        headers = {"Authorization": f"Bearer {token}"}

        emails = set()
        url = "https://graph.microsoft.com/v1.0/users?$select=mail,userPrincipalName&$top=999"

        async with aiohttp.ClientSession() as session:
            while url:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()

                        # Extraer emails
                        for user in data.get('value', []):
                            # Intentar primero con 'mail', luego con 'userPrincipalName'
                            email = user.get('mail') or user.get('userPrincipalName')

                            if email and email.lower().endswith(f"@{domain}"):
                                emails.add(email.lower())

                        # Verificar si hay más páginas
                        url = data.get('@odata.nextLink')
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Error obteniendo emails: {error_text}")
                        break

        logger.info(f"Se encontraron {len(emails)} emails existentes en el dominio @{domain}")
        return emails

    async def get_all_users_info(self, domain: str = "ecr.edu.co") -> list[dict]:
        """
        Obtiene información de todos los usuarios del dominio desde Office 365.

        Incluye email y displayName para cada usuario, permitiendo
        detectar usuarios existentes por nombre completo.

        Args:
            domain: Dominio a filtrar (default: ecr.edu.co)

        Returns:
            Lista de dicts con email y display_name de usuarios del dominio

        Example:
            [
                {"email": "laura.becerra@ecr.edu.co", "display_name": "Laura Sofia Becerra Sandoval"},
                {"email": "juan.perez@ecr.edu.co", "display_name": "Juan Carlos Perez Lopez"}
            ]
        """
        logger.info(f"Obteniendo usuarios existentes de Office 365 para dominio @{domain}...")

        token = self.get_token()
        headers = {"Authorization": f"Bearer {token}"}

        users_info = []
        url = "https://graph.microsoft.com/v1.0/users?$select=mail,userPrincipalName,displayName&$top=999"

        async with aiohttp.ClientSession() as session:
            while url:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()

                        # Extraer información de usuarios
                        for user in data.get('value', []):
                            # Intentar primero con 'mail', luego con 'userPrincipalName'
                            email = user.get('mail') or user.get('userPrincipalName')
                            display_name = user.get('displayName', '')

                            if email and email.lower().endswith(f"@{domain}"):
                                users_info.append({
                                    "email": email.lower(),
                                    "display_name": display_name
                                })

                        # Verificar si hay más páginas
                        url = data.get('@odata.nextLink')
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Error obteniendo usuarios: {error_text}")
                        break

        logger.info(f"Se encontraron {len(users_info)} usuarios en el dominio @{domain}")
        return users_info

    async def email_exists(self, email: str) -> bool:
        """
        Verifica si un email específico existe en Office 365.

        Args:
            email: Email a verificar

        Returns:
            True si el email existe, False en caso contrario
        """
        token = self.get_token()
        headers = {"Authorization": f"Bearer {token}"}

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://graph.microsoft.com/v1.0/users/{email}",
                headers=headers
            ) as response:
                if response.status == 200:
                    logger.debug(f"Email {email} existe en Office 365")
                    return True
                elif response.status == 404:
                    logger.debug(f"Email {email} no existe en Office 365")
                    return False
                else:
                    error_text = await response.text()
                    logger.warning(f"Error verificando email {email}: {error_text}")
                    return False

    async def get_group_id(self, group_name: str) -> str | None:
        """
        Obtiene el ID de un grupo por su nombre.

        Cachea el resultado para evitar búsquedas repetidas.

        Args:
            group_name: Nombre del grupo (displayName)

        Returns:
            ID del grupo si se encuentra, None en caso contrario

        Example:
            >>> group_id = await client.get_group_id("Estudiantes Licencias A5")
            >>> print(group_id)
            'abc123-def456-...'
        """
        # Verificar caché
        if group_name in self._group_cache:
            logger.debug(f"Grupo '{group_name}' encontrado en caché")
            return self._group_cache[group_name]

        logger.info(f"Buscando grupo: {group_name}")

        token = self.get_token()
        headers = {"Authorization": f"Bearer {token}"}

        # URL encode del nombre del grupo
        import urllib.parse
        encoded_name = urllib.parse.quote(group_name)
        url = f"https://graph.microsoft.com/v1.0/groups?$filter=displayName eq '{encoded_name}'"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    groups = data.get('value', [])

                    if groups:
                        group_id = groups[0]['id']
                        self._group_cache[group_name] = group_id
                        logger.info(f"Grupo '{group_name}' encontrado: {group_id}")
                        return group_id
                    else:
                        logger.warning(f"Grupo '{group_name}' no encontrado")
                        return None
                else:
                    error_text = await response.text()
                    logger.error(f"Error buscando grupo '{group_name}': {error_text}")
                    return None

    async def create_user(self, user_data: dict) -> dict:
        """
        Crea un nuevo usuario en Office 365.

        Args:
            user_data: Diccionario con datos del usuario:
                - display_name: Nombre completo
                - email: Email institucional
                - password: Contraseña temporal

        Returns:
            Diccionario con resultado:
                - success: True/False
                - user_id: ID del usuario creado
                - email: Email del usuario
                - error: Mensaje de error (si falló)

        Example:
            >>> result = await client.create_user({
            ...     "display_name": "Juan Perez",
            ...     "email": "juan.perez@ecr.edu.co",
            ...     "password": "TempPass123$"
            ... })
        """
        email = user_data['email']
        display_name = user_data['display_name']
        password = user_data['password']

        logger.info(f"Creando usuario: {email}")

        token = self.get_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # Extraer mailNickname (parte antes del @)
        mail_nickname = email.split('@')[0]

        # Construir body del request
        body = {
            "accountEnabled": True,
            "displayName": display_name,
            "mailNickname": mail_nickname,
            "userPrincipalName": email,
            "mail": email,
            "passwordProfile": {
                "password": password,
                "forceChangePasswordNextSignIn": True
            }
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://graph.microsoft.com/v1.0/users",
                headers=headers,
                json=body
            ) as response:
                if response.status == 201:
                    data = await response.json()
                    user_id = data['id']
                    logger.info(f"Usuario creado exitosamente: {email} (ID: {user_id})")
                    return {
                        "success": True,
                        "user_id": user_id,
                        "email": email
                    }
                else:
                    error_text = await response.text()
                    logger.error(f"Error creando usuario {email}: {error_text}")
                    return {
                        "success": False,
                        "email": email,
                        "error": error_text
                    }

    async def add_user_to_group(self, user_id: str, group_id: str, group_name: str = "") -> bool:
        """
        Agrega un usuario a un grupo de Office 365.

        Args:
            user_id: ID del usuario
            group_id: ID del grupo
            group_name: Nombre del grupo (para logging)

        Returns:
            True si se agregó exitosamente, False en caso contrario

        Example:
            >>> success = await client.add_user_to_group(
            ...     user_id="abc123",
            ...     group_id="def456",
            ...     group_name="Estudiantes Licencias A5"
            ... )
        """
        logger.info(f"Asignando usuario {user_id} a grupo: {group_name or group_id}")

        token = self.get_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # CORREGIDO: Usar directoryObjects en lugar de users
        body = {
            "@odata.id": f"https://graph.microsoft.com/v1.0/directoryObjects/{user_id}"
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"https://graph.microsoft.com/v1.0/groups/{group_id}/members/$ref",
                headers=headers,
                json=body
            ) as response:
                if response.status == 204:
                    # BUG FIX: Confiar en el status 204, no verificar inmediatamente
                    # La verificación inmediata falla por propagación en Azure AD
                    logger.info(f"Usuario asignado a grupo exitosamente")
                    return True

                elif response.status == 400:
                    error_text = await response.text()
                    # BUG FIX: Microsoft dice "already exist" sin 's'
                    if "already exist" in error_text.lower() or "already a member" in error_text.lower():
                        logger.warning(f"Usuario ya pertenece al grupo")
                        return True
                    else:
                        logger.error(f"Error 400 asignando usuario: {error_text}")
                        return False
                else:
                    error_text = await response.text()
                    logger.error(f"Error asignando usuario a grupo (status {response.status}): {error_text}")
                    return False

    async def verify_user_in_group(self, user_id: str, group_id: str) -> bool:
        """
        Verifica si un usuario está en un grupo.

        Args:
            user_id: ID del usuario
            group_id: ID del grupo

        Returns:
            True si el usuario está en el grupo, False en caso contrario

        Example:
            >>> is_member = await client.verify_user_in_group(
            ...     user_id="abc123",
            ...     group_id="def456"
            ... )
        """
        logger.debug(f"Verificando si usuario {user_id} está en grupo {group_id}")

        token = self.get_token()
        headers = {"Authorization": f"Bearer {token}"}

        async with aiohttp.ClientSession() as session:
            # Obtener todos los miembros del grupo
            async with session.get(
                f"https://graph.microsoft.com/v1.0/groups/{group_id}/members",
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    members = data.get('value', [])

                    # Buscar el usuario en la lista
                    for member in members:
                        if member.get('id') == user_id:
                            logger.debug(f"Usuario encontrado en grupo")
                            return True

                    logger.debug(f"Usuario NO encontrado en grupo")
                    return False
                else:
                    error_text = await response.text()
                    logger.error(f"Error verificando membresía: {error_text}")
                    return False

    async def send_email(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        from_email: str = None
    ) -> bool:
        """
        Envía un correo usando Microsoft Graph API.

        Args:
            to_email: Dirección de correo del destinatario
            subject: Asunto del correo
            body_html: Contenido HTML del correo
            from_email: Dirección del remitente (opcional, usa settings.email_sender_address por defecto)

        Returns:
            True si el correo se envió exitosamente, False en caso contrario

        Example:
            >>> success = await client.send_email(
            ...     to_email="usuario@gmail.com",
            ...     subject="Bienvenido",
            ...     body_html="<p>Hola</p>"
            ... )
        """
        from app.config import get_settings
        settings = get_settings()

        if from_email is None:
            from_email = settings.email_sender_address

        token = token = self.get_token()
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

        # Endpoint para enviar correo
        url = f"https://graph.microsoft.com/v1.0/users/{from_email}/sendMail"

        # Cuerpo del request
        payload = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": "HTML",
                    "content": body_html
                },
                "toRecipients": [
                    {
                        "emailAddress": {
                            "address": to_email
                        }
                    }
                ]
            },
            "saveToSentItems": False
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status == 202:
                    logger.debug(f"Correo enviado exitosamente a {to_email}")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"Error enviando correo (status {response.status}): {error_text}")
                    return False


# Singleton
_graph_client: Optional[GraphAPIClient] = None

def get_graph_client() -> GraphAPIClient:
    """Obtener instancia única de Graph API"""
    global _graph_client
    if _graph_client is None:
        _graph_client = GraphAPIClient()
    return _graph_client