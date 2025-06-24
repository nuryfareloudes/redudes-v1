# REDUDES - Sistema Red de Usuarios UDES

REDUDES es una plataforma avanzada para la gestión y recomendación de perfiles profesionales para proyectos de investigación y desarrollo.

## Descripción General

REDUDES es un sistema diseñado para facilitar la identificación y asignación de perfiles profesionales a proyectos específicos. Utiliza algoritmos de inteligencia artificial (Random Forest y KNN) para recomendar los candidatos más adecuados según las necesidades y requisitos de cada proyecto.

## Funcionalidades Principales

### Gestión de Proyectos
- Registro detallado de proyectos con información sobre convocatorias, objetivos y alcance
- Definición de roles requeridos con habilidades y conocimientos específicos
- Gestión de aliados estratégicos y productos esperados
- Dashboard visual con métricas e indicadores clave

### Gestión de Perfiles Profesionales
- Registro completo de usuarios con sus habilidades, conocimientos, estudios y experiencia laboral
- Importación automática de perfiles desde plataformas como CVLAC y LinkedIn
- Visualización detallada del historial profesional y académico
- Evaluación de competencias técnicas y habilidades blandas

### Sistema de Recomendación Inteligente
- Algoritmos de machine learning para la identificación de candidatos óptimos
- Análisis de compatibilidad entre perfiles profesionales y requisitos de proyectos
- Métricas de confianza para cada recomendación
- Ranking de candidatos según su idoneidad para cada rol

### Analítica de Datos
- Visualización de métricas de rendimiento de los algoritmos de recomendación
- Análisis de brechas de habilidades y conocimientos
- Estadísticas sobre perfiles disponibles y necesidades de proyectos
- Reportes dinámicos para toma de decisiones

## Casos de Uso

REDUDES es ideal para:

- **Instituciones educativas**: Asignación óptima de investigadores a proyectos de investigación
- **Centros de innovación**: Conformación de equipos multidisciplinarios para proyectos de desarrollo
- **Departamentos de I+D**: Identificación de talento interno para nuevas iniciativas
- **Oficinas de transferencia tecnológica**: Vinculación de expertos con proyectos de innovación
- **Redes de colaboración científica**: Formación de equipos interinstitucionales

## Tecnologías Utilizadas

- **Backend**: Django (Python)
- **Frontend**: Bootstrap, JavaScript
- **Base de datos**: SQLite (desarrollo), PostgreSQL (producción)
- **Machine Learning**: Scikit-learn, Pandas, NumPy
- **Extracción de datos**: Beautiful Soup, Selenium

## Notas

- La extracción de datos de LinkedIn puede requerir autenticación debido a las restricciones de la plataforma.
- Se recomienda usar URLs públicas de CVLAC para obtener mejores resultados.
- Los logs de depuración se almacenan en el directorio `debug_logs/`.

## Requisitos

- Python 3.12
- pip
- (Recomendado) Entorno virtual 