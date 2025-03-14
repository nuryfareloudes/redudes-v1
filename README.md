# REDUDES - Sistema de Información

Sistema de información para la Red de Universidades para el Desarrollo Sostenible.

## Requisitos

- Python 3.8+
- Navegador web moderno

## Instalación

1. Clonar el repositorio:
   ```
   git clone <url-del-repositorio>
   cd redudesv2
   ```

2. Crear un entorno virtual e instalar dependencias:
   ```
   python -m venv venv
   venv\Scripts\activate  # En Windows
   source venv/bin/activate  # En Linux/Mac
   pip install -r requirements.txt
   ```

3. Aplicar migraciones:
   ```
   python manage.py migrate
   ```

4. Crear un superusuario:
   ```
   python manage.py createsuperuser
   ```

## Ejecución

1. Iniciar el servidor Django:
   ```
   python manage.py runserver
   ```

2. Acceder a la aplicación en el navegador:
   ```
   http://localhost:8000
   ```

## Funcionalidades

- **Gestión de Proyectos**: Crear, editar y eliminar proyectos.
- **Gestión de Usuarios**: Administrar usuarios con sus habilidades, conocimientos, estudios y experiencia.
- **Extracción de Datos**: Extraer automáticamente información de perfiles de CVLAC y LinkedIn.

## Estructura del Proyecto

- `core/`: Aplicación principal
  - `models.py`: Definición de modelos de datos
  - `views.py`: Vistas y lógica de la aplicación
  - `urls.py`: Configuración de URLs
  - `templates/`: Plantillas HTML
  - `scraping_utils.py`: Utilidades para extracción de datos
  - `data_services.py`: Servicios para procesamiento de datos

- `redudes/`: Configuración del proyecto
  - `settings.py`: Configuración de Django

## Notas

- La extracción de datos de LinkedIn puede requerir autenticación debido a las restricciones de LinkedIn.
- Se recomienda usar URLs públicas de CVLAC para obtener mejores resultados.
- Los logs de depuración se almacenan en el directorio `debug_logs/`. 