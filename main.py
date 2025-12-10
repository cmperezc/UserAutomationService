"""
Script principal de automatización de creación de usuarios.

Flujo completo:
1. Leer y validar datos del Excel
2. Detectar usuarios existentes en Office 365
3. Mostrar resumen y solicitar confirmación
4. Crear usuarios en Office 365 con asignación de grupos
5. Crear usuarios en AppConnecto
6. Enviar correos de bienvenida con credenciales
7. Generar reportes en logs/

Uso:
    python main.py ruta/al/archivo.xlsx
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime
from loguru import logger

from app.config import get_settings
from app.user_processor import UserProcessor
from app.graph_api import GraphAPIClient
from app.user_creator import UserCreator
from app.appconnecto import AppConnectoClient
from app.email_sender import EmailSender

settings = get_settings()


def setup_logging():
    """Configura el sistema de logging."""
    # Crear directorio de logs si no existe
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    # Archivo de log con timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = logs_dir / f"automation_{timestamp}.log"

    # Configurar loguru
    logger.add(
        log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
        level=settings.log_level
    )

    return logs_dir, timestamp


def print_summary(new_users: list, existing_users: list):
    """Imprime resumen de usuarios a procesar."""
    print("\n" + "="*80)
    print("RESUMEN DE USUARIOS")
    print("="*80)
    print(f"\n📊 Total de usuarios en Excel: {len(new_users) + len(existing_users)}")
    print(f"   ✅ Usuarios nuevos a crear: {len(new_users)}")
    print(f"   ⚠️  Usuarios que ya existen: {len(existing_users)}")

    if new_users:
        print("\n👤 USUARIOS NUEVOS:")
        for i, user in enumerate(new_users, 1):
            print(f"   {i}. {user['full_name']} {user['full_last_name']}")
            print(f"      📧 Email institucional: {user['institutional_email']}")
            print(f"      🆔 Documento: {user['identification_id']}")
            print(f"      👥 Tipo: {user['vinculation_type']}")

    if existing_users:
        print("\n⚠️  USUARIOS EXISTENTES (se omitirán):")
        for i, user in enumerate(existing_users, 1):
            print(f"   {i}. {user['full_name']} {user['full_last_name']}")
            print(f"      📧 Email existente: {user['institutional_email']}")

    print("\n" + "="*80)


def get_user_confirmation() -> bool:
    """Solicita confirmación del usuario para continuar."""
    while True:
        response = input("\n¿Desea continuar con la creación de usuarios? (S/N): ").strip().upper()
        if response in ['S', 'SI', 'SÍ', 'Y', 'YES']:
            return True
        elif response in ['N', 'NO']:
            return False
        print("⚠️  Por favor, responda 'S' o 'N'")


async def process_office365_users(user_creator: UserCreator, users: list) -> list:
    """
    Procesa creación de usuarios en Office 365.

    Args:
        user_creator: Instancia de UserCreator
        users: Lista de usuarios con status='new'

    Returns:
        Lista de usuarios con información de creación agregada
    """
    print("\n" + "="*80)
    print("📝 FASE 1: CREACIÓN EN OFFICE 365")
    print("="*80)

    # UserCreator.create_users() filtra automáticamente solo los usuarios con status='new'
    results = await user_creator.create_users(users, create_in_office365=True)

    # Filtrar solo usuarios creados exitosamente
    created_users = [u for u in results if u.get('office365_created') and u.get('password_generated')]

    return created_users


async def process_appconnecto_users(users: list, headless: bool = True) -> dict:
    """
    Procesa creación de usuarios en AppConnecto.

    Args:
        users: Lista de usuarios a crear
        headless: Si True, ejecuta en modo headless

    Returns:
        Diccionario con estadísticas
    """
    print("\n" + "="*80)
    print("🌐 FASE 2: CREACIÓN EN APPCONNECTO")
    print("="*80)

    created = []
    already_exist = []
    failed = []

    client = AppConnectoClient(headless=headless, debug_screenshots=False)

    try:
        # Login
        login_success = await client.login()
        if not login_success:
            logger.error("❌ No se pudo hacer login en AppConnecto")
            print("❌ No se pudo hacer login en AppConnecto")
            return {
                "created": [],
                "already_exist": [],
                "failed": users
            }

        # Crear usuarios uno por uno
        for i, user in enumerate(users, 1):
            print(f"\n[{i}/{len(users)}] Procesando: {user['full_name']} {user['full_last_name']}")

            result = await client.create_user(user)

            if result['status'] == 'created':
                print(f"   ✅ Usuario creado en AppConnecto")
                created.append(user)
            elif result['status'] == 'already_exists':
                print(f"   ⚠️  Usuario ya existe en AppConnecto")
                already_exist.append(user)
            else:
                print(f"   ❌ Error: {result.get('error', 'Error desconocido')}")
                failed.append(user)
                logger.error(f"Error en AppConnecto para {user['identification_id']}: {result.get('error')}")

    finally:
        await client.close()

    return {
        "created": created,
        "already_exist": already_exist,
        "failed": failed
    }


async def process_welcome_emails(sender: EmailSender, users: list) -> dict:
    """
    Procesa envío de correos de bienvenida.

    Args:
        sender: Instancia de EmailSender
        users: Lista de usuarios a enviar correos

    Returns:
        Diccionario con estadísticas
    """
    print("\n" + "="*80)
    print("📧 FASE 3: ENVÍO DE CORREOS DE BIENVENIDA")
    print("="*80)

    results = await sender.send_welcome_emails(users)

    print(f"\n✅ Correos enviados: {len(results['sent'])}")
    if results['sent']:
        for user in results['sent']:
            print(f"   - {user['name']} ({user['email']})")

    if results['failed']:
        print(f"\n❌ Correos fallidos: {len(results['failed'])}")
        for user in results['failed']:
            print(f"   - {user['name']} ({user['email']}): {user['error']}")

    return results


def save_reports(logs_dir: Path, timestamp: str, office365_users: list,
                 appconnecto_results: dict, email_results: dict):
    """Guarda reportes en archivos JSON."""
    print("\n" + "="*80)
    print("💾 GUARDANDO REPORTES")
    print("="*80)

    # Reporte de usuarios creados en Office 365
    office365_report = logs_dir / f"usuarios_office365_{timestamp}.json"
    with open(office365_report, 'w', encoding='utf-8') as f:
        json.dump(office365_users, f, indent=2, ensure_ascii=False)
    print(f"✅ Reporte Office 365: {office365_report}")

    # Reporte de AppConnecto
    appconnecto_report = logs_dir / f"usuarios_appconnecto_{timestamp}.json"
    with open(appconnecto_report, 'w', encoding='utf-8') as f:
        json.dump({
            "created": [
                {
                    "name": f"{u['full_name']} {u['full_last_name']}",
                    "identification_id": u['identification_id']
                }
                for u in appconnecto_results['created']
            ],
            "already_exist": [
                {
                    "name": f"{u['full_name']} {u['full_last_name']}",
                    "identification_id": u['identification_id']
                }
                for u in appconnecto_results['already_exist']
            ],
            "failed": [
                {
                    "name": f"{u['full_name']} {u['full_last_name']}",
                    "identification_id": u['identification_id']
                }
                for u in appconnecto_results['failed']
            ]
        }, f, indent=2, ensure_ascii=False)
    print(f"✅ Reporte AppConnecto: {appconnecto_report}")

    # Reporte de correos
    email_report = logs_dir / f"correos_enviados_{timestamp}.json"
    with open(email_report, 'w', encoding='utf-8') as f:
        json.dump(email_results, f, indent=2, ensure_ascii=False)
    print(f"✅ Reporte correos: {email_report}")

    # Reporte consolidado
    consolidated_report = logs_dir / f"reporte_consolidado_{timestamp}.json"
    with open(consolidated_report, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": timestamp,
            "office365": {
                "total": len(office365_users),
                "users": office365_users
            },
            "appconnecto": {
                "created": len(appconnecto_results['created']),
                "already_exist": len(appconnecto_results['already_exist']),
                "failed": len(appconnecto_results['failed'])
            },
            "emails": {
                "sent": len(email_results['sent']),
                "failed": len(email_results['failed'])
            }
        }, f, indent=2, ensure_ascii=False)
    print(f"✅ Reporte consolidado: {consolidated_report}")


def print_final_summary(office365_users: list, appconnecto_results: dict, email_results: dict):
    """Imprime resumen final de la ejecución."""
    print("\n" + "="*80)
    print("📊 RESUMEN FINAL")
    print("="*80)

    print(f"\n📝 OFFICE 365:")
    print(f"   ✅ Usuarios creados: {len(office365_users)}")

    print(f"\n🌐 APPCONNECTO:")
    print(f"   ✅ Creados: {len(appconnecto_results['created'])}")
    print(f"   ⚠️  Ya existían: {len(appconnecto_results['already_exist'])}")
    print(f"   ❌ Fallidos: {len(appconnecto_results['failed'])}")

    print(f"\n📧 CORREOS:")
    print(f"   ✅ Enviados: {len(email_results['sent'])}")
    print(f"   ❌ Fallidos: {len(email_results['failed'])}")

    print("\n" + "="*80)
    print("✨ PROCESO COMPLETADO")
    print("="*80)


async def main():
    """Función principal del script."""
    # Verificar argumentos
    if len(sys.argv) < 2:
        print("❌ Error: Debe proporcionar la ruta del archivo Excel")
        print("Uso: python main.py ruta/al/archivo.xlsx")
        sys.exit(1)

    excel_path = sys.argv[1]

    # Configurar logging
    logs_dir, timestamp = setup_logging()
    logger.info("="*80)
    logger.info("INICIANDO PROCESO DE AUTOMATIZACIÓN DE USUARIOS")
    logger.info("="*80)

    try:
        # 1. Procesar Excel y detectar usuarios existentes
        print("\n🔍 PROCESANDO ARCHIVO EXCEL...")
        processor = UserProcessor()
        all_users = await processor.process_file(excel_path, skip_rows=0)

        # 2. Separar usuarios nuevos y existentes (usando el campo 'status')
        new_users = [u for u in all_users if u.get('status') == 'new']
        existing_users = [u for u in all_users if u.get('status') == 'existing']

        # 3. Mostrar resumen y solicitar confirmación
        print_summary(new_users, existing_users)

        if not new_users:
            print("\n⚠️  No hay usuarios nuevos para crear. Finalizando.")
            return

        if not get_user_confirmation():
            print("\n❌ Proceso cancelado por el usuario.")
            return

        # 4. Inicializar clientes
        print("\n🔐 Autenticando con servicios...")
        graph_client = GraphAPIClient()
        user_creator = UserCreator(graph_client)
        email_sender = EmailSender(graph_client)

        # 5. Crear usuarios en Office 365
        # Pasar todos los usuarios (new_users ya tienen status='new')
        office365_users = await process_office365_users(user_creator, new_users)

        if not office365_users:
            print("\n❌ No se pudo crear ningún usuario en Office 365. Finalizando.")
            return

        print(f"\n✅ {len(office365_users)} usuarios creados exitosamente en Office 365")

        # 6. Crear usuarios en AppConnecto
        # Preguntar si desea modo headless
        headless_response = input("\n¿Ejecutar AppConnecto en modo headless (sin navegador visible)? (S/N): ").strip().upper()
        headless = headless_response in ['S', 'SI', 'SÍ', 'Y', 'YES']

        appconnecto_results = await process_appconnecto_users(office365_users, headless=headless)

        # 7. Enviar correos de bienvenida
        # Solo a usuarios creados exitosamente en Office 365 con password_generated
        users_for_email = [u for u in office365_users if u.get('password_generated')]

        if users_for_email:
            email_response = input("\n¿Desea enviar correos de bienvenida ahora? (S/N): ").strip().upper()
            if email_response in ['S', 'SI', 'SÍ', 'Y', 'YES']:
                email_results = await process_welcome_emails(email_sender, users_for_email)
            else:
                print("\n⚠️  Envío de correos omitido.")
                email_results = {"sent": [], "failed": [], "total": 0}
        else:
            print("\n⚠️  No hay usuarios para enviar correos.")
            email_results = {"sent": [], "failed": [], "total": 0}

        # 8. Guardar reportes
        save_reports(logs_dir, timestamp, office365_users, appconnecto_results, email_results)

        # 9. Mostrar resumen final
        print_final_summary(office365_users, appconnecto_results, email_results)

        logger.info("Proceso completado exitosamente")

    except Exception as e:
        logger.error(f"❌ Error en el proceso principal: {e}")
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
