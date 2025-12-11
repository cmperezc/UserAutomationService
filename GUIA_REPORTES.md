# Guía de Reportes - Sistema de Automatización ECR

## 📄 Tipos de Reportes Generados

El sistema genera **3 tipos de reportes** automáticamente:

1. **Reportes JSON** (`logs/`) - Para integración con otros sistemas
2. **Reporte PDF** (`logs/reportes/`) - Para presentaciones y auditoría
3. **Reporte Excel** (`logs/reportes/`) - Para análisis detallado

---

## 📖 Resumen Rápido de Símbolos

| Símbolo | Significado | Interpretación |
|---------|-------------|----------------|
| **SI** | ✅ Creado exitosamente | Acción completada con éxito |
| **YA EXISTE** | ⚠️ Ya existía | NO es error, usuario detectado previamente |
| **NO** | ❌ Error al crear | Falló el intento de creación (requiere revisión) |
| **-** | ➖ No aplica | Acción no corresponde (ej: sin password para enviar) |

---

## 📊 Interpretación de Símbolos

### En el Reporte PDF y Excel

Las columnas de estado usan los siguientes valores:

| Columna | Símbolo | Significado |
|---------|---------|-------------|
| **O365** | SI | ✅ Usuario creado exitosamente en Office 365 |
| **O365** | YA EXISTE | ⚠️ Usuario ya existía en Office 365 (no es un error) |
| **O365** | NO | ❌ Error al intentar crear en Office 365 |
| **App** | SI | ✅ Usuario creado en AppConnecto |
| **App** | YA EXISTE | ⚠️ Usuario ya existía en AppConnecto (no es un error) |
| **App** | NO | ❌ Error al intentar crear en AppConnecto |
| **Email** | SI | ✅ Correo de bienvenida enviado exitosamente |
| **Email** | NO | ❌ No se envió correo |
| **Email** | - | ➖ No aplica (usuario ya existía, no hay password nuevo) |

---

## 🎯 Ejemplos de Lectura

### Ejemplo 1: Usuario Creado Exitosamente
```
O365: SI  |  App: SI  |  Email: SI
```
✅ **Todo perfecto:** Usuario creado en Office 365, AppConnecto y correo enviado.

### Ejemplo 2: Usuario Ya Existía (No es error)
```
O365: YA EXISTE  |  App: YA EXISTE  |  Email: -
```
⚠️ **Usuario existente:** No se realizó ninguna acción porque ya existe en ambos sistemas. Esto NO es un error.

### Ejemplo 3: Fallo en AppConnecto
```
O365: SI  |  App: NO  |  Email: SI
```
⚠️ **Parcial:** Creado en Office 365 y correo enviado, pero falló en AppConnecto (necesita corrección manual).

### Ejemplo 4: Error al Crear en Office 365
```
O365: NO  |  App: NO  |  Email: NO
```
❌ **Error crítico:** No se pudo crear en Office 365 (el proceso no continuó).

### Ejemplo 5: Usuario Nuevo en Office 365, Ya Existe en AppConnecto
```
O365: SI  |  App: YA EXISTE  |  Email: SI
```
✅ **Común:** Usuario creado en Office 365, pero ya estaba en AppConnecto. Correo enviado exitosamente.

---

## 📑 Estructura del Reporte PDF

### Página 1 - Portada
- Título del reporte
- Nombre de la institución (ECR)
- Fecha del proceso
- Archivo Excel procesado

### Página 2 - Resumen Ejecutivo
Tabla con estadísticas principales:
- Total usuarios en Excel
- Usuarios nuevos procesados
- Usuarios ya existentes
- Creados en Office 365
- Creados en AppConnecto
- Correos enviados

### Página 3+ - Detalle de Usuarios
Tabla con hasta 50 usuarios mostrando:
- Número secuencial
- Nombre completo
- Número de identificación
- Email institucional
- Estado en cada plataforma (O365, App, Email)

**Nota:** Si hay más de 50 usuarios, se muestra un mensaje indicando que el listado completo está en el Excel.

### Página Final - Errores (si existen)
Lista detallada de errores por plataforma:
- Errores en Office 365
- Errores en AppConnecto
- Errores en envío de correos

---

## 📊 Estructura del Reporte Excel

### Hoja 1: "Resumen"
Dashboard con:
- Información del proceso (fecha, archivo)
- Tabla de métricas con cantidad y porcentaje
- Formato profesional con colores ECR

### Hoja 2: "Usuarios"
Tabla completa con **14 columnas**:

| # | Columna | Descripción |
|---|---------|-------------|
| A | Nombre | Nombres del usuario |
| B | Apellido | Apellidos del usuario |
| C | Identificación | Número de documento |
| D | Tipo Doc | C.C, C.E, etc. |
| E | Email Personal | Email personal del usuario |
| F | Email Institucional | Email generado @ecr.edu.co |
| G | Tipo Vinculación | Estudiante o Docente |
| H | Programa Académico | Programa al que pertenece |
| I | Status General | new, existing, etc. |
| J | Office 365 | SI/NO |
| K | AppConnecto | SI/YA EXISTE/NO |
| L | Correo Enviado | SI/NO |
| M | Password | Contraseña generada (solo para nuevos) |
| N | Observaciones | Errores o notas adicionales |

**Características:**
- ✅ Filtros activados en todas las columnas
- ✅ Primera fila congelada
- ✅ Formato condicional por color:
  - 🟢 Verde: Usuario creado exitosamente
  - 🔴 Rojo: Usuario con errores
  - 🟡 Amarillo: Usuario pendiente
- ✅ Anchos de columna optimizados
- ✅ Bordes en todas las celdas

### Hoja 3: "Errores"
Lista de errores para seguimiento con columnas:
- Usuario (nombre completo)
- Plataforma (Office 365, AppConnecto, Email)
- Error (descripción del error)
- Fecha (timestamp del proceso)
- Acción Requerida (recomendación)

---

## 🎨 Códigos de Color en Excel

### Encabezados
- Fondo: Azul oscuro ECR (#003366)
- Texto: Blanco (#FFFFFF)

### Filas de Datos (según status)
- 🟢 **Verde claro (#d4edda):** Usuario creado exitosamente
- 🔴 **Rojo claro (#f8d7da):** Usuario con errores
- 🟡 **Amarillo claro (#fff3cd):** Usuario pendiente o advertencia

### Bordes
- Gris claro (#dee2e6) en todas las celdas

---

## 📍 Ubicación de los Reportes

Todos los reportes se guardan con timestamp:

```
logs/
├── reportes/
│   ├── reporte_YYYYMMDD_HHMMSS.pdf
│   └── reporte_YYYYMMDD_HHMMSS.xlsx
├── usuarios_office365_YYYYMMDD_HHMMSS.json
├── usuarios_appconnecto_YYYYMMDD_HHMMSS.json
├── correos_enviados_YYYYMMDD_HHMMSS.json
├── reporte_consolidado_YYYYMMDD_HHMMSS.json
└── automation_YYYYMMDD_HHMMSS.log
```

**Formato del timestamp:** `YYYYMMDD_HHMMSS`
- Ejemplo: `20251210_143052` = 10 de diciembre de 2025 a las 14:30:52

---

## 💡 Consejos de Uso

### Para Presentaciones a Directivos
✅ Usar el **reporte PDF** - Diseño profesional y conciso

### Para Análisis Detallado
✅ Usar el **reporte Excel** - Datos completos con filtros y formato condicional

### Para Integración con Otros Sistemas
✅ Usar los **archivos JSON** - Datos estructurados en formato estándar

### Para Debugging o Soporte
✅ Revisar el **archivo .log** - Trazabilidad completa del proceso

---

## 🔍 Cómo Identificar Problemas Rápidamente

### En el PDF:
1. Ve al **Resumen Ejecutivo** (página 2)
2. Compara "Total en Excel" vs "Creados en Office 365"
3. Si hay diferencia, ve a **página de Errores**

### En el Excel:
1. Abre la hoja **"Usuarios"**
2. Activa el filtro en columna **J (Office 365)**
3. Filtra por "NO" para ver usuarios con problemas
4. Ve a hoja **"Errores"** para detalles específicos

### Columnas Clave para Auditoría:
- **Columna M (Password):** Si está vacía en usuario "new" = error
- **Columna N (Observaciones):** Mensajes de error detallados
- **Hoja "Errores":** Lista completa de problemas con acciones recomendadas

---

## 📝 Notas Importantes

1. **Diferencia entre "YA EXISTE" y "NO":**
   - **YA EXISTE:** Usuario detectado como existente ANTES de intentar crear. ✅ No es un error, es el comportamiento esperado.
   - **NO:** Error al intentar crear usuario nuevo. ❌ Es un fallo que requiere investigación.

2. **Usuarios Existentes:** Si todos los usuarios ya existen, igual se genera el reporte mostrando "YA EXISTE" en las columnas correspondientes.

3. **Límite en PDF:** El PDF muestra máximo 50 usuarios. Para ver todos, consultar el Excel.

4. **Passwords en Excel:** Las contraseñas generadas se muestran en texto plano. **Proteger este archivo adecuadamente.**

5. **Timestamps:** Todos los reportes tienen el mismo timestamp del momento de ejecución para facilitar la correlación.

6. **Formato de Correos:** Los correos enviados usan el formato definido en `templates/welcome_email.html`.

---

## 🆘 Problemas Comunes

### "No se generaron reportes PDF/Excel"
**Causa:** Falta instalar reportlab
**Solución:** `pip install reportlab==4.0.7`

### "Todos los usuarios aparecen como existentes"
**Situación normal:** El sistema detecta correctamente usuarios ya creados previamente
**Acción:** Revisar si realmente son usuarios nuevos o duplicados en el Excel

### "Errores en la hoja de Errores"
**Acción requerida:** Revisar cada error, corregir datos en Excel y volver a ejecutar para esos usuarios específicos

---

**Generado para:** Escuela Colombiana de Rehabilitación
**Sistema:** Automatización de Usuarios
**Versión:** 1.0
