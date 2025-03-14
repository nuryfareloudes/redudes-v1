/**
 * REDUDES - Funciones JavaScript Globales
 */

// Función para mostrar el modal de carga
function showLoadingModal() {
    const loadingModal = document.getElementById('loadingModal');
    if (loadingModal) {
        loadingModal.style.display = 'flex';
    }
}

// Función para ocultar el modal de carga
function hideLoadingModal() {
    const loadingModal = document.getElementById('loadingModal');
    if (loadingModal) {
        loadingModal.style.display = 'none';
    }
}

// Función para validar formularios
function validateForm(formId, fieldsToValidate) {
    const form = document.getElementById(formId);
    if (!form) return true;
    
    let isValid = true;
    
    // Validar cada campo requerido
    fieldsToValidate.forEach(fieldId => {
        const field = document.getElementById(fieldId);
        if (!field) return;
        
        const value = field.value.trim();
        const errorElement = document.getElementById(`${fieldId}-error`);
        
        if (!value) {
            isValid = false;
            field.classList.add('is-invalid');
            if (errorElement) {
                errorElement.style.display = 'block';
            }
        } else {
            field.classList.remove('is-invalid');
            if (errorElement) {
                errorElement.style.display = 'none';
            }
        }
    });
    
    return isValid;
}

// Función para inicializar tooltips de Bootstrap
function initTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Función para inicializar popovers de Bootstrap
function initPopovers() {
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

// Función para formatear fechas
function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('es-ES', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
    });
}

// Función para confirmar eliminación
function confirmDelete(message, callback) {
    if (confirm(message || '¿Está seguro que desea eliminar este elemento?')) {
        if (typeof callback === 'function') {
            callback();
        }
        return true;
    }
    return false;
}

// Inicializar componentes cuando el DOM esté cargado
document.addEventListener('DOMContentLoaded', function() {
    // Inicializar tooltips y popovers
    initTooltips();
    initPopovers();
    
    // Agregar confirmación a todos los botones de eliminación
    const deleteButtons = document.querySelectorAll('.btn-delete');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            const message = this.getAttribute('data-confirm-message') || '¿Está seguro que desea eliminar este elemento?';
            if (!confirmDelete(message)) {
                e.preventDefault();
                return false;
            }
        });
    });
    
    // Agregar comportamiento de mostrar modal de carga a todos los formularios con la clase 'show-loading'
    const loadingForms = document.querySelectorAll('form.show-loading');
    loadingForms.forEach(form => {
        form.addEventListener('submit', function() {
            // Validar el formulario si tiene un ID y un atributo data-validate
            const formId = this.getAttribute('id');
            const fieldsToValidate = this.getAttribute('data-validate');
            
            if (formId && fieldsToValidate) {
                const fields = fieldsToValidate.split(',');
                if (!validateForm(formId, fields)) {
                    return false;
                }
            }
            
            // Mostrar modal de carga
            showLoadingModal();
            return true;
        });
    });
}); 