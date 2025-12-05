"""
Script de prueba para crear usuarios en AppConnecto.

Procesa el archivo Excel, filtra usuarios nuevos,
hace login en AppConnecto y crea los usuarios.
"""

import asyncio
from pathlib import Path
from loguru import logger
from app.user_processor import UserProcessor
from app.appconnecto import AppConnectoClient


def print_summary(results: dict) -> None:
    """Imprime un resumen final de resultados."""
    print("\n" + "=" * 80)
    print("📊 RESUMEN FINAL - APPCONNECTO")
    print("=" * 80)
    print(f"✅ Usuarios creados:     {len(results['created'])}")
    print(f"⚠️  Ya existían:         {len(results['already_exists'])}")
    print(f"❌ Errores:              {len(results['errors'])}")
    print(f"📋 Total procesados:     {results['total']}")

    if results['created']:
        print(f"\n✅ CREADOS:")
        for user in results['created']:
            print(f"   • {user}")

    if results['already_exists']:
        print(f"\n⚠️  YA EXISTÍAN:")
        for user in results['already_exists']:
            print(f"   • {user}")

    if results['errors']:
        print(f"\n❌ ERRORES:")
        for error in results['errors']:
            print(f"   • {error['username']}: {error['error']}")

    print("=" * 80)


async def main():
    """Ejecuta el flujo completo de creación de usuarios en AppConnecto."""

    print("=" * 80)
    print("CREACIÓN DE USUARIOS EN APPCONNECTO")
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
        # Paso 1: Procesar Excel y detectar usuarios
        print("📂 Archivo: Solicitud correos prueba.xlsx")
        print()

        processor = UserProcessor()
        users = await processor.process_file("Solicitud correos prueba.xlsx")

        # Filtrar solo usuarios nuevos
        new_users = [u for u in users if u.get('status') == 'new']
        existing_users = [u for u in users if u.get('status') == 'existing']

        print()
        print("=" * 80)
        print(f"USUARIOS A CREAR EN APPCONNECTO: {len(new_users)}")
        print("=" * 80)
        print()

        if len(new_users) == 0:
            print("⚠️  No hay usuarios nuevos para crear.")
            print(f"   Todos los {len(existing_users)} usuarios ya existen en Office 365.")
            print()
            return

        # Mostrar usuarios a crear
        for i, user in enumerate(new_users, 1):
            rol = "Estudiantes" if user['vinculation_type'] == "Estudiante" else "Docentes"
            print(f"{i}. {user['full_name']} {user['full_last_name']}")
            print(f"   ID: {user['identification_id']}")
            print(f"   Email: {user['institutional_email']}")
            print(f"   Rol: {rol}")
            print()

        # Pedir confirmación
        print("=" * 80)
        response = input(f"¿Crear estos {len(new_users)} usuarios en AppConnecto? (s/n): ").strip().lower()
        print()

        if response != 's':
            print("❌ Creación cancelada por el usuario")
            print()
            return

        # Paso 2: Crear usuarios en AppConnecto
        print("=" * 80)
        print("CREANDO USUARIOS EN APPCONNECTO...")
        print("=" * 80)
        print()

        # Inicializar cliente
        # headless=False para ver el proceso
        # debug_screenshots=False para solo capturar errores (más rápido)
        client = AppConnectoClient(headless=False, debug_screenshots=False)

        try:
            # Login
            login_success = await client.login()

            if not login_success:
                print("❌ No se pudo hacer login en AppConnecto. Abortando...")
                return

            # Crear usuarios
            results = await client.create_users(new_users)

            # Mostrar resultados
            print_summary(results)

        finally:
            # Cerrar navegador
            await client.close()

        # Nota final
        print()
        print("⚠️  IMPORTANTE:")
        print("   - Los usuarios creados tienen contraseña 'ECR2022'")
        print("   - Los usuarios deben cambiarla al primer inicio de sesión")
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
