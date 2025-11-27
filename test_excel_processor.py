"""
Script de prueba para el procesador de Excel.

Procesa el archivo Excel de prueba y muestra los resultados,
guardando también un JSON con los usuarios procesados.
"""

import json
from pathlib import Path
from app.excel_processor import process_excel, ExcelProcessorError


def test_excel_processor():
    """Prueba el procesador de Excel con archivo de prueba."""

    print("=" * 80)
    print("PRUEBA DEL EXCEL PROCESSOR")
    print("=" * 80)
    print()

    # Ruta al Excel de prueba
    excel_path = Path("Solicitud correos prueba.xlsx")

    # Verificar que existe
    if not excel_path.exists():
        print("❌ Error: Excel de prueba no encontrado")
        print(f"   Ruta esperada: {excel_path}")
        print()
        print("Por favor verifica que el archivo existe en la raíz del proyecto")
        return

    print(f"📂 Procesando: {excel_path}")
    print()

    try:
        # Procesar Excel
        users = process_excel(str(excel_path))

        print(f"✅ Procesamiento exitoso: {len(users)} usuarios validados")
        print()
        print("=" * 80)
        print("USUARIOS PROCESADOS")
        print("=" * 80)
        print()

        # Mostrar cada usuario
        for i, user in enumerate(users, 1):
            print(f"Usuario {i}:")
            print(f"  Tipo solicitud:      {user['request_type']}")
            print(f"  Nombre completo:     {user['full_name']}")
            print(f"  Apellido completo:   {user['full_last_name']}")
            print(f"  Tipo documento:      {user['type_document']}")
            print(f"  Número ID:           {user['identification_id']}")
            print(f"  Vinculación:         {user['vinculation_type']}")
            print(f"  Programa:            {user['academic_program']}")
            print(f"  Email personal:      {user['email_personal']}")
            print(f"  Primer nombre:       {user['first_name']}")
            print(f"  Primer apellido:     {user['first_last_name']}")
            print(f"  Segundo apellido:    '{user['second_last_name']}'")
            print()

        # Crear directorio logs si no existe
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)

        # Guardar JSON
        output_file = logs_dir / "usuarios_procesados.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(users, f, ensure_ascii=False, indent=2)

        print("=" * 80)
        print(f"💾 JSON guardado en: {output_file}")
        print("=" * 80)
        print()

        # Mostrar casos de normalización
        print("CASOS DE NORMALIZACIÓN DETECTADOS:")
        print()

        for i, user in enumerate(users, 1):
            print(f"Usuario {i}:")

            # Verificar apellidos con palabras especiales
            if any(word in user['full_last_name'].lower() for word in ['de', 'del', 'la', 'los', 'las', 'y']):
                print(f"  ✓ Apellido con palabras especiales: {user['full_last_name']}")

            # Verificar segundo apellido vacío
            if user['second_last_name'] == "":
                print(f"  ✓ Sin segundo apellido")

            # Verificar tipo documento normalizado
            if user['type_document'] in ['C.C', 'C.E']:
                print(f"  ✓ Tipo documento normalizado: {user['type_document']}")

            print()

    except ExcelProcessorError as e:
        print("❌ Error al procesar Excel:")
        print(f"   {str(e)}")
        print()

    except Exception as e:
        print("🔥 Error inesperado:")
        print(f"   {type(e).__name__}: {str(e)}")
        print()


if __name__ == "__main__":
    test_excel_processor()
