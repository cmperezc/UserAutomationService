"""
Schemas de validación Pydantic para datos de estudiantes.

Este módulo define los schemas de validación para procesar datos
de estudiantes que provienen de archivos Excel.
"""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator
from app.config import get_settings

settings = get_settings()


class UserSchema(BaseModel):
    """
    Schema de validación para datos de estudiantes.

    Valida y normaliza datos de estudiantes provenientes de Excel,
    aplicando reglas de formato, longitud y valores permitidos.

    Attributes:
        request_type: Tipo de solicitud (solo "Apertura" permitido)
        full_name: Nombres completos del estudiante
        full_last_name: Apellidos completos del estudiante
        type_document: Tipo de documento (C.C o C.E)
        identification_id: Número de identificación (solo dígitos)
        vinculation_type: Tipo de vinculación (solo "Estudiante")
        academic_program: Programa académico
        email_personal: Email personal del estudiante
        first_name: Primer nombre (calculado)
        first_last_name: Primer apellido (calculado)
        second_last_name: Segundo apellido (calculado)
        institutional_email: Email institucional (calculado posteriormente)
    """

    request_type: str = Field(..., description="Tipo de solicitud")
    full_name: str = Field(..., min_length=2, max_length=200, description="Nombres completos")
    full_last_name: str = Field(..., min_length=2, max_length=200, description="Apellidos completos")
    type_document: str = Field(..., description="Tipo de documento de identidad")
    identification_id: str = Field(..., min_length=1, max_length=20, description="Número de identificación")
    vinculation_type: str = Field(..., description="Tipo de vinculación")
    academic_program: str = Field(..., min_length=1, description="Programa académico")
    email_personal: EmailStr = Field(..., description="Email personal")

    # Campos calculados
    first_name: Optional[str] = Field(None, description="Primer nombre extraído")
    first_last_name: Optional[str] = Field(None, description="Primer apellido extraído")
    second_last_name: Optional[str] = Field(None, description="Segundo apellido extraído")
    institutional_email: Optional[str] = Field(None, description="Email institucional generado")

    @field_validator('request_type')
    @classmethod
    def validate_request_type(cls, v: str) -> str:
        """
        Valida y normaliza el tipo de solicitud.

        Args:
            v: Valor del tipo de solicitud

        Returns:
            Tipo de solicitud normalizado a Title Case

        Raises:
            ValueError: Si el tipo no está en la lista de permitidos
        """
        # Normalizar a title case
        normalized = v.strip().title()

        # Validar contra valores permitidos
        if normalized not in settings.allowed_request_types:
            allowed = ", ".join(settings.allowed_request_types)
            raise ValueError(
                f"Tipo de solicitud '{v}' no permitido. "
                f"Valores permitidos: {allowed}"
            )

        return normalized

    @field_validator('full_name')
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        """
        Valida y normaliza nombres completos.

        Args:
            v: Nombres completos

        Returns:
            Nombres normalizados a Title Case y sin espacios extras
        """
        # Trimear espacios y normalizar a title case
        return v.strip().title()

    @field_validator('full_last_name')
    @classmethod
    def validate_full_last_name(cls, v: str) -> str:
        """
        Valida y normaliza apellidos completos.

        Aplica title case y maneja palabras especiales (de, del, la, los, las, y)
        que deben ir en minúscula excepto si son la primera palabra.

        Args:
            v: Apellidos completos

        Returns:
            Apellidos normalizados con formato correcto
        """
        # Trimear espacios
        normalized = v.strip().title()

        # Palabras que deben ir en minúscula (excepto al inicio)
        special_words = {'De', 'Del', 'La', 'Los', 'Las', 'Y'}

        # Dividir en palabras
        words = normalized.split()

        # Procesar cada palabra (excepto la primera)
        result = []
        for i, word in enumerate(words):
            if i == 0:
                # Primera palabra siempre en title case
                result.append(word)
            elif word in special_words:
                # Palabras especiales en minúscula
                result.append(word.lower())
            else:
                result.append(word)

        return ' '.join(result)

    @field_validator('type_document')
    @classmethod
    def validate_type_document(cls, v: str) -> str:
        """
        Valida y normaliza el tipo de documento.

        Normaliza variaciones comunes (CC, cc, C.C., etc.) a formato estándar.

        Args:
            v: Tipo de documento

        Returns:
            Tipo de documento normalizado (C.C o C.E)

        Raises:
            ValueError: Si el tipo no es C.C o C.E después de normalizar
        """
        # Trimear y convertir a mayúsculas
        normalized = v.strip().upper()

        # Normalizar variaciones comunes
        document_map = {
            'CC': 'C.C',
            'C.C': 'C.C',
            'C.C.': 'C.C',
            'CE': 'C.E',
            'C.E': 'C.E',
            'C.E.': 'C.E'
        }

        # Buscar en el mapa
        normalized = document_map.get(normalized)

        # Validar contra valores permitidos
        if normalized not in settings.allowed_document_types:
            allowed = ", ".join(settings.allowed_document_types)
            raise ValueError(
                f"Tipo de documento '{v}' no permitido. "
                f"Valores permitidos: {allowed}"
            )

        return normalized

    @field_validator('identification_id')
    @classmethod
    def validate_identification_id(cls, v: str) -> str:
        """
        Valida el número de identificación.

        Args:
            v: Número de identificación

        Returns:
            Número de identificación sin espacios

        Raises:
            ValueError: Si contiene caracteres no numéricos
        """
        # Trimear espacios
        normalized = v.strip()

        # Validar que solo contenga dígitos
        if not normalized.isdigit():
            raise ValueError(
                f"Número de identificación '{v}' debe contener solo dígitos"
            )

        # NO rellenar con ceros
        return normalized

    @field_validator('vinculation_type')
    @classmethod
    def validate_vinculation_type(cls, v: str) -> str:
        """
        Valida y normaliza el tipo de vinculación.

        Args:
            v: Tipo de vinculación

        Returns:
            Tipo de vinculación normalizado a Title Case

        Raises:
            ValueError: Si el tipo no está en la lista de permitidos
        """
        # Normalizar a title case
        normalized = v.strip().title()

        # Validar contra valores permitidos
        if normalized not in settings.allowed_vinculation_types:
            allowed = ", ".join(settings.allowed_vinculation_types)
            raise ValueError(
                f"Tipo de vinculación '{v}' no permitido. "
                f"Valores permitidos: {allowed}"
            )

        return normalized

    @field_validator('academic_program')
    @classmethod
    def validate_academic_program(cls, v: str) -> str:
        """
        Valida y normaliza el programa académico.

        Args:
            v: Programa académico

        Returns:
            Programa académico sin espacios extras
        """
        return v.strip()

    def extract_names_for_email(self) -> 'UserSchema':
        """
        Extrae nombres y apellidos individuales para generación de email.

        Divide los nombres y apellidos completos para obtener:
        - first_name: primer nombre
        - first_last_name: primer apellido
        - second_last_name: segundo apellido (vacío si no existe)

        Returns:
            self: Para permitir method chaining

        Example:
            >>> user = UserSchema(**data)
            >>> user.extract_names_for_email()
            >>> print(user.first_name)  # "Laura"
        """
        # Extraer primer nombre
        name_parts = self.full_name.split()
        self.first_name = name_parts[0] if name_parts else ""

        # Extraer primer y segundo apellido
        last_name_parts = self.full_last_name.split()
        self.first_last_name = last_name_parts[0] if last_name_parts else ""
        self.second_last_name = last_name_parts[1] if len(last_name_parts) > 1 else ""

        return self

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "request_type": "Apertura",
                    "full_name": "Laura Sofia",
                    "full_last_name": "Becerra Sandoval",
                    "type_document": "C.C",
                    "identification_id": "1000227618",
                    "vinculation_type": "Estudiante",
                    "academic_program": "FISIOTERAPIA",
                    "email_personal": "laura.becerra@gmail.com",
                    "first_name": "Laura",
                    "first_last_name": "Becerra",
                    "second_last_name": "Sandoval",
                    "institutional_email": None
                }
            ]
        }
    }
