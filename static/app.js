// Global state
let token = localStorage.getItem('token');
let currentUser = null;
let previewPdfUrl = null;

function formatLocalDate(dateString) {
    if (!dateString) return '';
    const hasTimezone = /Z$|[+-]\d{2}:\d{2}$/.test(dateString);
    const normalized = hasTimezone ? dateString : `${dateString}Z`;
    const date = new Date(normalized);
    if (Number.isNaN(date.getTime())) return dateString;
    return date.toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' });
}

// API Base URL
const API_BASE = '/api';

// Helper function for API calls
async function apiCall(endpoint, options = {}) {
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers,
    };

    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers,
    });

    if (response.status === 401) {
        logout();
        throw new Error('Unauthorized');
    }

    const contentType = response.headers.get('content-type');
    const isJson = contentType && contentType.includes('application/json');

    if (!response.ok) {
        let errorMessage = 'An error occurred';
        if (isJson) {
            const error = await response.json();
            if (typeof error.detail === 'string') {
                errorMessage = error.detail;
            } else if (error.detail) {
                errorMessage = JSON.stringify(error.detail);
            } else if (error.message) {
                errorMessage = error.message;
            }
        } else {
            const text = await response.text();
            errorMessage = text || errorMessage;
        }
        throw new Error(errorMessage);
    }

    return isJson ? response.json() : response.text();
}

// Login
document.getElementById('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const errorDiv = document.getElementById('login-error');
    
    try {
        const formData = new FormData();
        formData.append('username', username);
        formData.append('password', password);
        
        const response = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            body: formData,
        });
        
        if (!response.ok) {
            throw new Error('Invalid credentials');
        }
        
        const data = await response.json();
        token = data.access_token;
        localStorage.setItem('token', token);
        
        await loadCurrentUser();
        showApp();
        errorDiv.textContent = '';
    } catch (error) {
        errorDiv.textContent = error.message;
    }
});

// User Menu
document.getElementById('user-menu-btn').addEventListener('click', () => {
    document.querySelector('.user-menu').classList.toggle('open');
});

// Close menu when clicking outside
document.addEventListener('click', (e) => {
    const userMenu = document.querySelector('.user-menu');
    if (!userMenu.contains(e.target)) {
        userMenu.classList.remove('open');
    }
});

// Show Profile Modal
function showProfileModal() {
    document.getElementById('profile-modal').style.display = 'flex';
    document.getElementById('profile-username').textContent = currentUser.username;
    document.getElementById('profile-email').textContent = currentUser.email;
    document.getElementById('profile-role').textContent = currentUser.role;
    document.querySelector('.user-menu').classList.remove('open');
}

// Close Profile Modal
function closeProfileModal() {
    document.getElementById('profile-modal').style.display = 'none';
}

// Change Password
document.getElementById('change-password-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const currentPassword = document.getElementById('current-password').value;
    const newPassword = document.getElementById('new-password-field').value;
    const confirmPassword = document.getElementById('confirm-password').value;
    const messageDiv = document.getElementById('password-message');
    
    if (newPassword !== confirmPassword) {
        messageDiv.className = 'message error';
        messageDiv.textContent = 'New passwords do not match';
        return;
    }
    
    try {
        await apiCall('/users/me/password', {
            method: 'PUT',
            body: JSON.stringify({
                current_password: currentPassword,
                new_password: newPassword,
            }),
        });
        
        messageDiv.className = 'message success';
        messageDiv.textContent = 'Password changed successfully!';
        
        setTimeout(() => {
            closeProfileModal();
            e.target.reset();
            messageDiv.textContent = '';
        }, 2000);
    } catch (error) {
        messageDiv.className = 'message error';
        messageDiv.textContent = error.message;
    }
});

// Logout
function logout() {
    token = null;
    currentUser = null;
    localStorage.removeItem('token');
    showLogin();
}

// Load current user
async function loadCurrentUser() {
    try {
        currentUser = await apiCall('/users/me');
        document.getElementById('user-display').textContent = `${currentUser.username} (${currentUser.role})`;
        
        // Show/hide admin tabs
        const isAdmin = currentUser.role === 'admin';
        document.getElementById('templates-tab-btn').style.display = isAdmin ? 'block' : 'none';
        document.getElementById('users-tab-btn').style.display = isAdmin ? 'block' : 'none';
        document.getElementById('audit-tab-btn').style.display = isAdmin ? 'block' : 'none';
        document.getElementById('backup-tab-btn').style.display = isAdmin ? 'block' : 'none';
        document.getElementById('sync-tab-btn').style.display = isAdmin ? 'block' : 'none';
        document.getElementById('admin-filters').style.display = isAdmin ? 'block' : 'none';
        
        // Load templates for dropdown
        await loadTemplatesForSelection();
        
        if (isAdmin) {
            loadTemplates();
            loadUsers();
            await loadUsersForFilter();
        }
    } catch (error) {
        console.error('Failed to load user:', error);
    }
}

// Show/hide sections
function showLogin() {
    document.getElementById('login-section').style.display = 'flex';
    document.getElementById('app-section').style.display = 'none';
    setActiveTab('documents');
}

function showApp() {
    document.getElementById('login-section').style.display = 'none';
    document.getElementById('app-section').style.display = 'block';
    setActiveTab('documents');
    loadDocuments();
    loadTemplatesForSelection();
    initializeCKEditor();
}

function setActiveTab(tabName) {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    const targetBtn = document.querySelector(`.tab-btn[data-tab="${tabName}"]`);
    const targetTab = document.getElementById(`${tabName}-tab`);
    if (targetBtn) targetBtn.classList.add('active');
    if (targetTab) targetTab.classList.add('active');
}

// Tabs
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const tab = btn.dataset.tab;
        
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        
        btn.classList.add('active');
        document.getElementById(`${tab}-tab`).classList.add('active');
        
        if (tab === 'documents') {
            loadDocuments();
            loadTemplatesForSelection();
            // Load users for filter dropdown if admin
            if (currentUser && currentUser.role === 'admin') {
                loadUsersForFilter();
            }
        } else if (tab === 'audit') {
            loadAuditLogs();
        } else if (tab === 'templates') {
            loadTemplates();
        } else if (tab === 'users') {
            loadUsers();
        } else if (tab === 'backup') {
            viewBackups();
        }
    });
});

// Pagination state
let currentDocPage = 0;
let documentsPerPage = 50;
let currentDocFilters = {};

// Load documents with optional filters
async function loadDocuments(filters = {}, page = 0) {
    currentDocFilters = filters;
    currentDocPage = page;
    
    const listDiv = document.getElementById('documents-list');
    
    // Show skeleton loading
    listDiv.innerHTML = Array(3).fill(`
        <div class="skeleton-card">
            <div class="skeleton-title"></div>
            <div class="skeleton-text"></div>
            <div class="skeleton-text"></div>
        </div>
    `).join('');
    
    try {
        let endpoint = '/documents/';
        const params = new URLSearchParams();
        
        params.append('skip', page * documentsPerPage);
        params.append('limit', documentsPerPage);
        
        if (filters.created_by) params.append('created_by', filters.created_by);
        if (filters.date_from) params.append('date_from', filters.date_from);
        if (filters.date_to) params.append('date_to', filters.date_to);
        
        if (params.toString()) {
            endpoint += '?' + params.toString();
        }
        
        const documents = await apiCall(endpoint);
        
        if (documents.length === 0) {
            listDiv.innerHTML = '<div class="empty-state"><h3>No documents found</h3><p>No documents match your criteria.</p></div>';
            return;
        }
        
        let html = documents.map(doc => `
            <div class="document-item">
                <div class="document-header">
                    <div style="flex: 1;">
                        <div class="document-number">${doc.document_number}</div>
                        <div style="color: #666; margin-top: 5px;">${doc.title}</div>
                    </div>
                </div>
                <div class="document-meta">
                    <span class="document-created-by">Created by: ${doc.requested_by ? doc.requested_by.username : 'Unknown'}</span>
                </div>
                <div class="document-meta">Created: ${formatLocalDate(doc.created_at)}</div>
                <div class="document-actions">
                    <button class="btn btn-secondary btn-small" onclick="previewDocument(${doc.id})">Preview</button>
                    <button class="btn btn-primary btn-small" onclick="downloadDocument(${doc.id})">Download PDF</button>
                </div>
            </div>
        `).join('');
        
        // Add pagination controls
        html += `
            <div class="pagination">
                <button class="btn btn-secondary" onclick="loadDocuments(currentDocFilters, ${page - 1})" ${page === 0 ? 'disabled' : ''}>Previous</button>
                <span class="page-info">Page ${page + 1}</span>
                <button class="btn btn-secondary" onclick="loadDocuments(currentDocFilters, ${page + 1})" ${documents.length < documentsPerPage ? 'disabled' : ''}>Next</button>
            </div>
        `;
        
        listDiv.innerHTML = html;
    } catch (error) {
        listDiv.innerHTML = `<div class="error">Failed to load documents: ${error.message}</div>`;
    }
}

// Load users for admin filter dropdown
async function loadUsersForFilter() {
    try {
        const users = await apiCall('/users/');
        const filterSelect = document.getElementById('filter-user');
        if (!filterSelect) return;
        filterSelect.innerHTML = '<option value="">-- All Users --</option>';

        users.forEach(user => {
            const option = document.createElement('option');
            option.value = user.id;
            option.textContent = user.username + (user.email ? ` (${user.email})` : '');
            filterSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Failed to load users for filter:', error);
    }
}

// Admin filters
if (document.getElementById('apply-filters-btn')) {
    document.getElementById('apply-filters-btn').addEventListener('click', () => {
        const filters = {
            created_by: document.getElementById('filter-user').value || null,
            date_from: document.getElementById('filter-date-from').value || null,
            date_to: document.getElementById('filter-date-to').value || null,
        };
        loadDocuments(filters);
    });
    
    document.getElementById('clear-filters-btn').addEventListener('click', () => {
        document.getElementById('filter-user').value = '';
        document.getElementById('filter-date-from').value = '';
        document.getElementById('filter-date-to').value = '';
        loadDocuments();
    });
}

// Search documents
document.getElementById('search-btn').addEventListener('click', async () => {
    const query = document.getElementById('search-input').value;
    const listDiv = document.getElementById('documents-list');
    
    if (!query) {
        loadDocuments();
        return;
    }
    
    listDiv.innerHTML = '<div class="loading">Searching...</div>';
    
    try {
        const documents = await apiCall(`/documents/search?title=${encodeURIComponent(query)}`);
        
        if (documents.length === 0) {
            listDiv.innerHTML = '<div class="empty-state"><h3>No documents found</h3><p>Try a different search term.</p></div>';
            return;
        }
        
        listDiv.innerHTML = documents.map(doc => `
            <div class="document-item">
                <div class="document-header">
                    <div>
                        <div class="document-number">${doc.document_number}</div>
                        <div class="document-title">${doc.title}</div>
                    </div>
                </div>
                <div class="document-meta">Template: ${doc.template_name}</div>
                <div class="document-meta">Created: ${formatLocalDate(doc.created_at)}</div>
                <div class="document-actions">
                    <button class="btn btn-secondary btn-small" onclick="previewDocument(${doc.id})">Preview</button>
                    <button class="btn btn-primary btn-small" onclick="downloadDocument(${doc.id})">Download PDF</button>
                </div>
            </div>
        `).join('');
    } catch (error) {
        listDiv.innerHTML = `<div class="error">Search failed: ${error.message}</div>`;
    }
});

// SunEditor - Office-like WYSIWYG editor
let editor = null;

function initializeCKEditor() {
    const textarea = document.getElementById('editor-container');
    if (!textarea) {
        setTimeout(() => initializeCKEditor(), 500);
        return;
    }

    editor = SUNEDITOR.create(textarea, {
        width: '100%',
        height: '400px',
        buttonList: [
            ['undo', 'redo'],
            ['font', 'fontSize', 'formatBlock'],
            ['bold', 'underline', 'italic', 'strike', 'subscript', 'superscript'],
            ['fontColor', 'hiliteColor'],
            ['removeFormat'],
            ['outdent', 'indent'],
            ['align', 'horizontalRule', 'list', 'lineHeight'],
            ['table', 'link', 'image'],
            ['fullScreen', 'showBlocks', 'codeView'],
            ['preview', 'print']
        ],
        font: ['Arial', 'Times New Roman', 'Courier New', 'Georgia', 'Verdana'],
        fontSize: [8, 10, 12, 14, 16, 18, 20, 24, 28, 32],
        defaultStyle: 'font-family: Times New Roman; font-size: 14px;',
        formats: ['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'],
        colorList: [
            ['#ff0000', '#ff5e00', '#ffe400', '#abf200'],
            ['#00d8ff', '#0055ff', '#6600ff', '#ff00dd'],
            ['#000000', '#ffffff', '#7f7f7f', '#bcbcbc']
        ]
    });

    // Update preview on input
    editor.onChange = function(contents) {
        updatePreview();
    };

    console.log('SunEditor ready with table support');
    updatePreview();
}

// Update preview with content and template
function updatePreview() {
    const previewContent = document.getElementById('preview-content');
    if (!previewContent || !editor) return;
    
    const html = editor.getContents();
    const isEmpty = !html || html.trim() === '' || html === '<br>' || html === '<p><br></p>' || html === '<div><br></div>';
    
    if (isEmpty) {
        previewContent.innerHTML = '<p class="preview-placeholder">Start typing to see a live preview...</p>';
    } else {
        previewContent.innerHTML = html;
    }
}

// Create document
document.getElementById('create-document-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const title = document.getElementById('doc-title').value;
    const template_id = document.getElementById('doc-template').value;
    const messageDiv = document.getElementById('create-message');
    
    // Get HTML content from SunEditor
    let content = '';
    if (editor) {
        content = editor.getContents();
        const textarea = document.getElementById('editor-container');
        if (textarea) {
            textarea.value = content;
        }
    }
    
    if (!template_id) {
        messageDiv.className = 'message error';
        messageDiv.textContent = 'Please select a template';
        return;
    }
    
    if (!content.trim()) {
        messageDiv.className = 'message error';
        messageDiv.textContent = 'Please enter document content';
        return;
    }
    
    try {
        const doc = await apiCall('/documents/', {
            method: 'POST',
            body: JSON.stringify({ 
                title, 
                template_id: parseInt(template_id),
                content: content
            }),
        });
        
        messageDiv.className = 'message success';
        messageDiv.textContent = `Document ${doc.document_number} created successfully!`;
        
        // Reset form and editor
        e.target.reset();
        if (editor) {
            editor.setContents('');
        }
        updatePreview();
        
        setTimeout(() => {
            messageDiv.textContent = '';
        }, 5000);
    } catch (error) {
        messageDiv.className = 'message error';
        messageDiv.textContent = `Failed to create document: ${error.message}`;
    }
});

// Template selection change - update preview
if (document.getElementById('doc-template')) {
    document.getElementById('doc-template').addEventListener('change', updatePreview);
}

// Download document
async function downloadDocument(documentId) {
    try {
        const response = await fetch(`${API_BASE}/documents/${documentId}/download`, {
            headers: {
                'Authorization': `Bearer ${token}`,
            },
        });
        
        if (!response.ok) throw new Error('Download failed');
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `document_${documentId}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    } catch (error) {
        alert(`Failed to download document: ${error.message}`);
    }
}

// Preview document
async function previewDocument(documentId) {
    try {
        const doc = await apiCall(`/documents/${documentId}`);

        // Populate document info
        document.getElementById('preview-doc-number').textContent = doc.document_number;
        document.getElementById('preview-doc-title').textContent = doc.title;
        document.getElementById('preview-doc-creator').textContent = doc.requested_by ? doc.requested_by.username : 'Unknown';
        document.getElementById('preview-doc-date').textContent = formatLocalDate(doc.created_at);

        // Load PDF for preview
        const response = await fetch(`${API_BASE}/documents/${documentId}/download`, {
            headers: {
                'Authorization': `Bearer ${token}`,
            },
        });

        if (!response.ok) throw new Error('Failed to load preview');

        const blob = await response.blob();
        if (previewPdfUrl) {
            window.URL.revokeObjectURL(previewPdfUrl);
        }
        previewPdfUrl = window.URL.createObjectURL(blob);
        const previewFrame = document.getElementById('document-preview-frame');
        previewFrame.src = previewPdfUrl;

        // Show modal
        document.getElementById('document-preview-modal').style.display = 'flex';
    } catch (error) {
        alert(`Failed to load document: ${error.message}`);
    }
}

// Close document preview modal
function closeDocumentPreview() {
    document.getElementById('document-preview-modal').style.display = 'none';
    const previewFrame = document.getElementById('document-preview-frame');
    if (previewFrame) {
        previewFrame.src = '';
    }
    if (previewPdfUrl) {
        window.URL.revokeObjectURL(previewPdfUrl);
        previewPdfUrl = null;
    }
}

// Load templates for dropdown
async function loadTemplatesForSelection() {
    try {
        const templates = await apiCall('/templates/');
        const select = document.getElementById('doc-template');
        
        if (select) {
            const currentValue = select.value;
            select.innerHTML = '<option value="">-- Select a Template --</option>';
            
            if (templates.length > 0) {
                templates.forEach(template => {
                    const option = document.createElement('option');
                    option.value = template.id;
                    option.textContent = template.name + (template.description ? ` - ${template.description}` : '');
                    select.appendChild(option);
                });
                
                if (currentValue) {
                    select.value = currentValue;
                }
            } else {
                const option = document.createElement('option');
                option.value = '';
                option.disabled = true;
                option.textContent = '-- No templates available --';
                select.appendChild(option);
            }
        }
    } catch (error) {
        console.error('Failed to load templates for selection:', error);
    }
}

// Load templates
async function loadTemplates() {
    const listDiv = document.getElementById('templates-list');
    listDiv.innerHTML = '<div class="loading">Loading templates...</div>';
    
    try {
        const templates = await apiCall('/templates/');
        
        if (templates.length === 0) {
            listDiv.innerHTML = '<div class="empty-state"><h3>No templates yet</h3><p>Upload your first PDF template.</p></div>';
            return;
        }
        
        listDiv.innerHTML = templates.map(template => `
            <div class="template-item">
                <div class="template-name">${template.name}</div>
                ${template.description ? `<div class="template-description">${template.description}</div>` : ''}
                <div class="template-meta">Created: ${new Date(template.created_at).toLocaleString()}</div>
                <div class="template-actions">
                    <button class="btn btn-danger btn-small" onclick="deleteTemplate(${template.id})">Delete</button>
                </div>
            </div>
        `).join('');
    } catch (error) {
        listDiv.innerHTML = `<div class="error">Failed to load templates: ${error.message}</div>`;
    }
}

// Upload template
if (document.getElementById('upload-template-form')) {
    document.getElementById('upload-template-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const name = document.getElementById('template-name').value;
        const description = document.getElementById('template-description').value;
        const fileInput = document.getElementById('template-file');
        const messageDiv = document.getElementById('upload-message');
        
        if (!fileInput.files.length) {
            messageDiv.className = 'message error';
            messageDiv.textContent = 'Please select a file';
            return;
        }
        
        const formData = new FormData();
        formData.append('name', name);
        formData.append('description', description);
        formData.append('file', fileInput.files[0]);
        
        try {
            const response = await fetch(`${API_BASE}/templates/upload`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
                body: formData,
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Upload failed');
            }
            
            messageDiv.className = 'message success';
            messageDiv.textContent = 'Template uploaded successfully!';
            
            e.target.reset();
            loadTemplates();
            
            setTimeout(() => {
                messageDiv.textContent = '';
            }, 3000);
        } catch (error) {
            messageDiv.className = 'message error';
            messageDiv.textContent = `Upload failed: ${error.message}`;
        }
    });
}

// Delete template
async function deleteTemplate(templateId) {
    if (!confirm('Are you sure you want to delete this template?')) {
        return;
    }
    
    try {
        await apiCall(`/templates/${templateId}`, {
            method: 'DELETE',
        });
        
        loadTemplates();
    } catch (error) {
        alert(`Failed to delete template: ${error.message}`);
    }
}

// Load users
async function loadUsers() {
    const listDiv = document.getElementById('users-list');
    listDiv.innerHTML = '<div class="loading">Loading users...</div>';
    
    try {
        const users = await apiCall('/users/');
        
        if (users.length === 0) {
            listDiv.innerHTML = '<div class="empty-state"><h3>No users yet</h3></div>';
            return;
        }
        
        listDiv.innerHTML = users.map(user => `
            <div class="user-item">
                <div class="user-name">${user.username}</div>
                <div class="user-meta">Email: ${user.email}</div>
                <div class="user-meta">Role: ${user.role}</div>
                <span class="user-status ${user.is_active ? 'active' : 'inactive'}">
                    ${user.is_active ? 'Active' : 'Inactive'}
                </span>
                <div class="user-actions">
                    ${currentUser.id !== user.id ? `
                        <button class="btn btn-secondary btn-small" onclick="toggleUserStatus(${user.id}, ${!user.is_active})">
                            ${user.is_active ? 'Deactivate' : 'Activate'}
                        </button>
                        <button class="btn btn-danger btn-small" onclick="deleteUser(${user.id})">Delete</button>
                    ` : '<span style="color: #999; font-size: 12px;">Current user</span>'}
                </div>
            </div>
        `).join('');
    } catch (error) {
        listDiv.innerHTML = `<div class="error">Failed to load users: ${error.message}</div>`;
    }
}

// Create user
if (document.getElementById('create-user-form')) {
    document.getElementById('create-user-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const username = document.getElementById('new-username').value;
        const email = document.getElementById('new-email').value;
        const password = document.getElementById('new-password').value;
        const role = document.getElementById('new-role').value;
        const messageDiv = document.getElementById('create-user-message');
        
        try {
            await apiCall('/auth/register', {
                method: 'POST',
                body: JSON.stringify({
                    username,
                    email,
                    password,
                    role,
                }),
            });
            
            messageDiv.className = 'message success';
            messageDiv.textContent = 'User created successfully!';
            
            e.target.reset();
            loadUsers();
            
            setTimeout(() => {
                messageDiv.textContent = '';
            }, 3000);
        } catch (error) {
            messageDiv.className = 'message error';
            messageDiv.textContent = `Failed to create user: ${error.message}`;
        }
    });
}

// Toggle user status
async function toggleUserStatus(userId, activate) {
    try {
        await apiCall(`/users/${userId}`, {
            method: 'PUT',
            body: JSON.stringify({
                is_active: activate,
            }),
        });
        
        loadUsers();
    } catch (error) {
        alert(`Failed to update user: ${error.message}`);
    }
}

// Delete user
async function deleteUser(userId) {
    if (!confirm('Are you sure you want to delete this user?')) {
        return;
    }
    
    try {
        await apiCall(`/users/${userId}`, {
            method: 'DELETE',
        });
        
        loadUsers();
    } catch (error) {
        alert(`Failed to delete user: ${error.message}`);
    }
}

// Load audit logs
// Audit log pagination state
let currentAuditPage = 0;
let auditsPerPage = 50;

async function loadAuditLogs(page = 0) {
    currentAuditPage = page;
    const listDiv = document.getElementById('audit-logs-list');
    listDiv.innerHTML = '<div class="loading">Loading audit logs...</div>';
    
    try {
        const logs = await apiCall(`/audit/?skip=${page * auditsPerPage}&limit=${auditsPerPage}`);
        
        if (logs.length === 0 && page === 0) {
            listDiv.innerHTML = '<div class="empty-state"><h3>No audit logs yet</h3></div>';
            return;
        }
        
        let html = logs.map(log => `
            <div class="audit-item">
                <div class="audit-action">${log.action}</div>
                <div class="audit-user">User: ${log.user ? log.user.username : 'Unknown'} (${log.user ? log.user.email : ''})</div>
                ${log.details ? `<div class="audit-details">${log.details}</div>` : ''}
                <div class="audit-time">${formatLocalDate(log.timestamp)}</div>
            </div>
        `).join('');
        
        // Add pagination controls
        html += `
            <div class="pagination">
                <button class="btn btn-secondary" onclick="loadAuditLogs(${page - 1})" ${page === 0 ? 'disabled' : ''}>Previous</button>
                <span class="page-info">Page ${page + 1}</span>
                <button class="btn btn-secondary" onclick="loadAuditLogs(${page + 1})" ${logs.length < auditsPerPage ? 'disabled' : ''}>Next</button>
            </div>
        `;
        
        listDiv.innerHTML = html;
    } catch (error) {
        listDiv.innerHTML = `<div class="error">Failed to load audit logs: ${error.message}</div>`;
    }
}

// Backup Functions
async function backupNow() {
    const msgDiv = document.getElementById('backup-message');
    try {
        msgDiv.className = 'message loading';
        msgDiv.textContent = 'Creating backup...';
        
        const response = await apiCall('/admin/backup/create', {
            method: 'POST'
        });
        
        msgDiv.className = 'message success';
        msgDiv.textContent = `✓ Backup created: ${response.backup_file}`;
        viewBackups();
    } catch (error) {
        msgDiv.className = 'message error';
        msgDiv.textContent = `Failed: ${error.message}`;
    }
}

async function viewBackups() {
    try {
        const response = await apiCall('/admin/backup/list');
        const listDiv = document.getElementById('backups-list');
        
        if (!response.backups || response.backups.length === 0) {
            listDiv.innerHTML = '<p style="color: #666;">No backups found</p>';
            return;
        }
        
        let html = '<div class="card"><h3>Available Backups</h3>';
        html += '<table style="width: 100%; border-collapse: collapse;">';
        html += '<tr style="background: #f5f5f5;"><th style="padding: 10px; text-align: left; border-bottom: 1px solid #ddd;">File</th><th style="padding: 10px; text-align: left; border-bottom: 1px solid #ddd;">Size</th><th style="padding: 10px; text-align: left; border-bottom: 1px solid #ddd;">Date</th><th style="padding: 10px; text-align: center; border-bottom: 1px solid #ddd;">Actions</th></tr>';
        
        response.backups.forEach(backup => {
            const size = (backup.size / (1024*1024)).toFixed(2);
            html += `<tr style="border-bottom: 1px solid #eee;">
                <td style="padding: 10px;">${backup.name}</td>
                <td style="padding: 10px;">${size} MB</td>
                <td style="padding: 10px;">${backup.date}</td>
                <td style="padding: 10px; text-align: center;">
                    <button class="btn btn-secondary btn-small" onclick="downloadBackupFile('${backup.name}')">Download</button>
                    <button class="btn btn-warning btn-small" onclick="confirmRestore('${backup.name}')">Restore</button>
                </td>
            </tr>`;
        });
        
        html += '</table></div>';
        listDiv.innerHTML = html;
    } catch (error) {
        const listDiv = document.getElementById('backups-list');
        listDiv.innerHTML = `<div class="error">Failed to load backups: ${error.message}</div>`;
    }
}

async function downloadBackupFile(backupName) {
    try {
        const response = await fetch(`${API_BASE}/admin/backup/download/${backupName}`, {
            headers: {
                'Authorization': `Bearer ${token}`,
            },
        });
        
        if (!response.ok) throw new Error('Download failed');
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = backupName;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    } catch (error) {
        alert(`Failed to download backup: ${error.message}`);
    }
}

async function confirmRestore(backupName) {
    if (confirm(`⚠️ Restore from ${backupName}? This will overwrite current data.`)) {
        await restoreBackup(backupName);
    }
}

async function restoreBackup(backupName) {
    const msgDiv = document.getElementById('backup-message');
    try {
        msgDiv.className = 'message loading';
        msgDiv.textContent = 'Restoring from backup...';
        
        const response = await apiCall('/admin/backup/restore', {
            method: 'POST',
            body: JSON.stringify({ backup_file: backupName })
        });
        
        msgDiv.className = 'message success';
        msgDiv.textContent = `✓ Restore successful. Reloading...`;
        setTimeout(() => {
            location.reload();
        }, 2000);
    } catch (error) {
        msgDiv.className = 'message error';
        msgDiv.textContent = `Restore failed: ${error.message}`;
    }
}

async function restoreFromFile() {
    alert('Upload backup file feature - create a file input and POST to /admin/backup/restore-upload');
}

// ==================== SYNC FUNCTIONS ====================

async function testSMBConnection() {
    const msgDiv = document.getElementById('smb-test-result');
    try {
        msgDiv.className = 'message loading';
        msgDiv.textContent = 'Testing connection...';
        
        const config = {
            host: document.getElementById('smb-host').value,
            port: parseInt(document.getElementById('smb-port').value),
            username: document.getElementById('smb-username').value,
            password: document.getElementById('smb-password').value,
            share: document.getElementById('smb-share').value,
            path: document.getElementById('smb-path').value
        };
        
        const response = await apiCall('/admin/sync/test-smb', {
            method: 'POST',
            body: JSON.stringify(config)
        });
        
        if (response.success) {
            msgDiv.className = 'message success';
            msgDiv.textContent = `✓ Connected to ${response.share}`;
        } else {
            msgDiv.className = 'message error';
            msgDiv.textContent = `Connection failed: ${response.message}`;
        }
    } catch (error) {
        msgDiv.className = 'message error';
        msgDiv.textContent = `Error: ${error.message}`;
    }
}

async function syncToSMB() {
    const msgDiv = document.getElementById('sync-message');
    try {
        msgDiv.className = 'message loading';
        msgDiv.textContent = 'Syncing to SMB/NAS...';
        
        const config = {
            host: document.getElementById('smb-host').value,
            port: parseInt(document.getElementById('smb-port').value),
            username: document.getElementById('smb-username').value,
            password: document.getElementById('smb-password').value,
            share: document.getElementById('smb-share').value,
            path: document.getElementById('smb-path').value
        };
        
        const syncType = document.querySelector('input[name="sync-type"]:checked').value;
        
        const response = await apiCall('/admin/sync/smb', {
            method: 'POST',
            body: JSON.stringify({
                config: config,
                request: {
                    sync_type: syncType
                }
            })
        });
        
        if (response.success) {
            msgDiv.className = 'message success';
            const details = response.results[syncType === 'all' ? Object.keys(response.results)[0] : syncType];
            const msg = details && details.message ? details.message : JSON.stringify(details);
            msgDiv.innerHTML = `✓ Sync completed<br>${msg}`;
        } else {
            msgDiv.className = 'message error';
            const msg = typeof response.message === 'string' ? response.message : JSON.stringify(response.message);
            msgDiv.textContent = `Sync failed: ${msg}`;
        }
    } catch (error) {
        msgDiv.className = 'message error';
        msgDiv.textContent = `Error: ${error.message || error}`;
    }
}

async function syncToLocal() {
    const msgDiv = document.getElementById('local-sync-message');
    try {
        msgDiv.className = 'message loading';
        msgDiv.textContent = 'Syncing to local directory...';
        
        const targetPath = document.getElementById('local-sync-path').value;
        if (!targetPath) {
            msgDiv.className = 'message error';
            msgDiv.textContent = 'Please enter a target directory path';
            return;
        }
        
        const syncType = document.querySelector('input[name="local-sync-type"]:checked').value;
        
        const response = await apiCall('/admin/sync/local', {
            method: 'POST',
            body: JSON.stringify({
                request: {
                    sync_type: syncType,
                    target: targetPath
                }
            })
        });
        
        if (response.success) {
            msgDiv.className = 'message success';
            const details = response.results[syncType === 'all' ? Object.keys(response.results)[0] : syncType];
            const msg = details && details.message ? details.message : JSON.stringify(details);
            msgDiv.innerHTML = `✓ Local sync completed<br>${msg}`;
        } else {
            msgDiv.className = 'message error';
            const msg = typeof response.message === 'string' ? response.message : JSON.stringify(response.message);
            msgDiv.textContent = `Sync failed: ${msg}`;
        }
    } catch (error) {
        msgDiv.className = 'message error';
        msgDiv.textContent = `Error: ${error.message || error}`;
    }
}

async function testNextcloudConnection() {
    const msgDiv = document.getElementById('nextcloud-test-result');
    try {
        msgDiv.className = 'message loading';
        msgDiv.textContent = 'Testing connection...';
        
        const config = {
            url: document.getElementById('nextcloud-url').value,
            username: document.getElementById('nextcloud-username').value,
            password: document.getElementById('nextcloud-password').value,
            path: document.getElementById('nextcloud-path').value
        };
        
        const response = await apiCall('/admin/sync/test-nextcloud', {
            method: 'POST',
            body: JSON.stringify(config)
        });
        
        if (response.success) {
            msgDiv.className = 'message success';
            msgDiv.textContent = `✓ Connected to Nextcloud: ${response.username}@${response.url}`;
        } else {
            msgDiv.className = 'message error';
            msgDiv.textContent = `Connection failed: ${response.message}`;
        }
    } catch (error) {
        msgDiv.className = 'message error';
        msgDiv.textContent = `Error: ${error.message}`;
    }
}

async function syncToNextcloud() {
    const msgDiv = document.getElementById('nextcloud-sync-message');
    try {
        msgDiv.className = 'message loading';
        msgDiv.textContent = 'Syncing to Nextcloud...';
        
        const config = {
            url: document.getElementById('nextcloud-url').value,
            username: document.getElementById('nextcloud-username').value,
            password: document.getElementById('nextcloud-password').value,
            path: document.getElementById('nextcloud-path').value
        };
        
        const syncType = document.querySelector('input[name="nextcloud-sync-type"]:checked').value;
        
        const response = await apiCall('/admin/sync/nextcloud', {
            method: 'POST',
            body: JSON.stringify({
                config: config,
                request: {
                    sync_type: syncType
                }
            })
        });
        
        if (response.success) {
            msgDiv.className = 'message success';
            const details = response.results[syncType === 'all' ? Object.keys(response.results)[0] : syncType];
            const msg = details && details.message ? details.message : JSON.stringify(details);
            msgDiv.innerHTML = `✓ Nextcloud sync completed<br>${msg}`;
        } else {
            msgDiv.className = 'message error';
            const msg = typeof response.message === 'string' ? response.message : JSON.stringify(response.message);
            msgDiv.textContent = `Sync failed: ${msg}`;
        }
    } catch (error) {
        msgDiv.className = 'message error';
        msgDiv.textContent = `Error: ${error.message || error}`;
    }
}

// Initialize
if (token) {
    loadCurrentUser().then(() => {
        showApp();
    });
} else {
    showLogin();
}
