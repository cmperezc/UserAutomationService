"""
Creador de usuarios en Office 365.

Este módulo orquesta la creación de usuarios nuevos en Office 365
y su asignación a los grupos correspondientes.
"""

import asyncio
from loguru import logger
from app.graph_api import GraphAPIClient
from app.password_generator import generate_secure_password
from app.config import get_settings

settings = get_settings()


class UserCreator:
    """
    Orquesta la creación de usuarios en Office 365.

    Crea usuarios nuevos y los asigna a grupos según su tipo de vinculación.
    """

    def __init__(self, graph_client: GraphAPIClient):
        """
        Inicializa el creador de usuarios.

        Args:
            graph_client: Cliente de Graph API configurado
        """
        self.graph_client = graph_client

    def _get_group_for_vinculation(self, vinculation_type: str) -> str:
        """
        Determina el grupo según el tipo de vinculación.

        Args:
            vinculation_type: Tipo de vinculación ("Estudiante" o "Docente")

        Returns:
            Nombre del grupo de Office 365
        """
        if vinculation_type == "Estudiante":
            return settings.student_group
        elif vinculation_type == "Docente":
            return settings.teacher_group
        else:
            logger.warning(f"Tipo de vinculación desconocido: {vinculation_type}. Usando grupo de estudiantes por defecto.")
            return settings.student_group

    async def _assign_to_group_with_retry(
        self,
        user_id: str,
        group_id: str,
        group_name: str,
        max_attempts: int = 3
    ) -> bool:
        """
        Asigna usuario a grupo con reintentos.

        Args:
            user_id: ID del usuario
            group_id: ID del grupo
            group_name: Nombre del grupo
            max_attempts: Número máximo de intentos

        Returns:
            True si se asignó exitosamente, False si falló después de todos los intentos
        """
        for attempt in range(1, max_attempts + 1):
            logger.info(f"Asignando a grupo: {group_name}... (intento {attempt}/{max_attempts})")

            success = await self.graph_client.add_user_to_group(
                user_id=user_id,
                group_id=group_id,
                group_name=group_name
            )

            if success:
                return True

            # Si falló y hay más intentos, esperar antes de reintentar
            if attempt < max_attempts:
                logger.warning(f"Fallo al asignar grupo, reintentando en 5 segundos (intento {attempt + 1}/{max_attempts})...")
                await asyncio.sleep(5)

        # Después de todos los intentos, reportar error
        logger.error(f"No se pudo asignar grupo después de {max_attempts} intentos")
        return False

    async def create_users(self, users: list[dict], create_in_office365: bool = True) -> list[dict]:
        """
        Crea usuarios nuevos en Office 365.

        Args:
            users: Lista de usuarios procesados (con status="new" o "existing")
            create_in_office365: Si False, solo genera datos sin crear en O365

        Returns:
            Lista de usuarios con campos adicionales:
                - office365_created: True/False
                - password_generated: Contraseña temporal
                - group_assigned: Nombre del grupo
                - creation_error: Mensaje de error si falló

        Example:
            >>> creator = UserCreator(graph_client)
            >>> results = await creator.create_users(users)
        """
        # Filtrar solo usuarios nuevos
        new_users = [u for u in users if u.get('status') == 'new']
        existing_users = [u for u in users if u.get('status') == 'existing']

        logger.info(f"Creando {len(new_users)} usuarios nuevos (ignorando {len(existing_users)} existentes)")

        results = []
        created_without_group = []  # Track usuarios creados pero sin grupo

        for user in new_users:
            try:
                # Generar contraseña
                password = generate_secure_password(settings.password_length)

                # Determinar grupo según tipo de vinculación
                group_name = self._get_group_for_vinculation(user['vinculation_type'])

                if create_in_office365:
                    # Crear usuario en Office 365
                    creation_result = await self.graph_client.create_user({
                        "display_name": f"{user['full_name']} {user['full_last_name']}",
                        "email": user['institutional_email'],
                        "password": password
                    })

                    if creation_result['success']:
                        user_id = creation_result['user_id']

                        # DELAY: Esperar propagación en Azure AD
                        logger.info("Usuario creado, esperando 15 segundos para propagación en Azure AD...")
                        await asyncio.sleep(15)

                        # Obtener ID del grupo
                        group_id = await self.graph_client.get_group_id(group_name)

                        if group_id:
                            # Asignar a grupo con reintentos
                            group_assigned = await self._assign_to_group_with_retry(
                                user_id=user_id,
                                group_id=group_id,
                                group_name=group_name,
                                max_attempts=3
                            )

                            # Actualizar datos del usuario
                            user['office365_created'] = True
                            user['office365_user_id'] = user_id
                            user['password_generated'] = password
                            user['group_assigned'] = group_name if group_assigned else None
                            user['creation_error'] = None

                            if not group_assigned:
                                # Guardar en lista de usuarios sin grupo
                                created_without_group.append({
                                    "name": f"{user['full_name']} {user['full_last_name']}",
                                    "email": user['institutional_email'],
                                    "user_id": user_id,
                                    "password": password,
                                    "group_pending": group_name
                                })
                                logger.error(
                                    f"Usuario {user['institutional_email']} creado pero NO asignado a grupo después de 3 intentos"
                                )
                        else:
                            # Usuario creado pero grupo no encontrado
                            user['office365_created'] = True
                            user['office365_user_id'] = user_id
                            user['password_generated'] = password
                            user['group_assigned'] = None
                            user['creation_error'] = f"Grupo '{group_name}' no encontrado"

                            # Guardar en lista de usuarios sin grupo
                            created_without_group.append({
                                "name": f"{user['full_name']} {user['full_last_name']}",
                                "email": user['institutional_email'],
                                "user_id": user_id,
                                "password": password,
                                "group_pending": group_name
                            })
                            logger.error(f"Grupo '{group_name}' no encontrado para {user['institutional_email']}")
                    else:
                        # Error al crear usuario
                        user['office365_created'] = False
                        user['password_generated'] = password  # Guardar para reintentar
                        user['group_assigned'] = None
                        user['creation_error'] = creation_result.get('error', 'Error desconocido')
                        logger.error(
                            f"Error creando usuario {user['institutional_email']}: {user['creation_error']}"
                        )
                else:
                    # Modo simulación: solo generar datos sin crear
                    user['office365_created'] = False
                    user['password_generated'] = password
                    user['group_assigned'] = group_name
                    user['creation_error'] = None
                    logger.info(f"[SIMULACIÓN] Usuario {user['institutional_email']} preparado (no creado)")

                results.append(user)

            except Exception as e:
                # Error inesperado
                user['office365_created'] = False
                user['password_generated'] = None
                user['group_assigned'] = None
                user['creation_error'] = str(e)
                logger.error(f"Error inesperado creando {user.get('institutional_email')}: {str(e)}")
                results.append(user)

        # Agregar usuarios existentes sin modificar
        for user in existing_users:
            user['office365_created'] = False
            user['password_generated'] = None
            user['group_assigned'] = None
            user['creation_error'] = None
            results.append(user)

        # Resumen con tres categorías
        created_with_group = sum(
            1 for u in results
            if u.get('office365_created') and u.get('group_assigned')
        )
        created_no_group = len(created_without_group)
        errors = sum(
            1 for u in results
            if u.get('office365_created') is False and u.get('status') == 'new'
        )

        logger.info("=" * 80)
        logger.info("RESUMEN DE CREACIÓN")
        logger.info("=" * 80)
        logger.info(f"✅ Creados y asignados: {created_with_group}")

        if created_no_group > 0:
            logger.warning(f"⚠️  Creados SIN grupo (asignar manualmente): {created_no_group}")
            for user_info in created_without_group:
                logger.warning(f"   - {user_info['name']} ({user_info['email']})")
                logger.warning(f"     Grupo pendiente: {user_info['group_pending']}")

        if errors > 0:
            logger.error(f"❌ Errores en creación: {errors}")

        logger.info("=" * 80)

        # Agregar lista de usuarios sin grupo al resultado para el JSON
        if created_without_group:
            for result in results:
                if result.get('status') == 'metadata':
                    continue
                result['created_without_group_list'] = created_without_group
                break
            else:
                # Si no hay metadata, agregar un item especial
                results.append({
                    'status': 'metadata',
                    'created_without_group': created_without_group
                })

        return results


async def create_users_in_office365(
    users: list[dict],
    graph_client: GraphAPIClient,
    create_in_office365: bool = True
) -> list[dict]:
    """
    Función helper para crear usuarios de forma simple.

    Args:
        users: Lista de usuarios a crear
        graph_client: Cliente de Graph API
        create_in_office365: Si False, solo simula la creación

    Returns:
        Lista de usuarios con resultados de creación

    Example:
        >>> from app.graph_api import get_graph_client
        >>> graph_client = get_graph_client()
        >>> results = await create_users_in_office365(users, graph_client)
    """
    creator = UserCreator(graph_client)
    return await creator.create_users(users, create_in_office365)
