/**
 * Dashboard GRUPO_GAD - Centro de Control Administrativo
 * Implementación completa con todas las funcionalidades integradas
 */
// Network helper: usa cookies y credentials: 'include' para sesiones HttpOnly
class NetworkManager {
  constructor(baseUrl = '') { this.baseUrl = baseUrl }
  async request(path, opts = {}) {
    const url = path.startsWith('http') ? path : `${this.baseUrl}${path}`
    const init = Object.assign({ credentials: 'include' }, opts)
    return fetch(url, init)
  }
}
class Dashboard {
  constructor() {
    // Configuración del mapa y capas
    this.map = null;
    this.markers = {
      usuarios: L.layerGroup(),
      tareas: L.layerGroup(),
      emergencias: L.layerGroup(),
      marcadores: L.layerGroup() // Marcadores personalizados
    };
    
    // Estado de visibilidad de las capas
    this.layersVisible = {
      usuarios: true,
      tareas: true,
      emergencias: true,
      marcadores: true
    };
    
  // Datos de la aplicación
  // No leer token desde localStorage (usar cookies HttpOnly)
  this.token = null
  this.network = new NetworkManager();
    this.notes = [];
    this.users = [];
    this.markedLocations = [];
    
    // Inicialización
    this.init();
  }

  // === INICIALIZACIÓN ===
  async init() {
    // Verificación de autenticación mediante endpoint que valide sesión (usa cookies HttpOnly)
    try {
      const resp = await this.network.request('/api/v1/users/me', { method: 'GET' })
      if (!resp.ok) {
        window.location.href = '/login'
        return
      }
      // usuario autenticado; token se gestiona por cookie HttpOnly en el backend
      this.token = null
    } catch (err) {
      console.error('Error verificando sesión:', err)
      window.location.href = '/login'
      return
    }
    
    // Inicialización de componentes
    this.initMap();
    this.initTabs();
    this.createQuickAlerts();
    
    // Carga de datos inicial
    this.loadData();
    this.loadUsers();
    this.loadNotes();
    this.loadMarkedLocations();
    
    // Utilidades
    this.startClock();
    this.startPeriodicUpdates();
  }

  // === CONFIGURACIÓN DEL MAPA ===
  initMap() {
    try {
      // Inicializar mapa centrado en Buenos Aires
      this.map = L.map('main-map').setView([-34.6037, -58.3816], 13);
      
      // Añadir capa base de OpenStreetMap
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19
      }).addTo(this.map);
      
      // Añadir todas las capas de marcadores
      Object.values(this.markers).forEach(layer => layer.addTo(this.map));
      
      // Evento click para mostrar coordenadas
      this.map.on('click', (e) => {
        L.popup()
          .setLatLng(e.latlng)
          .setContent(this.createCoordinatePopup(e.latlng.lat, e.latlng.lng))
          .openOn(this.map);
      });
    } catch (error) {
      console.error('Error inicializando mapa:', error);
      this.showNotification('Error al cargar el mapa', 'error');
    }
  }

  createCoordinatePopup(lat, lng) {
    return `
      <div style="text-align: center;">
        <b>📍 Coordenadas</b><br>
        ${lat.toFixed(6)}, ${lng.toFixed(6)}<br>
        <button onclick="dashboard.copyCoordinates(${lat}, ${lng})" class="btn btn-primary btn-sm" style="margin-top: 5px;">
          📋 Copiar
        </button>
      </div>
    `;
  }

  copyCoordinates(lat, lng) {
    navigator.clipboard.writeText(`${lat},${lng}`).then(() => {
      this.showNotification('Coordenadas copiadas', 'success');
    }).catch(() => {
      this.showNotification('Error copiando coordenadas', 'error');
    });
  }

  // === SISTEMA DE PESTAÑAS ===
  initTabs() {
    document.querySelectorAll('.tab').forEach(tab => {
      tab.addEventListener('click', (e) => {
        const tabName = e.target.dataset.tab;
        this.switchTab(tabName);
      });
    });
  }

  switchTab(tabName) {
    // Desactivar todas las pestañas
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    
    // Activar la pestaña seleccionada
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    document.querySelector(`[data-panel="${tabName}"]`).classList.add('active');
    
    // Acciones específicas por pestaña
    if (tabName === 'users') {
      this.loadUsers();
    } else if (tabName === 'notes') {
      this.renderNotes();
    }
  }

  // === CARGA DE DATOS ===
  async loadData() {
    try {
      await Promise.all([
        this.loadMapData(),
        this.updateMetrics()
      ]);
    } catch (error) {
      console.error('Error cargando datos:', error);
    }
  }

  async loadMapData() {
    try {
      const center = this.map.getCenter();
      const url = `/api/v1/geo/map/view?center_lat=${center.lat}&center_lng=${center.lng}&radius_m=10000`;
      
  //usar NetworkManager para enviar cookies de sesión en lugar de Authorization header
  const response = await this.network.request(url, { method: 'GET', headers: { 'Content-Type': 'application/json' } });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      const data = await response.json();
      this.updateMap(data);
      this.updateCounters(data);
    } catch (error) {
      console.error('Error cargando mapa:', error);
    }
  }

  updateMap(data) {
    // Limpiar marcadores existentes (excepto marcadores personalizados)
    this.markers.usuarios.clearLayers();
    this.markers.tareas.clearLayers();
    this.markers.emergencias.clearLayers();
    
    // Procesar usuarios/efectivos
    if (data.usuarios && Array.isArray(data.usuarios)) {
      data.usuarios.forEach(user => {
        if (user.lat && user.lng) {
          const marker = L.marker([user.lat, user.lng], {
            icon: this.createIcon('👮')
          });
          
          marker.bindPopup(this.createPopupContent(
            'Efectivo', 
            user.lat, 
            user.lng, 
            user.entity_id, 
            user.distance_m
          ));
          
          this.markers.usuarios.addLayer(marker);
        }
      });
    }
    
    // Procesar tareas y emergencias
    if (data.tareas && Array.isArray(data.tareas)) {
      data.tareas.forEach(task => {
        if (task.lat && task.lng) {
          const isEmergency = task.priority === 'CRITICA';
          const layer = isEmergency ? 'emergencias' : 'tareas';
          const icon = isEmergency ? '🚨' : '📋';
          
          const marker = L.marker([task.lat, task.lng], {
            icon: this.createIcon(icon)
          });
          
          marker.bindPopup(this.createPopupContent(
            isEmergency ? 'Emergencia' : 'Tarea', 
            task.lat, 
            task.lng, 
            task.entity_id, 
            task.distance_m,
            isEmergency
          ));
          
          this.markers[layer].addLayer(marker);
        }
      });
    }
  }

  createIcon(emoji) {
    return L.divIcon({
      html: `<div style="font-size: 20px; text-shadow: 1px 1px 2px rgba(0,0,0,0.5);">${emoji}</div>`,
      iconSize: [25, 25],
      className: ''
    });
  }

  createPopupContent(title, lat, lng, id, dist, isEmergency = false) {
    const distStr = Number.isFinite(dist) ? `${Math.round(dist)}m` : '-';
    const idStr = (id || '').substring(0, 8) + '...';
    
    return `
      <div style="min-width: 220px;">
        <b>${isEmergency ? '🚨' : ''}${title}</b><br>
        ID: ${idStr}<br>
        Distancia: ${distStr}<br>
        
        <div style="margin-top: 8px; display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 4px;">
          <a href="https://www.google.com/maps/@${lat},${lng},18z" target="_blank" class="btn btn-info btn-sm" style="font-size: 10px; text-decoration: none;">
            🗺 Mapa
          </a>
          <a href="https://www.google.com/maps/@${lat},${lng},19z/data=!3m1!1e3" target="_blank" class="btn btn-success btn-sm" style="font-size: 10px; text-decoration: none;">
            🛰 Satélite
          </a>
          <a href="https://www.google.com/maps?q=&layer=c&cbll=${lat},${lng}" target="_blank" class="btn btn-warning btn-sm" style="font-size: 10px; text-decoration: none;">
            👁 Street
          </a>
        </div>
        
        <div style="margin-top: 6px;">
          <button onclick="dashboard.showLocationModal(${lat}, ${lng}, '${title}')" class="btn btn-primary btn-sm" style="width: 100%; font-size: 10px;">
            📸 Ver Vistas Completas
          </button>
        </div>
      </div>
    `;
  }

  updateCounters(data) {
    const users = data.usuarios ? data.usuarios.length : 0;
    const tasks = data.tareas ? data.tareas.length : 0;
    const emergencies = data.tareas ? data.tareas.filter(t => t.priority === 'CRITICA').length : 0;
    
    document.getElementById('active-users').textContent = `${users} activos`;
    document.getElementById('emergency-count').textContent = `${emergencies} emergencias`;
    document.getElementById('metric-tasks').textContent = tasks;
    document.getElementById('metric-officers').textContent = users;
  }

  async updateMetrics() {
    // Métricas adicionales si hay endpoint específico
    // Por ahora se basan en los datos del mapa
  }

  // === CONTROL DEL MAPA ===
  toggleLayer(layerName) {
    const layer = this.markers[layerName];
    const button = document.getElementById(`btn-${layerName}`);
    
    if (!layer || !button) return;
    
    if (this.layersVisible[layerName]) {
      this.map.removeLayer(layer);
      button.style.opacity = '0.5';
    } else {
      layer.addTo(this.map);
      button.style.opacity = '1';
    }
    
    this.layersVisible[layerName] = !this.layersVisible[layerName];
  }

  async searchAddress() {
    const query = document.getElementById('search-address').value.trim();
    if (!query) return;
    
    try {
      const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&limit=1`;
      const response = await fetch(url);
      const results = await response.json();
      
      if (results.length > 0) {
        const lat = parseFloat(results[0].lat);
        const lng = parseFloat(results[0].lon);
        
        this.map.setView([lat, lng], 16);
        
        L.marker([lat, lng])
          .addTo(this.map)
          .bindPopup(`📍 ${results[0].display_name}`)
          .openPopup();
          
        this.showNotification('Ubicación encontrada', 'success');
        this.quickNote(`🔍 Búsqueda: ${query} -> ${lat.toFixed(4)}, ${lng.toFixed(4)}`);
      } else {
        this.showNotification('No se encontró la dirección', 'warning');
      }
    } catch (error) {
      this.showNotification('Error buscando dirección', 'error');
    }
  }

  refreshMap() {
    this.loadMapData();
    this.showNotification('Mapa actualizado', 'success');
  }

  openInGoogleMaps() {
    const center = this.map.getCenter();
    const zoom = this.map.getZoom();
    window.open(`https://www.google.com/maps/@${center.lat},${center.lng},${zoom}z`, '_blank');
  }

  // === CONTROL TELEGRAM ===
  async sendTelegram() {
    const group = document.getElementById('tg-group').value;
    const type = document.getElementById('tg-type').value;
    const message = document.getElementById('tg-message').value.trim();
    
    if (!message) {
      this.showNotification('Escriba un mensaje', 'warning');
      return;
    }
    
    try {
      const response = await fetch('/api/v1/admin/telegram/send', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ group, message, type })
      });
      
      if (response.ok) {
        document.getElementById('tg-message').value = '';
        document.getElementById('tg-message').style.background = '';
        this.showNotification('✅ Mensaje enviado', 'success');
        this.quickNote(`📱 Telegram ${group}/${type}: ${message.substring(0, 50)}...`);
      } else {
        const error = await response.json();
        this.showNotification(error.detail || 'Error enviando mensaje', 'error');
      }
    } catch (error) {
      this.showNotification('Error de conexión', 'error');
    }
  }

  clearTelegram() {
    document.getElementById('tg-message').value = '';
    document.getElementById('tg-message').style.background = '';
  }

  quickMessage(type) {
    const messages = {
      'status': { 
        text: '📊 Todos los efectivos reporten estado y ubicación actual', 
        type: 'alert' 
      },
      'meeting': { 
        text: '📅 Reunión de coordinación en 30 minutos - Asistencia obligatoria',
        type: 'alert' 
      },
      'patrol': { 
        text: '🚔 Intensificar patrullaje - Prioridad ALTA - Reportar cada 15 min',
        type: 'urgent' 
      },
      'report': { 
        text: '📝 Enviar reporte de turno antes de las 18:00',
        type: 'info' 
      }
    };
    
    const msg = messages[type];
    if (msg) {
      document.getElementById('tg-type').value = msg.type;
      document.getElementById('tg-message').value = msg.text;
      this.switchTab('telegram');
    }
  }

  // === PROTOCOLOS DE EMERGENCIA ===
  quickAlert(type) {
    const alerts = {
      'codigo-rojo': {
        group: 'emergencias',
        type: 'urgent',
        message: '🔴 CÓDIGO ROJO - ALERTA MÁXIMA\nTodos los efectivos reportar posición INMEDIATAMENTE'
      },
      'evacuacion': {
        group: 'emergencias',
        type: 'urgent',
        message: '🏃 PROTOCOLO EVACUACIÓN ACTIVADO\nProceder según plan establecido - Reportar cumplimiento'
      },
      'refuerzos': {
        group: 'operaciones',
        type: 'alert',
        message: '🆘 SOLICITUD REFUERZOS URGENTE\nTodas las unidades disponibles acudir al punto indicado'
      },
      'fin-operativo': {
        group: 'general',
        type: 'info',
        message: '✅ OPERATIVO FINALIZADO\nReanudar actividades normales - Enviar reporte final'
      },
      'reunion-urgente': {
        group: 'supervisores',
        type: 'alert',
        message: '📅 REUNIÓN URGENTE\nTodos los supervisores en 15 minutos - Asistencia obligatoria'
      }
    };
    
    const alert = alerts[type];
    if (!alert) return;
    
    document.getElementById('tg-group').value = alert.group;
    document.getElementById('tg-type').value = alert.type;
    document.getElementById('tg-message').value = alert.message;
    
    this.switchTab('telegram');
    document.getElementById('tg-message').style.background = '#fff3cd';
    
    this.showNotification(`⚠ Alerta ${type.replace('-', '').toUpperCase()} preparada`, 'warning');
    this.quickNote(`⚠ Protocolo preparado: ${type} - ${new Date().toLocaleTimeString()}`);
  }

  createQuickAlerts() {
    const html = `
      <div class="card" style="background: #f8d7da; border-color: #f5c6cb; margin-top: 15px;">
        <h4 style="color: #721c24; margin-bottom: 10px; font-size: 14px;">🚨 Protocolos de Emergencia</h4>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 8px;">
          <button class="btn btn-danger btn-sm" onclick="dashboard.quickAlert('codigo-rojo')">🔴 Código Rojo</button>
          <button class="btn btn-warning btn-sm" onclick="dashboard.quickAlert('evacuacion')">🏃 Evacuación</button>
          <button class="btn btn-info btn-sm" onclick="dashboard.quickAlert('refuerzos')">🆘 Refuerzos</button>
          <button class="btn btn-success btn-sm" onclick="dashboard.quickAlert('fin-operativo')">✅ Fin Operativo</button>
        </div>
        <button class="btn btn-primary btn-sm" onclick="dashboard.quickAlert('reunion-urgente')" style="width: 100%;">📅 Reunión Urgente Supervisores</button>
      </div>
    `;
    
    const dashPanel = document.querySelector('[data-panel="dashboard"]');
    if (dashPanel) dashPanel.insertAdjacentHTML('beforeend', html);
  }

  // === GESTIÓN DE USUARIOS ===
  async loadUsers() {
    try {
      const response = await fetch('/api/v1/users/', {
        headers: {
          'Authorization': `Bearer ${this.token}`
        }
      });
      
      if (response.ok) {
        this.users = await response.json();
        this.renderUsers();
        this.updateUsersSummary();
      } else {
        throw new Error(`HTTP ${response.status}`);
      }
    } catch (error) {
      console.error('Error cargando usuarios:', error);
      document.getElementById('users-list').innerHTML = '<div class="card">Error cargando usuarios</div>';
    }
  }

  renderUsers(filter = '') {
    const container = document.getElementById('users-list');
    if (!container) return;
    
    const filtered = this.users.filter(u => 
      !filter || 
      (u.nombre && u.nombre.toLowerCase().includes(filter.toLowerCase())) ||
      (u.email && u.email.toLowerCase().includes(filter.toLowerCase())) ||
      (u.telegram_id && u.telegram_id.toString().includes(filter))
    );
    
    container.innerHTML = filtered.map(user => `
      <div class="card user-card ${user.is_active ? 'online' : ''}" onclick="dashboard.showUser('${user.id}')">
        <div style="font-weight: 600; margin-bottom: 4px;">
          ${user.is_active ? '🟢' : '🔴'} ${user.nombre || 'Sin nombre'}
        </div>
        <div style="font-size: 11px; color: #6c757d;">
          📧 ${user.email || '-'}<br>
          👮 ${user.nivel || '-'}<br>
          📱 ${user.telegram_id ? `TG: ${user.telegram_id}` : 'Sin Telegram'}
        </div>
      </div>
    `).join('');
  }

  filterUsers(query) {
    this.renderUsers(query);
  }

  updateUsersSummary() {
    const total = this.users.length;
    const active = this.users.filter(u => u.is_active).length;
    const withTelegram = this.users.filter(u => u.telegram_id).length;
    
    document.getElementById('users-summary').textContent = `${total} total, ${active} activos, ${withTelegram} con Telegram`;
  }

  showUser(userId) {
    const user = this.users.find(u => u.id === userId);
    if (!user) return;
    
    const details = `👤 INFORMACIÓN DEL USUARIO
Nombre: ${user.nombre || '-'}
Email: ${user.email || '-'}
Nivel: ${user.nivel || '-'}
Telegram: ${user.telegram_id || 'No vinculado'}
Estado: ${user.is_active ? 'Activo' : 'Inactivo'}
ID: ${user.id}
Creado: ${user.created_at ? new Date(user.created_at).toLocaleString() : 'N/A'}`;
    
    alert(details);
    this.quickNote(`👤 Consultado usuario: ${user.nombre} (${user.email})`);
  }

  // === SISTEMA DE NOTAS ===
  loadNotes() {
    const saved = localStorage.getItem('admin_notes');
    if (saved) {
      try {
        this.notes = JSON.parse(saved);
      } catch {
        this.notes = [];
      }
    }
    this.renderNotes();
  }

  addNote() {
    const input = document.getElementById('new-note');
    const text = input.value.trim();
    if (!text) return;
    
    const note = {
      id: Date.now(),
      text: text,
      timestamp: new Date().toISOString(),
      category: 'manual'
    };
    
    this.notes.unshift(note);
    this.saveNotes();
    this.renderNotes();
    input.value = '';
    this.showNotification('Nota añadida', 'success');
  }

  quickNote(text) {
    const note = {
      id: Date.now(),
      text: `[AUTO] ${text}`,
      timestamp: new Date().toISOString(),
      category: 'auto'
    };
    
    this.notes.unshift(note);
    this.saveNotes();
    this.renderNotes();
  }

  deleteNote(noteId) {
    this.notes = this.notes.filter(n => n.id !== noteId);
    this.saveNotes();
    this.renderNotes();
  }

  renderNotes() {
    const container = document.getElementById('notes-list');
    if (!container) return;
    
    if (this.notes.length === 0) {
      container.innerHTML = '<div class="card">Sin notas</div>';
      return;
    }
    
    container.innerHTML = this.notes.map(note => `
      <div class="note">
        <button class="note-delete" onclick="dashboard.deleteNote(${note.id})">×</button>
        <div style="font-size: 10px; color: #856404; margin-bottom: 4px;">
          ${new Date(note.timestamp).toLocaleString()} ${note.category === 'auto' ? '📝' : '✏'}
        </div>
        <div>${note.text}</div>
      </div>
    `).join('');
  }

  saveNotes() {
    if (this.notes.length > 100) {
      this.notes = this.notes.slice(0, 100);
    }
    localStorage.setItem('admin_notes', JSON.stringify(this.notes));
  }

  exportNotes() {
    if (this.notes.length === 0) {
      this.showNotification('No hay notas para exportar', 'warning');
      return;
    }
    
    const text = this.notes.map(n => 
      `[${new Date(n.timestamp).toLocaleString()}] ${n.text}`
    ).join('\n\n');
    
    const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = `notas_grupo_gad_${new Date().toISOString().split('T')[0]}.txt`;
    a.click();
    
    URL.revokeObjectURL(url);
    this.showNotification('Notas exportadas', 'success');
  }

  clearNotes() {
    if (confirm('¿Eliminar todas las notas?')) {
      this.notes = [];
      this.saveNotes();
      this.renderNotes();
      this.showNotification('Notas eliminadas', 'success');
    }
  }

  // === GESTIÓN DE EMERGENCIAS ===
  async createEmergency() {
    const desc = document.getElementById('emergency-desc').value.trim();
    if (!desc) {
      this.showNotification('Ingrese descripción de la emergencia', 'warning');
      return;
    }
    
    const center = this.map.getCenter();
    
    try {
      const response = await fetch('/api/v1/tasks/emergency', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          telegram_id: 0,
          lat: center.lat,
          lng: center.lng,
          descripcion: desc
        })
      });
      
      if (response.ok) {
        const result = await response.json();
        document.getElementById('emergency-desc').value = '';
        
        this.showNotification(`✅ Emergencia creada: ${result.codigo || 'OK'}`, 'success');
        this.quickNote(`🚨 Emergencia creada: ${desc} en ${center.lat.toFixed(4)}, ${center.lng.toFixed(4)}`);
        this.refreshMap();
      } else {
        const error = await response.json();
        this.showNotification(error.detail || 'Error creando emergencia', 'error');
      }
    } catch (error) {
      this.showNotification('Error de conexión', 'error');
    }
  }

  // === HERRAMIENTAS DE MAPEO AVANZADO ===
  logAccess(portal) {
    this.quickNote(`🔗 Acceso portal: ${portal} - ${new Date().toLocaleTimeString()}`);
  }

  viewStreetView() {
    const address = document.getElementById('map-search-address').value.trim();
    if (!address) {
      const center = this.map.getCenter();
      this.openStreetView(center.lat, center.lng);
    } else {
      this.geocodeAndView(address, 'street');
    }
  }

  viewSatellite() {
    const address = document.getElementById('map-search-address').value.trim();
    if (!address) {
      const center = this.map.getCenter();
      this.openSatelliteView(center.lat, center.lng);
    } else {
      this.geocodeAndView(address, 'satellite');
    }
  }

  viewBoth() {
    const address = document.getElementById('map-search-address').value.trim();
    if (!address) {
      const center = this.map.getCenter();
      this.showLocationModal(center.lat, center.lng, 'Ubicación actual');
    } else {
      this.geocodeAndView(address, 'both');
    }
  }

  async geocodeAndView(address, viewType) {
    try {
      const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(address)}&limit=1`;
      const response = await fetch(url);
      const results = await response.json();
      
      if (results.length > 0) {
        const lat = parseFloat(results[0].lat);
        const lng = parseFloat(results[0].lon);
        
        if (viewType === 'street') {
          this.openStreetView(lat, lng);
        } else if (viewType === 'satellite') {
          this.openSatelliteView(lat, lng);
        } else {
          this.showLocationModal(lat, lng, address);
        }
        
        L.marker([lat, lng])
          .addTo(this.map)
          .bindPopup(`🔍 ${address}`)
          .openPopup();
          
        this.map.setView([lat, lng], 17);
      } else {
        this.showNotification('Dirección no encontrada', 'warning');
      }
    } catch (error) {
      this.showNotification('Error buscando dirección', 'error');
    }
  }

  openStreetView(lat, lng) {
    const url = `https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=${lat},${lng}`;
    window.open(url, '_blank');
    this.quickNote(`🏠 Vista frontal: ${lat.toFixed(5)}, ${lng.toFixed(5)}`);
  }

  openSatelliteView(lat, lng) {
    const url = `https://www.google.com/maps/@${lat},${lng},18z/data=!3m1!1e3`;
    window.open(url, '_blank');
    this.quickNote(`🛰 Vista aérea: ${lat.toFixed(5)}, ${lng.toFixed(5)}`);
  }

  showLocationModal(lat, lng, title) {
    const modalHtml = `
      <div id="location-modal" style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); display: flex; justify-content: center; align-items: center; z-index: 10000;">
        <div style="background: white; padding: 20px; border-radius: 8px; max-width: 90%; max-height: 90%; overflow-y: auto; position: relative;">
          <button onclick="document.getElementById('location-modal').remove()" style="position: absolute; top: 10px; right: 10px; background: #dc3545; color: white; border: none; border-radius: 50%; width: 30px; height: 30px; cursor: pointer; font-weight: bold;">×</button>
          
          <h3 style="margin-bottom: 15px; font-size: 16px;">📍 Vistas de: ${title}</h3>
          
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 15px;">
            <div>
              <h4 style="margin-bottom: 8px; font-size: 14px;">🛰 Vista Satelital</h4>
              <iframe src="https://www.google.com/maps/embed?pb=!1m14!1m12!1m3!1d500!2d${lng}!3d${lat}!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!5e1!3m2!1ses!2sar" width="100%" height="250" style="border:0; border-radius: 4px;" allowfullscreen loading="lazy"></iframe>
            </div>
            
            <div>
              <h4 style="margin-bottom: 8px; font-size: 14px;">👁 Street View</h4>
              <iframe src="https://www.google.com/maps/embed?pb=!4v1693526400000!6m8!1m7!1s${lat},${lng}!2m2!1d${lat}!2d${lng}!3f0!4f0!5f0.7" width="100%" height="250" style="border:0; border-radius: 4px;" allowfullscreen loading="lazy"></iframe>
            </div>
          </div>
          
          <div style="background: #f8f9fa; padding: 10px; border-radius: 4px; margin-bottom: 15px;">
            <strong>📍 Coordenadas:</strong> ${lat.toFixed(6)}, ${lng.toFixed(6)}<br>
            <strong>🕒 Consultado:</strong> ${new Date().toLocaleString()}
          </div>
          
          <div style="display: flex; gap: 10px; justify-content: center; flex-wrap: wrap;">
            <button onclick="dashboard.markQuickLocation(${lat}, ${lng}, '${title}')" class="btn btn-warning">📍 Marcar Ubicación</button>
            <button onclick="navigator.clipboard.writeText('${lat},${lng}'); dashboard.showNotification('Coordenadas copiadas', 'success')" class="btn btn-info">📋 Copiar Coords</button>
            <a href="https://www.google.com/maps/@${lat},${lng},18z" target="_blank" class="btn btn-success">🗺 Abrir en Google Maps</a>
          </div>
        </div>
      </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    this.quickNote(`📍 Vista dual: ${title} (${lat.toFixed(4)}, ${lng.toFixed(4)})`);
  }

  // === SISTEMA DE MARCADO DE UBICACIONES ===
  async markLocation() {
    const address = document.getElementById('map-search-address').value.trim();
    const description = prompt('Descripción del punto marcado:');
    if (!description) return;
    
    let lat, lng;
    
    if (address) {
      try {
        const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(address)}&limit=1`;
        const response = await fetch(url);
        const results = await response.json();
        
        if (results.length > 0) {
          lat = parseFloat(results[0].lat);
          lng = parseFloat(results[0].lon);
        } else {
          this.showNotification('Dirección no encontrada', 'warning');
          return;
        }
      } catch (error) {
        this.showNotification('Error geocodificando', 'error');
        return;
      }
    } else {
      const center = this.map.getCenter();
      lat = center.lat;
      lng = center.lng;
    }
    
    this.markQuickLocation(lat, lng, description);
  }

  markQuickLocation(lat, lng, description) {
    const type = prompt('Tipo:\n1) 🏠 Allanamiento\n2) 🔍 Inspección\n3) ⭐ Punto de Interés\n4) 🚔 Patrullaje', '3');
    const types = {'1': '🏠', '2': '🔍', '3': '⭐', '4': '🚔'};
    const typeNames = {'1': 'Allanamiento', '2': 'Inspección', '3': 'Punto Interés', '4': 'Patrullaje'};
    
    const icon = types[type] || '📍';
    const typeName = typeNames[type] || 'Marcador';
    
    const marks = JSON.parse(localStorage.getItem('marked_locations') || '[]');
    
    const newMark = {
      id: Date.now(),
      lat: lat,
      lng: lng,
      description: description,
      type: typeName,
      icon: icon,
      timestamp: new Date().toISOString()
    };
    
    marks.push(newMark);
    localStorage.setItem('marked_locations', JSON.stringify(marks));
    
    this.addMarkerToMap(newMark);
    
    this.showNotification(`${icon} ${typeName} marcado`, 'success');
    this.quickNote(`${icon} ${typeName}: ${description} en ${lat.toFixed(4)}, ${lng.toFixed(4)}`);
    
    const modal = document.getElementById('location-modal');
    if (modal) modal.remove();
  }

  addMarkerToMap(mark) {
    const marker = L.marker([mark.lat, mark.lng], {
      icon: L.divIcon({
        html: `<div style="background: #dc3545; color: white; border-radius: 50%; width: 20px; height: 20px; display: flex; align-items: center; justify-content: center; font-size: 12px; border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.3);">${mark.icon}</div>`,
        iconSize: [20, 20],
        className: ''
      })
    });
    
    marker.bindPopup(
      `
      <strong>${mark.icon} ${mark.type}</strong><br>
      ${mark.description}<br>
      <small>${new Date(mark.timestamp).toLocaleString()}</small><br>
      <button onclick="dashboard.deleteMarker(${mark.id})" style="margin-top: 5px; background: #dc3545; color: white; border: none; padding: 2px 6px; border-radius: 3px; cursor: pointer;">
        Eliminar
      </button>
    `
    );
    
    this.markers.marcadores.addLayer(marker);
    this.map.setView([mark.lat, mark.lng], 17);
  }

  loadMarkedLocations() {
    const marks = JSON.parse(localStorage.getItem('marked_locations') || '[]');
    marks.forEach(mark => this.addMarkerToMap(mark));
  }

  deleteMarker(markId) {
    const marks = JSON.parse(localStorage.getItem('marked_locations') || '[]');
    const filtered = marks.filter(m => m.id !== markId);
    
    localStorage.setItem('marked_locations', JSON.stringify(filtered));
    
    this.refreshMarkedLocations();
    this.showNotification('Marca eliminada', 'success');
  }

  refreshMarkedLocations() {
    this.markers.marcadores.clearLayers();
    this.loadMarkedLocations();
  }

  // === HERRAMIENTAS OSINT ===
  osintSearch(platform) {
    const target = document.getElementById('osint-target').value.trim();
    if (!target) {
      this.showNotification('Ingrese objetivo de investigación', 'warning');
      return;
    }
    
    const searches = {
      'google': `https://www.google.com/search?q="${target}"`, 
      'linkedin': `https://www.linkedin.com/search/results/all/?keywords=${encodeURIComponent(target)}`,
      'facebook': `https://www.facebook.com/search/top?q=${encodeURIComponent(target)}`,
      'instagram': `https://www.instagram.com/explore/tags/${encodeURIComponent(target.replace(/\s+/g, ''))}/`,
      'renaper': `https://www.argentina.gob.ar/interior/renaper`,
      'anses': `https://www.anses.gob.ar/`,
      'registro': `https://www.argentina.gob.ar/justicia/registro-automotor`,
      'judicial': `https://www.pjn.gov.ar/`
    };
    
    if (platform === 'comprehensive') {
      const urls = [
        `https://www.google.com/search?q="${target}" site:argentina.gob.ar`,
        `https://www.google.com/search?q="${target}" site:boletinoficial.gob.ar`,
        `https://www.google.com/search?q="${target}"`,
        `https://www.linkedin.com/search/results/all/?keywords=${encodeURIComponent(target)}`
      ];
      
      urls.forEach(url => window.open(url, '_blank'));
      
      this.quickNote(`🎯 Investigación completa: ${target} - ${urls.length} búsquedas`);
      this.showNotification(`Investigación completa iniciada (${urls.length} ventanas)`, 'info');
    } else if (searches[platform]) {
      window.open(searches[platform], '_blank');
      this.quickNote(`🔍 OSINT ${platform.toUpperCase()}: ${target}`);
      this.showNotification(`Búsqueda ${platform} iniciada`, 'info');
    }
  }

  // === ACCIONES RÁPIDAS ===
  quickEmergency() {
    this.switchTab('emergency');
    document.getElementById('emergency-desc').focus();
  }

  broadcastAlert() {
    document.getElementById('tg-group').value = 'emergencias';
    document.getElementById('tg-type').value = 'urgent';
    document.getElementById('tg-message').value = '🚨 ALERTA GENERAL - Todos los efectivos en alerta máxima - Reportar posición inmediatamente';
    this.switchTab('telegram');
    document.getElementById('tg-message').style.background = '#f8d7da';
  }

  requestStatus() {
    document.getElementById('tg-group').value = 'general';
    document.getElementById('tg-type').value = 'alert';
    document.getElementById('tg-message').value = '📊 Todos los efectivos reporten estado y ubicación actual';
    this.switchTab('telegram');
  }

  refreshAll() {
    Promise.all([
      this.loadData(),
      this.loadUsers()
    ]).then(() => {
      this.showNotification('Todo actualizado', 'success');
    });
  }

  // === UTILIDADES ===
  startClock() {
    const updateClock = () => {
      const now = new Date();
      const clock = document.getElementById('clock');
      if (clock) {
        clock.textContent = now.toLocaleTimeString('es-AR');
      }
    };
    
    updateClock();
    setInterval(updateClock, 1000);
  }

  startPeriodicUpdates() {
    setInterval(() => {
      this.loadMapData();
    }, 30000);
  }

  showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
      notification.style.animation = 'slideOut 0.3s ease';
      setTimeout(() => notification.remove(), 300);
    }, 3000);
  }

  logout() {
    if (confirm('¿Cerrar sesión?')) {
      localStorage.removeItem('admin_token');
      localStorage.removeItem('admin_notes');
      localStorage.removeItem('marked_locations');
      window.location.href = '/login';
    }
  }
}

// === INICIALIZACIÓN ===
document.addEventListener('DOMContentLoaded', () => {
  window.dashboard = new Dashboard();
});

// CSS adicional para animaciones
const style = document.createElement('style');
style.textContent = `
  @keyframes slideOut {
    from { transform: translateX(0); opacity: 1; }
    to { transform: translateX(100%); opacity: 0; }
  }
`;
document.head.appendChild(style);
