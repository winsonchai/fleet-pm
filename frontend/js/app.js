/**
 * FleetPM - Interactive Frontend Application Logic
 */
document.addEventListener('DOMContentLoaded', () => {
  // State
  let currentTab = 'dashboard';
  let vehicleCategoryFilter = null;
  let vehicleStatusFilter = null;
  let vehicleSearchTerm = '';
  let cachedVehicles = [];
  let cachedProjects = [];
  let cachedCategories = [];
  let cachedUsers = [];

  // Toast System
  const toastContainer = document.getElementById('toastContainer');
  function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    const icon = type === 'success' ? '✓' : type === 'error' ? '✕' : 'ℹ';
    toast.innerHTML = `<span>${icon}</span> <div>${message}</div>`;
    toastContainer.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(8px)';
      toast.style.transition = 'all 0.25s ease';
      setTimeout(() => toast.remove(), 250);
    }, 4000);
  }

  // Auth & Persona Switcher
  async function switchPersona(email, password = 'password123') {
    try {
      showToast(`Switching tenant to ${email}...`, 'info');
      await API.login(email, password);
      updateHeaderUser();
      await refreshCurrentView();
      showToast(`Logged in successfully!`, 'success');
    } catch (err) {
      showToast(`Login failed: ${err.message}`, 'error');
    }
  }

  function updateHeaderUser() {
    const { user } = API.getAuth();
    if (!user) {
      document.getElementById('userName').textContent = 'Guest';
      document.getElementById('userCompanyBadge').textContent = 'Not logged in';
      return;
    }

    document.getElementById('userName').textContent = `${user.name} (${user.role.replace('_', ' ')})`;
    document.getElementById('userCompanyBadge').textContent = user.company_name || 'FleetPM System';

    // Highlight active demo button
    document.querySelectorAll('.demo-btn').forEach(btn => {
      if (btn.dataset.email === user.email) {
        btn.classList.add('active');
      } else {
        btn.classList.remove('active');
      }
    });
  }

  // Navigation
  const navTabs = document.querySelectorAll('.nav-tab');
  const viewSections = document.querySelectorAll('.view-section');

  function switchTab(tabId) {
    currentTab = tabId;
    navTabs.forEach(t => {
      if (t.dataset.tab === tabId) {
        t.classList.add('active');
      } else {
        t.classList.remove('active');
      }
    });

    viewSections.forEach(s => {
      if (s.id === `view-${tabId}`) {
        s.classList.add('active');
      } else {
        s.classList.remove('active');
      }
    });

    refreshCurrentView();
  }

  navTabs.forEach(tab => {
    tab.addEventListener('click', () => switchTab(tab.dataset.tab));
  });

  // Modal Helpers
  function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.add('active');
  }

  function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.remove('active');
  }

  document.querySelectorAll('.modal-close, [data-close-modal]').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const modal = e.target.closest('.modal-backdrop');
      if (modal) modal.classList.remove('active');
    });
  });

  // -------------------------------------------------------------
  // VIEW RENDERERS
  // -------------------------------------------------------------

  async function refreshCurrentView() {
    if (currentTab === 'dashboard') {
      await loadDashboard();
    } else if (currentTab === 'vehicles') {
      await loadVehicles();
    } else if (currentTab === 'projects') {
      await loadProjects();
    } else if (currentTab === 'logs') {
      await loadLogs();
    } else if (currentTab === 'categories') {
      await loadCategories();
    }
  }

  // 1. Dashboard View
  async function loadDashboard() {
    try {
      const stats = await API.getDashboardStats();
      document.getElementById('kpiTotal').textContent = stats.total_vehicles;
      document.getElementById('kpiAvailable').textContent = stats.available_vehicles;
      document.getElementById('kpiInUse').textContent = stats.in_use_vehicles;
      document.getElementById('kpiMaintenance').textContent = stats.maintenance_vehicles;
      document.getElementById('kpiProjects').textContent = stats.active_projects;

      // Active Trips List
      const activeTripsEl = document.getElementById('dashboardActiveTrips');
      const activeTrips = stats.recent_logs.filter(l => l.status === 'active');
      if (activeTrips.length === 0) {
        activeTripsEl.innerHTML = `
          <div style="text-align:center; padding: 32px; color: var(--text-dim);">
            No vehicles currently on the road. All active fleet units are in depot.
          </div>
        `;
      } else {
        activeTripsEl.innerHTML = `
          <div class="vehicle-grid">
            ${activeTrips.map(trip => `
              <div class="vehicle-card" style="border-left: 4px solid var(--warning);">
                <div>
                  <div class="vehicle-card-top">
                    <span class="plate-tag">${trip.vehicle_plate}</span>
                    <span class="status-badge in_use">● On Trip</span>
                  </div>
                  <div class="vehicle-model">${trip.vehicle_model}</div>
                  <div class="assignment-box" style="margin-top: 12px;">
                    <div class="assignment-row"><span class="k">Driver:</span> <span class="v">${trip.driver_name}</span></div>
                    <div class="assignment-row"><span class="k">Project:</span> <span class="v">${trip.project_name} (${trip.project_code})</span></div>
                    <div class="assignment-row"><span class="k">Start Odo:</span> <span class="v">${trip.start_odometer.toLocaleString()} km</span></div>
                    <div class="assignment-row"><span class="k">Departed:</span> <span class="v">${new Date(trip.checkout_time).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span></div>
                  </div>
                </div>
                <div class="vehicle-card-actions">
                  <button class="btn btn-primary btn-sm btn-quick-checkin" data-log-id="${trip.id}" data-start-odo="${trip.start_odometer}" data-plate="${trip.vehicle_plate}">
                    Check In Vehicle
                  </button>
                </div>
              </div>
            `).join('')}
          </div>
        `;
      }

      // Recent Activity Table
      const recentBody = document.getElementById('recentLogsTableBody');
      if (stats.recent_logs.length === 0) {
        recentBody.innerHTML = `<tr><td colspan="7" style="text-align:center; color: var(--text-dim); padding: 24px;">No trip history recorded yet.</td></tr>`;
      } else {
        recentBody.innerHTML = stats.recent_logs.map(log => `
          <tr>
            <td><span class="plate-tag" style="font-size: 13px;">${log.vehicle_plate}</span></td>
            <td><strong>${log.driver_name}</strong></td>
            <td>${log.project_name} <br><small style="color:var(--text-dim);">${log.project_code}</small></td>
            <td>
              <span class="status-badge ${log.status}">
                ${log.status === 'active' ? '● In Progress' : '✓ Completed'}
              </span>
            </td>
            <td>${log.start_odometer.toLocaleString()} km</td>
            <td>${log.end_odometer ? `${log.end_odometer.toLocaleString()} km` : '—'}</td>
            <td><strong style="color: var(--accent-cyan);">${log.distance_traveled ? `+${log.distance_traveled} km` : '—'}</strong></td>
          </tr>
        `).join('');
      }

      // Attach checkin listeners
      document.querySelectorAll('.btn-quick-checkin').forEach(btn => {
        btn.addEventListener('click', () => {
          openCheckInModal(
            parseInt(btn.dataset.logId),
            parseFloat(btn.dataset.startOdo),
            btn.dataset.plate
          );
        });
      });
    } catch (err) {
      showToast(`Error loading dashboard: ${err.message}`, 'error');
    }
  }

  // 2. Vehicles View
  async function loadVehicles() {
    try {
      const [vehicles, categories] = await Promise.all([
        API.getVehicles({
          category_id: vehicleCategoryFilter,
          status: vehicleStatusFilter,
          q: vehicleSearchTerm,
        }),
        API.getCategories(),
      ]);

      cachedVehicles = vehicles;
      cachedCategories = categories;

      // Render Category Chips
      const catChipsContainer = document.getElementById('categoryChips');
      catChipsContainer.innerHTML = `
        <button class="filter-chip ${!vehicleCategoryFilter ? 'active' : ''}" data-cat-id="">All Types</button>
        ${categories.map(c => `
          <button class="filter-chip ${vehicleCategoryFilter == c.id ? 'active' : ''}" data-cat-id="${c.id}">
            ${c.name} (${c.vehicle_count})
          </button>
        `).join('')}
      `;

      catChipsContainer.querySelectorAll('.filter-chip').forEach(chip => {
        chip.addEventListener('click', () => {
          const catId = chip.dataset.catId;
          vehicleCategoryFilter = catId ? parseInt(catId) : null;
          loadVehicles();
        });
      });

      // Render Vehicles Grid
      const grid = document.getElementById('vehiclesGrid');
      if (vehicles.length === 0) {
        grid.innerHTML = `
          <div style="grid-column: 1/-1; text-align: center; padding: 48px; background: var(--bg-card); border-radius: var(--radius-lg); color: var(--text-dim);">
            <h3>No vehicles match the selected filters</h3>
            <p style="margin-top: 6px;">Try clearing search or category filters, or add a new vehicle.</p>
          </div>
        `;
        return;
      }

      grid.innerHTML = vehicles.map(v => `
        <div class="vehicle-card">
          <div>
            <div class="vehicle-card-top">
              <span class="plate-tag">${v.plate_number}</span>
              <span class="status-badge ${v.status}">
                ${v.status === 'available' ? '● Available' : v.status === 'in_use' ? '● In Use' : '✕ Maintenance'}
              </span>
            </div>
            <div class="vehicle-model">${v.model_name}</div>
            <div class="vehicle-category">
              <span>🏷️ ${v.category_name || 'Fleet'}</span>
              ${v.year ? `• <span>${v.year}</span>` : ''}
              ${v.color ? `• <span>${v.color}</span>` : ''}
            </div>

            <div class="vehicle-specs">
              <div class="spec-item">
                <span class="spec-label">Odometer</span>
                <span class="spec-val">${v.current_odometer.toLocaleString()} km</span>
              </div>
              <div class="spec-item">
                <span class="spec-label">Fuel Type</span>
                <span class="spec-val" style="text-transform: capitalize;">${v.fuel_type}</span>
              </div>
            </div>

            ${v.current_assignment ? `
              <div class="assignment-box">
                <div class="assignment-title">🚗 Current Assignment</div>
                <div class="assignment-row"><span class="k">Driver:</span> <span class="v">${v.current_assignment.driver_name}</span></div>
                <div class="assignment-row"><span class="k">Project:</span> <span class="v">${v.current_assignment.project_name}</span></div>
                <div class="assignment-row"><span class="k">Purpose:</span> <span class="v">${v.current_assignment.purpose || 'General site duty'}</span></div>
              </div>
            ` : ''}
          </div>

          <div class="vehicle-card-actions">
            ${v.status === 'available' ? `
              <button class="btn btn-primary btn-sm btn-checkout" data-id="${v.id}" data-plate="${v.plate_number}" data-odo="${v.current_odometer}">
                Check Out
              </button>
            ` : v.status === 'in_use' ? `
              <button class="btn btn-warning btn-sm btn-checkin" data-log-id="${v.current_assignment ? v.current_assignment.log_id : ''}" data-plate="${v.plate_number}" data-start-odo="${v.current_assignment ? v.current_assignment.start_odometer : v.current_odometer}">
                Check In
              </button>
            ` : `
              <button class="btn btn-secondary btn-sm" disabled style="opacity: 0.5;">
                In Maintenance
              </button>
            `}
          </div>
        </div>
      `).join('');

      // Wire Action Buttons
      document.querySelectorAll('.btn-checkout').forEach(b => {
        b.addEventListener('click', () => {
          openCheckOutModal(parseInt(b.dataset.id), b.dataset.plate, parseFloat(b.dataset.odo));
        });
      });

      document.querySelectorAll('.btn-checkin').forEach(b => {
        b.addEventListener('click', () => {
          openCheckInModal(parseInt(b.dataset.logId), parseFloat(b.dataset.startOdo), b.dataset.plate);
        });
      });
    } catch (err) {
      showToast(`Error loading vehicles: ${err.message}`, 'error');
    }
  }

  // 3. Projects View
  async function loadProjects() {
    try {
      const projects = await API.getProjects();
      cachedProjects = projects;

      const grid = document.getElementById('projectsGrid');
      if (projects.length === 0) {
        grid.innerHTML = `
          <div style="grid-column: 1/-1; text-align: center; padding: 48px; background: var(--bg-card); border-radius: var(--radius-lg); color: var(--text-dim);">
            <h3>No projects registered</h3>
            <p style="margin-top: 6px;">Create a new project to allocate fleet vehicles.</p>
          </div>
        `;
        return;
      }

      grid.innerHTML = projects.map(p => `
        <div class="project-card">
          <div>
            <div class="project-header">
              <span class="project-code">${p.project_code}</span>
              <span class="status-badge ${p.status}">
                ${p.status === 'in_progress' ? 'In Progress' : p.status === 'planning' ? 'Planning' : 'Completed'}
              </span>
            </div>
            <div class="project-name">${p.project_name}</div>
            <div class="project-client">🏛️ Client: <strong>${p.client_name || 'Direct'}</strong></div>
            <p class="project-desc">${p.description || 'No detailed scope description provided.'}</p>
          </div>
          <div class="project-meta">
            <span>📍 ${p.site_location || 'Main Depot'}</span>
            <span class="project-active-vehicles">
              🚗 ${p.active_vehicles_count || 0} active vehicle(s)
            </span>
          </div>
        </div>
      `).join('');
    } catch (err) {
      showToast(`Error loading projects: ${err.message}`, 'error');
    }
  }

  // 4. Usage Logs View
  async function loadLogs() {
    try {
      const logs = await API.getLogs({ limit: 100 });
      const tbody = document.getElementById('logsTableBody');

      if (logs.length === 0) {
        tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; padding:32px; color:var(--text-dim);">No usage history recorded for this company.</td></tr>`;
        return;
      }

      tbody.innerHTML = logs.map(l => `
        <tr>
          <td><span class="plate-tag" style="font-size: 13px;">${l.vehicle_plate}</span></td>
          <td><strong>${l.driver_name}</strong></td>
          <td>${l.project_name} <br><small style="color:var(--text-dim);">${l.project_code}</small></td>
          <td>${new Date(l.checkout_time).toLocaleString([], {dateStyle:'short', timeStyle:'short'})}</td>
          <td>${l.checkin_time ? new Date(l.checkin_time).toLocaleString([], {dateStyle:'short', timeStyle:'short'}) : '<span style="color:var(--warning);">Active</span>'}</td>
          <td>${l.start_odometer.toLocaleString()} km</td>
          <td>${l.end_odometer ? `${l.end_odometer.toLocaleString()} km` : '—'}</td>
          <td><strong style="color: var(--accent-cyan);">${l.distance_traveled ? `+${l.distance_traveled} km` : '—'}</strong></td>
        </tr>
      `).join('');
    } catch (err) {
      showToast(`Error loading usage logs: ${err.message}`, 'error');
    }
  }

  // 5. Categories View
  async function loadCategories() {
    try {
      const categories = await API.getCategories();
      const grid = document.getElementById('categoriesGrid');

      if (categories.length === 0) {
        grid.innerHTML = `
          <div style="grid-column: 1/-1; text-align: center; padding: 48px; background: var(--bg-card); border-radius: var(--radius-lg); color: var(--text-dim);">
            <h3>No categories found</h3>
          </div>
        `;
        return;
      }

      grid.innerHTML = categories.map(c => `
        <div class="vehicle-card">
          <div class="vehicle-card-top">
            <span style="font-size: 28px;">🚚</span>
            <span class="status-badge available">${c.vehicle_count} Vehicle(s)</span>
          </div>
          <div class="vehicle-model">${c.name}</div>
          <p style="color: var(--text-dim); font-size: 13px; margin-top: 8px;">
            ${c.description || 'General fleet category'}
          </p>
        </div>
      `).join('');
    } catch (err) {
      showToast(`Error loading categories: ${err.message}`, 'error');
    }
  }

  // -------------------------------------------------------------
  // MODAL HANDLERS
  // -------------------------------------------------------------

  // Checkout Modal
  async function openCheckOutModal(vehicleId, plate, currentOdo) {
    document.getElementById('checkoutVehicleId').value = vehicleId;
    document.getElementById('checkoutVehicleTitle').textContent = `Check Out: ${plate}`;
    document.getElementById('checkoutStartOdo').value = currentOdo;
    document.getElementById('checkoutMinOdo').textContent = `${currentOdo} km`;

    // Populate Projects & Drivers dropdown
    try {
      const [projects, users] = await Promise.all([
        API.getProjects({ status: 'in_progress' }),
        API.getCompanyUsers(),
      ]);

      const projectSelect = document.getElementById('checkoutProjectSelect');
      projectSelect.innerHTML = projects.map(p => `
        <option value="${p.id}">${p.project_name} (${p.project_code})</option>
      `).join('');

      const driverSelect = document.getElementById('checkoutDriverSelect');
      const { user } = API.getAuth();
      driverSelect.innerHTML = users.map(u => `
        <option value="${u.id}" ${user && user.id === u.id ? 'selected' : ''}>
          ${u.name} (${u.role})
        </option>
      `).join('');

      openModal('checkoutModal');
    } catch (err) {
      showToast(`Failed to load projects/drivers: ${err.message}`, 'error');
    }
  }

  document.getElementById('checkoutForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const vehicleId = parseInt(document.getElementById('checkoutVehicleId').value);
    const projectId = parseInt(document.getElementById('checkoutProjectSelect').value);
    const driverId = parseInt(document.getElementById('checkoutDriverSelect').value);
    const startOdo = parseFloat(document.getElementById('checkoutStartOdo').value);
    const purpose = document.getElementById('checkoutPurpose').value;

    try {
      await API.checkoutVehicle({
        vehicle_id: vehicleId,
        project_id: projectId,
        driver_id: driverId,
        start_odometer: startOdo,
        purpose,
      });
      closeModal('checkoutModal');
      showToast('Vehicle checked out successfully! Trip is now in progress.', 'success');
      refreshCurrentView();
    } catch (err) {
      showToast(err.message, 'error');
    }
  });

  // Checkin Modal
  function openCheckInModal(logId, startOdo, plate) {
    document.getElementById('checkinLogId').value = logId;
    document.getElementById('checkinPlateTitle').textContent = `Check In: ${plate}`;
    document.getElementById('checkinStartOdo').textContent = `${startOdo} km`;
    document.getElementById('checkinEndOdo').value = startOdo + 15; // default +15km
    document.getElementById('checkinEndOdo').min = startOdo;
    openModal('checkinModal');
  }

  document.getElementById('checkinForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const logId = parseInt(document.getElementById('checkinLogId').value);
    const endOdo = parseFloat(document.getElementById('checkinEndOdo').value);
    const notes = document.getElementById('checkinNotes').value;

    try {
      await API.checkinVehicle(logId, {
        end_odometer: endOdo,
        condition_notes: notes,
      });
      closeModal('checkinModal');
      showToast('Vehicle checked in! Odometer updated and vehicle is available.', 'success');
      refreshCurrentView();
    } catch (err) {
      showToast(err.message, 'error');
    }
  });

  // Add Vehicle Modal
  document.getElementById('btnAddVehicle').addEventListener('click', async () => {
    try {
      const categories = await API.getCategories();
      const select = document.getElementById('newVehicleCategory');
      select.innerHTML = categories.map(c => `
        <option value="${c.id}">${c.name}</option>
      `).join('');
      openModal('addVehicleModal');
    } catch (err) {
      showToast(err.message, 'error');
    }
  });

  document.getElementById('addVehicleForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const category_id = parseInt(document.getElementById('newVehicleCategory').value);
    const plate_number = document.getElementById('newVehiclePlate').value;
    const model_name = document.getElementById('newVehicleModel').value;
    const current_odometer = parseFloat(document.getElementById('newVehicleOdo').value || 0);
    const fuel_type = document.getElementById('newVehicleFuel').value;

    try {
      await API.createVehicle({
        category_id,
        plate_number,
        model_name,
        current_odometer,
        fuel_type,
        status: 'available',
      });
      closeModal('addVehicleModal');
      showToast(`Vehicle ${plate_number} added to fleet!`, 'success');
      loadVehicles();
    } catch (err) {
      showToast(err.message, 'error');
    }
  });

  // Add Project Modal
  document.getElementById('btnAddProject').addEventListener('click', () => {
    openModal('addProjectModal');
  });

  document.getElementById('addProjectForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const project_name = document.getElementById('newProjectName').value;
    const project_code = document.getElementById('newProjectCode').value;
    const client_name = document.getElementById('newProjectClient').value;
    const site_location = document.getElementById('newProjectLocation').value;
    const description = document.getElementById('newProjectDesc').value;

    try {
      await API.createProject({
        project_name,
        project_code,
        client_name,
        site_location,
        description,
        status: 'in_progress',
      });
      closeModal('addProjectModal');
      showToast(`Project ${project_code} created!`, 'success');
      loadProjects();
    } catch (err) {
      showToast(err.message, 'error');
    }
  });

  // Search & Filter Events
  const searchInput = document.getElementById('vehicleSearch');
  if (searchInput) {
    let debounceTimer;
    searchInput.addEventListener('input', (e) => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        vehicleSearchTerm = e.target.value;
        loadVehicles();
      }, 300);
    });
  }

  document.querySelectorAll('.status-filter-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.status-filter-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      vehicleStatusFilter = btn.dataset.status || null;
      loadVehicles();
    });
  });

  // Demo Persona Switch Buttons
  document.querySelectorAll('.demo-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      switchPersona(btn.dataset.email, btn.dataset.password);
    });
  });

  // Logout Button
  document.getElementById('btnLogout').addEventListener('click', () => {
    API.logout();
    updateHeaderUser();
    showToast('Logged out. Please select a demo user.', 'info');
  });

  // -------------------------------------------------------------
  // INITIALIZATION
  // -------------------------------------------------------------
  async function init() {
    const { token } = API.getAuth();
    if (!token) {
      // Auto login as Alex Morgan (Apex Admin) for a seamless first-load demonstration
      await switchPersona('alex@apex.com', 'password123');
    } else {
      try {
        await API.getMe();
        updateHeaderUser();
        refreshCurrentView();
      } catch {
        await switchPersona('alex@apex.com', 'password123');
      }
    }
  }

  init();
});
