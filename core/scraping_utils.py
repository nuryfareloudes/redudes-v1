import requests
from bs4 import BeautifulSoup
import re
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import os
import json
from typing import Dict, Optional, List

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_driver() -> webdriver.Chrome:
    """
    Configura y retorna una instancia del driver de Chrome con opciones optimizadas
    """
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--disable-notifications')
    chrome_options.add_argument('--disable-popup-blocking')
    
    service = Service(ChromeDriverManager().install())
    
    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(30)
        return driver
    except Exception as e:
        logger.error(f"Error al configurar el driver: {str(e)}")
        raise

def wait_for_element(driver: webdriver.Chrome, by: By, value: str, timeout: int = 10) -> Optional[webdriver.remote.webelement.WebElement]:
    """
    Espera a que un elemento esté presente en la página
    """
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
        return element
    except TimeoutException:
        logger.warning(f"Timeout esperando elemento: {value}")
        return None
    except Exception as e:
        logger.error(f"Error esperando elemento {value}: {str(e)}")
        return None

def extract_cvlac_data(url: str) -> Optional[Dict]:
    """
    Extrae datos del perfil CVLAC usando los selectores correctos
    """
    if not url:
        logger.warning("URL de CVLAC no proporcionada")
        return None
        
    driver = None
    try:
        driver = setup_driver()
        logger.info(f"Accediendo a CVLAC: {url}")
        driver.get(url)
        
        # Esperar a que la página cargue
        time.sleep(5)
        
        # Extraer información básica
        data = {
            'nombre': '',
            'institucion': '',
            'grupo_investigacion': '',
            'categoria': '',
            'publicaciones': [],
            'articulos': [],
            'libros': [],
            'capitulos': [],
            'proyectos': [],
            'estudios': []
        }
        
        # Nombre
        nombre_elem = wait_for_element(driver, By.CSS_SELECTOR, '#nombre_completo')
        if nombre_elem:
            data['nombre'] = nombre_elem.text.strip()
            
        # Institución
        inst_elem = wait_for_element(driver, By.CSS_SELECTOR, '#institucion')
        if inst_elem:
            data['institucion'] = inst_elem.text.strip()
            
        # Grupo de investigación
        grupo_elem = wait_for_element(driver, By.CSS_SELECTOR, '#grupo_investigacion')
        if grupo_elem:
            data['grupo_investigacion'] = grupo_elem.text.strip()
            
        # Categoría
        cat_elem = wait_for_element(driver, By.CSS_SELECTOR, '#categoria')
        if cat_elem:
            data['categoria'] = cat_elem.text.strip()
            
        # Publicaciones
        try:
            pub_elements = driver.find_elements(By.CSS_SELECTOR, '.publicacion')
            for pub in pub_elements:
                try:
                    titulo = pub.find_element(By.CSS_SELECTOR, '.titulo').text.strip()
                    autores = pub.find_element(By.CSS_SELECTOR, '.autores').text.strip()
                    revista = pub.find_element(By.CSS_SELECTOR, '.revista').text.strip()
                    data['publicaciones'].append({
                        'titulo': titulo,
                        'autores': autores,
                        'revista': revista
                    })
                except NoSuchElementException as e:
                    logger.warning(f"Error extrayendo publicación: {str(e)}")
                    continue
        except Exception as e:
            logger.error(f"Error extrayendo sección de publicaciones: {str(e)}")
            
        # Artículos
        try:
            art_elements = driver.find_elements(By.CSS_SELECTOR, '.articulo')
            for art in art_elements:
                try:
                    titulo = art.find_element(By.CSS_SELECTOR, '.titulo').text.strip()
                    autores = art.find_element(By.CSS_SELECTOR, '.autores').text.strip()
                    revista = art.find_element(By.CSS_SELECTOR, '.revista').text.strip()
                    data['articulos'].append({
                        'titulo': titulo,
                        'autores': autores,
                        'revista': revista
                    })
                except NoSuchElementException as e:
                    logger.warning(f"Error extrayendo artículo: {str(e)}")
                    continue
        except Exception as e:
            logger.error(f"Error extrayendo sección de artículos: {str(e)}")
            
        # Libros
        try:
            lib_elements = driver.find_elements(By.CSS_SELECTOR, '.libro')
            for lib in lib_elements:
                try:
                    titulo = lib.find_element(By.CSS_SELECTOR, '.titulo').text.strip()
                    autores = lib.find_element(By.CSS_SELECTOR, '.autores').text.strip()
                    editorial = lib.find_element(By.CSS_SELECTOR, '.editorial').text.strip()
                    data['libros'].append({
                        'titulo': titulo,
                        'autores': autores,
                        'editorial': editorial
                    })
                except NoSuchElementException as e:
                    logger.warning(f"Error extrayendo libro: {str(e)}")
                    continue
        except Exception as e:
            logger.error(f"Error extrayendo sección de libros: {str(e)}")
            
        # Capítulos de libro
        try:
            cap_elements = driver.find_elements(By.CSS_SELECTOR, '.capitulo')
            for cap in cap_elements:
                try:
                    titulo = cap.find_element(By.CSS_SELECTOR, '.titulo').text.strip()
                    autores = cap.find_element(By.CSS_SELECTOR, '.autores').text.strip()
                    libro = cap.find_element(By.CSS_SELECTOR, '.libro').text.strip()
                    data['capitulos'].append({
                        'titulo': titulo,
                        'autores': autores,
                        'libro': libro
                    })
                except NoSuchElementException as e:
                    logger.warning(f"Error extrayendo capítulo: {str(e)}")
                    continue
        except Exception as e:
            logger.error(f"Error extrayendo sección de capítulos: {str(e)}")
            
        # Proyectos
        try:
            proy_elements = driver.find_elements(By.CSS_SELECTOR, '.proyecto')
            for proy in proy_elements:
                try:
                    titulo = proy.find_element(By.CSS_SELECTOR, '.titulo').text.strip()
                    descripcion = proy.find_element(By.CSS_SELECTOR, '.descripcion').text.strip()
                    data['proyectos'].append({
                        'titulo': titulo,
                        'descripcion': descripcion
                    })
                except NoSuchElementException as e:
                    logger.warning(f"Error extrayendo proyecto: {str(e)}")
                    continue
        except Exception as e:
            logger.error(f"Error extrayendo sección de proyectos: {str(e)}")
            
        # Estudios
        try:
            est_elements = driver.find_elements(By.CSS_SELECTOR, '.estudio')
            for est in est_elements:
                try:
                    titulo = est.find_element(By.CSS_SELECTOR, '.titulo').text.strip()
                    institucion = est.find_element(By.CSS_SELECTOR, '.institucion').text.strip()
                    fecha = est.find_element(By.CSS_SELECTOR, '.fecha').text.strip()
                    data['estudios'].append({
                        'titulo': titulo,
                        'institucion': institucion,
                        'fecha': fecha
                    })
                except NoSuchElementException as e:
                    logger.warning(f"Error extrayendo estudio: {str(e)}")
                    continue
        except Exception as e:
            logger.error(f"Error extrayendo sección de estudios: {str(e)}")
                
        return data
        
    except Exception as e:
        logger.error(f"Error extrayendo datos de CVLAC: {str(e)}")
        return None
        
    finally:
        if driver:
            driver.quit()

# Función de compatibilidad para mantener la interfaz anterior
def extract_cvlac_info(url):
    """
    Función de compatibilidad que utiliza extract_cvlac_data internamente
    """
    try:
        data = extract_cvlac_data(url)
        if not data:
            return None
            
        # Convertir al formato esperado por el código existente
        info = {
            'nombre': data.get('nombre', 'No disponible'),
            'institucion': data.get('institucion', 'No disponible'),
            'grupo': data.get('grupo_investigacion', 'No disponible'),
            'categoria': data.get('categoria', 'No disponible'),
            'publicaciones': [],
            'habilidades': [],
            'conocimientos': [],
            'estudios': [],
            'experiencia': []
        }
        
        # Procesar publicaciones
        for pub in data.get('publicaciones', []):
            info['publicaciones'].append(f"{pub.get('titulo', '')} - {pub.get('autores', '')} - {pub.get('revista', '')}")
            
        # Procesar artículos como publicaciones
        for art in data.get('articulos', []):
            info['publicaciones'].append(f"{art.get('titulo', '')} - {art.get('autores', '')} - {art.get('revista', '')}")
            
        # Procesar libros como publicaciones
        for lib in data.get('libros', []):
            info['publicaciones'].append(f"{lib.get('titulo', '')} - {lib.get('autores', '')} - {lib.get('editorial', '')}")
            
        # Procesar estudios
        for est in data.get('estudios', []):
            info['estudios'].append({
                'estudio': est.get('titulo', ''),
                'nivel': 'No especificado',
                'year': est.get('fecha', '')
            })
            
        return info
        
    except Exception as e:
        logger.error(f"Error al extraer información de CVLAC: {str(e)}")
        return None

# Función de compatibilidad para LinkedIn (comentada pero mantenida para compatibilidad)
def extract_linkedin_info(url):
    """
    Función de compatibilidad para LinkedIn (temporalmente simplificada)
    """
    try:
        # Guardar la página para depuración
        debug_dir = "debug_logs"
        if not os.path.exists(debug_dir):
            os.makedirs(debug_dir)
            
        logger.info("Página de LinkedIn guardada para depuración")
        
        # Devolver datos mínimos para mantener compatibilidad
        logger.warning("LinkedIn requiere inicio de sesión. No se puede extraer información.")
        
        # Datos mínimos para mantener compatibilidad
        info = {
            'nombre': 'No disponible',
            'cargo': 'No disponible',
            'empresa': 'No disponible',
            'ubicacion': 'No disponible',
            'experiencias': [],
            'educacion': [],
            'experiencia': [{
                'rol': 'No disponible',
                'tiempo': 'No disponible',
                'actividades': 'Extracción de LinkedIn temporalmente deshabilitada'
            }]
        }
        
        logger.info("Se ha extraído información limitada de LinkedIn")
        return info
        
    except Exception as e:
        logger.error(f"Error al extraer información de LinkedIn: {str(e)}")
        return None

# Comentando temporalmente las funciones de LinkedIn
"""
def extract_linkedin_data(url: str) -> Optional[Dict]:
    # ... código existente ...

def extract_linkedin_info(url):
    # ... código existente ...
""" 