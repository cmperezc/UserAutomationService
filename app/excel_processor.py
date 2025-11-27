"""
Procesador de archivos Excel de estudiantes.

Este módulo lee, valida y normaliza datos de estudiantes
desde archivos Excel usando el schema UserSchema.
"""

from pathlib import Path
import pandas as pd
from loguru import logger
from pydantic import ValidationError
from app.schemas import UserSchema


class ExcelProcessorError(Exception):
    """Error al procesar archivo Excel."""
    pass


class ExcelProcessor:
    """
    Procesa archivos Excel de estudiantes.

    Lee archivos Excel, valida datos con UserSchema y retorna
    una lista de diccionarios con usuarios normalizados.

    Attributes:
        skip_rows: Número de filas a saltar al inicio del archivo
    """

    # Mapeo de columnas Excel → campos UserSchema
    COLUMN_MAPPING = {
        "Tipo de Solicitud": "request_type",
        "Nombre": "full_name",
        "Apellido": "full_last_name",
        "Tipo de Identificación": "type_document",
        "Número de Identificación": "identification_id",
        "Tipo de Vinculación": "vinculation_type",
        "Dependencia Administrativa / Programa Académico": "academic_program",
        "Correo Electrónico Personal": "email_personal"
    }

    def __init__(self, skip_rows: int = 0):
        """
        Inicializa el procesador.

        Args:
            skip_rows: Número de filas a saltar al inicio del archivo
        """
        self.skip_rows = skip_rows

    def process(self, file_path: str) -> list[dict]:
        """
        Procesa un archivo Excel y retorna lista de usuarios validados.

        Args:
            file_path: Ruta al archivo Excel (.xlsx o .xls)

        Returns:
            Lista de diccionarios con datos de usuarios validados y normalizados

        Raises:
            ExcelProcessorError: Si hay errores de validación o lectura
        """
        logger.info(f"Iniciando procesamiento de Excel: {file_path}")

        # 1. Validar archivo
        self._validate_file(file_path)

        # 2. Leer Excel
        df = self._read_excel(file_path)

        # 3. Validar columnas
        self._validate_columns(df)

        # 4. Limpiar datos
        df = self._clean_data(df)

        # 5. Procesar filas
        users = self._process_rows(df)

        logger.info(f"Procesamiento completado: {len(users)} usuarios válidos")
        return users

    def _validate_file(self, file_path: str) -> None:
        """
        Valida que el archivo existe y tiene extensión correcta.

        Args:
            file_path: Ruta al archivo

        Raises:
            ExcelProcessorError: Si el archivo no existe o extensión inválida
        """
        path = Path(file_path)

        if not path.exists():
            raise ExcelProcessorError(f"Archivo no encontrado: {file_path}")

        if path.suffix.lower() not in ['.xlsx', '.xls']:
            raise ExcelProcessorError(
                f"Formato inválido: {path.suffix}. "
                f"Se requiere .xlsx o .xls"
            )

    def _read_excel(self, file_path: str) -> pd.DataFrame:
        """
        Lee el archivo Excel.

        Args:
            file_path: Ruta al archivo

        Returns:
            DataFrame con los datos

        Raises:
            ExcelProcessorError: Si hay error al leer el archivo
        """
        try:
            df = pd.read_excel(
                file_path,
                skiprows=self.skip_rows,
                engine='openpyxl'
            )
            logger.info(f"Excel leído: {len(df)} filas encontradas")
            return df
        except Exception as e:
            raise ExcelProcessorError(f"Error al leer Excel: {str(e)}")

    def _validate_columns(self, df: pd.DataFrame) -> None:
        """
        Valida que el DataFrame tenga todas las columnas requeridas.

        Args:
            df: DataFrame a validar

        Raises:
            ExcelProcessorError: Si faltan columnas
        """
        required_columns = set(self.COLUMN_MAPPING.keys())
        actual_columns = set(df.columns)
        missing_columns = required_columns - actual_columns

        if missing_columns:
            raise ExcelProcessorError(
                f"Columnas faltantes en Excel: {', '.join(sorted(missing_columns))}"
            )

        logger.info("Todas las columnas requeridas están presentes")

    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Limpia y prepara los datos del DataFrame.

        Args:
            df: DataFrame a limpiar

        Returns:
            DataFrame limpio
        """
        # Eliminar filas completamente vacías
        df = df.dropna(how='all')

        # Limpiar espacios en strings
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].astype(str).str.strip()

        # Convertir IDs float a string (1234567890.0 → "1234567890")
        id_col = "Número de Identificación"
        if id_col in df.columns:
            df[id_col] = df[id_col].apply(self._clean_id)

        # Eliminar filas donde campos críticos estén vacíos
        critical_fields = ["Nombre", "Apellido", "Número de Identificación", "Correo Electrónico Personal"]
        df = df.dropna(subset=critical_fields)

        # Reemplazar valores 'nan' string por vacío
        df = df.replace('nan', '')

        logger.info(f"Datos limpios: {len(df)} filas válidas")
        return df

    def _clean_id(self, value) -> str:
        """
        Limpia el número de identificación.

        Args:
            value: Valor del ID (puede ser float, int o string)

        Returns:
            ID como string sin decimales
        """
        if pd.isna(value):
            return ""

        # Convertir a string y limpiar
        str_value = str(value).strip()

        # Si es float (1234567890.0), quitar decimales
        if '.' in str_value:
            try:
                return str(int(float(str_value)))
            except ValueError:
                return str_value

        return str_value

    def _process_rows(self, df: pd.DataFrame) -> list[dict]:
        """
        Procesa cada fila del DataFrame con UserSchema.

        Args:
            df: DataFrame con datos limpios

        Returns:
            Lista de diccionarios con usuarios validados

        Raises:
            ExcelProcessorError: Si hay errores de validación
        """
        users = []
        errors = []

        for idx, row in df.iterrows():
            row_number = idx + 1 + self.skip_rows  # Número de fila en Excel

            try:
                # Mapear columnas Excel → campos schema
                user_data = {
                    schema_field: row[excel_col]
                    for excel_col, schema_field in self.COLUMN_MAPPING.items()
                }

                # Validar con schema
                user = UserSchema(**user_data)

                # Extraer nombres para email
                user.extract_names_for_email()

                # Agregar a lista
                users.append(user.model_dump())

            except ValidationError as e:
                error_details = []
                for error in e.errors():
                    field = error['loc'][0]
                    msg = error['msg']
                    error_details.append(f"{field}: {msg}")

                error_msg = f"Fila {row_number}: {'; '.join(error_details)}"
                logger.warning(error_msg)
                errors.append(error_msg)

            except Exception as e:
                error_msg = f"Fila {row_number}: Error inesperado - {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)

        # Si hay errores, lanzar excepción con todos los detalles
        if errors:
            raise ExcelProcessorError(
                f"Se encontraron {len(errors)} errores de validación:\n" +
                "\n".join(errors)
            )

        return users


def process_excel(file_path: str, skip_rows: int = 0) -> list[dict]:
    """
    Función helper para procesar Excel de forma simple.

    Args:
        file_path: Ruta al archivo Excel
        skip_rows: Número de filas a saltar

    Returns:
        Lista de diccionarios con usuarios validados

    Example:
        >>> users = process_excel("estudiantes.xlsx")
        >>> print(f"Procesados {len(users)} usuarios")
    """
    return ExcelProcessor(skip_rows).process(file_path)
