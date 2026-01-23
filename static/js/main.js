/**
 * Sistema de Gestión de Seguros UTPL
 * Main JavaScript File - Modern Interactions
 */

// ==================== Document Ready ====================
document.addEventListener('DOMContentLoaded', function () {
    console.log('Sistema de Seguros UTPL - Cargado');

    // Initialize all components
    initAnimations();
    initTooltips();
    initModals();
    initFormValidation();
    initDataTables();
    initDeleteConfirmations();
});

// ==================== Smooth Animations ====================
function initAnimations() {
    // Fade in elements on scroll
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver(function (entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    document.querySelectorAll('.card, .dashboard-card').forEach(el => {
        observer.observe(el);
    });
}

// ==================== Tooltip Initialization ====================
function initTooltips() {
    // Initialize tooltips for elements with data-tooltip
    document.querySelectorAll('[data-tooltip]').forEach(element => {
        element.addEventListener('mouseenter', showTooltip);
        element.addEventListener('mouseleave', hideTooltip);
    });
}

function showTooltip(e) {
    const tooltip = document.createElement('div');
    tooltip.className = 'custom-tooltip bg-gray-900 text-white px-3 py-2 rounded-lg text-sm';
    tooltip.textContent = e.target.getAttribute('data-tooltip');
    tooltip.style.position = 'absolute';
    tooltip.style.zIndex = '9999';

    document.body.appendChild(tooltip);

    const rect = e.target.getBoundingClientRect();
    tooltip.style.top = (rect.top - tooltip.offsetHeight - 10) + 'px';
    tooltip.style.left = (rect.left + rect.width / 2 - tooltip.offsetWidth / 2) + 'px';
}

function hideTooltip() {
    const tooltip = document.querySelector('.custom-tooltip');
    if (tooltip) {
        tooltip.remove();
    }
}

// ==================== Modal Functions ====================
function initModals() {
    // Close modals on background click
    document.querySelectorAll('.modal-backdrop').forEach(backdrop => {
        backdrop.addEventListener('click', closeModal);
    });

    // Close modals on ESC key
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') {
            closeAllModals();
        }
    });
}

function closeModal(e) {
    if (e.target.classList.contains('modal-backdrop')) {
        e.target.closest('.modal').classList.add('hidden');
    }
}

function closeAllModals() {
    document.querySelectorAll('.modal').forEach(modal => {
        modal.classList.add('hidden');
    });
}

// ==================== Form Validation ====================
function initFormValidation() {
    const forms = document.querySelectorAll('form[data-validate]');

    forms.forEach(form => {
        form.addEventListener('submit', function (e) {
            if (!validateForm(form)) {
                e.preventDefault();
                showFormErrors(form);
            }
        });

        // Real-time validation
        form.querySelectorAll('input, select, textarea').forEach(field => {
            field.addEventListener('blur', function () {
                validateField(field);
            });
        });
    });
}

function validateForm(form) {
    let isValid = true;
    const fields = form.querySelectorAll('[required]');

    fields.forEach(field => {
        if (!validateField(field)) {
            isValid = false;
        }
    });

    return isValid;
}

function validateField(field) {
    const value = field.value.trim();
    const fieldType = field.type;
    let isValid = true;
    let errorMessage = '';

    // Required field check
    if (field.hasAttribute('required') && !value) {
        isValid = false;
        errorMessage = 'Este campo es obligatorio';
    }

    // Email validation
    if (fieldType === 'email' && value) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(value)) {
            isValid = false;
            errorMessage = 'Ingrese un email válido';
        }
    }

    // Number validation
    if (fieldType === 'number' && value) {
        if (isNaN(value)) {
            isValid = false;
            errorMessage = 'Ingrese un número válido';
        }
    }

    // Display error
    const errorElement = field.nextElementSibling;
    if (errorElement && errorElement.classList.contains('error-message')) {
        errorElement.remove();
    }

    if (!isValid) {
        const error = document.createElement('div');
        error.className = 'error-message text-red-600 text-sm mt-1';
        error.textContent = errorMessage;
        field.parentNode.insertBefore(error, field.nextSibling);
        field.classList.add('border-red-500');
    } else {
        field.classList.remove('border-red-500');
        field.classList.add('border-green-500');
    }

    return isValid;
}

function showFormErrors(form) {
    const firstError = form.querySelector('.error-message');
    if (firstError) {
        firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}

// ==================== Data Tables Enhancement ====================
function initDataTables() {
    // Add search functionality to tables
    const tables = document.querySelectorAll('.data-table');

    tables.forEach(table => {
        const searchInput = table.previousElementSibling;
        if (searchInput && searchInput.classList.contains('table-search')) {
            searchInput.addEventListener('input', function () {
                filterTable(table, this.value);
            });
        }
    });
}

function filterTable(table, query) {
    const rows = table.querySelectorAll('tbody tr');
    const searchQuery = query.toLowerCase();

    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(searchQuery) ? '' : 'none';
    });
}

// ==================== Delete Confirmations ====================
function initDeleteConfirmations() {
    const deleteButtons = document.querySelectorAll('[data-confirm-delete]');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function (e) {
            const message = this.getAttribute('data-confirm-delete') || '¿Está seguro de que desea eliminar este elemento?';
            e.preventDefault();
            confirmAction(message, () => {
                if (this.tagName === 'BUTTON') {
                    this.closest('form').submit();
                } else {
                    window.location.href = this.href;
                }
            });
        });
    });
}

// ==================== Notification System ====================
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    const colors = {
        success: 'bg-green-50 border-green-500 text-green-700',
        error: 'bg-red-50 border-red-500 text-red-700',
        warning: 'bg-amber-50 border-amber-500 text-amber-700',
        info: 'bg-blue-50 border-blue-500 text-blue-700'
    };

    notification.className = `notification fixed top-4 right-4 px-6 py-4 rounded-xl shadow-2xl z-50 transform translate-x-full transition-transform duration-300 border-l-4 ${colors[type] || colors.info}`;

    const icon = getNotificationIcon(type);
    notification.innerHTML = `
        <div class="flex items-center space-x-3">
            <div class="flex-shrink-0">
                ${icon}
            </div>
            <p class="font-medium">${message}</p>
            <button onclick="this.parentElement.parentElement.remove()" class="ml-4 text-gray-400 hover:text-gray-600">
                <i class="bi bi-x-lg"></i>
            </button>
        </div>
    `;

    document.body.appendChild(notification);

    // Animate in
    setTimeout(() => {
        notification.classList.remove('translate-x-full');
    }, 100);

    // Auto remove after 5 seconds
    setTimeout(() => {
        notification.classList.add('translate-x-full');
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}

function getNotificationIcon(type) {
    const icons = {
        success: '<i class="bi bi-check-circle-fill text-green-600 text-2xl"></i>',
        error: '<i class="bi bi-x-circle-fill text-red-600 text-2xl"></i>',
        warning: '<i class="bi bi-exclamation-triangle-fill text-amber-600 text-2xl"></i>',
        info: '<i class="bi bi-info-circle-fill text-blue-600 text-2xl"></i>'
    };
    return icons[type] || icons.info;
}

// ==================== Loading Spinner ====================
function showLoading() {
    const loader = document.createElement('div');
    loader.id = 'global-loader';
    loader.className = 'fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50';
    loader.innerHTML = `
        <div class="bg-white rounded-2xl p-8 shadow-2xl">
            <div class="animate-spin rounded-full h-16 w-16 border-4 border-blue-600 border-t-transparent mx-auto"></div>
            <p class="mt-4 text-gray-700 font-medium">Cargando...</p>
        </div>
    `;
    document.body.appendChild(loader);
}

function hideLoading() {
    const loader = document.getElementById('global-loader');
    if (loader) {
        loader.remove();
    }
}

// ==================== Confirmation Dialog ====================
function confirmAction(message, callback) {
    const dialog = document.createElement('div');
    dialog.className = 'fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50';
    dialog.innerHTML = `
        <div class="bg-white rounded-2xl p-8 shadow-2xl max-w-md mx-4 transform scale-95 transition-transform">
            <div class="text-center">
                <div class="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-amber-100 mb-4">
                    <i class="bi bi-exclamation-triangle text-amber-600 text-3xl"></i>
                </div>
                <h3 class="text-xl font-bold text-gray-900 mb-3">Confirmar Acción</h3>
                <p class="text-gray-600 mb-6">${message}</p>
                <div class="flex gap-3">
                    <button onclick="this.closest('div.fixed').remove()" 
                            class="flex-1 px-6 py-3 bg-gray-200 text-gray-700 rounded-xl font-semibold hover:bg-gray-300 transition-colors">
                        Cancelar
                    </button>
                    <button onclick="window.confirmCallback(); this.closest('div.fixed').remove()" 
                            class="flex-1 px-6 py-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-xl font-semibold hover:from-blue-700 hover:to-blue-800 transition-all">
                        Confirmar
                    </button>
                </div>
            </div>
        </div>
    `;

    document.body.appendChild(dialog);
    window.confirmCallback = callback;

    // Animate in
    setTimeout(() => {
        dialog.querySelector('.bg-white').classList.remove('scale-95');
        dialog.querySelector('.bg-white').classList.add('scale-100');
    }, 10);
}

// ==================== Copy to Clipboard ====================
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function () {
        showNotification('Copiado al portapapeles', 'success');
    }).catch(function () {
        showNotification('Error al copiar', 'error');
    });
}

// ==================== Utility Functions ====================
function formatCurrency(amount) {
    return new Intl.NumberFormat('es-EC', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('es-EC', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

// ==================== Export Global Functions ====================
window.showNotification = showNotification;
window.showLoading = showLoading;
window.hideLoading = hideLoading;
window.confirmAction = confirmAction;
window.copyToClipboard = copyToClipboard;
window.formatCurrency = formatCurrency;
window.formatDate = formatDate;

// ==================== AJAX Form Submit ====================
function submitFormAjax(form, successCallback) {
    const formData = new FormData(form);
    const url = form.action || window.location.href;

    showLoading();

    fetch(url, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': formData.get('csrfmiddlewaretoken')
        }
    })
        .then(response => response.json())
        .then(data => {
            hideLoading();
            if (data.success) {
                showNotification(data.message || 'Operación exitosa', 'success');
                if (successCallback) successCallback(data);
            } else {
                showNotification(data.message || 'Error en la operación', 'error');
            }
        })
        .catch(error => {
            hideLoading();
            showNotification('Error de conexión', 'error');
            console.error('Error:', error);
        });
}


window.submitFormAjax = submitFormAjax;

console.log('✓ Sistema de Seguros UTPL - JavaScript cargado correctamente');
