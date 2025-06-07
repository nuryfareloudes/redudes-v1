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

class RecomendacionProyecto(models.Model):
    id = models.BigAutoField(primary_key=True)
    project_id = models.ForeignKey(Proyecto, on_delete=models.CASCADE)
    fecha_recomendacion = models.DateTimeField(auto_now_add=True)
    rf_accuracy = models.FloatField()
    rf_precision = models.FloatField()
    rf_recall = models.FloatField()
    rf_f1 = models.FloatField()
    knn_accuracy = models.FloatField()
    knn_precision = models.FloatField()
    knn_recall = models.FloatField()
    knn_f1 = models.FloatField()
    nn_accuracy = models.FloatField(null=True, blank=True)
    nn_precision = models.FloatField(null=True, blank=True)
    nn_recall = models.FloatField(null=True, blank=True)
    nn_f1 = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"Recomendación para {self.project_id.nombre} - {self.fecha_recomendacion}"

class RecomendacionUsuario(models.Model):
    id = models.BigAutoField(primary_key=True)
    recomendacion_id = models.ForeignKey(RecomendacionProyecto, on_delete=models.CASCADE, related_name='usuarios_recomendados')
    user_id = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    score_combinado = models.FloatField()
    score_rf = models.FloatField()
    score_knn = models.FloatField()
    score_nn = models.FloatField(null=True, blank=True)
    ranking = models.IntegerField()
    nivel_confianza = models.CharField(max_length=50, default='Media')  # Alta, Media, Baja
    match_habilidades = models.FloatField(default=0.0)
    match_conocimientos = models.FloatField(default=0.0)
    match_experiencia = models.FloatField(default=0.0)
    match_educacion = models.FloatField(default=0.0)

    class Meta:
        ordering = ['-score_combinado']

    def __str__(self):
        return f"Recomendación: {self.user_id.nombres} {self.user_id.apellidos} - Score: {self.score_combinado}"

    def get_nivel_confianza(self):
        if self.score_combinado > 0.7:
            return 'Alta'
        elif self.score_combinado > 0.5:
            return 'Media'
        return 'Baja'

    def save(self, *args, **kwargs):
        self.nivel_confianza = self.get_nivel_confianza()
        super().save(*args, **kwargs)
