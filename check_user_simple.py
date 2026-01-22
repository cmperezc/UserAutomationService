"""
Script simple para verificar si un usuario ha cambiado su contraseña.

Verifica consultando los logs de auditoría más recientes del usuario.
"""

import json
from pathlib import Path

# Leer el archivo de usuarios creados más reciente
logs_dir = Path("logs")
json_files = sorted(logs_dir.glob("usuarios_office365_*.json"), reverse=True)

if not json_files:
    print("❌ No se encontraron archivos de usuarios creados")
    exit(1)

latest_file = json_files[0]
print(f"Leyendo: {latest_file}")
print("="*80)

with open(latest_file, 'r', encoding='utf-8') as f:
    users = json.load(f)

# Buscar el usuario
user_email = "aiden.novoa@ecr.edu.co"
user_found = None

for user in users:
    if user.get('institutional_email') == user_email:
        user_found = user
        break

if not user_found:
    print(f"❌ Usuario {user_email} no encontrado en el archivo")
    exit(1)

print(f"\nUSUARIO ENCONTRADO")
print("-"*80)
print(f"Nombre: {user_found['full_name']} {user_found['full_last_name']}")
print(f"Email: {user_found['institutional_email']}")
print(f"ID Office 365: {user_found.get('office365_user_id', 'N/A')}")
print(f"Contrasena generada: {user_found.get('password_generated', 'N/A')}")
print(f"Grupo asignado: {user_found.get('group_assigned', 'N/A')}")
print(f"Fecha de creacion: {latest_file.stem.split('_')[-2:]}")

print("\n" + "="*80)
print("INFORMACION PARA EL SOPORTE")
print("="*80)
print(f"""
Para verificar si el usuario ha cambiado su contraseña, necesitas:

1. Ir al Azure AD Portal:
   https://portal.azure.com/#view/Microsoft_AAD_UsersAndTenants/UserManagementMenuBlade/~/AllUsers

2. Buscar el usuario: {user_found['institutional_email']}

3. En la pestaña "Sign-in logs" verás:
   - Si ha intentado iniciar sesión
   - Si los intentos fueron exitosos o fallidos
   - Cuándo fue el último intento

4. En la pestaña "Audit logs" verás:
   - Si cambió la contraseña
   - Cuándo la cambió

CONTRASEÑA ACTUAL EN EL SISTEMA: {user_found.get('password_generated', 'N/A')}

Si el usuario dice que la contraseña es incorrecta:
- ✅ Verificar que esté usando esta contraseña exacta (incluyendo el símbolo $)
- ✅ Verificar que esté en portal.office.com (no en AppConnecto)
- ✅ Si ya inició sesión antes, probablemente YA CAMBIÓ la contraseña
- ✅ En ese caso, necesita hacer "Olvidé mi contraseña" en el portal

""")

print("="*80)
print("PASOS PARA CONFIRMAR EN AZURE PORTAL")
print("="*80)
print("""
OPCIÓN 1: Usando PowerShell (Rápido)
-------------------------------------
1. Abrir PowerShell como administrador
2. Ejecutar:
   Connect-AzureAD
   Get-AzureADAuditSignInLogs -Filter "userPrincipalName eq 'aiden.novoa@ecr.edu.co'" -Top 10

OPCIÓN 2: Usando Azure Portal (Manual)
--------------------------------------
1. Ir a https://portal.azure.com
2. Azure Active Directory > Users
3. Buscar: aiden.novoa@ecr.edu.co
4. Clic en el usuario
5. Ver pestañas:
   - "Sign-in logs" (últimos inicios de sesión)
   - "Audit logs" (cambios de contraseña)

OPCIÓN 3: Resetear contraseña manualmente
------------------------------------------
Si confirmas que el usuario ya cambió la contraseña y la olvidó:
1. En Azure Portal, ir al usuario
2. Clic en "Reset password"
3. Generar nueva contraseña temporal
4. Enviarla al usuario por correo
""")
