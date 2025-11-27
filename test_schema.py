"""
Script de prueba para validar el UserSchema.

Ejecuta casos de prueba para verificar que las validaciones
y normalizaciones del schema funcionan correctamente.
"""

from pydantic import ValidationError
from app.schemas import UserSchema


def test_case(name: str, data: dict, should_fail: bool = False) -> bool:
    """
    Ejecuta un caso de prueba del schema.

    Args:
        name: Nombre descriptivo del caso
        data: Datos a validar
        should_fail: True si se espera que falle la validación

    Returns:
        bool: True si el test pasó correctamente
    """
    try:
        user = UserSchema(**data)
        user.extract_names_for_email()

        if should_fail:
            print(f"❌ {name}")
            print(f"   FALLÓ: Se esperaba ValidationError pero pasó la validación")
            print(f"   Datos: {data}")
            print()
            return False
        else:
            print(f"✅ {name}")
            print(f"   full_name: {user.full_name}")
            print(f"   full_last_name: {user.full_last_name}")
            print(f"   first_name: {user.first_name}")
            print(f"   first_last_name: {user.first_last_name}")
            print(f"   second_last_name: '{user.second_last_name}'")
            print(f"   type_document: {user.type_document}")
            print(f"   identification_id: {user.identification_id}")
            print()
            return True

    except ValidationError as e:
        if should_fail:
            print(f"✅ {name}")
            print(f"   ValidationError capturado correctamente:")
            # Mostrar primer error
            error = e.errors()[0]
            print(f"   - Campo: {error['loc'][0]}")
            print(f"   - Mensaje: {error['msg']}")
            print()
            return True
        else:
            print(f"🔥 {name}")
            print(f"   FALLÓ: ValidationError inesperado")
            print(f"   Errores:")
            for error in e.errors():
                print(f"   - {error['loc'][0]}: {error['msg']}")
            print()
            return False


def run_tests():
    """Ejecuta todos los casos de prueba."""

    print("=" * 70)
    print("PRUEBAS DE VALIDACIÓN - UserSchema")
    print("=" * 70)
    print()

    results = []

    # Datos base válidos para reutilizar
    base_valid_data = {
        "request_type": "Apertura",
        "full_name": "Juan Carlos",
        "full_last_name": "Perez Lopez",
        "type_document": "C.C",
        "identification_id": "123456789",
        "vinculation_type": "Estudiante",
        "academic_program": "FISIOTERAPIA",
        "email_personal": "test@gmail.com"
    }

    # CASO 1: Usuario válido completo
    results.append(test_case(
        "Caso 1: Usuario válido completo",
        {
            "request_type": "Apertura",
            "full_name": "LAURA SOFIA",
            "full_last_name": "BECERRA SANDOVAL",
            "type_document": "C.C",
            "identification_id": "1000227618",
            "vinculation_type": "Estudiante",
            "academic_program": "ESPECIALIZACIÓN: FISIOTERAPIA EN NEUROREHABILITACIÓN",
            "email_personal": "sofiabecerra251@gmail.com"
        }
    ))

    # CASO 2: Normalización de mayúsculas/minúsculas
    results.append(test_case(
        "Caso 2: Normalización de mayúsculas/minúsculas",
        {
            **base_valid_data,
            "full_name": "maría josé",
            "full_last_name": "rodriguez lopez"
        }
    ))

    # CASO 3: Apellidos con palabras especiales
    results.append(test_case(
        "Caso 3: Apellidos con palabras especiales",
        {
            **base_valid_data,
            "full_last_name": "SILVA DE LA CRUZ"
        }
    ))

    # CASO 4: Apellido sin segundo nombre
    results.append(test_case(
        "Caso 4: Apellido sin segundo nombre",
        {
            **base_valid_data,
            "full_last_name": "Gomez"
        }
    ))

    # CASO 5: Normalización de tipo documento
    results.append(test_case(
        "Caso 5: Normalización de tipo documento (CC -> C.C)",
        {
            **base_valid_data,
            "type_document": "CC"
        }
    ))

    # CASO 6: ID sin padding
    results.append(test_case(
        "Caso 6: ID sin padding de ceros",
        {
            **base_valid_data,
            "identification_id": "123"
        }
    ))

    # CASO 7: Espacios extra
    results.append(test_case(
        "Caso 7: Trimeo de espacios extra",
        {
            **base_valid_data,
            "full_name": "  Pedro  ",
            "identification_id": "  456  "
        }
    ))

    # CASO 8: ERROR - ID con letras
    results.append(test_case(
        "Caso 8: ERROR - ID con letras",
        {
            **base_valid_data,
            "identification_id": "abc123"
        },
        should_fail=True
    ))

    # CASO 9: ERROR - Email inválido
    results.append(test_case(
        "Caso 9: ERROR - Email inválido",
        {
            **base_valid_data,
            "email_personal": "not-an-email"
        },
        should_fail=True
    ))

    # CASO 10: ERROR - Tipo solicitud inválido
    results.append(test_case(
        "Caso 10: ERROR - Tipo solicitud inválido",
        {
            **base_valid_data,
            "request_type": "Actualización"
        },
        should_fail=True
    ))

    # CASOS ADICIONALES: Validar otras variaciones de documento
    print("=" * 70)
    print("CASOS ADICIONALES")
    print("=" * 70)
    print()

    results.append(test_case(
        "Caso Extra 1: Tipo documento C.E (Cédula de Extranjería)",
        {
            **base_valid_data,
            "type_document": "CE"
        }
    ))

    results.append(test_case(
        "Caso Extra 2: Apellido con 'Y' (Silva y Rodriguez)",
        {
            **base_valid_data,
            "full_last_name": "SILVA Y RODRIGUEZ"
        }
    ))

    results.append(test_case(
        "Caso Extra 3: Apellido con 'Del' (Del Carmen)",
        {
            **base_valid_data,
            "full_last_name": "DEL CARMEN RODRIGUEZ"
        }
    ))

    # RESUMEN
    print("=" * 70)
    print("RESUMEN DE RESULTADOS")
    print("=" * 70)

    passed = sum(results)
    total = len(results)

    print(f"\nCasos pasados: {passed}/{total}")

    if passed == total:
        print("🎉 ¡Todos los tests pasaron exitosamente!")
    else:
        print(f"⚠️  {total - passed} test(s) fallaron")

    print()


if __name__ == "__main__":
    run_tests()
