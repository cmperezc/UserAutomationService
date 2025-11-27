"""
Script para crear archivo Excel de prueba con datos de estudiantes.

Genera tests/fixtures/estudiantes_test.xlsx con 5 filas variadas
para probar el ExcelProcessor.
"""

import pandas as pd
from pathlib import Path


def create_test_excel():
    """Crea archivo Excel de prueba con datos variados."""

    # Datos de prueba con casos variados
    data = {
        "Tipo de Solicitud": [
            "Apertura",
            "apertura",  # Minúsculas (se normalizará)
            "Apertura",
            "Apertura",
            "Apertura"
        ],
        "Nombre": [
            "LAURA SOFIA",  # Mayúsculas
            "maría josé",   # Minúsculas con tilde
            "  Pedro  ",    # Con espacios extra
            "Ana María",    # Formato correcto
            "CARLOS ANDRES"
        ],
        "Apellido": [
            "BECERRA SANDOVAL",       # Normal
            "SILVA DE LA CRUZ",       # Con palabras especiales
            "rodriguez lopez",        # Minúsculas
            "Gomez",                  # Sin segundo apellido
            "DEL CARMEN RODRIGUEZ"    # Con "Del"
        ],
        "Tipo de Identificación": [
            "C.C",
            "CC",   # Sin puntos (se normalizará)
            "C.C",
            "CE",   # Cédula extranjería
            "C.C"
        ],
        "Número de Identificación": [
            1000227618.0,   # Float (se convertirá a string)
            123456789,      # Int
            "  456789  ",   # String con espacios
            1234567.0,      # Float
            987654321
        ],
        "Tipo de Vinculación": [
            "Estudiante",
            "estudiante",  # Minúsculas
            "Estudiante",
            "Estudiante",
            "Estudiante"
        ],
        "Dependencia Administrativa / Programa Académico": [
            "ESPECIALIZACIÓN: FISIOTERAPIA EN NEUROREHABILITACIÓN",
            "FISIOTERAPIA",
            "TERAPIA OCUPACIONAL",
            "FONOAUDIOLOGÍA",
            "ESPECIALIZACIÓN: TERAPIA MANUAL ORTOPÉDICA"
        ],
        "Correo Electrónico Personal": [
            "sofiabecerra251@gmail.com",
            "maria.silva@hotmail.com",
            "pedro.rodriguez@yahoo.com",
            "ana.gomez@gmail.com",
            "carlos.delcarmen@outlook.com"
        ]
    }

    # Crear DataFrame
    df = pd.DataFrame(data)

    # Crear directorio si no existe
    output_dir = Path(__file__).parent / "fixtures"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Guardar Excel
    output_file = output_dir / "estudiantes_test.xlsx"
    df.to_excel(output_file, index=False, engine='openpyxl')

    print(f"✅ Excel de prueba creado exitosamente")
    print(f"📁 Ubicación: {output_file}")
    print(f"📊 Filas: {len(df)}")
    print(f"📋 Columnas: {len(df.columns)}")
    print()
    print("Casos de prueba incluidos:")
    print("  - Normalización de mayúsculas/minúsculas")
    print("  - Apellidos con palabras especiales (de, del, la)")
    print("  - Apellido sin segundo nombre")
    print("  - IDs como float que se convierten a string")
    print("  - Espacios extra que se trimean")
    print("  - Tipos de documento con y sin puntos")
    print("  - Cédula de extranjería (C.E)")


if __name__ == "__main__":
    create_test_excel()
