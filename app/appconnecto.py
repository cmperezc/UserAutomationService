"""
Cliente para AppConnecto usando Playwright.

Este módulo maneja la automatización de creación de usuarios en AppConnecto,
incluyendo login, creación de usuarios y asignación de roles.
"""

import asyncio
from pathlib import Path
from datetime import datetime
from loguru import logger
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from app.config import get_settings

settings = get_settings()


class AppConnectoClient:
    """
    Cliente para automatizar operaciones en AppConnecto.

    Maneja login, creación de usuarios y asignación de roles
    usando Playwright para automatización web.
    """

    def __init__(self, headless: bool = False):
        """
        Inicializa el cliente de AppConnecto.

        Args:
            headless: Si True, ejecuta el navegador en modo headless (sin interfaz gráfica)
        """
        self.headless = headless
        self.login_url = settings.appconnecto_url
        self.form_url = settings.appconnecto_form_url
        self.username = settings.appconnecto_user
        self.password = settings.appconnecto_pass

        self.playwright = None
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None

        # Configuración de screenshots
        self.screenshots_dir = Path("screenshots")
        self.screenshots_dir.mkdir(exist_ok=True)

    async def _take_screenshot(self, name: str) -> str:
        """
        Toma una captura de pantalla.

        Args:
            name: Nombre descriptivo para el screenshot

        Returns:
            Ruta del archivo creado
        """
        if not self.page:
            return ""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.screenshots_dir / f"{name}_{timestamp}.png"
        await self.page.screenshot(path=str(filename))
        logger.debug(f"📸 Captura: {filename}")
        return str(filename)

    async def _init_browser(self) -> None:
        """Inicializa el navegador y contexto de Playwright."""
        if self.browser:
            return

        logger.info("Inicializando navegador...")
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled"
            ]
        )

        self.context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080}
        )
        self.page = await self.context.new_page()
        self.page.set_default_timeout(30000)  # 30 segundos
        logger.info("✅ Navegador listo")

    async def login(self) -> bool:
        """
        Realiza el login en AppConnecto.

        Returns:
            True si el login fue exitoso, False en caso contrario

        Example:
            >>> client = AppConnectoClient()
            >>> success = await client.login()
            >>> if success:
            ...     print("Login exitoso")
        """
        try:
            await self._init_browser()
            logger.info("🔐 Iniciando sesión en AppConnecto...")

            # Navegar a la página de login
            await self.page.goto(self.login_url)
            await self.page.wait_for_selector("#username_val")
            await asyncio.sleep(1)
            await self._take_screenshot("01_pagina_login")

            # Llenar credenciales
            logger.info(f"   Usuario: {self.username}")
            await self.page.fill("#username_val", self.username)
            await self.page.fill("#password", self.password)

            # Aceptar términos y condiciones
            await self.page.check("#tyc")
            await asyncio.sleep(0.5)

            await self._take_screenshot("02_credenciales_ingresadas")

            # Click en botón de login
            await self.page.click("#btn-login")

            # Esperar a que redirija
            await asyncio.sleep(3)
            await self._take_screenshot("03_despues_login")

            # Verificar si el login fue exitoso
            current_url = self.page.url
            if "login" not in current_url.lower():
                logger.info("✅ Login exitoso")
                return True

            logger.error("❌ Login fallido - Aún en página de login")
            return False

        except Exception as e:
            logger.error(f"❌ Error durante el login: {e}")
            await self._take_screenshot("error_login")
            import traceback
            traceback.print_exc()
            return False

    def _map_vinculation_to_role(self, vinculation_type: str) -> str:
        """
        Mapea tipo de vinculación a rol de AppConnecto.

        Args:
            vinculation_type: Tipo de vinculación ("Estudiante" o "Docente")

        Returns:
            Nombre del rol en AppConnecto
        """
        if vinculation_type == "Estudiante":
            return "Estudiantes"
        elif vinculation_type == "Docente":
            return "Docentes"
        else:
            logger.warning(f"Tipo de vinculación desconocido: {vinculation_type}. Usando 'Estudiantes' por defecto.")
            return "Estudiantes"

    def _map_document_type(self, type_document: str) -> str:
        """
        Mapea tipo de documento a valor del select.

        Args:
            type_document: Tipo de documento ("C.C" o "C.E")

        Returns:
            Valor para el select ("1" o "2")
        """
        mapping = {
            "C.C": "1",
            "C.E": "2"
        }
        return mapping.get(type_document, "1")

    async def create_user(self, user_data: dict) -> dict:
        """
        Crea un usuario en AppConnecto.

        Args:
            user_data: Diccionario con datos del usuario:
                - identification_id: Número de documento
                - full_name: Nombres completos
                - full_last_name: Apellidos completos
                - type_document: Tipo de documento ("C.C" o "C.E")
                - institutional_email: Email institucional
                - vinculation_type: Tipo de vinculación ("Estudiante" o "Docente")

        Returns:
            Diccionario con resultado:
                - success: True/False
                - username: identification_id del usuario
                - status: "created", "already_exists" o "error"
                - error: Mensaje de error (si falló)

        Example:
            >>> result = await client.create_user({
            ...     "identification_id": "1234567890",
            ...     "full_name": "Juan Carlos",
            ...     "full_last_name": "Perez Lopez",
            ...     "type_document": "C.C",
            ...     "institutional_email": "juan.perez@ecr.edu.co",
            ...     "vinculation_type": "Estudiante"
            ... })
        """
        username = user_data.get("identification_id", "unknown")

        try:
            logger.info("=" * 70)
            logger.info(f"👤 Creando usuario: {username}")
            logger.info(f"   Nombre: {user_data.get('full_name')} {user_data.get('full_last_name')}")
            logger.info("=" * 70)

            # 1. Navegar al formulario
            await self.page.goto(self.form_url)
            await self.page.wait_for_selector("#form")
            await asyncio.sleep(1)

            url_before = self.page.url
            logger.debug(f"URL actual: {url_before}")

            # 2. Llenar formulario
            await self.page.fill("#id_username", username)
            await self.page.fill("#id_identification_id", username)

            # Seleccionar tipo de documento
            document_type_value = self._map_document_type(user_data.get("type_document", "C.C"))
            await self.page.select_option("#id_type_document", document_type_value)

            await self.page.fill("#id_first_name", user_data.get("full_name", ""))
            await self.page.fill("#id_last_name", user_data.get("full_last_name", ""))

            # Llenar fecha de nacimiento usando JavaScript
            await self.page.evaluate(
                f"document.getElementById('id_birth_date').value = '{settings.appconnecto_default_birth_date}'"
            )

            await self.page.fill("#id_email", user_data.get("institutional_email", ""))
            await self.page.fill("#id_password_field", settings.appconnecto_default_password)

            await self._take_screenshot(f"formulario_lleno_{username}")

            # 3. Hacer scroll y enviar
            logger.info("📤 Enviando formulario...")
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(1)

            # Click con JavaScript
            await self.page.evaluate("document.getElementById('enviar').click()")

            # 4. Esperar cambio de URL
            try:
                await self.page.wait_for_url(lambda url: url != url_before, timeout=5000)
                url_after = self.page.url
            except Exception:
                # Si no cambió la URL, el usuario ya existe
                logger.warning(f"⚠️  Usuario ya existe: {username}")
                await self._take_screenshot(f"usuario_existe_{username}")
                return {
                    "success": False,
                    "username": username,
                    "status": "already_exists",
                    "error": "Usuario ya existe en AppConnecto"
                }

            logger.info(f"✅ URL cambió: {url_after}")
            await self._take_screenshot(f"resultado_{username}")

            # 5. Seleccionar rol
            rol = self._map_vinculation_to_role(user_data.get("vinculation_type", "Estudiante"))
            logger.info(f"👥 Seleccionando rol: {rol}")
            await asyncio.sleep(1)

            # Abrir dropdown de Select2
            await self.page.click(".select2-selection--multiple")
            await asyncio.sleep(1)

            # Escribir en el campo de búsqueda
            await self.page.fill(".select2-search__field", rol)
            await asyncio.sleep(0.5)

            # Click en la primera opción
            await self.page.click(".select2-results__option")
            logger.info(f"✅ Rol seleccionado: {rol}")
            await asyncio.sleep(0.5)

            # 6. Guardar cambios
            logger.info("💾 Guardando usuario...")
            await asyncio.sleep(0.5)

            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(0.5)

            await self.page.evaluate("document.querySelector('button[name=\"enviar\"]').click()")
            await asyncio.sleep(2)

            logger.info(f"✅ Usuario creado exitosamente: {username}")
            await self._take_screenshot(f"guardado_{username}")

            return {
                "success": True,
                "username": username,
                "status": "created",
                "error": None
            }

        except Exception as e:
            logger.error(f"❌ Error creando usuario {username}: {e}")
            await self._take_screenshot(f"error_{username}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "username": username,
                "status": "error",
                "error": str(e)
            }

    async def create_users(self, users: list[dict]) -> dict:
        """
        Crea múltiples usuarios en AppConnecto.

        Args:
            users: Lista de diccionarios con datos de usuarios

        Returns:
            Diccionario con estadísticas:
                - created: Lista de usernames creados exitosamente
                - already_exists: Lista de usernames que ya existían
                - errors: Lista de dicts con username y error
                - total: Total de usuarios procesados

        Example:
            >>> client = AppConnectoClient()
            >>> await client.login()
            >>> results = await client.create_users(users_list)
            >>> print(f"Creados: {len(results['created'])}")
        """
        created = []
        already_exists = []
        errors = []

        logger.info("=" * 70)
        logger.info("📋 INICIANDO CREACIÓN DE USUARIOS EN APPCONNECTO")
        logger.info("=" * 70)

        for i, user_data in enumerate(users, 1):
            logger.info(f"\n[{i}/{len(users)}]")

            try:
                result = await self.create_user(user_data)

                if result["status"] == "created":
                    created.append(result["username"])
                elif result["status"] == "already_exists":
                    already_exists.append(result["username"])
                else:
                    errors.append({
                        "username": result["username"],
                        "error": result.get("error", "Error desconocido")
                    })

            except Exception as e:
                username = user_data.get("identification_id", "unknown")
                logger.error(f"❌ Error crítico con usuario {username}: {e}")
                errors.append({
                    "username": username,
                    "error": str(e)
                })

            # Pausa entre usuarios
            await asyncio.sleep(2)

        return {
            "created": created,
            "already_exists": already_exists,
            "errors": errors,
            "total": len(users)
        }

    async def close(self) -> None:
        """
        Cierra el navegador y libera recursos.

        Example:
            >>> client = AppConnectoClient()
            >>> await client.login()
            >>> # ... hacer operaciones ...
            >>> await client.close()
        """
        logger.info("🔒 Cerrando navegador...")

        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

        self.page = None
        self.context = None
        self.browser = None
        self.playwright = None

        logger.info("✅ Navegador cerrado")


async def create_users_in_appconnecto(
    users: list[dict],
    headless: bool = False
) -> dict:
    """
    Función helper para crear usuarios en AppConnecto de forma simple.

    Args:
        users: Lista de usuarios a crear
        headless: Si True, ejecuta en modo headless

    Returns:
        Diccionario con resultados de creación

    Example:
        >>> results = await create_users_in_appconnecto(users_list)
        >>> print(f"Creados: {len(results['created'])}")
    """
    client = AppConnectoClient(headless=headless)

    try:
        # Login
        login_success = await client.login()
        if not login_success:
            logger.error("No se pudo hacer login en AppConnecto")
            return {
                "created": [],
                "already_exists": [],
                "errors": [{"username": "login", "error": "Login fallido"}],
                "total": len(users)
            }

        # Crear usuarios
        results = await client.create_users(users)
        return results

    finally:
        await client.close()
