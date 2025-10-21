/**
 * Sistema de Notificaciones Real-time para GRUPO_GAD Dashboard
 * 
 * Maneja notificaciones push vía WebSocket:
 * - Alertas críticas (tareas urgentes)
 * - Notificaciones generales
 * - Warnings
 * - Errores del sistema
 * 
 * Integración con admin_dashboard.html
 */

class NotificationSystem {
    constructor() {
        this.notifications = [];
        this.maxNotifications = 50;  // Keep last 50 notifications
        this.soundEnabled = true;
        this.websocket = null;
        this.notificationContainer = null;
        this.badge = null;
        this.unreadCount = 0;
        
        this.init();
    }
    
    init() {
        // Create notification UI elements
        this.createNotificationUI();
        
        // Load saved preferences
        this.loadPreferences();
        
        // Setup WebSocket connection
        this.setupWebSocket();
        
        // Check browser notification permission
        this.requestNotificationPermission();
    }
    
    createNotificationUI() {
        // Create notification bell icon in header
        const header = document.querySelector('.dashboard-header') || document.body;
        
        const bellHTML = `
            <div class="notification-bell" id="notificationBell">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
                    <path d="M13.73 21a2 2 0 0 1-3.46 0" />
                </svg>
                <span class="notification-badge" id="notificationBadge" style="display:none;">0</span>
            </div>
        `;
        
        header.insertAdjacentHTML('beforeend', bellHTML);
        
        // Create notification panel
        const panelHTML = `
            <div class="notification-panel" id="notificationPanel" style="display:none;">
                <div class="notification-header">
                    <h3>🔔 Notificaciones</h3>
                    <div class="notification-actions">
                        <button id="markAllReadBtn" title="Marcar todas como leídas">✅</button>
                        <button id="clearAllBtn" title="Limpiar todas">🗑️</button>
                        <button id="soundToggleBtn" title="Activar/Desactivar sonido">🔊</button>
                        <button id="closePanelBtn" title="Cerrar">✖️</button>
                    </div>
                </div>
                <div class="notification-list" id="notificationList">
                    <p class="no-notifications">No hay notificaciones</p>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', panelHTML);
        
        // Get elements
        this.notificationContainer = document.getElementById('notificationList');
        this.badge = document.getElementById('notificationBadge');
        
        // Setup event listeners
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        const bell = document.getElementById('notificationBell');
        const panel = document.getElementById('notificationPanel');
        const closeBtn = document.getElementById('closePanelBtn');
        const markAllBtn = document.getElementById('markAllReadBtn');
        const clearAllBtn = document.getElementById('clearAllBtn');
        const soundBtn = document.getElementById('soundToggleBtn');
        
        bell.addEventListener('click', () => this.togglePanel());
        closeBtn.addEventListener('click', () => this.hidePanel());
        markAllBtn.addEventListener('click', () => this.markAllAsRead());
        clearAllBtn.addEventListener('click', () => this.clearAll());
        soundBtn.addEventListener('click', () => this.toggleSound());
        
        // Close panel when clicking outside
        document.addEventListener('click', (e) => {
            if (!panel.contains(e.target) && !bell.contains(e.target)) {
                this.hidePanel();
            }
        });
    }
    
    setupWebSocket() {
        // Reuse existing WebSocket connection from dashboard
        if (window.dashboardWebSocket && window.dashboardWebSocket.readyState === WebSocket.OPEN) {
            this.websocket = window.dashboardWebSocket;
            console.log('✅ Notification system using existing WebSocket connection');
        } else {
            console.warn('⚠️ No WebSocket connection available. Notifications disabled.');
            return;
        }
        
        // Listen to WebSocket messages
        this.websocket.addEventListener('message', (event) => {
            const message = JSON.parse(event.data);
            this.handleWebSocketMessage(message);
        });
    }
    
    handleWebSocketMessage(message) {
        const { event_type, data } = message;
        
        switch (event_type) {
            case 'ALERT':
                this.showNotification({
                    type: 'alert',
                    title: '🚨 Alerta Crítica',
                    message: data.message || 'Nueva tarea urgente',
                    data: data,
                    priority: 'high'
                });
                break;
                
            case 'NOTIFICATION':
                this.showNotification({
                    type: 'info',
                    title: '📢 Notificación',
                    message: data.message || 'Nueva notificación',
                    data: data,
                    priority: 'normal'
                });
                break;
                
            case 'WARNING':
                this.showNotification({
                    type: 'warning',
                    title: '⚠️ Advertencia',
                    message: data.message || 'Advertencia del sistema',
                    data: data,
                    priority: 'medium'
                });
                break;
                
            case 'ERROR':
                this.showNotification({
                    type: 'error',
                    title: '❌ Error',
                    message: data.message || 'Error del sistema',
                    data: data,
                    priority: 'high'
                });
                break;
                
            case 'TASK_CREATED':
                if (data.prioridad === 'urgente') {
                    this.showNotification({
                        type: 'alert',
                        title: '🆘 Tarea Urgente Creada',
                        message: `${data.codigo}: ${data.titulo}`,
                        data: data,
                        priority: 'high'
                    });
                }
                break;
                
            case 'TASK_STATUS_CHANGED':
                if (data.estado === 'completada') {
                    this.showNotification({
                        type: 'success',
                        title: '✅ Tarea Completada',
                        message: `${data.codigo} finalizada`,
                        data: data,
                        priority: 'low'
                    });
                }
                break;
        }
    }
    
    showNotification(notification) {
        // Add timestamp and ID
        notification.id = Date.now() + Math.random();
        notification.timestamp = new Date();
        notification.read = false;
        
        // Add to notifications array
        this.notifications.unshift(notification);
        
        // Limit notifications
        if (this.notifications.length > this.maxNotifications) {
            this.notifications = this.notifications.slice(0, this.maxNotifications);
        }
        
        // Update UI
        this.updateNotificationList();
        this.updateBadge();
        
        // Play sound if enabled
        if (this.soundEnabled && notification.priority !== 'low') {
            this.playNotificationSound(notification.priority);
        }
        
        // Show browser notification for high priority
        if (notification.priority === 'high') {
            this.showBrowserNotification(notification);
        }
        
        // Save to localStorage
        this.saveNotifications();
    }
    
    updateNotificationList() {
        const noNotificationsMsg = this.notificationContainer.querySelector('.no-notifications');
        
        if (this.notifications.length === 0) {
            if (noNotificationsMsg) noNotificationsMsg.style.display = 'block';
            return;
        }
        
        if (noNotificationsMsg) noNotificationsMsg.style.display = 'none';
        
        // Clear and rebuild list
        this.notificationContainer.innerHTML = '';
        
        this.notifications.forEach(notif => {
            const notifEl = this.createNotificationElement(notif);
            this.notificationContainer.appendChild(notifEl);
        });
    }
    
    createNotificationElement(notif) {
        const div = document.createElement('div');
        div.className = `notification-item ${notif.type} ${notif.read ? 'read' : 'unread'}`;
        div.dataset.notificationId = notif.id;
        
        const timeAgo = this.getTimeAgo(notif.timestamp);
        
        div.innerHTML = `
            <div class="notification-content">
                <div class="notification-title">${notif.title}</div>
                <div class="notification-message">${notif.message}</div>
                <div class="notification-time">${timeAgo}</div>
            </div>
            <button class="notification-delete" onclick="notificationSystem.deleteNotification(${notif.id})">
                ✖️
            </button>
        `;
        
        // Mark as read when clicked
        div.addEventListener('click', (e) => {
            if (!e.target.classList.contains('notification-delete')) {
                this.markAsRead(notif.id);
                
                // Handle notification action (e.g., navigate to task)
                if (notif.data && notif.data.task_id) {
                    this.handleNotificationClick(notif);
                }
            }
        });
        
        return div;
    }
    
    handleNotificationClick(notif) {
        console.log('Notification clicked:', notif);
        // TODO: Implement navigation to task detail page
        // Example: window.location.href = `/task/${notif.data.task_id}`;
    }
    
    markAsRead(notificationId) {
        const notif = this.notifications.find(n => n.id === notificationId);
        if (notif && !notif.read) {
            notif.read = true;
            this.unreadCount = Math.max(0, this.unreadCount - 1);
            this.updateBadge();
            this.updateNotificationList();
            this.saveNotifications();
        }
    }
    
    markAllAsRead() {
        this.notifications.forEach(n => n.read = true);
        this.unreadCount = 0;
        this.updateBadge();
        this.updateNotificationList();
        this.saveNotifications();
    }
    
    deleteNotification(notificationId) {
        const index = this.notifications.findIndex(n => n.id === notificationId);
        if (index !== -1) {
            const wasUnread = !this.notifications[index].read;
            this.notifications.splice(index, 1);
            if (wasUnread) {
                this.unreadCount = Math.max(0, this.unreadCount - 1);
            }
            this.updateBadge();
            this.updateNotificationList();
            this.saveNotifications();
        }
    }
    
    clearAll() {
        if (confirm('¿Estás seguro de que quieres eliminar todas las notificaciones?')) {
            this.notifications = [];
            this.unreadCount = 0;
            this.updateBadge();
            this.updateNotificationList();
            this.saveNotifications();
        }
    }
    
    updateBadge() {
        this.unreadCount = this.notifications.filter(n => !n.read).length;
        
        if (this.unreadCount > 0) {
            this.badge.textContent = this.unreadCount > 99 ? '99+' : this.unreadCount;
            this.badge.style.display = 'flex';
        } else {
            this.badge.style.display = 'none';
        }
    }
    
    togglePanel() {
        const panel = document.getElementById('notificationPanel');
        panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
    }
    
    hidePanel() {
        document.getElementById('notificationPanel').style.display = 'none';
    }
    
    toggleSound() {
        this.soundEnabled = !this.soundEnabled;
        const btn = document.getElementById('soundToggleBtn');
        btn.textContent = this.soundEnabled ? '🔊' : '🔇';
        btn.title = this.soundEnabled ? 'Desactivar sonido' : 'Activar sonido';
        this.savePreferences();
    }
    
    playNotificationSound(priority) {
        // Create and play notification sound
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        // Different frequencies for different priorities
        const frequency = priority === 'high' ? 800 : 500;
        oscillator.frequency.value = frequency;
        oscillator.type = 'sine';
        
        gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3);
        
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.3);
    }
    
    async requestNotificationPermission() {
        if ('Notification' in window && Notification.permission === 'default') {
            await Notification.requestPermission();
        }
    }
    
    showBrowserNotification(notif) {
        if ('Notification' in window && Notification.permission === 'granted') {
            const browserNotif = new Notification(notif.title, {
                body: notif.message,
                icon: '/static/logo.png',  // TODO: Add app logo
                badge: '/static/badge.png',
                tag: notif.id,
                requireInteraction: notif.priority === 'high'
            });
            
            browserNotif.onclick = () => {
                window.focus();
                this.togglePanel();
                browserNotif.close();
            };
        }
    }
    
    getTimeAgo(timestamp) {
        const seconds = Math.floor((new Date() - new Date(timestamp)) / 1000);
        
        const intervals = {
            'año': 31536000,
            'mes': 2592000,
            'día': 86400,
            'hora': 3600,
            'minuto': 60,
            'segundo': 1
        };
        
        for (const [name, value] of Object.entries(intervals)) {
            const interval = Math.floor(seconds / value);
            if (interval >= 1) {
                return interval === 1 ? `Hace 1 ${name}` : `Hace ${interval} ${name}s`;
            }
        }
        
        return 'Justo ahora';
    }
    
    saveNotifications() {
        try {
            localStorage.setItem('grupogad_notifications', JSON.stringify(this.notifications));
        } catch (e) {
            console.error('Error saving notifications:', e);
        }
    }
    
    loadNotifications() {
        try {
            const saved = localStorage.getItem('grupogad_notifications');
            if (saved) {
                this.notifications = JSON.parse(saved);
                this.notifications.forEach(n => {
                    n.timestamp = new Date(n.timestamp);
                });
                this.updateNotificationList();
                this.updateBadge();
            }
        } catch (e) {
            console.error('Error loading notifications:', e);
        }
    }
    
    savePreferences() {
        try {
            localStorage.setItem('grupogad_notification_prefs', JSON.stringify({
                soundEnabled: this.soundEnabled
            }));
        } catch (e) {
            console.error('Error saving preferences:', e);
        }
    }
    
    loadPreferences() {
        try {
            const saved = localStorage.getItem('grupogad_notification_prefs');
            if (saved) {
                const prefs = JSON.parse(saved);
                this.soundEnabled = prefs.soundEnabled !== false;
                
                // Update sound button
                const btn = document.getElementById('soundToggleBtn');
                if (btn) {
                    btn.textContent = this.soundEnabled ? '🔊' : '🔇';
                }
            }
        } catch (e) {
            console.error('Error loading preferences:', e);
        }
        
        // Load saved notifications
        this.loadNotifications();
    }
}

// Initialize notification system when DOM is ready
let notificationSystem;
document.addEventListener('DOMContentLoaded', () => {
    notificationSystem = new NotificationSystem();
    console.log('✅ Notification System initialized');
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = NotificationSystem;
}
