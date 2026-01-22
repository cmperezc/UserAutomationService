"""
Script para verificar actividad y logs de un usuario en Office 365.

Consulta:
- Intentos de inicio de sesión
- Cambios de contraseña
- Última actividad del usuario

Uso:
    python check_user_activity.py aiden.novoa@ecr.edu.co
"""

import asyncio
import sys
from datetime import datetime, timedelta
from app.graph_api import GraphAPIClient
from loguru import logger


async def get_user_sign_in_logs(graph_client: GraphAPIClient, user_email: str, days: int = 1):
    """
    Obtiene los logs de inicio de sesión del usuario.

    Args:
        graph_client: Cliente de Graph API autenticado
        user_email: Email del usuario
        days: Días hacia atrás para buscar logs

    Returns:
        Lista de intentos de inicio de sesión
    """
    token = graph_client.get_token()
    headers = {"Authorization": f"Bearer {token}"}

    # Calcular fecha de inicio
    start_date = (datetime.utcnow() - timedelta(days=days)).isoformat() + "Z"

    # Filtro para el usuario específico
    filter_query = f"userPrincipalName eq '{user_email}' and createdDateTime ge {start_date}"
    url = f"https://graph.microsoft.com/v1.0/auditLogs/signIns?$filter={filter_query}&$top=50"

    import aiohttp
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                return data.get('value', [])
            else:
                error_text = await response.text()
                logger.warning(f"No se pudieron obtener logs de inicio de sesión: {error_text}")
                return []


async def get_user_password_changes(graph_client: GraphAPIClient, user_email: str, days: int = 1):
    """
    Obtiene los logs de cambio de contraseña del usuario.

    Args:
        graph_client: Cliente de Graph API autenticado
        user_email: Email del usuario
        days: Días hacia atrás para buscar logs

    Returns:
        Lista de cambios de contraseña
    """
    token = graph_client.get_token()
    headers = {"Authorization": f"Bearer {token}"}

    # Calcular fecha de inicio
    start_date = (datetime.utcnow() - timedelta(days=days)).isoformat() + "Z"

    # Filtro para cambios de contraseña del usuario
    filter_query = f"activityDisplayName eq 'Change user password' and targetResources/any(t: t/userPrincipalName eq '{user_email}') and activityDateTime ge {start_date}"
    url = f"https://graph.microsoft.com/v1.0/auditLogs/directoryAudits?$filter={filter_query}&$top=50"

    import aiohttp
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                return data.get('value', [])
            else:
                error_text = await response.text()
                logger.warning(f"No se pudieron obtener logs de cambio de contraseña: {error_text}")
                return []


async def get_user_info(graph_client: GraphAPIClient, user_email: str):
    """
    Obtiene información básica del usuario.

    Args:
        graph_client: Cliente de Graph API autenticado
        user_email: Email del usuario

    Returns:
        Diccionario con información del usuario
    """
    token = graph_client.get_token()
    headers = {"Authorization": f"Bearer {token}"}

    url = f"https://graph.microsoft.com/v1.0/users/{user_email}"

    import aiohttp
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                logger.error(f"Error obteniendo información del usuario: {error_text}")
                return None


def print_header(text):
    """Imprime un encabezado formateado."""
    print("\n" + "="*80)
    print(text)
    print("="*80)


async def main():
    """Función principal."""
    # Verificar argumentos
    if len(sys.argv) < 2:
        print("❌ Error: Debe proporcionar el email del usuario")
        print("Uso: python check_user_activity.py usuario@ecr.edu.co")
        sys.exit(1)

    user_email = sys.argv[1]

    print_header(f"🔍 VERIFICANDO ACTIVIDAD DEL USUARIO: {user_email}")

    # Inicializar cliente
    graph_client = GraphAPIClient()

    try:
        # 1. Información básica del usuario
        print("\n📋 INFORMACIÓN DEL USUARIO")
        print("-" * 80)

        user_info = await get_user_info(graph_client, user_email)
        if user_info:
            print(f"Nombre: {user_info.get('displayName')}")
            print(f"Email: {user_info.get('mail') or user_info.get('userPrincipalName')}")
            print(f"ID: {user_info.get('id')}")
            print(f"Cuenta habilitada: {user_info.get('accountEnabled')}")
            print(f"Usuario creado: {user_info.get('createdDateTime')}")

            # Verificar si debe cambiar contraseña
            password_profile = user_info.get('passwordProfile', {})
            if password_profile:
                force_change = password_profile.get('forceChangePasswordNextSignIn', False)
                print(f"Debe cambiar contraseña en próximo inicio: {force_change}")
        else:
            print("⚠️  No se pudo obtener información del usuario")
            return

        # 2. Logs de inicio de sesión
        print_header("🔐 INTENTOS DE INICIO DE SESIÓN (ÚLTIMAS 24 HORAS)")

        sign_in_logs = await get_user_sign_in_logs(graph_client, user_email, days=1)

        if sign_in_logs:
            print(f"\n✅ Se encontraron {len(sign_in_logs)} intentos de inicio de sesión:\n")

            for i, log in enumerate(sign_in_logs, 1):
                created_time = log.get('createdDateTime', 'N/A')
                status = log.get('status', {})
                error_code = status.get('errorCode', 0)

                # Determinar si fue exitoso
                if error_code == 0:
                    result = "✅ EXITOSO"
                else:
                    result = f"❌ FALLIDO (código {error_code})"

                app_name = log.get('appDisplayName', 'N/A')
                ip_address = log.get('ipAddress', 'N/A')
                location = log.get('location', {})
                city = location.get('city', 'N/A')
                country = location.get('countryOrRegion', 'N/A')

                print(f"{i}. {result}")
                print(f"   Fecha/Hora: {created_time}")
                print(f"   Aplicación: {app_name}")
                print(f"   IP: {ip_address}")
                print(f"   Ubicación: {city}, {country}")

                # Mostrar error si hubo
                if error_code != 0:
                    failure_reason = status.get('failureReason', 'Desconocido')
                    print(f"   Razón del fallo: {failure_reason}")

                # Verificar si se cambió la contraseña
                if log.get('authenticationDetails'):
                    auth_details = log.get('authenticationDetails', [])
                    for detail in auth_details:
                        if 'password' in detail.get('authenticationMethod', '').lower():
                            print(f"   Método de autenticación: Contraseña")

                print()
        else:
            print("\n⚠️  No se encontraron intentos de inicio de sesión en las últimas 24 horas")
            print("Esto significa que el usuario AÚN NO ha intentado iniciar sesión.")

        # 3. Logs de cambio de contraseña
        print_header("🔑 CAMBIOS DE CONTRASEÑA (ÚLTIMAS 24 HORAS)")

        password_logs = await get_user_password_changes(graph_client, user_email, days=1)

        if password_logs:
            print(f"\n✅ Se encontraron {len(password_logs)} cambios de contraseña:\n")

            for i, log in enumerate(password_logs, 1):
                activity_time = log.get('activityDateTime', 'N/A')
                result = log.get('result', 'N/A')
                initiated_by = log.get('initiatedBy', {})
                user = initiated_by.get('user', {})
                initiator = user.get('userPrincipalName', 'Sistema')

                print(f"{i}. Cambio de contraseña")
                print(f"   Fecha/Hora: {activity_time}")
                print(f"   Resultado: {result}")
                print(f"   Iniciado por: {initiator}")
                print()
        else:
            print("\n⚠️  No se encontraron cambios de contraseña en las últimas 24 horas")
            print("Esto significa que el usuario AÚN NO ha cambiado su contraseña.")

        # 4. Resumen y recomendaciones
        print_header("📊 RESUMEN Y RECOMENDACIONES")

        if not sign_in_logs and not password_logs:
            print("\n🔍 ANÁLISIS:")
            print("   • El usuario NO ha intentado iniciar sesión")
            print("   • El usuario NO ha cambiado su contraseña")
            print("   • La contraseña temporal sigue siendo válida")
            print("\n💡 RECOMENDACIÓN:")
            print("   1. Verificar que el usuario esté usando la contraseña correcta del correo")
            print("   2. Confirmar que está intentando ingresar a portal.office.com")
            print("   3. Copiar la contraseña sin espacios adicionales")
            print("   4. Esperar 10-15 minutos si el usuario fue creado muy recientemente")

        elif sign_in_logs and any(log.get('status', {}).get('errorCode') == 0 for log in sign_in_logs):
            print("\n✅ ANÁLISIS:")
            print("   • El usuario SÍ ha iniciado sesión exitosamente")
            print("   • La contraseña ha sido validada correctamente")
            print("\n💡 POSIBLES CAUSAS DEL PROBLEMA:")
            print("   1. El usuario ya cambió la contraseña y no recuerda cuál es")
            print("   2. El usuario está intentando usar la contraseña vieja")
            print("   3. El usuario necesita resetear su contraseña")

        elif sign_in_logs:
            print("\n⚠️  ANÁLISIS:")
            print("   • El usuario SÍ ha intentado iniciar sesión")
            print("   • TODOS los intentos han fallado")
            print("\n💡 POSIBLES CAUSAS:")
            print("   1. Está usando la contraseña incorrecta")
            print("   2. Hay un error de tipeo al copiar la contraseña")
            print("   3. Necesita resetear la contraseña")

        print("\n" + "="*80)

    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
