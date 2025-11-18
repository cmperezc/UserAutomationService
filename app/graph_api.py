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


# Singleton
_graph_client: Optional[GraphAPIClient] = None

def get_graph_client() -> GraphAPIClient:
    """Obtener instancia única de Graph API"""
    global _graph_client
    if _graph_client is None:
        _graph_client = GraphAPIClient()
    return _graph_client