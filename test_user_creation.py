"""
Script de prueba para crear usuarios en Office 365.

Procesa el archivo Excel, muestra usuarios a crear,
pide confirmación y crea los usuarios en Office 365.
"""

import asyncio
import json
from pathlib import Path
from loguru import logger
from app.user_processor import UserProcessor


async def main():
    """Ejecuta el flujo completo de creación de usuarios."""

    print("=" * 80)
    print("CREACIÓN DE USUARIOS EN OFFICE 365")
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

        # Filtrar usuarios nuevos
        new_users = [u for u in users if u.get('status') == 'new']
        existing_users = [u for u in users if u.get('status') == 'existing']

        print()
        print("=" * 80)
        print(f"USUARIOS A CREAR: {len(new_users)}")
        print("=" * 80)
        print()

        if len(new_users) == 0:
            print("⚠️  No hay usuarios nuevos para crear.")
            print(f"   Todos los {len(existing_users)} usuarios ya existen en Office 365.")
            print()
            return

        # Mostrar usuarios a crear
        for i, user in enumerate(new_users, 1):
            group_name = processor.user_creator._get_group_for_vinculation(user['vinculation_type'])
            print(f"{i}. {user['full_name']} {user['full_last_name']}")
            print(f"   Email: {user['institutional_email']}")
            print(f"   Grupo: {group_name}")
            print()

        # Pedir confirmación
        print("=" * 80)
        response = input(f"¿Crear estos {len(new_users)} usuarios en Office 365? (s/n): ").strip().lower()
        print()

        if response != 's':
            print("❌ Creación cancelada por el usuario")
            print()
            return

        # Paso 2: Crear usuarios
        print("=" * 80)
        print("CREANDO USUARIOS...")
        print("=" * 80)
        print()

        users_created = await processor.create_new_users(users, create_in_office365=True)

        # Mostrar resultados
        print()
        print("=" * 80)
        print("RESULTADOS DE CREACIÓN")
        print("=" * 80)
        print()

        created_count = 0
        error_count = 0

        for user in users_created:
            if user.get('status') == 'new':
                if user.get('office365_created'):
                    created_count += 1
                    print(f"✅ {user['full_name']} {user['full_last_name']}")
                    print(f"   Email: {user['institutional_email']}")
                    print(f"   Contraseña: {user.get('password_generated', 'N/A')}")
                    print(f"   Grupo: {user.get('group_assigned', 'No asignado')}")
                    print()
                else:
                    error_count += 1
                    print(f"❌ {user['full_name']} {user['full_last_name']}")
                    print(f"   Email: {user['institutional_email']}")
                    print(f"   Error: {user.get('creation_error', 'Error desconocido')}")
                    print()

        # Guardar JSON
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)

        output_file = logs_dir / "usuarios_creados.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(users_created, f, ensure_ascii=False, indent=2)

        print("=" * 80)
        print(f"💾 JSON guardado en: {output_file}")
        print("=" * 80)
        print()

        # Resumen final con tres categorías
        created_with_group = sum(
            1 for u in users_created
            if u.get('office365_created') and u.get('group_assigned')
        )

        # Extraer lista de usuarios sin grupo
        created_without_group_list = []
        for user in users_created:
            if user.get('created_without_group_list'):
                created_without_group_list = user['created_without_group_list']
                break
            elif user.get('status') == 'metadata' and user.get('created_without_group'):
                created_without_group_list = user['created_without_group']
                break

        print("=" * 80)
        print("RESUMEN")
        print("=" * 80)
        print(f"Total usuarios procesados:       {len(users)}")
        print(f"Usuarios ya existentes:          {len(existing_users)}")
        print(f"Usuarios nuevos:                 {len(new_users)}")
        print(f"✅ Creados y asignados:          {created_with_group}")

        if created_without_group_list:
            print(f"⚠️  Creados SIN grupo (manual):     {len(created_without_group_list)}")
            for user_info in created_without_group_list:
                print(f"    - {user_info['name']} ({user_info['email']})")
                print(f"      Grupo pendiente: {user_info['group_pending']}")
                print(f"      Contraseña: {user_info['password']}")

        print(f"❌ Errores en creación:          {error_count}")
        print("=" * 80)
        print()

        if created_count > 0:
            print("⚠️  IMPORTANTE:")
            print("   - Las contraseñas son temporales")
            print("   - Los usuarios deben cambiarlas al primer inicio de sesión")
            print("   - Guarda el archivo JSON con las credenciales")
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
