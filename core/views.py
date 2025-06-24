from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, FormView
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from .models import (
    Proyecto, ProyectoRoles, ProyectoAliados, ProyectoProductos,
    Usuario, UsuarioHabilidades, UsuarioConocimiento, UsuarioEstudios, UsuarioExperiencia,
    RecomendacionProyecto, RecomendacionUsuario
)
from .data_services import process_user_data
from django import forms
import logging
import datetime
from .ml_models import RecommendationSystem
from .forms import (
    UsuarioForm, HabilidadFormSet, ConocimientoFormSet,
    EstudioFormSet, ExperienciaFormSet
)
from .advanced_ml_models import AdvancedRecommendationSystem
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import io
from django.db.models import Count, Avg, Q, Max
from django.utils import timezone
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Create your views here.

class HomeView(LoginRequiredMixin, TemplateView):
    template_name = 'core/home.html'

# Vistas para Proyectos
class ProyectoListView(LoginRequiredMixin, ListView):
    model = Proyecto
    template_name = 'core/proyecto_list.html'
    context_object_name = 'proyectos'
    ordering = ['-fecha']

class ProyectoDetailView(LoginRequiredMixin, DetailView):
    model = Proyecto
    template_name = 'core/proyecto_detail.html'
    context_object_name = 'proyecto'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        proyecto = self.get_object()
        context['proyecto_roles'] = ProyectoRoles.objects.filter(project_id=proyecto)
        context['proyecto_aliados'] = ProyectoAliados.objects.filter(project_id=proyecto)
        context['proyecto_productos'] = ProyectoProductos.objects.filter(project_id=proyecto)
        return context

class ProyectoCreateView(LoginRequiredMixin, CreateView):
    model = Proyecto
    template_name = 'core/proyecto_form.html'
    fields = ['nombre', 'convocatoria', 'tipo_proyecto', 'tipo_convocatoria', 
              'alcance', 'objetivo', 'presupuesto', 'fecha']
    success_url = reverse_lazy('proyecto_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Proyecto creado exitosamente.')
        return super().form_valid(form)

class ProyectoUpdateView(LoginRequiredMixin, UpdateView):
    model = Proyecto
    template_name = 'core/proyecto_form.html'
    fields = ['nombre', 'convocatoria', 'tipo_proyecto', 'tipo_convocatoria', 
              'alcance', 'objetivo', 'presupuesto', 'fecha']
    
    def get_success_url(self):
        return reverse_lazy('proyecto_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, 'Proyecto actualizado exitosamente.')
        return super().form_valid(form)

class ProyectoDeleteView(LoginRequiredMixin, DeleteView):
    model = Proyecto
    template_name = 'core/proyecto_confirm_delete.html'
    context_object_name = 'proyecto'
    success_url = reverse_lazy('proyecto_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Proyecto eliminado exitosamente.')
        return super().delete(request, *args, **kwargs)

# Vistas para Usuarios
class UsuarioListView(LoginRequiredMixin, ListView):
    model = Usuario
    template_name = 'core/usuario_list.html'
    context_object_name = 'usuarios'
    ordering = ['nombres']

class UsuarioDetailView(LoginRequiredMixin, DetailView):
    model = Usuario
    template_name = 'core/usuario_detail.html'
    context_object_name = 'usuario'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        usuario = self.get_object()
        context['habilidad_formset'] = HabilidadFormSet(instance=usuario, prefix='habilidades')
        context['conocimiento_formset'] = ConocimientoFormSet(instance=usuario, prefix='conocimientos')
        context['estudio_formset'] = EstudioFormSet(instance=usuario, prefix='estudios')
        context['experiencia_formset'] = ExperienciaFormSet(instance=usuario, prefix='experiencias')
        return context

    def post(self, request, *args, **kwargs):
        usuario = self.get_object()
        habilidad_formset = HabilidadFormSet(request.POST, instance=usuario, prefix='habilidades')
        conocimiento_formset = ConocimientoFormSet(request.POST, instance=usuario, prefix='conocimientos')
        estudio_formset = EstudioFormSet(request.POST, instance=usuario, prefix='estudios')
        experiencia_formset = ExperienciaFormSet(request.POST, instance=usuario, prefix='experiencias')

        if habilidad_formset.is_valid():
            habilidad_formset.save()
        if conocimiento_formset.is_valid():
            conocimiento_formset.save()
        if estudio_formset.is_valid():
            estudio_formset.save()
        if experiencia_formset.is_valid():
            experiencia_formset.save()

        return redirect('usuario_detail', pk=usuario.pk)

class UsuarioCreateView(LoginRequiredMixin, CreateView):
    model = Usuario
    template_name = 'core/usuario_form.html'
    fields = ['nombres', 'apellidos', 'email', 'telefono', 'puesto_actual', 
              'dependencia', 'url_cvlac', 'url_linkedin', 'fecha_ingreso']
    success_url = reverse_lazy('usuario_list')
    
    def form_valid(self, form):
        messages.success(self.request, "Usuario creado exitosamente.")
        response = super().form_valid(form)
        
        # Procesar datos automáticamente si se proporcionaron URLs
        usuario = self.object
        if usuario.url_cvlac or usuario.url_linkedin:
            try:
                # Procesar datos de forma síncrona
                result = process_user_data(usuario.id)
                
                if result.get('error'):
                    messages.warning(self.request, f"Error al procesar datos: {result['error']}")
                else:
                    messages.success(self.request, "Datos procesados exitosamente.")
            except Exception as e:
                logger.error(f"Error al procesar datos: {str(e)}")
                messages.warning(self.request, f"Error al procesar datos: {str(e)}")
        
        return response

class UsuarioUpdateView(LoginRequiredMixin, UpdateView):
    model = Usuario
    template_name = 'core/usuario_form.html'
    fields = ['nombres', 'apellidos', 'email', 'telefono', 'puesto_actual', 'dependencia', 'url_cvlac', 'url_linkedin', 'fecha_ingreso']
    
    def get_success_url(self):
        return reverse_lazy('usuario_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, "Usuario actualizado exitosamente.")
        response = super().form_valid(form)
        
        # Procesar datos automáticamente si se modificaron las URLs
        usuario = self.object
        if form.has_changed() and ('url_cvlac' in form.changed_data or 'url_linkedin' in form.changed_data):
            try:
                # Procesar datos de forma síncrona
                result = process_user_data(usuario.id)
                
                if result.get('error'):
                    messages.warning(self.request, f"Error al procesar datos: {result['error']}")
                else:
                    messages.success(self.request, "Datos procesados exitosamente.")
            except Exception as e:
                logger.error(f"Error al procesar datos: {str(e)}")
                messages.warning(self.request, f"Error al procesar datos: {str(e)}")
        
        return response

class UsuarioDeleteView(LoginRequiredMixin, DeleteView):
    model = Usuario
    template_name = 'core/usuario_confirm_delete.html'
    success_url = reverse_lazy('usuario_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, "Usuario eliminado exitosamente.")
        return super().delete(request, *args, **kwargs)

# Vistas para procesar datos de usuario
@method_decorator(login_required, name='dispatch')
class ProcesarDatosUsuarioView(FormView):
    template_name = 'core/procesar_datos_usuario.html'
    form_class = forms.Form
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['usuario'] = get_object_or_404(Usuario, pk=self.kwargs['pk'])
        return context
    
    def form_valid(self, form):
        usuario = get_object_or_404(Usuario, pk=self.kwargs['pk'])
        
        if not usuario.url_cvlac and not usuario.url_linkedin:
            messages.warning(self.request, 'El usuario no tiene URLs de CVLAC o LinkedIn para procesar.')
            return redirect('usuario_detail', pk=usuario.id)
        
        try:
            # Procesar datos
            summary = process_user_data(usuario.id)
            
            # Mostrar resumen de los datos procesados
            if 'error' in summary:
                messages.error(self.request, f"Error al procesar datos: {summary['error']}")
            else:
                success_msg = f"Se han importado: {summary['habilidades_added']} habilidades, "
                success_msg += f"{summary['conocimientos_added']} conocimientos, "
                success_msg += f"{summary['estudios_added']} estudios, "
                success_msg += f"{summary['experiencia_added']} experiencias."
                
                if summary['errors']:
                    success_msg += f" Errores: {', '.join(summary['errors'])}"
                
                messages.success(self.request, success_msg)
        except Exception as e:
            messages.error(self.request, f"Error al procesar datos: {str(e)}")
        
        return redirect('usuario_detail', pk=usuario.id)

# Formularios para datos de usuario
class UsuarioHabilidadForm(forms.ModelForm):
    EXPERIENCIA_CHOICES = [
        ('', 'Seleccione nivel de experiencia'),
        ('Menos de 1 año', 'Menos de 1 año'),
        ('1-2 años', '1-2 años'),
        ('3-5 años', '3-5 años'),
        ('5-10 años', '5-10 años'),
        ('Más de 10 años', 'Más de 10 años'),
    ]
    
    experiencia = forms.ChoiceField(choices=EXPERIENCIA_CHOICES, required=True)
    
    class Meta:
        model = UsuarioHabilidades
        fields = ['habilidad', 'experiencia']

class UsuarioConocimientoForm(forms.ModelForm):
    class Meta:
        model = UsuarioConocimiento
        fields = ['conocimiento', 'nivel']
        widgets = {
            'nivel': forms.NumberInput(attrs={'min': 1, 'max': 10}),
        }

class UsuarioEstudioForm(forms.ModelForm):
    NIVEL_CHOICES = [
        (1, 'Técnico'),
        (2, 'Tecnólogo'),
        (3, 'Pregrado'),
        (4, 'Especialización'),
        (5, 'Maestría'),
        (6, 'Doctorado'),
    ]
    
    nivel = forms.ChoiceField(choices=NIVEL_CHOICES)
    
    class Meta:
        model = UsuarioEstudios
        fields = ['estudio', 'nivel', 'year']

class UsuarioExperienciaForm(forms.ModelForm):
    class Meta:
        model = UsuarioExperiencia
        fields = ['rol', 'tiempo', 'actividades']
        widgets = {
            'actividades': forms.Textarea(attrs={'rows': 3}),
        }

# Vistas para Habilidades de Usuario
class UsuarioHabilidadCreateView(LoginRequiredMixin, CreateView):
    model = UsuarioHabilidades
    form_class = UsuarioHabilidadForm
    template_name = 'core/usuario_habilidad_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['usuario'] = get_object_or_404(Usuario, pk=self.kwargs['pk'])
        return context
    
    def form_valid(self, form):
        form.instance.user_id = get_object_or_404(Usuario, pk=self.kwargs['pk'])
        messages.success(self.request, 'Habilidad agregada exitosamente.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('usuario_detail', kwargs={'pk': self.kwargs['pk']})

class UsuarioHabilidadUpdateView(LoginRequiredMixin, UpdateView):
    model = UsuarioHabilidades
    form_class = UsuarioHabilidadForm
    template_name = 'core/usuario_habilidad_form.html'
    pk_url_kwarg = 'habilidad_pk'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['usuario'] = self.object.user_id
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Habilidad actualizada exitosamente.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('usuario_detail', kwargs={'pk': self.object.user_id.id})

class UsuarioHabilidadDeleteView(LoginRequiredMixin, DeleteView):
    model = UsuarioHabilidades
    template_name = 'core/usuario_habilidad_confirm_delete.html'
    pk_url_kwarg = 'habilidad_pk'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['usuario'] = self.object.user_id
        return context
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Habilidad eliminada exitosamente.')
        return super().delete(request, *args, **kwargs)
    
    def get_success_url(self):
        return reverse_lazy('usuario_detail', kwargs={'pk': self.object.user_id.id})

# Vistas para Conocimientos de Usuario
class UsuarioConocimientoCreateView(LoginRequiredMixin, CreateView):
    model = UsuarioConocimiento
    form_class = UsuarioConocimientoForm
    template_name = 'core/usuario_conocimiento_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['usuario'] = get_object_or_404(Usuario, pk=self.kwargs['pk'])
        return context
    
    def form_valid(self, form):
        form.instance.user_id = get_object_or_404(Usuario, pk=self.kwargs['pk'])
        messages.success(self.request, 'Conocimiento agregado exitosamente.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('usuario_detail', kwargs={'pk': self.kwargs['pk']})

class UsuarioConocimientoUpdateView(LoginRequiredMixin, UpdateView):
    model = UsuarioConocimiento
    form_class = UsuarioConocimientoForm
    template_name = 'core/usuario_conocimiento_form.html'
    pk_url_kwarg = 'conocimiento_pk'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['usuario'] = self.object.user_id
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Conocimiento actualizado exitosamente.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('usuario_detail', kwargs={'pk': self.object.user_id.id})

class UsuarioConocimientoDeleteView(LoginRequiredMixin, DeleteView):
    model = UsuarioConocimiento
    template_name = 'core/usuario_conocimiento_confirm_delete.html'
    pk_url_kwarg = 'conocimiento_pk'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['usuario'] = self.object.user_id
        return context
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Conocimiento eliminado exitosamente.')
        return super().delete(request, *args, **kwargs)
    
    def get_success_url(self):
        return reverse_lazy('usuario_detail', kwargs={'pk': self.object.user_id.id})

# Vistas para Estudios de Usuario
class UsuarioEstudioCreateView(LoginRequiredMixin, CreateView):
    model = UsuarioEstudios
    form_class = UsuarioEstudioForm
    template_name = 'core/usuario_estudio_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['usuario'] = get_object_or_404(Usuario, pk=self.kwargs['pk'])
        return context
    
    def form_valid(self, form):
        form.instance.user_id = get_object_or_404(Usuario, pk=self.kwargs['pk'])
        messages.success(self.request, 'Estudio agregado exitosamente.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('usuario_detail', kwargs={'pk': self.kwargs['pk']})

class UsuarioEstudioUpdateView(LoginRequiredMixin, UpdateView):
    model = UsuarioEstudios
    form_class = UsuarioEstudioForm
    template_name = 'core/usuario_estudio_form.html'
    pk_url_kwarg = 'estudio_pk'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['usuario'] = self.object.user_id
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Estudio actualizado exitosamente.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('usuario_detail', kwargs={'pk': self.object.user_id.id})

class UsuarioEstudioDeleteView(LoginRequiredMixin, DeleteView):
    model = UsuarioEstudios
    template_name = 'core/usuario_estudio_confirm_delete.html'
    pk_url_kwarg = 'estudio_pk'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['usuario'] = self.object.user_id
        return context
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Estudio eliminado exitosamente.')
        return super().delete(request, *args, **kwargs)
    
    def get_success_url(self):
        return reverse_lazy('usuario_detail', kwargs={'pk': self.object.user_id.id})

# Vistas para Experiencia de Usuario
class UsuarioExperienciaCreateView(LoginRequiredMixin, CreateView):
    model = UsuarioExperiencia
    form_class = UsuarioExperienciaForm
    template_name = 'core/usuario_experiencia_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['usuario'] = get_object_or_404(Usuario, pk=self.kwargs['pk'])
        return context
    
    def form_valid(self, form):
        form.instance.user_id = get_object_or_404(Usuario, pk=self.kwargs['pk'])
        messages.success(self.request, 'Experiencia agregada exitosamente.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('usuario_detail', kwargs={'pk': self.kwargs['pk']})

class UsuarioExperienciaUpdateView(LoginRequiredMixin, UpdateView):
    model = UsuarioExperiencia
    form_class = UsuarioExperienciaForm
    template_name = 'core/usuario_experiencia_form.html'
    pk_url_kwarg = 'experiencia_pk'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['usuario'] = self.object.user_id
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Experiencia actualizada exitosamente.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('usuario_detail', kwargs={'pk': self.object.user_id.id})

class UsuarioExperienciaDeleteView(LoginRequiredMixin, DeleteView):
    model = UsuarioExperiencia
    template_name = 'core/usuario_experiencia_confirm_delete.html'
    pk_url_kwarg = 'experiencia_pk'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['usuario'] = self.object.user_id
        return context
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Experiencia eliminada exitosamente.')
        return super().delete(request, *args, **kwargs)
    
    def get_success_url(self):
        return reverse_lazy('usuario_detail', kwargs={'pk': self.object.user_id.id})

@login_required
@require_POST
def process_user_data_view(request, pk):
    """
    Vista para procesar manualmente los datos de un usuario
    """
    try:
        # Verificar que el usuario existe
        usuario = get_object_or_404(Usuario, id=pk)
        
        # Procesar datos de forma síncrona
        result = process_user_data(pk)
        
        if result.get('error'):
            messages.error(request, f"Error al procesar datos: {result['error']}")
        else:
            # Mensaje de éxito con detalles
            success_msg = "Datos procesados exitosamente. "
            if result.get('habilidades_added', 0) > 0:
                success_msg += f"Se agregaron {result['habilidades_added']} habilidades. "
            if result.get('conocimientos_added', 0) > 0:
                success_msg += f"Se agregaron {result['conocimientos_added']} conocimientos. "
            if result.get('estudios_added', 0) > 0:
                success_msg += f"Se agregaron {result['estudios_added']} estudios. "
            if result.get('experiencia_added', 0) > 0:
                success_msg += f"Se agregaron {result['experiencia_added']} experiencias. "
            
            messages.success(request, success_msg)
    
    except Exception as e:
        logger.error(f"Error al procesar datos del usuario {pk}: {str(e)}")
        messages.error(request, f"Error al procesar datos: {str(e)}")
    
    return redirect('usuario_detail', pk=pk)

# Vistas para gestionar habilidades, conocimientos, estudios y experiencia
@login_required
def add_user_skill(request, user_id):
    """
    Vista para añadir una habilidad a un usuario
    """
    usuario = get_object_or_404(Usuario, id=user_id)
    
    if request.method == 'POST':
        try:
            habilidad = request.POST.get('habilidad', '').strip()
            experiencia = request.POST.get('experiencia', '').strip()
            
            if not habilidad:
                messages.error(request, "La habilidad no puede estar vacía.")
                return redirect('usuario_detail', pk=user_id)
            
            # Verificar si ya existe
            existing = UsuarioHabilidades.objects.filter(
                user_id=usuario,
                habilidad__iexact=habilidad
            ).first()
            
            if existing:
                messages.warning(request, f"La habilidad '{habilidad}' ya existe para este usuario.")
            else:
                UsuarioHabilidades.objects.create(
                    user_id=usuario,
                    habilidad=habilidad,
                    experiencia=experiencia
                )
                messages.success(request, f"Habilidad '{habilidad}' añadida exitosamente.")
        
        except Exception as e:
            logger.error(f"Error al añadir habilidad: {str(e)}")
            messages.error(request, f"Error al añadir habilidad: {str(e)}")
        
        return redirect('usuario_detail', pk=user_id)
    
    # Si es una solicitud GET, mostrar el formulario
    context = {
        'usuario': usuario,
        'form': UsuarioHabilidadForm()
    }
    return render(request, 'core/usuario_habilidad_form.html', context)

@login_required
def add_user_knowledge(request, user_id):
    """
    Vista para añadir un conocimiento a un usuario
    """
    usuario = get_object_or_404(Usuario, id=user_id)
    
    if request.method == 'POST':
        try:
            conocimiento = request.POST.get('conocimiento', '').strip()
            nivel = request.POST.get('nivel', '').strip()
            
            if not conocimiento:
                messages.error(request, "El conocimiento no puede estar vacío.")
                return redirect('usuario_detail', pk=user_id)
            
            # Verificar si ya existe
            existing = UsuarioConocimiento.objects.filter(
                user_id=usuario,
                conocimiento__iexact=conocimiento
            ).first()
            
            if existing:
                messages.warning(request, f"El conocimiento '{conocimiento}' ya existe para este usuario.")
            else:
                UsuarioConocimiento.objects.create(
                    user_id=usuario,
                    conocimiento=conocimiento,
                    nivel=nivel
                )
                messages.success(request, f"Conocimiento '{conocimiento}' añadido exitosamente.")
        
        except Exception as e:
            logger.error(f"Error al añadir conocimiento: {str(e)}")
            messages.error(request, f"Error al añadir conocimiento: {str(e)}")
        
        return redirect('usuario_detail', pk=user_id)
    
    # Si es una solicitud GET, mostrar el formulario
    context = {
        'usuario': usuario,
        'form': UsuarioConocimientoForm()
    }
    return render(request, 'core/usuario_conocimiento_form.html', context)

@login_required
def add_user_study(request, user_id):
    """
    Vista para añadir un estudio a un usuario
    """
    usuario = get_object_or_404(Usuario, id=user_id)
    
    if request.method == 'POST':
        try:
            estudio = request.POST.get('estudio', '').strip()
            nivel = request.POST.get('nivel', '').strip()
            year = request.POST.get('year', '').strip()
            
            if not estudio:
                messages.error(request, "El estudio no puede estar vacío.")
                return redirect('usuario_detail', pk=user_id)
            
            # Verificar si ya existe
            existing = UsuarioEstudios.objects.filter(
                user_id=usuario,
                estudio__iexact=estudio,
                nivel=nivel
            ).first()
            
            if existing:
                messages.warning(request, f"El estudio '{estudio}' ya existe para este usuario.")
            else:
                UsuarioEstudios.objects.create(
                    user_id=usuario,
                    estudio=estudio,
                    nivel=nivel,
                    year=year
                )
                messages.success(request, f"Estudio '{estudio}' añadido exitosamente.")
        
        except Exception as e:
            logger.error(f"Error al añadir estudio: {str(e)}")
            messages.error(request, f"Error al añadir estudio: {str(e)}")
        
        return redirect('usuario_detail', pk=user_id)
    
    # Si es una solicitud GET, mostrar el formulario
    context = {
        'usuario': usuario,
        'form': UsuarioEstudioForm(),
        'current_year': datetime.datetime.now().year
    }
    return render(request, 'core/usuario_estudio_form.html', context)

@login_required
def add_user_experience(request, user_id):
    """
    Vista para añadir una experiencia a un usuario
    """
    usuario = get_object_or_404(Usuario, id=user_id)
    
    if request.method == 'POST':
        try:
            rol = request.POST.get('rol', '').strip()
            tiempo = request.POST.get('tiempo', '').strip()
            actividades = request.POST.get('actividades', '').strip()
            
            if not rol:
                messages.error(request, "El rol no puede estar vacío.")
                return redirect('usuario_detail', pk=user_id)
            
            # Verificar si ya existe
            existing = UsuarioExperiencia.objects.filter(
                user_id=usuario,
                rol__iexact=rol
            ).first()
            
            if existing:
                messages.warning(request, f"La experiencia '{rol}' ya existe para este usuario.")
            else:
                UsuarioExperiencia.objects.create(
                    user_id=usuario,
                    rol=rol,
                    tiempo=tiempo,
                    actividades=actividades
                )
                messages.success(request, f"Experiencia '{rol}' añadida exitosamente.")
        
        except Exception as e:
            logger.error(f"Error al añadir experiencia: {str(e)}")
            messages.error(request, f"Error al añadir experiencia: {str(e)}")
        
        return redirect('usuario_detail', pk=user_id)
    
    # Si es una solicitud GET, mostrar el formulario
    context = {
        'usuario': usuario,
        'form': UsuarioExperienciaForm()
    }
    return render(request, 'core/usuario_experiencia_form.html', context)

@login_required
def delete_user_skill(request, pk):
    """
    Vista para eliminar una habilidad de un usuario
    """
    try:
        habilidad = get_object_or_404(UsuarioHabilidades, id=pk)
        user_id = habilidad.user_id.id
        habilidad_nombre = habilidad.habilidad
        habilidad.delete()
        messages.success(request, f"Habilidad '{habilidad_nombre}' eliminada exitosamente.")
    except Exception as e:
        logger.error(f"Error al eliminar habilidad: {str(e)}")
        messages.error(request, f"Error al eliminar habilidad: {str(e)}")
        user_id = request.GET.get('user_id')
    
    return redirect('usuario_detail', pk=user_id)

@login_required
def delete_user_knowledge(request, pk):
    """
    Vista para eliminar un conocimiento de un usuario
    """
    try:
        conocimiento = get_object_or_404(UsuarioConocimiento, id=pk)
        user_id = conocimiento.user_id.id
        conocimiento_nombre = conocimiento.conocimiento
        conocimiento.delete()
        messages.success(request, f"Conocimiento '{conocimiento_nombre}' eliminado exitosamente.")
    except Exception as e:
        logger.error(f"Error al eliminar conocimiento: {str(e)}")
        messages.error(request, f"Error al eliminar conocimiento: {str(e)}")
        user_id = request.GET.get('user_id')
    
    return redirect('usuario_detail', pk=user_id)

@login_required
def delete_user_study(request, pk):
    """
    Vista para eliminar un estudio de un usuario
    """
    try:
        estudio = get_object_or_404(UsuarioEstudios, id=pk)
        user_id = estudio.user_id.id
        estudio_nombre = estudio.estudio
        estudio.delete()
        messages.success(request, f"Estudio '{estudio_nombre}' eliminado exitosamente.")
    except Exception as e:
        logger.error(f"Error al eliminar estudio: {str(e)}")
        messages.error(request, f"Error al eliminar estudio: {str(e)}")
        user_id = request.GET.get('user_id')
    
    return redirect('usuario_detail', pk=user_id)

@login_required
def delete_user_experience(request, pk):
    """
    Vista para eliminar una experiencia de un usuario
    """
    try:
        experiencia = get_object_or_404(UsuarioExperiencia, id=pk)
        user_id = experiencia.user_id.id
        experiencia_nombre = experiencia.rol
        experiencia.delete()
        messages.success(request, f"Experiencia '{experiencia_nombre}' eliminada exitosamente.")
    except Exception as e:
        logger.error(f"Error al eliminar experiencia: {str(e)}")
        messages.error(request, f"Error al eliminar experiencia: {str(e)}")
        user_id = request.GET.get('user_id')
    
    return redirect('usuario_detail', pk=user_id)

@login_required
def check_task_status(request, task_id):
    """
    Vista para verificar el estado de una tarea de Celery
    """
    try:
        # Obtener resultado de la tarea
        task_result = AsyncResult(task_id)
        
        # Preparar respuesta
        data = {
            'task_id': task_id,
            'status': task_result.status,
        }
        
        # Si la tarea está completa, incluir el resultado
        if task_result.ready():
            if task_result.successful():
                result = task_result.result
                data['result'] = result
                
                # Formatear mensaje de éxito
                success_msg = "Datos procesados exitosamente. "
                
                if isinstance(result, dict):
                    if result.get('habilidades_added', 0) > 0:
                        success_msg += f"Habilidades añadidas: {result['habilidades_added']}. "
                    
                    if result.get('conocimientos_added', 0) > 0:
                        success_msg += f"Conocimientos añadidos: {result['conocimientos_added']}. "
                    
                    if result.get('estudios_added', 0) > 0:
                        success_msg += f"Estudios añadidos: {result['estudios_added']}. "
                    
                    if result.get('experiencia_added', 0) > 0:
                        success_msg += f"Experiencias añadidas: {result['experiencia_added']}. "
                    
                    if 'errors' in result and result['errors']:
                        data['warnings'] = result['errors']
                
                data['success_message'] = success_msg
            else:
                data['error'] = str(task_result.result)
        
        return JsonResponse(data)
    
    except Exception as e:
        logger.error(f"Error al verificar estado de tarea {task_id}: {str(e)}")
        return JsonResponse({
            'task_id': task_id,
            'status': 'ERROR',
            'error': str(e)
        }, status=500)

@login_required
def task_history_view(request):
    """
    Vista para ver el historial de tareas de Celery
    """
    # Obtener todas las tareas ordenadas por fecha de creación (más recientes primero)
    tasks = TaskResult.objects.all().order_by('-date_done')[:50]  # Limitar a las 50 más recientes
    
    return render(request, 'core/task_history.html', {
        'tasks': tasks,
        'title': 'Historial de Tareas'
    })

# Formularios para datos de proyecto
class ProyectoRolForm(forms.ModelForm):
    class Meta:
        model = ProyectoRoles
        fields = ['rol', 'habilidades', 'experiencia', 'conocimientos']
        widgets = {
            'habilidades': forms.TextInput(attrs={'placeholder': 'Ej: Python, Django, SQL'}),
            'experiencia': forms.TextInput(attrs={'placeholder': 'Ej: 3-5 años en desarrollo web'}),
            'conocimientos': forms.TextInput(attrs={'placeholder': 'Ej: Bases de datos, APIs REST'}),
        }

class ProyectoAliadoForm(forms.ModelForm):
    TIPO_ALIADO_CHOICES = [
        ('', 'Seleccione tipo de aliado'),
        ('Académico', 'Académico'),
        ('Empresarial', 'Empresarial'),
        ('Gubernamental', 'Gubernamental'),
        ('ONG', 'ONG'),
        ('Internacional', 'Internacional'),
        ('Otro', 'Otro'),
    ]
    
    tipo_aliado = forms.ChoiceField(choices=TIPO_ALIADO_CHOICES, required=True)
    
    class Meta:
        model = ProyectoAliados
        fields = ['entidad', 'tipo_aliado', 'responsabilidades']
        widgets = {
            'responsabilidades': forms.Textarea(attrs={'rows': 3}),
        }

class ProyectoProductoForm(forms.ModelForm):
    TIPO_PRODUCTO_CHOICES = [
        ('', 'Seleccione tipo de producto'),
        ('Software', 'Software'),
        ('Hardware', 'Hardware'),
        ('Documento', 'Documento'),
        ('Servicio', 'Servicio'),
        ('Capacitación', 'Capacitación'),
        ('Otro', 'Otro'),
    ]
    
    tipo = forms.ChoiceField(choices=TIPO_PRODUCTO_CHOICES, required=True)
    
    class Meta:
        model = ProyectoProductos
        fields = ['producto', 'tipo', 'cantidad']
        widgets = {
            'cantidad': forms.NumberInput(attrs={'min': 1}),
        }

# Vistas para Roles de Proyecto
class ProyectoRolCreateView(LoginRequiredMixin, CreateView):
    model = ProyectoRoles
    form_class = ProyectoRolForm
    template_name = 'core/proyecto_rol_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['proyecto'] = get_object_or_404(Proyecto, pk=self.kwargs['pk'])
        return context
    
    def form_valid(self, form):
        form.instance.project_id = get_object_or_404(Proyecto, pk=self.kwargs['pk'])
        messages.success(self.request, 'Rol agregado exitosamente.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('proyecto_detail', kwargs={'pk': self.kwargs['pk']})

class ProyectoRolUpdateView(LoginRequiredMixin, UpdateView):
    model = ProyectoRoles
    form_class = ProyectoRolForm
    template_name = 'core/proyecto_rol_form.html'
    pk_url_kwarg = 'rol_pk'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['proyecto'] = self.object.project_id
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Rol actualizado exitosamente.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('proyecto_detail', kwargs={'pk': self.object.project_id.id})

class ProyectoRolDeleteView(LoginRequiredMixin, DeleteView):
    model = ProyectoRoles
    template_name = 'core/proyecto_rol_confirm_delete.html'
    pk_url_kwarg = 'rol_pk'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['proyecto'] = self.object.project_id
        return context
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Rol eliminado exitosamente.')
        return super().delete(request, *args, **kwargs)
    
    def get_success_url(self):
        return reverse_lazy('proyecto_detail', kwargs={'pk': self.object.project_id.id})

# Vistas para Aliados de Proyecto
class ProyectoAliadoCreateView(LoginRequiredMixin, CreateView):
    model = ProyectoAliados
    form_class = ProyectoAliadoForm
    template_name = 'core/proyecto_aliado_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['proyecto'] = get_object_or_404(Proyecto, pk=self.kwargs['pk'])
        return context
    
    def form_valid(self, form):
        form.instance.project_id = get_object_or_404(Proyecto, pk=self.kwargs['pk'])
        messages.success(self.request, 'Aliado agregado exitosamente.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('proyecto_detail', kwargs={'pk': self.kwargs['pk']})

class ProyectoAliadoUpdateView(LoginRequiredMixin, UpdateView):
    model = ProyectoAliados
    form_class = ProyectoAliadoForm
    template_name = 'core/proyecto_aliado_form.html'
    pk_url_kwarg = 'aliado_pk'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['proyecto'] = self.object.project_id
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Aliado actualizado exitosamente.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('proyecto_detail', kwargs={'pk': self.object.project_id.id})

class ProyectoAliadoDeleteView(LoginRequiredMixin, DeleteView):
    model = ProyectoAliados
    template_name = 'core/proyecto_aliado_confirm_delete.html'
    pk_url_kwarg = 'aliado_pk'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['proyecto'] = self.object.project_id
        return context
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Aliado eliminado exitosamente.')
        return super().delete(request, *args, **kwargs)
    
    def get_success_url(self):
        return reverse_lazy('proyecto_detail', kwargs={'pk': self.object.project_id.id})

# Vistas para Productos de Proyecto
class ProyectoProductoCreateView(LoginRequiredMixin, CreateView):
    model = ProyectoProductos
    form_class = ProyectoProductoForm
    template_name = 'core/proyecto_producto_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['proyecto'] = get_object_or_404(Proyecto, pk=self.kwargs['pk'])
        return context
    
    def form_valid(self, form):
        form.instance.project_id = get_object_or_404(Proyecto, pk=self.kwargs['pk'])
        messages.success(self.request, 'Producto agregado exitosamente.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('proyecto_detail', kwargs={'pk': self.kwargs['pk']})

class ProyectoProductoUpdateView(LoginRequiredMixin, UpdateView):
    model = ProyectoProductos
    form_class = ProyectoProductoForm
    template_name = 'core/proyecto_producto_form.html'
    pk_url_kwarg = 'producto_pk'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['proyecto'] = self.object.project_id
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Producto actualizado exitosamente.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('proyecto_detail', kwargs={'pk': self.object.project_id.id})

class ProyectoProductoDeleteView(LoginRequiredMixin, DeleteView):
    model = ProyectoProductos
    template_name = 'core/proyecto_producto_confirm_delete.html'
    pk_url_kwarg = 'producto_pk'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['proyecto'] = self.object.project_id
        return context
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Producto eliminado exitosamente.')
        return super().delete(request, *args, **kwargs)
    
    def get_success_url(self):
        return reverse_lazy('proyecto_detail', kwargs={'pk': self.object.project_id.id})

@login_required
def add_proyecto_rol(request, proyecto_id):
    """
    Vista para añadir un rol a un proyecto
    """
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)
    
    if request.method == 'POST':
        try:
            rol = request.POST.get('rol', '').strip()
            habilidades = request.POST.get('habilidades', '').strip()
            experiencia = request.POST.get('experiencia', '').strip()
            conocimientos = request.POST.get('conocimientos', '').strip()
            
            if not rol:
                messages.error(request, "El rol no puede estar vacío.")
                return redirect('proyecto_detail', pk=proyecto_id)
            
            # Verificar si ya existe
            existing = ProyectoRoles.objects.filter(
                project_id=proyecto,
                rol__iexact=rol
            ).first()
            
            if existing:
                messages.warning(request, f"El rol '{rol}' ya existe para este proyecto.")
            else:
                ProyectoRoles.objects.create(
                    project_id=proyecto,
                    rol=rol,
                    habilidades=habilidades,
                    experiencia=experiencia,
                    conocimientos=conocimientos
                )
                messages.success(request, f"Rol '{rol}' añadido exitosamente.")
        
        except Exception as e:
            logger.error(f"Error al añadir rol: {str(e)}")
            messages.error(request, f"Error al añadir rol: {str(e)}")
        
        return redirect('proyecto_detail', pk=proyecto_id)
    
    # Si es una solicitud GET, mostrar el formulario
    context = {
        'proyecto': proyecto,
        'form': ProyectoRolForm()
    }
    return render(request, 'core/proyecto_rol_form.html', context)

@login_required
def add_proyecto_aliado(request, proyecto_id):
    """
    Vista para añadir un aliado a un proyecto
    """
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)
    
    if request.method == 'POST':
        try:
            entidad = request.POST.get('entidad', '').strip()
            tipo_aliado = request.POST.get('tipo_aliado', '').strip()
            responsabilidades = request.POST.get('responsabilidades', '').strip()
            
            if not entidad:
                messages.error(request, "La entidad no puede estar vacía.")
                return redirect('proyecto_detail', pk=proyecto_id)
            
            # Verificar si ya existe
            existing = ProyectoAliados.objects.filter(
                project_id=proyecto,
                entidad__iexact=entidad
            ).first()
            
            if existing:
                messages.warning(request, f"El aliado '{entidad}' ya existe para este proyecto.")
            else:
                ProyectoAliados.objects.create(
                    project_id=proyecto,
                    entidad=entidad,
                    tipo_aliado=tipo_aliado,
                    responsabilidades=responsabilidades
                )
                messages.success(request, f"Aliado '{entidad}' añadido exitosamente.")
        
        except Exception as e:
            logger.error(f"Error al añadir aliado: {str(e)}")
            messages.error(request, f"Error al añadir aliado: {str(e)}")
        
        return redirect('proyecto_detail', pk=proyecto_id)
    
    # Si es una solicitud GET, mostrar el formulario
    context = {
        'proyecto': proyecto,
        'form': ProyectoAliadoForm()
    }
    return render(request, 'core/proyecto_aliado_form.html', context)

@login_required
def add_proyecto_producto(request, proyecto_id):
    """
    Vista para añadir un producto a un proyecto
    """
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)
    
    if request.method == 'POST':
        try:
            producto = request.POST.get('producto', '').strip()
            tipo = request.POST.get('tipo', '').strip()
            cantidad = request.POST.get('cantidad', '').strip()
            
            if not producto:
                messages.error(request, "El producto no puede estar vacío.")
                return redirect('proyecto_detail', pk=proyecto_id)
            
            # Verificar si ya existe
            existing = ProyectoProductos.objects.filter(
                project_id=proyecto,
                producto__iexact=producto,
                tipo=tipo
            ).first()
            
            if existing:
                messages.warning(request, f"El producto '{producto}' ya existe para este proyecto.")
            else:
                ProyectoProductos.objects.create(
                    project_id=proyecto,
                    producto=producto,
                    tipo=tipo,
                    cantidad=cantidad
                )
                messages.success(request, f"Producto '{producto}' añadido exitosamente.")
        
        except Exception as e:
            logger.error(f"Error al añadir producto: {str(e)}")
            messages.error(request, f"Error al añadir producto: {str(e)}")
        
        return redirect('proyecto_detail', pk=proyecto_id)
    
    # Si es una solicitud GET, mostrar el formulario
    context = {
        'proyecto': proyecto,
        'form': ProyectoProductoForm()
    }
    return render(request, 'core/proyecto_producto_form.html', context)

@login_required
def delete_proyecto_rol(request, pk):
    """
    Vista para eliminar un rol de un proyecto
    """
    try:
        rol = get_object_or_404(ProyectoRoles, id=pk)
        proyecto_id = rol.project_id.id
        rol_nombre = rol.rol
        rol.delete()
        messages.success(request, f"Rol '{rol_nombre}' eliminado exitosamente.")
    except Exception as e:
        logger.error(f"Error al eliminar rol: {str(e)}")
        messages.error(request, f"Error al eliminar rol: {str(e)}")
        proyecto_id = request.GET.get('proyecto_id')
    
    return redirect('proyecto_detail', pk=proyecto_id)

@login_required
def delete_proyecto_aliado(request, pk):
    """
    Vista para eliminar un aliado de un proyecto
    """
    try:
        aliado = get_object_or_404(ProyectoAliados, id=pk)
        proyecto_id = aliado.project_id.id
        aliado_nombre = aliado.entidad
        aliado.delete()
        messages.success(request, f"Aliado '{aliado_nombre}' eliminado exitosamente.")
    except Exception as e:
        logger.error(f"Error al eliminar aliado: {str(e)}")
        messages.error(request, f"Error al eliminar aliado: {str(e)}")
        proyecto_id = request.GET.get('proyecto_id')
    
    return redirect('proyecto_detail', pk=proyecto_id)

@login_required
def delete_proyecto_producto(request, pk):
    """
    Vista para eliminar un producto de un proyecto
    """
    try:
        producto = get_object_or_404(ProyectoProductos, id=pk)
        proyecto_id = producto.project_id.id
        producto_nombre = producto.producto
        producto.delete()
        messages.success(request, f"Producto '{producto_nombre}' eliminado exitosamente.")
    except Exception as e:
        logger.error(f"Error al eliminar producto: {str(e)}")
        messages.error(request, f"Error al eliminar producto: {str(e)}")
        proyecto_id = request.GET.get('proyecto_id')
    
    return redirect('proyecto_detail', pk=proyecto_id)

@login_required
def generar_recomendaciones(request, proyecto_id):
    """
    Vista para generar recomendaciones de usuarios para un proyecto
    """
    try:
        # Obtener el proyecto
        proyecto = get_object_or_404(Proyecto, id=proyecto_id)
        
        # Obtener todos los usuarios
        usuarios = Usuario.objects.all()
        
        # Obtener roles del proyecto
        roles_proyecto = ProyectoRoles.objects.filter(project_id=proyecto)
        
        # Inicializar sistema de recomendación
        recommender = RecommendationSystem()
        
        # Preparar datos
        X, user_ids = recommender.prepare_data(usuarios, roles_proyecto)
        
        # Entrenar modelos y obtener métricas
        rf_scores, knn_scores, nn_scores = recommender.train_models(X, user_ids)
        
        # Obtener recomendaciones (ahora 10 candidatos)
        recommendations = recommender.get_recommendations(X, user_ids, top_n=10)
        
        # Guardar resultados en la base de datos
        recomendacion = RecomendacionProyecto.objects.create(
            project_id=proyecto,
            rf_accuracy=rf_scores['accuracy'],
            rf_precision=rf_scores['precision'],
            rf_recall=rf_scores['recall'],
            rf_f1=rf_scores['f1'],
            knn_accuracy=knn_scores['accuracy'],
            knn_precision=knn_scores['precision'],
            knn_recall=knn_scores['recall'],
            knn_f1=knn_scores['f1'],
            nn_accuracy = nn_scores['accuracy'],
            nn_precision = nn_scores['precision'],
            nn_recall = nn_scores['recall'],
            nn_f1 = nn_scores['f1']
        )
        
        # Guardar recomendaciones de usuarios
        for idx, rec in enumerate(recommendations, 1):
            usuario = Usuario.objects.get(id=rec['user_id'])
            RecomendacionUsuario.objects.create(
                recomendacion_id=recomendacion,
                user_id=usuario,
                score_combinado=rec['score'],
                score_rf=rec['rf_score'],
                score_knn=rec['knn_score'],
                score_nn=rec['nn_score'],
                ranking=idx
            )
        
        messages.success(request, "Recomendaciones generadas exitosamente.")
        return redirect('ver_recomendaciones', recomendacion_id=recomendacion.id)
    
    except Exception as e:
        logger.error(f"Error generando recomendaciones: {str(e)}")
        messages.error(request, f"Error generando recomendaciones: {str(e)}")
        return redirect('proyecto_detail', pk=proyecto_id)

class RecomendacionDetailView(LoginRequiredMixin, DetailView):
    model = RecomendacionProyecto
    template_name = 'core/recomendacion_detail.html'
    context_object_name = 'recomendacion'
    pk_url_kwarg = 'recomendacion_id'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['usuarios_recomendados'] = self.object.usuarios_recomendados.all()
        
        # Agregar información específica de la red neuronal
        context['model_weights'] = {
            'rf': 0.0,
            'knn': 0.0,
            'nn': 1.0
        }
        context['active_model'] = 'Red Neuronal'
        context['model_description'] = 'Sistema de recomendación basado únicamente en Red Neuronal (MLP)'
        
        return context

def crear_usuario(request):
    if request.method == 'POST':
        form = UsuarioForm(request.POST)
        habilidad_formset = HabilidadFormSet(request.POST, prefix='habilidades')
        conocimiento_formset = ConocimientoFormSet(request.POST, prefix='conocimientos')
        estudio_formset = EstudioFormSet(request.POST, prefix='estudios')
        experiencia_formset = ExperienciaFormSet(request.POST, prefix='experiencias')

        if form.is_valid() and all([
            habilidad_formset.is_valid(),
            conocimiento_formset.is_valid(),
            estudio_formset.is_valid(),
            experiencia_formset.is_valid()
        ]):
            usuario = form.save()
            
            # Guardar los formsets
            habilidad_formset.instance = usuario
            conocimiento_formset.instance = usuario
            estudio_formset.instance = usuario
            experiencia_formset.instance = usuario
            
            habilidad_formset.save()
            conocimiento_formset.save()
            estudio_formset.save()
            experiencia_formset.save()

            messages.success(request, 'Usuario creado exitosamente.')
            return redirect('usuario_detail', pk=usuario.pk)
    else:
        form = UsuarioForm()
        habilidad_formset = HabilidadFormSet(prefix='habilidades')
        conocimiento_formset = ConocimientoFormSet(prefix='conocimientos')
        estudio_formset = EstudioFormSet(prefix='estudios')
        experiencia_formset = ExperienciaFormSet(prefix='experiencias')

    context = {
        'form': form,
        'habilidad_formset': habilidad_formset,
        'conocimiento_formset': conocimiento_formset,
        'estudio_formset': estudio_formset,
        'experiencia_formset': experiencia_formset,
    }
    return render(request, 'core/crear_usuario.html', context)

@login_required
def generar_recomendaciones_avanzadas(request, proyecto_id):
    """
    Vista para generar recomendaciones avanzadas de usuarios para un proyecto
    """
    try:
        proyecto = get_object_or_404(Proyecto, id=proyecto_id)
        usuarios = Usuario.objects.all()
        roles_proyecto = ProyectoRoles.objects.filter(project_id=proyecto)
        recommender = AdvancedRecommendationSystem()
        X, user_ids = recommender.prepare_advanced_data(usuarios, roles_proyecto)
        recommender.train_advanced_models(X, user_ids)
        adv_scores = recommender.get_advanced_performance_summary()
        recommendations = recommender.get_advanced_recommendations(X, user_ids, top_n=10)
        # Guardar resultados en la base de datos (puedes crear un nuevo objeto o reutilizar el modelo existente)
        recomendacion = RecomendacionProyecto.objects.create(
            project_id=proyecto,
            rf_accuracy=0,
            rf_precision=0,
            rf_recall=0,
            rf_f1=0,
            knn_accuracy=0,
            knn_precision=0,
            knn_recall=0,
            knn_f1=0,
            nn_accuracy=adv_scores.get('accuracy', 0),
            nn_precision=adv_scores.get('precision', 0),
            nn_recall=adv_scores.get('recall', 0),
            nn_f1=adv_scores.get('f1', 0)
        )
        for idx, rec in enumerate(recommendations, 1):
            usuario = Usuario.objects.get(id=rec['user_id'])
            RecomendacionUsuario.objects.create(
                recomendacion_id=recomendacion,
                user_id=usuario,
                score_combinado=rec['score'],
                score_rf=0,
                score_knn=0,
                score_nn=rec['score'],
                ranking=idx
            )
        messages.success(request, "Recomendación avanzada generada exitosamente.")
        return redirect('ver_recomendaciones_avanzadas', recomendacion_id=recomendacion.id)
    except Exception as e:
        logger.error(f"Error generando recomendación avanzada: {str(e)}")
        messages.error(request, f"Error generando recomendación avanzada: {str(e)}")
        return redirect('proyecto_detail', pk=proyecto_id)

class RecomendacionAvanzadaDetailView(LoginRequiredMixin, DetailView):
    model = RecomendacionProyecto
    template_name = 'core/recomendacion_avanzada_detail.html'
    context_object_name = 'recomendacion'
    pk_url_kwarg = 'recomendacion_id'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        usuarios_recomendados = self.object.usuarios_recomendados.all()
        # Agregar score_avanzado a cada usuario recomendado
        for u in usuarios_recomendados:
            u.score_avanzado = u.score_nn
        context['usuarios_recomendados'] = usuarios_recomendados
        # Para compatibilidad con el template avanzado
        context['advanced_accuracy'] = self.object.nn_accuracy
        context['advanced_precision'] = self.object.nn_precision
        context['advanced_recall'] = self.object.nn_recall
        context['advanced_f1'] = self.object.nn_f1
        return context

@login_required
def generar_recomendaciones_cnn(request, proyecto_id):
    """
    Vista para generar recomendaciones de usuarios usando CNN para un proyecto
    """
    try:
        proyecto = get_object_or_404(Proyecto, id=proyecto_id)
        usuarios = Usuario.objects.all()
        roles_proyecto = ProyectoRoles.objects.filter(project_id=proyecto)
        recommender = AdvancedRecommendationSystem()
        X, user_ids = recommender.prepare_advanced_data(usuarios, roles_proyecto)
        recommendations = recommender.get_cnn_recommendations(X, user_ids, top_n=10)
        # Guardar resultados en la base de datos
        recomendacion = RecomendacionProyecto.objects.create(
            project_id=proyecto,
            rf_accuracy=0,
            rf_precision=0,
            rf_recall=0,
            rf_f1=0,
            knn_accuracy=0,
            knn_precision=0,
            knn_recall=0,
            knn_f1=0,
            nn_accuracy=0,
            nn_precision=0,
            nn_recall=0,
            nn_f1=0
        )
        for idx, rec in enumerate(recommendations, 1):
            usuario = Usuario.objects.get(id=rec['user_id'])
            RecomendacionUsuario.objects.create(
                recomendacion_id=recomendacion,
                user_id=usuario,
                score_combinado=rec['score'],
                score_rf=0,
                score_knn=0,
                score_nn=rec['cnn_score'],
                ranking=idx
            )
        messages.success(request, "Recomendación CNN generada exitosamente.")
        return redirect('ver_recomendaciones_cnn', recomendacion_id=recomendacion.id)
    except Exception as e:
        logger.error(f"Error generando recomendación CNN: {str(e)}")
        messages.error(request, f"Error generando recomendación CNN: {str(e)}")
        return redirect('proyecto_detail', pk=proyecto_id)

class RecomendacionCNNDetailView(LoginRequiredMixin, DetailView):
    model = RecomendacionProyecto
    template_name = 'core/recomendacion_cnn_detail.html'
    context_object_name = 'recomendacion'
    pk_url_kwarg = 'recomendacion_id'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        usuarios_recomendados = self.object.usuarios_recomendados.all()
        for u in usuarios_recomendados:
            u.score_cnn = u.score_nn
        context['usuarios_recomendados'] = usuarios_recomendados
        return context

@login_required
def exportar_recomendaciones_pdf(request, recomendacion_id):
    """
    Vista para exportar recomendaciones a PDF
    """
    try:
        recomendacion = get_object_or_404(RecomendacionProyecto, id=recomendacion_id)
        usuarios_recomendados = recomendacion.usuarios_recomendados.all()
        
        # Crear el PDF
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="recomendaciones_{recomendacion.project_id.nombre}_{recomendacion.fecha_recomendacion.strftime("%Y%m%d")}.pdf"'
        
        # Crear el documento
        doc = SimpleDocTemplate(response, pagesize=A4)
        elements = []
        
        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=TA_CENTER
        )
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=20
        )
        normal_style = styles['Normal']
        
        # Título
        elements.append(Paragraph("Sistema de Recomendación REDUDES", title_style))
        elements.append(Spacer(1, 20))
        
        # Información del proyecto
        elements.append(Paragraph(f"<b>Proyecto:</b> {recomendacion.project_id.nombre}", subtitle_style))
        elements.append(Paragraph(f"<b>Fecha de Recomendación:</b> {recomendacion.fecha_recomendacion.strftime('%d/%m/%Y %H:%M')}", normal_style))
        elements.append(Paragraph(f"<b>Convocatoria:</b> {recomendacion.project_id.convocatoria}", normal_style))
        elements.append(Paragraph(f"<b>Tipo de Proyecto:</b> {recomendacion.project_id.tipo_proyecto}", normal_style))
        elements.append(Spacer(1, 20))
        
        # Métricas del modelo
        elements.append(Paragraph("Métricas del Modelo", subtitle_style))
        metrics_data = [
            ['Métrica', 'Valor'],
            ['Accuracy', f"{recomendacion.nn_accuracy:.4f}"],
            ['Precision', f"{recomendacion.nn_precision:.4f}"],
            ['Recall', f"{recomendacion.nn_recall:.4f}"],
            ['F1-Score', f"{recomendacion.nn_f1:.4f}"]
        ]
        metrics_table = Table(metrics_data, colWidths=[2*inch, 1.5*inch])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(metrics_table)
        elements.append(Spacer(1, 20))
        
        # Tabla de usuarios recomendados
        if usuarios_recomendados:
            elements.append(Paragraph("Perfiles Recomendados", subtitle_style))
            
            # Datos de la tabla
            table_data = [['#', 'Usuario', 'Email', 'Score', 'Confianza']]
            
            for rec in usuarios_recomendados:
                # Determinar nivel de confianza
                score = rec.score_nn
                if score > 0.7:
                    confianza = "Alta"
                elif score > 0.5:
                    confianza = "Media"
                else:
                    confianza = "Baja"
                
                table_data.append([
                    str(rec.ranking),
                    f"{rec.user_id.nombres} {rec.user_id.apellidos}",
                    rec.user_id.email,
                    f"{score:.4f}",
                    confianza
                ])
            
            # Crear tabla
            table = Table(table_data, colWidths=[0.5*inch, 2*inch, 2.5*inch, 1*inch, 1*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('ALIGN', (0, 0), (0, -1), 'CENTER'),  # Centrar columna #
                ('ALIGN', (3, 1), (3, -1), 'CENTER'),  # Centrar columna Score
                ('ALIGN', (4, 1), (4, -1), 'CENTER'),  # Centrar columna Confianza
            ]))
            elements.append(table)
            
            # Estadísticas
            elements.append(Spacer(1, 20))
            elements.append(Paragraph("Estadísticas de Recomendaciones", subtitle_style))
            
            alta_confianza = len([u for u in usuarios_recomendados if u.score_nn > 0.7])
            media_confianza = len([u for u in usuarios_recomendados if 0.5 <= u.score_nn <= 0.7])
            baja_confianza = len([u for u in usuarios_recomendados if u.score_nn < 0.5])
            
            stats_data = [
                ['Nivel de Confianza', 'Cantidad'],
                ['Alta (≥0.7)', str(alta_confianza)],
                ['Media (0.5-0.7)', str(media_confianza)],
                ['Baja (<0.5)', str(baja_confianza)],
                ['Total', str(len(usuarios_recomendados))]
            ]
            
            stats_table = Table(stats_data, colWidths=[2*inch, 1*inch])
            stats_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.green),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgreen),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(stats_table)
        else:
            elements.append(Paragraph("No hay recomendaciones disponibles", normal_style))
        
        # Construir PDF
        doc.build(elements)
        return response
        
    except Exception as e:
        logger.error(f"Error exportando PDF: {str(e)}")
        messages.error(request, f"Error exportando PDF: {str(e)}")
        return redirect('ver_recomendaciones', recomendacion_id=recomendacion_id)

@login_required
def informes_plataforma(request):
    """
    Vista para mostrar informes de uso de la plataforma
    """
    try:
        # Estadísticas generales
        total_proyectos = Proyecto.objects.count()
        total_usuarios = Usuario.objects.count()
        total_recomendaciones = RecomendacionProyecto.objects.count()
        
        # Proyectos por tipo
        proyectos_por_tipo = Proyecto.objects.values('tipo_proyecto').annotate(
            cantidad=Count('id')
        ).order_by('-cantidad')
        
        # Proyectos por convocatoria
        proyectos_por_convocatoria = Proyecto.objects.values('convocatoria').annotate(
            cantidad=Count('id')
        ).order_by('-cantidad')[:10]
        
        # Usuarios con más habilidades
        usuarios_mas_habilidades = Usuario.objects.annotate(
            num_habilidades=Count('habilidades')
        ).order_by('-num_habilidades')[:10]
        
        # Usuarios con más conocimientos
        usuarios_mas_conocimientos = Usuario.objects.annotate(
            num_conocimientos=Count('conocimientos')
        ).order_by('-num_conocimientos')[:10]
        
        # Recomendaciones por mes (últimos 6 meses)
        fecha_limite = timezone.now() - timedelta(days=180)
        recomendaciones_por_mes = RecomendacionProyecto.objects.filter(
            fecha_recomendacion__gte=fecha_limite
        ).extra(
            select={'mes': "DATE_TRUNC('month', fecha_recomendacion)"}
        ).values('mes').annotate(
            cantidad=Count('id')
        ).order_by('mes')
        
        # Proyectos más activos (con más roles)
        proyectos_mas_activos = Proyecto.objects.annotate(
            num_roles=Count('proyectoroles')
        ).order_by('-num_roles')[:10]
        
        # Estadísticas de usuarios recomendados
        total_usuarios_recomendados = RecomendacionUsuario.objects.count()
        if total_usuarios_recomendados > 0:
            promedio_score = RecomendacionUsuario.objects.aggregate(
                promedio=Avg('score_combinado')
            )['promedio']
        else:
            promedio_score = 0
        
        # Usuarios más recomendados
        usuarios_mas_recomendados = Usuario.objects.annotate(
            veces_recomendado=Count('recomendacionusuario')
        ).filter(veces_recomendado__gt=0).order_by('-veces_recomendado')[:10]
        
        context = {
            'total_proyectos': total_proyectos,
            'total_usuarios': total_usuarios,
            'total_recomendaciones': total_recomendaciones,
            'total_usuarios_recomendados': total_usuarios_recomendados,
            'promedio_score': promedio_score,
            'proyectos_por_tipo': proyectos_por_tipo,
            'proyectos_por_convocatoria': proyectos_por_convocatoria,
            'usuarios_mas_habilidades': usuarios_mas_habilidades,
            'usuarios_mas_conocimientos': usuarios_mas_conocimientos,
            'recomendaciones_por_mes': recomendaciones_por_mes,
            'proyectos_mas_activos': proyectos_mas_activos,
            'usuarios_mas_recomendados': usuarios_mas_recomendados,
        }
        
        return render(request, 'core/informes_plataforma.html', context)
        
    except Exception as e:
        logger.error(f"Error generando informes: {str(e)}")
        messages.error(request, f"Error generando informes: {str(e)}")
        return redirect('home')

@login_required
def informes_recomendaciones(request):
    """
    Vista para mostrar informes específicos de recomendaciones
    """
    try:
        # Consulta básica para verificar que funciona
        todas_recomendaciones = RecomendacionProyecto.objects.select_related('project_id').order_by('-fecha_recomendacion')
        
        # Estadísticas por proyecto - simplificada
        recomendaciones_por_proyecto = RecomendacionProyecto.objects.values(
            'project_id__nombre'
        ).annotate(
            cantidad=Count('id')
        ).order_by('-cantidad')
        
        # Distribución de scores - simplificada
        scores_distribucion = {
            'alta_confianza': RecomendacionUsuario.objects.filter(score_combinado__gt=0.7).count(),
            'media_confianza': RecomendacionUsuario.objects.filter(
                score_combinado__gt=0.5, 
                score_combinado__lte=0.7
            ).count(),
            'baja_confianza': RecomendacionUsuario.objects.filter(score_combinado__lte=0.5).count(),
        }
        
        # Recomendaciones recientes - simplificada
        fecha_reciente = timezone.now() - timedelta(days=30)
        recomendaciones_recientes = RecomendacionProyecto.objects.filter(
            fecha_recomendacion__gte=fecha_reciente
        ).select_related('project_id').order_by('-fecha_recomendacion')
        
        # Top usuarios por score - simplificada
        top_usuarios_score = RecomendacionUsuario.objects.select_related('user_id').order_by('-score_combinado')[:20]
        
        # Proyectos sin recomendaciones - simplificada
        proyectos_sin_recomendaciones = Proyecto.objects.filter(
            ~Q(recomendacionproyecto__isnull=False)
        )
        
        context = {
            'todas_recomendaciones': todas_recomendaciones,
            'recomendaciones_por_proyecto': recomendaciones_por_proyecto,
            'proyectos_mejores_scores': [],  # Simplificado por ahora
            'scores_distribucion': scores_distribucion,
            'recomendaciones_recientes': recomendaciones_recientes,
            'top_usuarios_score': top_usuarios_score,
            'proyectos_sin_recomendaciones': proyectos_sin_recomendaciones,
        }
        
        return render(request, 'core/informes_recomendaciones.html', context)
        
    except Exception as e:
        logger.error(f"Error generando informes de recomendaciones: {str(e)}")
        messages.error(request, f"Error generando informes de recomendaciones: {str(e)}")
        return redirect('home')

@login_required
def exportar_informe_plataforma_pdf(request):
    """
    Vista para exportar informe de plataforma a PDF
    """
    try:
        # Obtener datos para el informe
        total_proyectos = Proyecto.objects.count()
        total_usuarios = Usuario.objects.count()
        total_recomendaciones = RecomendacionProyecto.objects.count()
        
        proyectos_por_tipo = Proyecto.objects.values('tipo_proyecto').annotate(
            cantidad=Count('id')
        ).order_by('-cantidad')
        
        recomendaciones_por_mes = RecomendacionProyecto.objects.filter(
            fecha_recomendacion__gte=timezone.now() - timedelta(days=180)
        ).extra(
            select={'mes': "DATE_TRUNC('month', fecha_recomendacion)"}
        ).values('mes').annotate(
            cantidad=Count('id')
        ).order_by('mes')
        
        # Crear PDF
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="informe_plataforma_{timezone.now().strftime("%Y%m%d")}.pdf"'
        
        doc = SimpleDocTemplate(response, pagesize=A4)
        elements = []
        
        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER
        )
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=20
        )
        
        # Título
        elements.append(Paragraph("Informe de Uso de la Plataforma REDUDES", title_style))
        elements.append(Spacer(1, 20))
        
        # Estadísticas generales
        elements.append(Paragraph("Estadísticas Generales", subtitle_style))
        stats_data = [
            ['Métrica', 'Cantidad'],
            ['Total Proyectos', str(total_proyectos)],
            ['Total Usuarios', str(total_usuarios)],
            ['Total Recomendaciones', str(total_recomendaciones)]
        ]
        
        stats_table = Table(stats_data, colWidths=[3*inch, 1.5*inch])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(stats_table)
        elements.append(Spacer(1, 20))
        
        # Proyectos por tipo
        if proyectos_por_tipo:
            elements.append(Paragraph("Proyectos por Tipo", subtitle_style))
            tipo_data = [['Tipo de Proyecto', 'Cantidad']]
            for item in proyectos_por_tipo:
                tipo_data.append([item['tipo_proyecto'], str(item['cantidad'])])
            
            tipo_table = Table(tipo_data, colWidths=[3*inch, 1.5*inch])
            tipo_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.green),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgreen),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(tipo_table)
            elements.append(Spacer(1, 20))
        
        # Recomendaciones por mes
        if recomendaciones_por_mes:
            elements.append(Paragraph("Recomendaciones por Mes (Últimos 6 meses)", subtitle_style))
            mes_data = [['Mes', 'Cantidad de Recomendaciones']]
            for item in recomendaciones_por_mes:
                mes_str = item['mes'].strftime('%B %Y') if item['mes'] else 'N/A'
                mes_data.append([mes_str, str(item['cantidad'])])
            
            mes_table = Table(mes_data, colWidths=[3*inch, 1.5*inch])
            mes_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.orange),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightyellow),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(mes_table)
        
        # Construir PDF
        doc.build(elements)
        return response
        
    except Exception as e:
        logger.error(f"Error exportando informe PDF: {str(e)}")
        messages.error(request, f"Error exportando informe PDF: {str(e)}")
        return redirect('informes_plataforma')
