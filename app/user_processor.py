"""
Procesador de usuarios que orquesta el flujo completo.

Este módulo coordina:
- Lectura y validación de Excel
- Obtención de emails existentes de Office 365
- Generación de emails institucionales únicos
"""

from loguru import logger
from app.excel_processor import process_excel
from app.graph_api import get_graph_client
from app.email_generator import EmailGenerator
from app.user_creator import UserCreator


class UserProcessor:
    """
    Orquesta el procesamiento completo de usuarios.

    Flujo:
    1. Procesar Excel con ExcelProcessor
    2. Obtener emails existentes de Graph API
    3. Generar email institucional para cada usuario
    4. Retornar usuarios con institutional_email asignado
    """

    def __init__(self, domain: str = "ecr.edu.co"):
        """
        Inicializa el procesador.

        Args:
            domain: Dominio para emails institucionales
        """
        self.domain = domain
        self.graph_client = get_graph_client()
        self.email_generator = EmailGenerator(domain)
        self.user_creator = UserCreator(self.graph_client)

    async def process_file(self, file_path: str, skip_rows: int = 0) -> list[dict]:
        """
        Procesa un archivo Excel completo.

        Args:
            file_path: Ruta al archivo Excel
            skip_rows: Número de filas a saltar

        Returns:
            Lista de usuarios con emails institucionales generados

        Example:
            >>> processor = UserProcessor()
            >>> users = await processor.process_file("estudiantes.xlsx")
            >>> print(users[0]['institutional_email'])
            'laura.becerra@ecr.edu.co'
        """
        logger.info(f"Iniciando procesamiento completo de archivo: {file_path}")

        # 1. Procesar Excel
        logger.info("Paso 1/3: Procesando archivo Excel...")
        users = process_excel(file_path, skip_rows)
        logger.info(f"✓ {len(users)} usuarios validados desde Excel")

        # 2. Obtener usuarios existentes de Office 365
        logger.info("Paso 2/3: Obteniendo usuarios existentes de Office 365...")
        existing_users_info = await self.graph_client.get_all_users_info(self.domain)
        self.email_generator.load_existing_users(existing_users_info)
        logger.info(f"✓ {len(existing_users_info)} usuarios existentes cargados")

        # 3. Procesar cada usuario: verificar si existe o generar email nuevo
        logger.info("Paso 3/3: Verificando usuarios y generando emails...")
        new_users = 0
        existing_users = 0

        for user in users:
            logger.info(f"Verificando usuario: {user['full_name']} {user['full_last_name']}")

            # Verificar si el usuario ya existe por nombre completo
            existing_email = self.email_generator.check_existing_user(
                full_name=user['full_name'],
                full_last_name=user['full_last_name']
            )

            if existing_email:
                # Usuario existe - asignar email existente
                user['institutional_email'] = existing_email
                user['status'] = 'existing'
                user['status_message'] = 'Usuario ya existe en Office 365'
                existing_users += 1
            else:
                # Usuario nuevo - generar email
                email = self.email_generator.generate_email(
                    first_name=user['first_name'],
                    first_last_name=user['first_last_name'],
                    second_last_name=user['second_last_name']
                )
                user['institutional_email'] = email
                user['status'] = 'new'
                user['status_message'] = 'Usuario nuevo'
                new_users += 1

        logger.info(f"✓ Procesamiento completado: {new_users} nuevos, {existing_users} existentes")
        logger.info("Procesamiento completo finalizado exitosamente")

        return users

    async def create_new_users(self, users: list[dict], create_in_office365: bool = True) -> list[dict]:
        """
        Crea usuarios nuevos en Office 365.

        Args:
            users: Lista de usuarios procesados (con status)
            create_in_office365: Si False, solo simula sin crear realmente

        Returns:
            Lista de usuarios con campos de creación agregados

        Example:
            >>> processor = UserProcessor()
            >>> users = await processor.process_file("estudiantes.xlsx")
            >>> users_created = await processor.create_new_users(users)
        """
        logger.info("Paso 4/4: Creando usuarios nuevos en Office 365...")

        users_with_creation = await self.user_creator.create_users(
            users,
            create_in_office365=create_in_office365
        )

        return users_with_creation


async def process_users(file_path: str, skip_rows: int = 0, domain: str = "ecr.edu.co") -> list[dict]:
    """
    Función helper para procesar usuarios de forma simple.

    Args:
        file_path: Ruta al archivo Excel
        skip_rows: Número de filas a saltar
        domain: Dominio para emails institucionales

    Returns:
        Lista de usuarios con emails institucionales

    Example:
        >>> import asyncio
        >>> users = asyncio.run(process_users("estudiantes.xlsx"))
    """
    processor = UserProcessor(domain)
    return await processor.process_file(file_path, skip_rows)
