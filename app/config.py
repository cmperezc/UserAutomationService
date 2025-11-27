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
    
    # Database
    database_url: str
    
    # General
    debug: bool = False
    log_level: str = "INFO"

    # Valores permitidos para validación de usuarios
    allowed_request_types: list[str] = ["Apertura", "Activación"]
    allowed_document_types: list[str] = ["C.C", "C.E"]
    allowed_vinculation_types: list[str] = ["Estudiante"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Singleton de configuración"""
    return Settings()