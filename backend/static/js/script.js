function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('-translate-x-full');
}

window.uiConfirm = function(title, message, onConfirm) {
    const container = document.getElementById('modal-container');
    container.innerHTML = `
        <div class="bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden transform transition-all animate-scale-in">
            <div class="p-6">
                <div class="flex items-center justify-center w-12 h-12 mx-auto bg-red-100 rounded-full mb-4">
                    <i class="fas fa-exclamation-triangle text-red-600"></i>
                </div>
                <h3 class="text-lg font-bold text-center text-slate-900">${title}</h3>
                <p class="mt-2 text-sm text-center text-slate-500">${message}</p>
            </div>
            <div class="flex border-t border-slate-100">
                <button onclick="closeModal()" class="flex-1 px-4 py-3 text-sm font-medium text-slate-600 hover:bg-slate-50 border-r border-slate-100 transition-colors">取消</button>
                <button id="confirm-btn" class="flex-1 px-4 py-3 text-sm font-medium text-red-600 hover:bg-red-50 transition-colors">确认删除</button>
            </div>
        </div>
    `;
    container.classList.remove('hidden');
    document.getElementById('confirm-btn').onclick = function() {
        onConfirm();
        closeModal();
    };
};

window.closeModal = function() {
    document.getElementById('modal-container').classList.add('hidden');
};

document.querySelectorAll('.btn-primary').forEach(btn => {
    btn.classList.add('px-4', 'py-2', 'bg-primary', 'text-white', 'rounded-lg', 'hover:bg-opacity-90', 'transition-all', 'duration-300');
});

class NotificationManager {
    constructor() {
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 3;
        this.reconnectDelay = 5000;
        this.currentFilter = '';
        this.notifications = [];
        this.unreadCount = 0;
        
        this.init();
    }

    init() {
        const isAuthenticated = document.getElementById('notification-btn');
        if (!isAuthenticated) return;

        this.connectWebSocket();
        this.bindEvents();
        this.loadNotifications();
    }

    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/notifications/`;
        
        try {
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = () => {
                console.log('WebSocket 连接已建立');
                this.reconnectAttempts = 0;
            };

            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleWebSocketMessage(data);
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket 错误:', error);
            };

            this.ws.onclose = () => {
                console.log('WebSocket 连接已关闭');
                this.attemptReconnect();
            };
        } catch (error) {
            console.error('WebSocket 连接失败:', error);
            this.attemptReconnect();
        }
    }

    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`尝试重新连接 (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
            setTimeout(() => this.connectWebSocket(), this.reconnectDelay);
        } else {
            console.log('已达到最大重连次数，请刷新页面重试');
        }
    }

    handleWebSocketMessage(data) {
        if (data.type === 'unread_count') {
            this.updateUnreadBadge(data.count);
        } else if (data.type === 'notification') {
            this.showToast(data.notification);
            this.notifications.unshift(data.notification);
            this.renderNotifications();
            this.updateUnreadBadge(this.unreadCount + 1);
        }
    }

    showToast(notification) {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        
        const typeColors = {
            'borrow_audit': 'bg-blue-500',
            'due_reminder': 'bg-amber-500',
            'system_announcement': 'bg-purple-500',
            'transfer_notice': 'bg-green-500'
        };

        const typeIcons = {
            'borrow_audit': 'fa-check-circle',
            'due_reminder': 'fa-clock',
            'system_announcement': 'fa-bullhorn',
            'transfer_notice': 'fa-exchange-alt'
        };

        toast.className = `bg-white rounded-xl shadow-lg border-l-4 ${typeColors[notification.type] || 'bg-blue-500'} p-4 transform transition-all duration-300 translate-x-full opacity-0 pointer-events-auto`;
        toast.innerHTML = `
            <div class="flex items-start">
                <div class="flex-shrink-0">
                    <i class="fas ${typeIcons[notification.type] || 'fa-bell'} text-${notification.type === 'due_reminder' ? 'amber' : 'blue'}-500 text-xl"></i>
                </div>
                <div class="ml-3 flex-1">
                    <p class="text-sm font-semibold text-slate-800">${notification.title}</p>
                    <p class="text-sm text-slate-600 mt-1">${notification.content}</p>
                </div>
                <button class="ml-4 text-slate-400 hover:text-slate-600 transition-colors" onclick="this.parentElement.parentElement.remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;

        container.appendChild(toast);

        requestAnimationFrame(() => {
            toast.classList.remove('translate-x-full', 'opacity-0');
        });

        setTimeout(() => {
            toast.classList.add('translate-x-full', 'opacity-0');
            setTimeout(() => toast.remove(), 300);
        }, 5000);
    }

    updateUnreadBadge(count) {
        this.unreadCount = count;
        const badge = document.getElementById('unread-badge');
        if (badge) {
            if (count > 0) {
                badge.textContent = count > 99 ? '99+' : count;
                badge.classList.remove('hidden');
            } else {
                badge.classList.add('hidden');
            }
        }
    }

    bindEvents() {
        const notificationBtn = document.getElementById('notification-btn');
        const closeBtn = document.getElementById('close-notification-btn');
        const overlay = document.getElementById('notification-overlay');
        const markAllReadBtn = document.getElementById('mark-all-read-btn');
        const filterBtns = document.querySelectorAll('.notification-filter-btn');

        if (notificationBtn) {
            notificationBtn.addEventListener('click', () => this.openPanel());
        }
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.closePanel());
        }
        if (overlay) {
            overlay.addEventListener('click', () => this.closePanel());
        }
        if (markAllReadBtn) {
            markAllReadBtn.addEventListener('click', () => this.markAllAsRead());
        }
        filterBtns.forEach(btn => {
            btn.addEventListener('click', (e) => this.setFilter(e.target.dataset.type));
        });
    }

    openPanel() {
        const panel = document.getElementById('notification-panel');
        const overlay = document.getElementById('notification-overlay');
        panel.classList.remove('translate-x-full');
        overlay.classList.remove('hidden');
        this.loadNotifications();
    }

    closePanel() {
        const panel = document.getElementById('notification-panel');
        const overlay = document.getElementById('notification-overlay');
        panel.classList.add('translate-x-full');
        overlay.classList.add('hidden');
    }

    setFilter(type) {
        this.currentFilter = type;
        document.querySelectorAll('.notification-filter-btn').forEach(btn => {
            if (btn.dataset.type === type) {
                btn.className = 'notification-filter-btn px-3 py-1.5 text-sm rounded-full bg-primary text-white';
            } else {
                btn.className = 'notification-filter-btn px-3 py-1.5 text-sm rounded-full bg-slate-100 text-slate-600 hover:bg-slate-200 transition-colors';
            }
        });
        this.renderNotifications();
    }

    async loadNotifications() {
        try {
            const response = await fetch(`/notifications/list/?type=${this.currentFilter}`);
            const data = await response.json();
            this.notifications = data.notifications;
            this.unreadCount = data.unread_count;
            this.updateUnreadBadge(this.unreadCount);
            this.renderNotifications();
        } catch (error) {
            console.error('加载通知失败:', error);
        }
    }

    renderNotifications() {
        const list = document.getElementById('notification-list');
        if (!list) return;

        const filtered = this.currentFilter 
            ? this.notifications.filter(n => n.type === this.currentFilter)
            : this.notifications;

        if (filtered.length === 0) {
            list.innerHTML = `
                <div class="flex flex-col items-center justify-center h-32 text-slate-400">
                    <i class="fas fa-inbox text-3xl mb-2"></i>
                    <span>暂无通知</span>
                </div>
            `;
            return;
        }

        const typeColors = {
            'borrow_audit': 'text-blue-500 bg-blue-50',
            'due_reminder': 'text-amber-500 bg-amber-50',
            'system_announcement': 'text-purple-500 bg-purple-50',
            'transfer_notice': 'text-green-500 bg-green-50'
        };

        list.innerHTML = filtered.map(n => `
            <div class="notification-item p-4 rounded-xl border ${n.is_read ? 'bg-slate-50 border-slate-200' : 'bg-white border-primary/20 shadow-sm'} cursor-pointer hover:shadow-md transition-all duration-200" data-id="${n.id}">
                <div class="flex items-start">
                    <div class="flex-shrink-0 w-10 h-10 rounded-full ${typeColors[n.type] || 'bg-blue-50 text-blue-500'} flex items-center justify-center">
                        <i class="fas fa-bell"></i>
                    </div>
                    <div class="ml-3 flex-1 min-w-0">
                        <div class="flex items-center justify-between">
                            <span class="text-xs font-medium ${n.is_read ? 'text-slate-400' : 'text-primary'}">${n.type_display}</span>
                            ${!n.is_read ? '<span class="w-2 h-2 bg-primary rounded-full"></span>' : ''}
                        </div>
                        <h4 class="text-sm font-semibold text-slate-800 mt-1 truncate">${n.title}</h4>
                        <p class="text-sm text-slate-600 mt-1 line-clamp-2">${n.content}</p>
                        <p class="text-xs text-slate-400 mt-2">${n.created_at}</p>
                    </div>
                </div>
            </div>
        `).join('');

        list.querySelectorAll('.notification-item').forEach(item => {
            item.addEventListener('click', () => {
                const id = item.dataset.id;
                this.markAsRead(id);
            });
        });
    }

    async markAsRead(id) {
        try {
            const response = await fetch(`/notifications/${id}/read/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken()
                }
            });
            const data = await response.json();
            if (data.success) {
                const notification = this.notifications.find(n => n.id === parseInt(id));
                if (notification) {
                    notification.is_read = true;
                }
                this.updateUnreadBadge(data.unread_count);
                this.renderNotifications();
            }
        } catch (error) {
            console.error('标记已读失败:', error);
        }
    }

    async markAllAsRead() {
        try {
            const response = await fetch('/notifications/read-all/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken()
                }
            });
            const data = await response.json();
            if (data.success) {
                this.notifications.forEach(n => n.is_read = true);
                this.updateUnreadBadge(0);
                this.renderNotifications();
            }
        } catch (error) {
            console.error('全部已读失败:', error);
        }
    }

    getCSRFToken() {
        const cookie = document.cookie.split(';').find(c => c.trim().startsWith('csrftoken='));
        return cookie ? cookie.split('=')[1] : '';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('notification-btn')) {
        window.notificationManager = new NotificationManager();
    }
});
