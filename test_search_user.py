"""
Script de prueba para buscar un usuario específico
"""

import asyncio
from loguru import logger
from app.graph_api import get_graph_client
import aiohttp


async def test_search():
    """Prueba de búsqueda de usuario"""
    client = get_graph_client()
    token = client.get_token()

    headers = {"Authorization": f"Bearer {token}"}

    # Obtener primeros 10 usuarios
    url = "https://graph.microsoft.com/v1.0/users?$select=displayName,mail,userPrincipalName,assignedLicenses&$top=10"

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                users = data.get('value', [])

                logger.info(f"Primeros 10 usuarios en Office 365:")
                logger.info("="*80)

                for i, user in enumerate(users, 1):
                    display_name = user.get('displayName', 'N/A')
                    mail = user.get('mail', 'N/A')
                    upn = user.get('userPrincipalName', 'N/A')
                    licenses = user.get('assignedLicenses', [])

                    logger.info(f"\n{i}. {display_name}")
                    logger.info(f"   Mail: {mail}")
                    logger.info(f"   UPN: {upn}")
                    logger.info(f"   Licencias: {len(licenses)} asignadas")

            else:
                error_text = await response.text()
                logger.error(f"Error: {error_text}")


if __name__ == "__main__":
    asyncio.run(test_search())
