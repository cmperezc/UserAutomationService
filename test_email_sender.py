"""
Script de prueba para enviar correos de bienvenida con credenciales.

Lee usuarios desde logs/usuarios_creados.json y envía correos a sus emails personales.
"""

import asyncio
import json
from pathlib import Path
from loguru import logger
from app.graph_api import get_graph_client
from app.email_sender import EmailSender


def print_summary(results: dict) -> None:
    """Imprime un resumen final de resultados."""
    print("\n" + "=" * 80)
    print("RESUMEN DE ENVÍO")
    print("=" * 80)
    print(f"✅ Enviados: {len(results['sent'])}")
    print(f"❌ Fallidos: {len(results['failed'])}")
    print(f"📋 Total: {results['total']}")

    if results['sent']:
        print(f"\n✅ ENVIADOS:")
        for email in results['sent']:
            print(f"   • {email}")

    if results['failed']:
        print(f"\n❌ FALLIDOS:")
        for error in results['failed']:
            print(f"   • {error['email']}: {error['error']}")

    print("=" * 80)


def load_users_from_json(file_path: Path) -> list[dict]:
    """
    Carga usuarios desde el archivo JSON de logs.

    Args:
        file_path: Ruta al archivo usuarios_creados.json

    Returns:
        Lista de usuarios que tienen password_generated (creados exitosamente)
    """
    if not file_path.exists():
        print(f"❌ No se encontró el archivo: {file_path}")
        print("   Primero debes crear usuarios con test_user_creation.py")
        return []

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Filtrar solo usuarios con password_generated
    users_with_password = [
        user for user in data
        if user.get('password_generated')
    ]

    return users_with_password


async def main():
    """Ejecuta el flujo completo de envío de correos."""

    print("=" * 80)
    print("ENVÍO DE CORREOS DE BIENVENIDA")
    print("=" * 80)
    print()

    # Configurar logging
    logger.remove()  # Remover handler por defecto
    logger.add(
        lambda msg: print(msg, end=""),
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )

    try:
        # Paso 1: Cargar usuarios desde JSON
        json_path = Path("logs/usuarios_creados.json")
        print(f"📂 Cargando usuarios desde: {json_path}")
        print()

        users = load_users_from_json(json_path)

        if len(users) == 0:
            print("⚠️  No hay usuarios para enviar correos.")
            print()
            return

        print("=" * 80)
        print(f"USUARIOS PARA ENVÍO DE CORREOS: {len(users)}")
        print("=" * 80)
        print()

        # Mostrar usuarios
        for i, user in enumerate(users, 1):
            print(f"{i}. {user['full_name']} {user['full_last_name']}")
            print(f"   Email personal: {user['email_personal']}")
            print(f"   Email institucional: {user['institutional_email']}")
            print(f"   Password Office 365: {user['password_generated']}")
            print()

        # Paso 2: Mostrar preview del primer correo
        print("=" * 80)
        print("PREVIEW DEL CORREO (primer usuario)")
        print("=" * 80)
        print()

        graph_client = get_graph_client()
        sender = EmailSender(graph_client)

        first_user_html = sender.render_welcome_email(users[0])
        print(first_user_html)
        print()

        # Paso 3: Pedir confirmación
        print("=" * 80)
        response = input(f"¿Enviar {len(users)} correos de bienvenida? (s/n): ").strip().lower()
        print()

        if response != 's':
            print("❌ Envío cancelado por el usuario")
            print()
            return

        # Paso 4: Enviar correos
        print("=" * 80)
        print("ENVIANDO CORREOS...")
        print("=" * 80)
        print()

        results = await sender.send_welcome_emails(users)

        # Paso 5: Mostrar resumen
        print_summary(results)

        # Nota final
        print()
        print("⚠️  IMPORTANTE:")
        print("   - Los correos fueron enviados a los emails personales")
        print("   - Los usuarios deben revisar su bandeja de entrada")
        print("   - Si no ven el correo, revisar spam/correo no deseado")
        print()

    except Exception as e:
        print()
        print("=" * 80)
        print("❌ ERROR EN EL PROCESAMIENTO")
        print("=" * 80)
        print(f"Tipo: {type(e).__name__}")
        print(f"Mensaje: {str(e)}")
        print()

        # Mostrar traceback completo
        import traceback
        print("Traceback:")
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
