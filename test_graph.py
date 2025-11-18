import asyncio
from loguru import logger
import sys
from app.graph_api import get_graph_client

# Configurar logging
logger.remove()
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>"
)

async def test_connection():
    """Probar conexión con Microsoft Graph API"""
    
    logger.info("="*60)
    logger.info("🧪 PROBANDO CONEXIÓN CON MICROSOFT GRAPH API")
    logger.info("="*60)
    
    try:
        client = get_graph_client()
        
        # Test 1: Obtener token
        logger.info("\n1️⃣  Obteniendo token de autenticación...")
        token = client.get_token()
        logger.success(f"✅ Token obtenido (primeros 30 chars): {token[:30]}...")
        
        # Test 2: Listar usuarios
        logger.info("\n2️⃣  Listando primeros 5 usuarios...")
        result = await client.list_users(limit=5)
        
        if "error" in result:
            logger.error(f"❌ Error: {result['error']}")
            return
        
        users = result.get("value", [])
        logger.success(f"✅ Se encontraron {len(users)} usuarios\n")
        
        logger.info("👥 USUARIOS ENCONTRADOS:")
        logger.info("-" * 60)
        for i, user in enumerate(users, 1):
            name = user.get('displayName', 'Sin nombre')
            email = user.get('userPrincipalName', 'Sin email')
            logger.info(f"{i}. {name}")
            logger.info(f"   📧 {email}\n")
        
        logger.info("="*60)
        logger.success("🎉 ¡CONEXIÓN EXITOSA CON GRAPH API!")
        logger.info("="*60)
        logger.info("\n✅ Todo configurado correctamente")
        logger.info("✅ Puedes continuar con el desarrollo\n")
        
    except Exception as e:
        logger.error("="*60)
        logger.error(f"❌ ERROR: {e}")
        logger.error("="*60)
        logger.error("\n🔍 VERIFICA:")
        logger.error("  1. AZURE_TENANT_ID correcto en .env")
        logger.error("  2. AZURE_CLIENT_ID correcto en .env")
        logger.error("  3. AZURE_CLIENT_SECRET correcto en .env")
        logger.error("  4. Permisos concedidos en Azure Portal\n")


if __name__ == "__main__":
    asyncio.run(test_connection())