"""
Generador de emails institucionales únicos.

Este módulo genera emails institucionales para estudiantes,
garantizando unicidad y aplicando reglas de normalización.
"""

import unicodedata
from loguru import logger


class EmailGenerator:
    """
    Genera emails institucionales únicos.

    Usa el formato: primer_nombre.primer_apellido@dominio
    Si el email ya existe, agrega letras del segundo apellido.
    Si se agota el segundo apellido, agrega números.

    Attributes:
        domain: Dominio del email institucional
        _existing_emails: Set de emails existentes en Office 365
        _generated_in_batch: Set de emails generados en el batch actual
    """

    def __init__(self, domain: str = "ecr.edu.co"):
        """
        Inicializa el generador.

        Args:
            domain: Dominio para los emails generados
        """
        self.domain = domain
        self._existing_emails: set[str] = set()
        self._generated_in_batch: set[str] = set()
        self._existing_users: dict[str, str] = {}  # nombre_normalizado -> email

    def load_existing_emails(self, emails: set[str]) -> None:
        """
        Carga emails existentes desde Office 365.

        Args:
            emails: Set de emails existentes (obtenidos de Graph API)
        """
        self._existing_emails = {e.lower() for e in emails}
        logger.info(f"Cargados {len(self._existing_emails)} emails existentes")

    def load_existing_users(self, users_info: list[dict]) -> None:
        """
        Carga información de usuarios existentes desde Office 365.

        Permite detectar si un usuario ya existe por nombre completo
        antes de generar un nuevo email.

        Args:
            users_info: Lista de dicts con email y display_name
                       [{"email": "...", "display_name": "..."}, ...]
        """
        for user in users_info:
            email = user.get('email', '').lower()
            display_name = user.get('display_name', '')

            if email and display_name:
                # Normalizar nombre para comparación
                normalized_name = self._normalize_name_for_comparison_from_display(display_name)
                self._existing_users[normalized_name] = email

                # También agregar a existing_emails
                self._existing_emails.add(email)

        logger.info(f"Cargados {len(self._existing_users)} usuarios existentes con nombres")

    def check_existing_user(self, full_name: str, full_last_name: str) -> str | None:
        """
        Verifica si un usuario ya existe por nombre completo.

        Args:
            full_name: Nombres completos del usuario
            full_last_name: Apellidos completos del usuario

        Returns:
            Email del usuario existente si se encuentra, None si es nuevo

        Example:
            >>> generator.check_existing_user("Laura Sofia", "Becerra Sandoval")
            'laura.becerra@ecr.edu.co'  # Si existe
            None  # Si no existe
        """
        normalized_name = self._normalize_name_for_comparison(full_name, full_last_name)
        existing_email = self._existing_users.get(normalized_name)

        if existing_email:
            logger.warning(
                f"Usuario ya existe: {full_name} {full_last_name} → {existing_email}"
            )
        else:
            logger.info(f"Usuario nuevo, generando email: {full_name} {full_last_name}")

        return existing_email

    def generate_email(
        self,
        first_name: str,
        first_last_name: str,
        second_last_name: str = ""
    ) -> str:
        """
        Genera un email institucional único.

        Args:
            first_name: Primer nombre del estudiante
            first_last_name: Primer apellido del estudiante
            second_last_name: Segundo apellido del estudiante (opcional)

        Returns:
            Email institucional único en formato: nombre.apellido@dominio

        Example:
            >>> generator.generate_email("Laura", "Becerra", "Sandoval")
            'laura.becerra@ecr.edu.co'
        """
        logger.debug(f"Generando email para: {first_name} {first_last_name} {second_last_name}")

        # Normalizar componentes
        name_normalized = self._normalize_for_email(first_name)
        last_name_normalized = self._normalize_for_email(first_last_name)
        second_last_normalized = self._normalize_for_email(second_last_name) if second_last_name else ""

        # Email base: nombre.apellido
        base_email = f"{name_normalized}.{last_name_normalized}"
        email = f"{base_email}@{self.domain}"

        # Si está disponible, retornar
        if self._is_available(email):
            self._generated_in_batch.add(email)
            logger.info(f"Email generado: {email}")
            return email

        # Si no está disponible, intentar con letras del segundo apellido
        if second_last_normalized:
            logger.warning(f"Email {email} ya existe, agregando letras del segundo apellido...")

            for i in range(1, len(second_last_normalized) + 1):
                suffix = second_last_normalized[:i]
                candidate = f"{base_email}{suffix}@{self.domain}"

                if self._is_available(candidate):
                    self._generated_in_batch.add(candidate)
                    logger.info(f"Email generado: {candidate}")
                    return candidate

        # Si se agotó el segundo apellido (o no existe), usar números
        logger.warning(f"Segundo apellido agotado para {base_email}, agregando números...")

        counter = 1
        while True:
            candidate = f"{base_email}{counter}@{self.domain}"

            if self._is_available(candidate):
                self._generated_in_batch.add(candidate)
                logger.info(f"Email generado: {candidate}")
                return candidate

            counter += 1

            # Límite de seguridad (evitar loop infinito)
            if counter > 9999:
                raise Exception(f"No se pudo generar email único para {first_name} {first_last_name}")

    def _normalize_name_for_comparison(self, full_name: str, full_last_name: str) -> str:
        """
        Normaliza nombre completo para comparación.

        Combina nombres y apellidos, normaliza (minúsculas, sin tildes),
        y ordena palabras alfabéticamente para comparación flexible.

        Args:
            full_name: Nombres completos
            full_last_name: Apellidos completos

        Returns:
            Nombre normalizado y ordenado

        Example:
            >>> _normalize_name_for_comparison("Laura Sofia", "Becerra Sandoval")
            'becerra laura sandoval sofia'
        """
        # Combinar nombres y apellidos
        combined = f"{full_name} {full_last_name}"

        # Normalizar: minúsculas, sin tildes, preservando espacios
        normalized = self._normalize_for_email(combined, preserve_spaces=True)

        # Dividir en palabras individuales
        words = normalized.split()

        # Ordenar alfabéticamente para comparación flexible
        words_sorted = sorted(words)

        # Unir con espacios
        return ' '.join(words_sorted)

    def _normalize_name_for_comparison_from_display(self, display_name: str) -> str:
        """
        Normaliza displayName de Office 365 para comparación.

        Args:
            display_name: Nombre completo desde Office 365

        Returns:
            Nombre normalizado y ordenado

        Example:
            >>> _normalize_name_for_comparison_from_display("Laura Sofia Becerra Sandoval")
            'becerra laura sandoval sofia'
        """
        # Normalizar: minúsculas, sin tildes, preservando espacios
        normalized = self._normalize_for_email(display_name, preserve_spaces=True)

        # Dividir en palabras individuales
        words = normalized.split()

        # Ordenar alfabéticamente
        words_sorted = sorted(words)

        # Unir con espacios
        return ' '.join(words_sorted)

    def _normalize_for_email(self, text: str, preserve_spaces: bool = False) -> str:
        """
        Normaliza texto para uso en email.

        Aplica:
        - Minúsculas
        - Elimina tildes (á→a, é→e, í→i, ó→o, ú→u, ñ→n)
        - Elimina espacios (opcional)

        Args:
            text: Texto a normalizar
            preserve_spaces: Si True, preserva espacios (para comparación de nombres)

        Returns:
            Texto normalizado para email

        Example:
            >>> _normalize_for_email("María José")
            'mariajose'
            >>> _normalize_for_email("María José", preserve_spaces=True)
            'maria jose'
        """
        if not text:
            return ""

        # Convertir a minúsculas
        text = text.lower()

        # Eliminar tildes usando NFD (Canonical Decomposition)
        # NFD separa caracteres compuestos: á → a + ´
        text = unicodedata.normalize('NFD', text)

        # Filtrar solo caracteres ASCII (elimina acentos y diacríticos)
        text = ''.join(char for char in text if unicodedata.category(char) != 'Mn')

        # Normalizar caracteres especiales manualmente
        replacements = {
            'ñ': 'n',
            'ü': 'u',
        }

        for old, new in replacements.items():
            text = text.replace(old, new)

        if preserve_spaces:
            # Normalizar espacios múltiples a uno solo
            text = ' '.join(text.split())
            # Eliminar caracteres no alfanuméricos excepto espacios
            text = ''.join(char for char in text if char.isalnum() or char == ' ')
        else:
            # Eliminar espacios
            text = text.replace(' ', '')
            # Eliminar caracteres no alfanuméricos
            text = ''.join(char for char in text if char.isalnum())

        return text

    def _is_available(self, email: str) -> bool:
        """
        Verifica si un email está disponible.

        Un email está disponible si:
        - No existe en Office 365 (_existing_emails)
        - No ha sido generado en el batch actual (_generated_in_batch)

        Args:
            email: Email a verificar

        Returns:
            True si está disponible, False en caso contrario
        """
        email_lower = email.lower()
        return (
            email_lower not in self._existing_emails and
            email_lower not in self._generated_in_batch
        )

    def reset_batch(self) -> None:
        """
        Reinicia el tracking de emails generados en el batch.

        Útil si se procesan múltiples archivos Excel secuencialmente.
        """
        self._generated_in_batch.clear()
        logger.debug("Batch de emails generados reiniciado")
