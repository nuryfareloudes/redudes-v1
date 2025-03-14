from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    CustomUser, Proyecto, Usuario, ProyectoRoles, ProyectoAliados,
    ProyectoProductos, UsuarioHabilidades, UsuarioConocimiento,
    UsuarioEstudios, UsuarioExperiencia
)

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'email', 'is_admin', 'is_evaluator', 'is_researcher']
    fieldsets = UserAdmin.fieldsets + (
        ('Roles', {'fields': ('is_admin', 'is_evaluator', 'is_researcher')}),
    )

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Proyecto)
admin.site.register(Usuario)
admin.site.register(ProyectoRoles)
admin.site.register(ProyectoAliados)
admin.site.register(ProyectoProductos)
admin.site.register(UsuarioHabilidades)
admin.site.register(UsuarioConocimiento)
admin.site.register(UsuarioEstudios)
admin.site.register(UsuarioExperiencia)
