from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

class Proyecto(models.Model):
    id = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=255)
    convocatoria = models.CharField(max_length=255)
    tipo_proyecto = models.CharField(max_length=255)
    tipo_convocatoria = models.CharField(max_length=255)
    alcance = models.TextField()
    objetivo = models.TextField()
    presupuesto = models.BigIntegerField()
    fecha = models.DateTimeField()

    def __str__(self):
        return self.nombre

class Usuario(models.Model):
    id = models.BigAutoField(primary_key=True)
    nombres = models.CharField(max_length=255)
    apellidos = models.CharField(max_length=255)
    email = models.CharField(max_length=255)
    telefono = models.BigIntegerField()
    puesto_actual = models.CharField(max_length=255)
    dependencia = models.CharField(max_length=255)
    url_cvlac = models.CharField(max_length=255)
    url_linkedin = models.CharField(max_length=255)
    fecha_ingreso = models.DateTimeField()

    def __str__(self):
        return f"{self.nombres} {self.apellidos}"

class ProyectoRoles(models.Model):
    id = models.BigAutoField(primary_key=True)
    project_id = models.ForeignKey(Proyecto, on_delete=models.CASCADE)
    rol = models.CharField(max_length=255)
    habilidades = models.CharField(max_length=255)
    experiencia = models.CharField(max_length=255)
    conocimientos = models.CharField(max_length=255)

class ProyectoAliados(models.Model):
    id = models.BigAutoField(primary_key=True)
    project_id = models.ForeignKey(Proyecto, on_delete=models.CASCADE)
    entidad = models.CharField(max_length=255)
    tipo_aliado = models.CharField(max_length=255)
    responsabilidades = models.TextField()

class ProyectoProductos(models.Model):
    id = models.BigAutoField(primary_key=True)
    project_id = models.ForeignKey(Proyecto, on_delete=models.CASCADE)
    producto = models.CharField(max_length=255)
    tipo = models.CharField(max_length=255)
    cantidad = models.IntegerField()

class UsuarioHabilidades(models.Model):
    id = models.BigAutoField(primary_key=True)
    user_id = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='habilidades')
    habilidad = models.CharField(max_length=255)
    experiencia = models.TextField()

class UsuarioConocimiento(models.Model):
    id = models.BigAutoField(primary_key=True)
    user_id = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='conocimientos')
    conocimiento = models.CharField(max_length=255)
    nivel = models.IntegerField()

class UsuarioEstudios(models.Model):
    id = models.BigAutoField(primary_key=True)
    user_id = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='estudios')
    estudio = models.CharField(max_length=255)
    nivel = models.IntegerField()
    year = models.BigIntegerField()

class UsuarioExperiencia(models.Model):
    id = models.BigAutoField(primary_key=True)
    user_id = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='experiencias')
    rol = models.CharField(max_length=255)
    tiempo = models.IntegerField()
    actividades = models.TextField()

class CustomUser(AbstractUser):
    is_admin = models.BooleanField(default=False)
    is_evaluator = models.BooleanField(default=False)
    is_researcher = models.BooleanField(default=False)
