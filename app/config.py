from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """Configuración centralizada desde variables de entorno"""
    
    # Azure
    azure_tenant_id: str
    azure_client_id: str
    azure_client_secret: str
    
    # AppConnecto
    appconnecto_url: str
    appconnecto_user: str
    appconnecto_pass: str
    appconnecto_form_url: str = "https://ecr.appconnecto.com/es/headquarters/principal/member/create"
    appconnecto_default_password: str = "ECR2022"
    appconnecto_default_birth_date: str = "1990-01-01"

    # Database
    database_url: str
    
    # General
    debug: bool = False
    log_level: str = "INFO"

    # Valores permitidos para validación de usuarios
    allowed_request_types: list[str] = ["Apertura", "Activación"]
    allowed_document_types: list[str] = ["C.C", "C.E"]
    allowed_vinculation_types: list[str] = ["Estudiante", "Docente"]

    # Mapeo de tipos de vinculación a grupos de Office 365
    student_group: str = "Estudiantes Licencias A5"
    teacher_group: str = "Administrativos Licencia A5"

    # Configuración de contraseñas
    password_length: int = 12

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Singleton de configuración"""
    return Settings()