import os
import sys
import django
import random
from datetime import datetime, timedelta
from faker import Faker

# Configurar el entorno de Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'redudes.settings')
django.setup()

from core.models import (
    Usuario, UsuarioHabilidades, UsuarioConocimiento,
    UsuarioEstudios, UsuarioExperiencia, Proyecto,
    ProyectoRoles, ProyectoAliados, ProyectoProductos
)

# Inicializar Faker
fake = Faker('es_ES')

# Constantes para generación de datos
HABILIDADES = [
    'Liderazgo',
    'Trabajo en equipo',
    'Comunicación efectiva',
    'Resolución de problemas',
    'Gestión del tiempo',
    'Pensamiento crítico',
    'Adaptabilidad',
    'Creatividad'
]

CONOCIMIENTOS = [
    'Python',
    'JavaScript',
    'React',
    'Django',
    'SQL',
    'AWS',
    'Docker',
    'Machine Learning',
    'Data Science'
]

NIVELES_EDUCACION = [
    (1, 'Técnico'),
    (2, 'Tecnólogo'),
    (3, 'Profesional'),
    (4, 'Especialización'),
    (5, 'Maestría'),
    (6, 'Doctorado')
]

TIPOS_ALIADOS = [
    'Universidad',
    'Empresa privada',
    'Entidad gubernamental',
    'ONG',
    'Centro de investigación'
]

TIPOS_PRODUCTOS = [
    'Software',
    'Hardware',
    'Documento',
    'Prototipo',
    'Servicio',
    'Metodología',
    'Patente'
]

def crear_usuario():
    """Crea un usuario con sus habilidades, conocimientos, estudios y experiencias"""
    usuario = Usuario.objects.create(
        nombres=fake.first_name(),
        apellidos=fake.last_name(),
        email=fake.email(),
        telefono=fake.random_number(digits=10),
        puesto_actual=fake.job(),
        dependencia=fake.company(),
        url_cvlac=fake.url(),
        url_linkedin=fake.url(),
        fecha_ingreso=fake.date_time_this_year()
    )
    
    # Agregar habilidades
    num_habilidades = random.randint(3, 8)
    for _ in range(num_habilidades):
        UsuarioHabilidades.objects.create(
            user_id=usuario,
            habilidad=random.choice(HABILIDADES),
            experiencia=fake.text(max_nb_chars=200)
        )
    
    # Agregar conocimientos
    num_conocimientos = random.randint(3, 6)
    for _ in range(num_conocimientos):
        UsuarioConocimiento.objects.create(
            user_id=usuario,
            conocimiento=random.choice(CONOCIMIENTOS),
            nivel=random.randint(1, 5)
        )
    
    # Agregar estudios
    num_estudios = random.randint(1, 3)
    for _ in range(num_estudios):
        nivel = random.choice(NIVELES_EDUCACION)
        UsuarioEstudios.objects.create(
            user_id=usuario,
            estudio=fake.job(),
            nivel=nivel[0],
            year=fake.random_int(min=2000, max=2024)
        )
    
    # Agregar experiencias
    num_experiencias = random.randint(1, 4)
    for _ in range(num_experiencias):
        UsuarioExperiencia.objects.create(
            user_id=usuario,
            rol=fake.job(),
            tiempo=random.randint(1, 15),
            actividades=fake.text(max_nb_chars=200)
        )
    
    return usuario

def crear_proyecto():
    """Crea un proyecto con sus roles, aliados y productos"""
    proyecto = Proyecto.objects.create(
        nombre=fake.company(),
        convocatoria=fake.catch_phrase(),
        tipo_proyecto=random.choice(['Investigación', 'Desarrollo', 'Innovación', 'Consultoría']),
        tipo_convocatoria=random.choice(['Interna', 'Externa', 'Internacional', 'Especial']),
        alcance=fake.text(max_nb_chars=500),
        objetivo=fake.text(max_nb_chars=500),
        presupuesto=random.randint(1000000, 100000000),
        fecha=fake.date_time_this_year()
    )
    
    # Agregar roles
    num_roles = random.randint(1, 3)
    for _ in range(num_roles):
        rol = ProyectoRoles.objects.create(
            project_id=proyecto,
            rol=fake.job(),
            habilidades=','.join(random.sample(HABILIDADES, random.randint(3, 6))),
            conocimientos=','.join(random.sample(CONOCIMIENTOS, random.randint(2, 4))),
            experiencia=f"{random.randint(1, 10)} años"
        )
    
    # Agregar aliados
    num_aliados = random.randint(1, 3)
    for _ in range(num_aliados):
        ProyectoAliados.objects.create(
            project_id=proyecto,
            entidad=fake.company(),
            tipo_aliado=random.choice(TIPOS_ALIADOS),
            responsabilidades=fake.text(max_nb_chars=200)
        )
    
    # Agregar productos
    num_productos = random.randint(1, 4)
    for _ in range(num_productos):
        ProyectoProductos.objects.create(
            project_id=proyecto,
            producto=fake.catch_phrase(),
            tipo=random.choice(TIPOS_PRODUCTOS),
            cantidad=random.randint(1, 100)
        )
    
    return proyecto

def main():
    print("Iniciando generación de datos de prueba...")
    
    # Crear 3 usuarios
    for i in range(3):
        print(f"Creando usuario {i+1}/3...")
        crear_usuario()
    
    # Crear 3 proyectos
    for i in range(3):
        print(f"Creando proyecto {i+1}/3...")
        crear_proyecto()
    
    print("\nDatos de prueba generados exitosamente:")
    print(f"- Usuarios creados: 3")
    print(f"- Proyectos creados: 3")

if __name__ == "__main__":
    main() 