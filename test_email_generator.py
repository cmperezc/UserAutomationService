"""
Script de prueba para generación de emails institucionales.

Procesa el archivo Excel real y genera emails institucionales únicos
para cada estudiante, verificando contra Office 365.
"""

import asyncio
import json
from pathlib import Path
from loguru import logger
from app.user_processor import process_users


async def main():
    """Ejecuta el procesamiento completo de usuarios."""

    print("=" * 80)
    print("GENERACIÓN DE EMAILS INSTITUCIONALES")
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
        # Procesar archivo
        print("📂 Archivo: Solicitud correos prueba.xlsx")
        print()

        users = await process_users("Solicitud correos prueba.xlsx")

        print()
        print("=" * 80)
        print(f"✅ PROCESAMIENTO EXITOSO: {len(users)} USUARIOS")
        print("=" * 80)
        print()

        # Mostrar resumen por usuario
        for i, user in enumerate(users, 1):
            status = user.get('status', 'unknown')
            status_emoji = "✅" if status == "new" else "⚠️ "
            status_note = "" if status == "new" else " (no crear en O365)"

            print(f"{i:2}. {status_emoji} {user['full_name']} {user['full_last_name']}{status_note}")
            print(f"    ID: {user['identification_id']} ({user['type_document']})")
            print(f"    Email personal: {user['email_personal']}")
            print(f"    Email institucional: {user['institutional_email']}")
            print(f"    Estado: {user.get('status_message', 'Desconocido')}")
            print()

        # Crear directorio logs si no existe
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)

        # Guardar JSON completo
        output_file = logs_dir / "usuarios_con_emails.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(users, f, ensure_ascii=False, indent=2)

        print("=" * 80)
        print(f"💾 JSON guardado en: {output_file}")
        print("=" * 80)
        print()

        # Resumen de usuarios
        new_count = sum(1 for u in users if u.get('status') == 'new')
        existing_count = sum(1 for u in users if u.get('status') == 'existing')

        print("=" * 80)
        print("RESUMEN")
        print("=" * 80)
        print(f"Total usuarios:    {len(users)}")
        print(f"✅ Nuevos:         {new_count}")
        print(f"⚠️  Existentes:     {existing_count}")
        print("=" * 80)
        print()

        # Análisis de duplicados en nombres
        print("ANÁLISIS DE DUPLICADOS:")
        print()

        name_counts: dict[str, list[dict]] = {}
        for user in users:
            key = f"{user['first_name']} {user['first_last_name']}"
            if key not in name_counts:
                name_counts[key] = []
            name_counts[key].append(user)

        duplicates_found = False
        for name, user_list in name_counts.items():
            if len(user_list) > 1:
                duplicates_found = True
                print(f"📋 Nombre duplicado: {name} ({len(user_list)} usuarios)")
                for user in user_list:
                    print(f"   → {user['institutional_email']}")
                print()

        if not duplicates_found:
            print("✓ No se encontraron nombres duplicados en el batch")
            print()

        # Resumen de normalización
        print("=" * 80)
        print("CASOS DE NORMALIZACIÓN APLICADOS:")
        print("=" * 80)
        print()

        for i, user in enumerate(users, 1):
            normalizations = []

            # Detectar si tiene tildes en el nombre original
            if any(c in user['full_name'] for c in 'áéíóúÁÉÍÓÚñÑ'):
                normalizations.append("eliminación de tildes")

            # Detectar si el email tiene sufijo del segundo apellido
            base_email = f"{user['first_name'].lower()}.{user['first_last_name'].lower()}"
            email_part = user['institutional_email'].split('@')[0]

            if len(email_part) > len(base_email) and not email_part[-1].isdigit():
                normalizations.append("agregó letras del segundo apellido")

            # Detectar si tiene sufijo numérico
            if email_part[-1].isdigit():
                normalizations.append("agregó sufijo numérico")

            if normalizations:
                print(f"{i}. {user['full_name']} {user['full_last_name']}")
                print(f"   → {user['institutional_email']}")
                print(f"   Normalización: {', '.join(normalizations)}")
                print()

    except Exception as e:
        print()
        print("=" * 80)
        print("❌ ERROR EN EL PROCESAMIENTO")
        print("=" * 80)
        print(f"Tipo: {type(e).__name__}")
        print(f"Mensaje: {str(e)}")
        print()

        # Mostrar traceback completo si es útil
        import traceback
        print("Traceback:")
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
