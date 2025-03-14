from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('proyectos/', views.ProyectoListView.as_view(), name='proyecto_list'),
    path('proyectos/nuevo/', views.ProyectoCreateView.as_view(), name='proyecto_create'),
    path('proyectos/<int:pk>/', views.ProyectoDetailView.as_view(), name='proyecto_detail'),
    path('proyectos/<int:pk>/editar/', views.ProyectoUpdateView.as_view(), name='proyecto_update'),
    path('proyectos/<int:pk>/eliminar/', views.ProyectoDeleteView.as_view(), name='proyecto_delete'),
    
    # URLs para Usuarios
    path('usuarios/', views.UsuarioListView.as_view(), name='usuario_list'),
    path('usuarios/nuevo/', views.UsuarioCreateView.as_view(), name='usuario_create'),
    path('usuarios/<int:pk>/', views.UsuarioDetailView.as_view(), name='usuario_detail'),
    path('usuarios/<int:pk>/editar/', views.UsuarioUpdateView.as_view(), name='usuario_update'),
    path('usuarios/<int:pk>/eliminar/', views.UsuarioDeleteView.as_view(), name='usuario_delete'),
    
    # URLs para procesamiento de datos
    path('usuarios/<int:pk>/procesar-datos/', views.process_user_data_view, name='process_user_data'),
    
    # URLs para gestión de habilidades
    path('usuarios/<int:user_id>/habilidades/agregar/', views.add_user_skill, name='add_user_skill'),
    path('habilidades/<int:pk>/eliminar/', views.delete_user_skill, name='delete_user_skill'),
    
    # URLs para gestión de conocimientos
    path('usuarios/<int:user_id>/conocimientos/agregar/', views.add_user_knowledge, name='add_user_knowledge'),
    path('conocimientos/<int:pk>/eliminar/', views.delete_user_knowledge, name='delete_user_knowledge'),
    
    # URLs para gestión de estudios
    path('usuarios/<int:user_id>/estudios/agregar/', views.add_user_study, name='add_user_study'),
    path('estudios/<int:pk>/eliminar/', views.delete_user_study, name='delete_user_study'),
    
    # URLs para gestión de experiencia
    path('usuarios/<int:user_id>/experiencia/agregar/', views.add_user_experience, name='add_user_experience'),
    path('experiencia/<int:pk>/eliminar/', views.delete_user_experience, name='delete_user_experience'),
    
    # Autenticación
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login', template_name='core/logout.html'), name='logout'),
] 