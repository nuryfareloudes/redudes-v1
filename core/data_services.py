import logging
import os
import json
from datetime import datetime
from .models import (
    Usuario, UsuarioHabilidades, UsuarioConocimiento, 
    UsuarioEstudios, UsuarioExperiencia
)
from .scraping_utils import extract_cvlac_info, extract_linkedin_info
from django.db import transaction
from django.conf import settings

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def process_user_data(user_id):
    """
    Procesa los datos de un usuario, extrayendo información de CVLAC y LinkedIn
    y guardándola en la base de datos.
    
    Args:
        user_id: ID del usuario a procesar
    
    Returns:
        dict: Resumen de los datos procesados
    """
    try:
        # Crear directorio para logs
        debug_dir = "debug_logs"
        if not os.path.exists(debug_dir):
            os.makedirs(debug_dir)
        
        # Obtener el usuario
        usuario = Usuario.objects.get(id=user_id)
        
        logger.info(f"Procesando datos para el usuario: {usuario.nombres} {usuario.apellidos} (ID: {user_id})")
        
        # Inicializar contadores
        summary = {
            'habilidades_added': 0,
            'conocimientos_added': 0,
            'estudios_added': 0,
            'experiencia_added': 0,
            'errors': []
        }
        
        # Extraer datos de CVLAC
        if usuario.url_cvlac and usuario.url_cvlac.strip():
            logger.info(f"Procesando URL de CVLAC: {usuario.url_cvlac}")
            
            # Verificar si la URL es válida
            if not (usuario.url_cvlac.startswith('http://') or usuario.url_cvlac.startswith('https://')):
                logger.warning(f"URL de CVLAC inválida: {usuario.url_cvlac}")
                summary['errors'].append(f"URL de CVLAC inválida: {usuario.url_cvlac}")
            else:
                cvlac_data = extract_cvlac_info(usuario.url_cvlac)
                if cvlac_data:
                    # Guardar datos de CVLAC
                    logger.info("Datos de CVLAC extraídos correctamente. Guardando en la base de datos...")
                    save_user_data(usuario, cvlac_data, 'CVLAC', summary)
                else:
                    error_msg = "No se pudo extraer información de CVLAC. Verifique que la URL sea correcta y que el perfil sea público."
                    logger.warning(error_msg)
                    summary['errors'].append(error_msg)
        else:
            logger.info("No se proporcionó URL de CVLAC")
        
        # Extraer datos de LinkedIn
        if usuario.url_linkedin and usuario.url_linkedin.strip():
            logger.info(f"Procesando URL de LinkedIn: {usuario.url_linkedin}")
            
            # Verificar si la URL es válida
            if not (usuario.url_linkedin.startswith('http://') or usuario.url_linkedin.startswith('https://')):
                logger.warning(f"URL de LinkedIn inválida: {usuario.url_linkedin}")
                summary['errors'].append(f"URL de LinkedIn inválida: {usuario.url_linkedin}")
            else:
                linkedin_data = extract_linkedin_info(usuario.url_linkedin)
                if linkedin_data:
                    # Guardar datos de LinkedIn
                    logger.info("Datos de LinkedIn extraídos correctamente. Guardando en la base de datos...")
                    save_user_data(usuario, linkedin_data, 'LinkedIn', summary)
                else:
                    error_msg = "No se pudo extraer información de LinkedIn. LinkedIn requiere inicio de sesión para ver perfiles completos."
                    logger.warning(error_msg)
                    summary['errors'].append(error_msg)
        else:
            logger.info("No se proporcionó URL de LinkedIn")
        
        # Guardar resumen para depuración
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(f"{debug_dir}/process_summary_{user_id}_{timestamp}.json", "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=4)
        
        logger.info(f"Procesamiento completado para el usuario {user_id}. Resumen: {summary}")
        return summary
    
    except Usuario.DoesNotExist:
        error_msg = f"Usuario con ID {user_id} no encontrado"
        logger.error(error_msg)
        return {'error': error_msg}
    except Exception as e:
        error_msg = f"Error al procesar datos del usuario: {str(e)}"
        logger.error(error_msg)
        return {'error': error_msg}

@transaction.atomic
def save_user_data(usuario, data, source, summary):
    """
    Guarda los datos extraídos en la base de datos
    
    Args:
        usuario: Instancia del modelo Usuario
        data: Diccionario con los datos extraídos
        source: Fuente de los datos (CVLAC o LinkedIn)
        summary: Diccionario para actualizar con el resumen
    """
    try:
        # Guardar habilidades
        if 'habilidades' in data and data['habilidades']:
            logger.info(f"Procesando {len(data['habilidades'])} habilidades de {source}")
            for item in data['habilidades']:
                try:
                    # Verificar si ya existe una habilidad similar
                    existing = UsuarioHabilidades.objects.filter(
                        user_id=usuario,
                        habilidad__icontains=item['habilidad']
                    ).first()
                    
                    if not existing:
                        UsuarioHabilidades.objects.create(
                            user_id=usuario,
                            habilidad=item['habilidad'],
                            experiencia=f"{item['experiencia']} (Fuente: {source})"
                        )
                        summary['habilidades_added'] += 1
                        logger.info(f"Habilidad agregada: {item['habilidad']}")
                    else:
                        logger.info(f"Habilidad ya existe: {item['habilidad']}")
                except Exception as e:
                    error_msg = f"Error al guardar habilidad {item.get('habilidad', 'desconocida')}: {str(e)}"
                    logger.error(error_msg)
                    summary['errors'].append(error_msg)
        
        # Guardar conocimientos
        if 'conocimientos' in data and data['conocimientos']:
            logger.info(f"Procesando {len(data['conocimientos'])} conocimientos de {source}")
            for item in data['conocimientos']:
                try:
                    # Verificar si ya existe un conocimiento similar
                    existing = UsuarioConocimiento.objects.filter(
                        user_id=usuario,
                        conocimiento__icontains=item['conocimiento']
                    ).first()
                    
                    if not existing:
                        UsuarioConocimiento.objects.create(
                            user_id=usuario,
                            conocimiento=item['conocimiento'],
                            nivel=item['nivel']
                        )
                        summary['conocimientos_added'] += 1
                        logger.info(f"Conocimiento agregado: {item['conocimiento']}")
                    else:
                        logger.info(f"Conocimiento ya existe: {item['conocimiento']}")
                except Exception as e:
                    error_msg = f"Error al guardar conocimiento {item.get('conocimiento', 'desconocido')}: {str(e)}"
                    logger.error(error_msg)
                    summary['errors'].append(error_msg)
        
        # Guardar estudios
        if 'estudios' in data and data['estudios']:
            logger.info(f"Procesando {len(data['estudios'])} estudios de {source}")
            for item in data['estudios']:
                try:
                    # Verificar si ya existe un estudio similar
                    existing = UsuarioEstudios.objects.filter(
                        user_id=usuario,
                        estudio__icontains=item['estudio'],
                        nivel=item['nivel']
                    ).first()
                    
                    if not existing:
                        UsuarioEstudios.objects.create(
                            user_id=usuario,
                            estudio=item['estudio'],
                            nivel=item['nivel'],
                            year=item['year']
                        )
                        summary['estudios_added'] += 1
                        logger.info(f"Estudio agregado: {item['estudio']}")
                    else:
                        logger.info(f"Estudio ya existe: {item['estudio']}")
                except Exception as e:
                    error_msg = f"Error al guardar estudio {item.get('estudio', 'desconocido')}: {str(e)}"
                    logger.error(error_msg)
                    summary['errors'].append(error_msg)
        
        # Guardar experiencia
        if 'experiencia' in data and data['experiencia']:
            logger.info(f"Procesando {len(data['experiencia'])} experiencias de {source}")
            for item in data['experiencia']:
                try:
                    # Verificar si ya existe una experiencia similar
                    existing = UsuarioExperiencia.objects.filter(
                        user_id=usuario,
                        rol__icontains=item['rol']
                    ).first()
                    
                    if not existing:
                        UsuarioExperiencia.objects.create(
                            user_id=usuario,
                            rol=item['rol'],
                            tiempo=item['tiempo'],
                            actividades=f"{item['actividades']} (Fuente: {source})"
                        )
                        summary['experiencia_added'] += 1
                        logger.info(f"Experiencia agregada: {item['rol']}")
                    else:
                        logger.info(f"Experiencia ya existe: {item['rol']}")
                except Exception as e:
                    error_msg = f"Error al guardar experiencia {item.get('rol', 'desconocida')}: {str(e)}"
                    logger.error(error_msg)
                    summary['errors'].append(error_msg)
    
    except Exception as e:
        error_msg = f"Error al guardar datos del usuario: {str(e)}"
        logger.error(error_msg)
        summary['errors'].append(f"Error al guardar datos de {source}: {str(e)}")
        raise 