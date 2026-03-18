"""
Script de prueba para exportar miembros del grupo "Administrativos Licencia A5" a CSV.
"""
import asyncio
import csv
from app.graph_api import get_graph_client
from loguru import logger


async def get_group_members(group_name: str) -> list[dict]:
    """
    Obtiene todos los miembros de un grupo de seguridad.

    Args:
        group_name: Nombre del grupo a buscar

    Returns:
        Lista de diccionarios con DisplayName y UserPrincipalName de cada miembro
    """
    client = get_graph_client()

    # 1. Buscar el grupo por nombre
    group_id = await client.get_group_id(group_name)

    if not group_id:
        logger.error(f"No se encontró el grupo: {group_name}")
        return []

    logger.info(f"Grupo encontrado: {group_name} (ID: {group_id})")

    # 2. Obtener todos los miembros con paginación
    token = client.get_token()
    headers = {"Authorization": f"Bearer {token}"}

    members = []
    url = f"https://graph.microsoft.com/v1.0/groups/{group_id}/members?$select=displayName,userPrincipalName,mail&$top=999"

    import aiohttp
    async with aiohttp.ClientSession() as session:
        while url:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()

                    for member in data.get('value', []):
                        # Solo incluir usuarios (no grupos anidados)
                        if member.get('@odata.type') == '#microsoft.graph.user' or 'userPrincipalName' in member:
                            members.append({
                                'DisplayName': member.get('displayName', ''),
                                'UserPrincipalName': member.get('userPrincipalName', ''),
                                'Mail': member.get('mail', '')
                            })

                    # Siguiente página si existe
                    url = data.get('@odata.nextLink')
                else:
                    error_text = await response.text()
                    logger.error(f"Error obteniendo miembros: {error_text}")
                    break

    logger.info(f"Se encontraron {len(members)} miembros en el grupo")
    return members


def export_to_csv(members: list[dict], filename: str = "MiembrosA5.csv"):
    """
    Exporta la lista de miembros a un archivo CSV.

    Args:
        members: Lista de diccionarios con datos de miembros
        filename: Nombre del archivo de salida
    """
    if not members:
        logger.warning("No hay miembros para exportar")
        return

    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['DisplayName', 'UserPrincipalName', 'Mail'])
        writer.writeheader()
        writer.writerows(members)

    logger.info(f"Archivo exportado: {filename} ({len(members)} registros)")


async def main():
    """Función principal"""
    group_name = "Administrativos Licencia A5"

    logger.info(f"Iniciando exportación de miembros del grupo: {group_name}")

    # Obtener miembros
    members = await get_group_members(group_name)

    # Exportar a CSV
    export_to_csv(members, "MiembrosA5.csv")

    # Mostrar primeros 5 como preview
    if members:
        print("\n--- Preview (primeros 5 miembros) ---")
        for m in members[:5]:
            print(f"  {m['DisplayName']} | {m['UserPrincipalName']}")
        print(f"  ... y {len(members) - 5} más")


if __name__ == "__main__":
    asyncio.run(main())
