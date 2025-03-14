from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, FormView
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from .models import (
    Proyecto, ProyectoRoles, ProyectoAliados, ProyectoProductos,
    Usuario, UsuarioHabilidades, UsuarioConocimiento, UsuarioEstudios, UsuarioExperiencia
)
from .data_services import process_user_data
from django import forms
import logging
import datetime

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

class UsuarioCreateView(LoginRequiredMixin, CreateView):
    model = Usuario
    template_name = 'core/usuario_form.html'
    fields = ['nombres', 'apellidos', 'email', 'telefono', 'cargo_actual', 
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
    fields = ['nombres', 'apellidos', 'email', 'telefono', 'cargo_actual', 
              'dependencia', 'url_cvlac', 'url_linkedin', 'fecha_ingreso']
    
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
