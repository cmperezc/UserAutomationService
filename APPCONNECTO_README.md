# Módulo AppConnecto - Creación Automatizada de Usuarios

## Descripción

Este módulo automatiza la creación de usuarios en AppConnecto usando Playwright. Se integra con el sistema existente de creación de usuarios en Office 365.

## Instalación

1. Instalar las dependencias:
```bash
pip install -r requirements.txt
```

2. Instalar los navegadores de Playwright:
```bash
playwright install chromium
```

## Configuración

Agregar las siguientes variables al archivo `.env`:

```env
# AppConnecto
APPCONNECTO_URL=https://ecr.appconnecto.com/es/accounts/login
APPCONNECTO_USER=1103121810
APPCONNECTO_PASS=ECR.2025
```

## Uso

### Opción 1: Script de prueba completo

```bash
python test_appconnecto.py
```

Este script:
1. Lee el archivo Excel de prueba
2. Filtra usuarios nuevos (que no existen en Office 365)
3. Hace login en AppConnecto
4. Crea cada usuario
5. Asigna roles según el tipo de vinculación
6. Muestra un resumen final

### Opción 2: Uso programático

```python
import asyncio
from app.appconnecto import AppConnectoClient

async def main():
    # Crear cliente (headless=False para ver el proceso)
    client = AppConnectoClient(headless=False)

    try:
        # Login
        success = await client.login()
        if not success:
            print("Login fallido")
            return

        # Crear un usuario
        user_data = {
            "identification_id": "1234567890",
            "full_name": "Juan Carlos",
            "full_last_name": "Perez Lopez",
            "type_document": "C.C",
            "institutional_email": "juan.perez@ecr.edu.co",
            "vinculation_type": "Estudiante"
        }

        result = await client.create_user(user_data)
        print(f"Resultado: {result}")

    finally:
        await client.close()

asyncio.run(main())
```

### Opción 3: Función helper

```python
import asyncio
from app.appconnecto import create_users_in_appconnecto

users = [
    {
        "identification_id": "1234567890",
        "full_name": "Juan Carlos",
        "full_last_name": "Perez Lopez",
        "type_document": "C.C",
        "institutional_email": "juan.perez@ecr.edu.co",
        "vinculation_type": "Estudiante"
    }
]

results = asyncio.run(create_users_in_appconnecto(users, headless=True))
print(f"Creados: {len(results['created'])}")
```

## Estructura de datos

### Entrada (user_data)

```python
{
    "identification_id": "1234567890",      # Número de documento (username)
    "full_name": "Juan Carlos",             # Nombres completos
    "full_last_name": "Perez Lopez",        # Apellidos completos
    "type_document": "C.C",                 # Tipo de documento (C.C o C.E)
    "institutional_email": "juan.perez@ecr.edu.co",  # Email institucional
    "vinculation_type": "Estudiante"        # Tipo de vinculación (Estudiante o Docente)
}
```

### Salida (resultado)

```python
{
    "success": True,                        # True si se creó exitosamente
    "username": "1234567890",               # identification_id del usuario
    "status": "created",                    # "created", "already_exists" o "error"
    "error": None                           # Mensaje de error (si falló)
}
```

### Estadísticas (create_users)

```python
{
    "created": ["1234567890", "9876543210"],           # Usuarios creados
    "already_exists": ["1111111111"],                  # Usuarios que ya existían
    "errors": [                                        # Errores
        {"username": "2222222222", "error": "timeout"}
    ],
    "total": 4                                         # Total procesados
}
```

## Mapeos

### Tipos de documento
- `"C.C"` → valor `"1"` en el select
- `"C.E"` → valor `"2"` en el select

### Tipos de vinculación → Roles
- `"Estudiante"` → rol `"Estudiantes"`
- `"Docente"` → rol `"Docentes"`

## Valores por defecto

Configurados en `app/config.py`:

- **Contraseña por defecto**: `ECR2022`
- **Fecha de nacimiento**: `1990-01-01`
- **URL del formulario**: `https://ecr.appconnecto.com/es/headquarters/principal/member/create`

## Screenshots

Los screenshots se guardan automáticamente en la carpeta `screenshots/` con timestamp:

- `01_pagina_login_YYYYMMDD_HHMMSS.png` - Página de login
- `02_credenciales_ingresadas_YYYYMMDD_HHMMSS.png` - Credenciales ingresadas
- `03_despues_login_YYYYMMDD_HHMMSS.png` - Después del login
- `formulario_lleno_{username}_YYYYMMDD_HHMMSS.png` - Formulario completado
- `resultado_{username}_YYYYMMDD_HHMMSS.png` - Resultado de creación
- `error_{username}_YYYYMMDD_HHMMSS.png` - En caso de error

## Detección de usuarios existentes

Si un usuario ya existe en AppConnecto:
- La URL no cambia después de enviar el formulario
- El sistema detecta esto y marca el usuario como `"already_exists"`
- No se considera un error, solo se registra en las estadísticas

## Manejo de errores

- **Login fallido**: Se aborta la operación y se retorna error
- **Usuario ya existe**: Se registra y continúa con el siguiente
- **Error en creación**: Se toma screenshot, se registra el error y continúa con el siguiente
- **Error crítico**: Se captura, se muestra traceback y se aborta

## Modo headless

El parámetro `headless` controla si el navegador se muestra:

- `headless=False` (recomendado para desarrollo/debug): Muestra el navegador
- `headless=True` (para producción): Ejecuta sin interfaz gráfica, más rápido

```python
# Desarrollo: ver el proceso
client = AppConnectoClient(headless=False)

# Producción: más rápido, sin interfaz
client = AppConnectoClient(headless=True)
```

## Logging

El módulo usa `loguru` para logging con los siguientes niveles:

- **INFO**: Operaciones principales (login, creación de usuarios)
- **WARNING**: Usuario ya existe
- **ERROR**: Errores en creación
- **DEBUG**: Información detallada (URLs, screenshots)

## Integración con Office 365

El flujo completo recomendado es:

1. **Procesar Excel** con `UserProcessor`
2. **Crear usuarios en Office 365** con `UserCreator`
3. **Crear usuarios en AppConnecto** con `AppConnectoClient`

```python
from app.user_processor import UserProcessor
from app.appconnecto import AppConnectoClient

async def create_users_complete():
    # 1. Procesar Excel y detectar usuarios
    processor = UserProcessor()
    users = await processor.process_file("Solicitud correos prueba.xlsx")

    # 2. Crear en Office 365
    users_created = await processor.create_new_users(users, create_in_office365=True)

    # 3. Filtrar solo los creados exitosamente
    new_users = [u for u in users_created if u.get('office365_created')]

    # 4. Crear en AppConnecto
    client = AppConnectoClient(headless=True)
    try:
        await client.login()
        results = await client.create_users(new_users)
        return results
    finally:
        await client.close()
```

## Troubleshooting

### Error: "playwright not found"
```bash
pip install playwright
playwright install chromium
```

### Error: "Login fallido"
- Verificar credenciales en `.env`
- Verificar que la URL de login es correcta
- Revisar screenshot `error_login_*.png`

### Error: "Timeout waiting for selector"
- Verificar que la página de AppConnecto está disponible
- Aumentar el timeout en `page.set_default_timeout()`
- Usar `headless=False` para ver qué está pasando

### Usuario no se crea pero no hay error
- Verificar que todos los campos requeridos tienen valores
- Revisar screenshots `formulario_lleno_*.png` y `resultado_*.png`
- Verificar mapeos de tipo de documento y roles
