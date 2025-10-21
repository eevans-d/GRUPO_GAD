/**
 * Users Management System
 * 
 * Handles user CRUD operations from the admin dashboard.
 * Features:
 * - List users with pagination
 * - Create new user (modal form)
 * - Edit user details (modal form)
 * - Delete user with confirmation
 * - Real-time table updates
 */

class UsersManagementSystem {
    constructor(apiBaseUrl = '/api/v1') {
        this.apiBaseUrl = apiBaseUrl;
        this.usuarios = [];
        this.currentPage = 1;
        this.pageSize = 10;
        this.editingUserId = null;
        
        // Initialize
        this.init();
    }
    
    /**
     * Initialize the users management system
     */
    async init() {
        this.setupEventListeners();
        await this.loadUsers();
        this.renderTable();
    }
    
    /**
     * Setup event listeners for buttons and modals
     */
    setupEventListeners() {
        // Create user button
        const createBtn = document.getElementById('users-create-btn');
        if (createBtn) {
            createBtn.addEventListener('click', () => this.openCreateModal());
        }
        
        // Modal buttons
        const modalSaveBtn = document.getElementById('users-modal-save');
        if (modalSaveBtn) {
            modalSaveBtn.addEventListener('click', () => this.saveUser());
        }
        
        const modalCancelBtn = document.getElementById('users-modal-cancel');
        if (modalCancelBtn) {
            modalCancelBtn.addEventListener('click', () => this.closeModal());
        }
        
        // Close modal on backdrop click
        const modal = document.getElementById('users-modal');
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) this.closeModal();
            });
        }
        
        // Search functionality
        const searchInput = document.getElementById('users-search');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.filterUsers(e.target.value);
            });
        }
    }
    
    /**
     * Load users from API
     */
    async loadUsers() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/usuarios`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            this.usuarios = await response.json();
            console.log(`✅ Loaded ${this.usuarios.length} users`);
        } catch (error) {
            console.error('❌ Error loading users:', error);
            this.showNotification('Error al cargar usuarios', 'error');
        }
    }
    
    /**
     * Render users table
     */
    renderTable() {
        const tableBody = document.getElementById('users-table-body');
        if (!tableBody) return;
        
        tableBody.innerHTML = '';
        
        if (this.usuarios.length === 0) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="4" class="text-center py-8 text-gray-500">
                        No hay usuarios. <button class="text-blue-600 hover:underline" onclick="usersManager.openCreateModal()">Crear uno</button>
                    </td>
                </tr>
            `;
            return;
        }
        
        // Start and end index for current page
        const start = (this.currentPage - 1) * this.pageSize;
        const end = start + this.pageSize;
        const pageUsuarios = this.usuarios.slice(start, end);
        
        pageUsuarios.forEach(usuario => {
            const row = document.createElement('tr');
            row.className = 'border-t hover:bg-gray-50 dark:hover:bg-gray-900';
            
            const nivelBadges = {
                '1': '<span class="px-2 py-1 bg-green-100 text-green-800 rounded text-xs font-medium">Nivel 1</span>',
                '2': '<span class="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs font-medium">Nivel 2</span>',
                '3': '<span class="px-2 py-1 bg-purple-100 text-purple-800 rounded text-xs font-medium">Nivel 3</span>'
            };
            
            row.innerHTML = `
                <td class="px-4 py-3">${usuario.id}</td>
                <td class="px-4 py-3">
                    <div>
                        <div class="font-medium">${this.escapeHtml(usuario.nombre)}</div>
                        <div class="text-sm text-gray-500">@${usuario.telegram_id}</div>
                    </div>
                </td>
                <td class="px-4 py-3">${nivelBadges[usuario.nivel] || usuario.nivel}</td>
                <td class="px-4 py-3">
                    <div class="flex gap-2">
                        <button 
                            class="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 text-sm"
                            onclick="usersManager.openEditModal(${usuario.id})"
                        >
                            Editar
                        </button>
                        <button 
                            class="px-3 py-1 bg-red-500 text-white rounded hover:bg-red-600 text-sm"
                            onclick="usersManager.confirmDelete(${usuario.id}, '${this.escapeHtml(usuario.nombre)}')"
                        >
                            Eliminar
                        </button>
                    </div>
                </td>
            `;
            
            tableBody.appendChild(row);
        });
        
        this.renderPagination();
    }
    
    /**
     * Render pagination controls
     */
    renderPagination() {
        const paginationDiv = document.getElementById('users-pagination');
        if (!paginationDiv) return;
        
        const totalPages = Math.ceil(this.usuarios.length / this.pageSize);
        paginationDiv.innerHTML = '';
        
        if (totalPages <= 1) return;
        
        // Previous button
        if (this.currentPage > 1) {
            const prevBtn = document.createElement('button');
            prevBtn.textContent = '← Anterior';
            prevBtn.className = 'px-3 py-1 bg-gray-200 rounded hover:bg-gray-300';
            prevBtn.onclick = () => {
                this.currentPage--;
                this.renderTable();
            };
            paginationDiv.appendChild(prevBtn);
        }
        
        // Page numbers
        for (let i = 1; i <= totalPages; i++) {
            const btn = document.createElement('button');
            btn.textContent = i;
            btn.className = i === this.currentPage 
                ? 'px-3 py-1 bg-blue-500 text-white rounded' 
                : 'px-3 py-1 bg-gray-200 rounded hover:bg-gray-300';
            btn.onclick = () => {
                this.currentPage = i;
                this.renderTable();
            };
            paginationDiv.appendChild(btn);
        }
        
        // Next button
        if (this.currentPage < totalPages) {
            const nextBtn = document.createElement('button');
            nextBtn.textContent = 'Siguiente →';
            nextBtn.className = 'px-3 py-1 bg-gray-200 rounded hover:bg-gray-300';
            nextBtn.onclick = () => {
                this.currentPage++;
                this.renderTable();
            };
            paginationDiv.appendChild(nextBtn);
        }
    }
    
    /**
     * Filter users by search term
     */
    filterUsers(searchTerm) {
        const filtered = this.usuarios.filter(u => 
            u.nombre.toLowerCase().includes(searchTerm.toLowerCase()) ||
            u.telegram_id.toString().includes(searchTerm) ||
            u.id.toString().includes(searchTerm)
        );
        
        // Temporarily show filtered results
        const originalUsuarios = this.usuarios;
        this.usuarios = filtered;
        this.currentPage = 1;
        this.renderTable();
        this.usuarios = originalUsuarios; // Restore for future operations
    }
    
    /**
     * Open create user modal
     */
    openCreateModal() {
        this.editingUserId = null;
        document.getElementById('users-modal-title').textContent = 'Crear Nuevo Usuario';
        document.getElementById('users-form-id').value = '';
        document.getElementById('users-form-telegram-id').value = '';
        document.getElementById('users-form-nombre').value = '';
        document.getElementById('users-form-nivel').value = '1';
        document.getElementById('users-modal').classList.remove('hidden');
    }
    
    /**
     * Open edit user modal
     */
    async openEditModal(usuarioId) {
        const usuario = this.usuarios.find(u => u.id === usuarioId);
        if (!usuario) {
            this.showNotification('Usuario no encontrado', 'error');
            return;
        }
        
        this.editingUserId = usuarioId;
        document.getElementById('users-modal-title').textContent = 'Editar Usuario';
        document.getElementById('users-form-id').value = usuario.id;
        document.getElementById('users-form-telegram-id').value = usuario.telegram_id;
        document.getElementById('users-form-telegram-id').disabled = true; // Can't edit telegram_id
        document.getElementById('users-form-nombre').value = usuario.nombre;
        document.getElementById('users-form-nivel').value = usuario.nivel;
        document.getElementById('users-modal').classList.remove('hidden');
    }
    
    /**
     * Close modal
     */
    closeModal() {
        document.getElementById('users-modal').classList.add('hidden');
        document.getElementById('users-form-telegram-id').disabled = false;
        this.editingUserId = null;
    }
    
    /**
     * Save user (create or update)
     */
    async saveUser() {
        const id = document.getElementById('users-form-id').value;
        const telegramId = parseInt(document.getElementById('users-form-telegram-id').value);
        const nombre = document.getElementById('users-form-nombre').value.trim();
        const nivel = document.getElementById('users-form-nivel').value;
        
        // Validation
        if (!nombre) {
            this.showNotification('El nombre es requerido', 'error');
            return;
        }
        
        if (this.editingUserId === null && !telegramId) {
            this.showNotification('El telegram_id es requerido', 'error');
            return;
        }
        
        try {
            let response;
            const payload = {
                nombre,
                nivel
            };
            
            if (this.editingUserId) {
                // Update
                response = await fetch(`${this.apiBaseUrl}/usuarios/${this.editingUserId}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload)
                });
            } else {
                // Create
                response = await fetch(`${this.apiBaseUrl}/usuarios`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        telegram_id: telegramId,
                        ...payload
                    })
                });
            }
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || `HTTP error! status: ${response.status}`);
            }
            
            const result = await response.json();
            
            this.showNotification(
                this.editingUserId 
                    ? '✅ Usuario actualizado correctamente' 
                    : '✅ Usuario creado correctamente',
                'success'
            );
            
            this.closeModal();
            await this.loadUsers();
            this.renderTable();
            
        } catch (error) {
            console.error('❌ Error saving user:', error);
            this.showNotification(`Error: ${error.message}`, 'error');
        }
    }
    
    /**
     * Confirm before deleting user
     */
    confirmDelete(usuarioId, nombre) {
        const confirmed = window.confirm(`¿Seguro que deseas eliminar a "${nombre}"? Esta acción no se puede deshacer.`);
        if (confirmed) {
            this.deleteUser(usuarioId);
        }
    }
    
    /**
     * Delete user
     */
    async deleteUser(usuarioId) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/usuarios/${usuarioId}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            this.showNotification('✅ Usuario eliminado correctamente', 'success');
            await this.loadUsers();
            this.renderTable();
            
        } catch (error) {
            console.error('❌ Error deleting user:', error);
            this.showNotification(`Error al eliminar: ${error.message}`, 'error');
        }
    }
    
    /**
     * Show notification
     */
    showNotification(message, type = 'info') {
        console.log(`[${type.toUpperCase()}] ${message}`);
        // Could integrate with existing notification system here
        alert(message);
    }
    
    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize when DOM is ready
let usersManager;
document.addEventListener('DOMContentLoaded', () => {
    usersManager = new UsersManagementSystem('/api/v1');
});
