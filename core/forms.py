from django import forms
from .models import Usuario, UsuarioHabilidades, UsuarioConocimiento, UsuarioEstudios, UsuarioExperiencia

class UsuarioForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = [
            'nombres', 'apellidos', 'email', 'telefono',
            'puesto_actual', 'dependencia', 'url_cvlac',
            'url_linkedin', 'fecha_ingreso'
        ]
        widgets = {
            'fecha_ingreso': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'url_cvlac': forms.URLInput(attrs={'placeholder': 'https://scienti.minciencias.gov.co/cvlac/...'}),
            'url_linkedin': forms.URLInput(attrs={'placeholder': 'https://www.linkedin.com/in/...'}),
        }

class HabilidadForm(forms.ModelForm):
    class Meta:
        model = UsuarioHabilidades
        fields = ['habilidad', 'experiencia']
        widgets = {
            'experiencia': forms.Textarea(attrs={'rows': 3}),
        }

class ConocimientoForm(forms.ModelForm):
    class Meta:
        model = UsuarioConocimiento
        fields = ['conocimiento', 'nivel']
        widgets = {
            'nivel': forms.Select(choices=[
                (1, 'Básico'),
                (2, 'Intermedio Bajo'),
                (3, 'Intermedio'),
                (4, 'Intermedio Alto'),
                (5, 'Avanzado')
            ])
        }

class EstudioForm(forms.ModelForm):
    class Meta:
        model = UsuarioEstudios
        fields = ['estudio', 'nivel', 'year']
        widgets = {
            'nivel': forms.Select(choices=[
                (1, 'Técnico'),
                (2, 'Tecnólogo'),
                (3, 'Pregrado'),
                (4, 'Maestría'),
                (5, 'Doctorado')
            ]),
            'year': forms.NumberInput(attrs={'min': 1950, 'max': 2024})
        }

class ExperienciaForm(forms.ModelForm):
    class Meta:
        model = UsuarioExperiencia
        fields = ['rol', 'tiempo', 'actividades']
        widgets = {
            'tiempo': forms.NumberInput(attrs={'min': 0, 'max': 50}),
            'actividades': forms.Textarea(attrs={'rows': 3})
        }

# Formset para manejar múltiples habilidades, conocimientos, estudios y experiencias
HabilidadFormSet = forms.inlineformset_factory(
    Usuario, UsuarioHabilidades,
    form=HabilidadForm,
    extra=1,
    can_delete=True
)

ConocimientoFormSet = forms.inlineformset_factory(
    Usuario, UsuarioConocimiento,
    form=ConocimientoForm,
    extra=1,
    can_delete=True
)

EstudioFormSet = forms.inlineformset_factory(
    Usuario, UsuarioEstudios,
    form=EstudioForm,
    extra=1,
    can_delete=True
)

ExperienciaFormSet = forms.inlineformset_factory(
    Usuario, UsuarioExperiencia,
    form=ExperienciaForm,
    extra=1,
    can_delete=True
) 