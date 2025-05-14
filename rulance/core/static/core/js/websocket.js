class WebSocketManager {
    constructor() {
        this.connections = new Map();
        this.handlers = new Map();
    }

    connect(url, onOpen, onError, onClose) {
        if (this.connections.has(url)) {
            console.log(`WebSocket для ${url} уже открыт`);
            return this.connections.get(url);
        }

        const wsScheme = location.protocol === 'https:' ? 'wss' : 'ws';
        const socket = new WebSocket(`${wsScheme}://${location.host}${url}`);

        socket.onopen = () => {
            console.log(`[WebSocket] Подключено к ${url}`);
            if (onOpen) onOpen(socket);
        };

        socket.onerror = (e) => {
            console.error(`[WebSocket] Ошибка на ${url}:`, e);
            if (onError) onError(e);
        };

        socket.onclose = (e) => {
            console.warn(`[WebSocket] Закрыто ${url}:`, e);
            this.connections.delete(url);
            if (onClose) onClose(e);
        };

        this.connections.set(url, socket);
        return socket;
    }

    registerHandler(group, callback) {
        this.handlers.set(group, callback);
    }

    send(url, data) {
        const socket = this.connections.get(url);
        if (socket && socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify(data));
        } else {
            console.error(`[WebSocket] Соединение ${url} не открыто`);
        }
    }

    attachMessageHandler(url, group) {
    const socket = this.connections.get(url);
    if (!socket) return;

    socket.onmessage = (e) => {
        let data;
        try {
        data = JSON.parse(e.data);
        } catch (err) {
        console.error(`[WebSocket] Ошибка парсинга на ${url}:`, err);
        return;
        }
        const handler = this.handlers.get(group);
        if (handler) {
        handler(data);
        } else {
        console.warn(`[WebSocket] Нет обработчика для группы ${group}`, data);
        }
    };
    }
    disconnect(url) {
        const socket = this.connections.get(url);
        if (socket) {
            socket.close();
            this.connections.delete(url);
            console.log(`[WebSocket] Соединение ${url} закрыто`);
        }
    }

    isConnected(url) {
        const socket = this.connections.get(url);
        return socket && socket.readyState === WebSocket.OPEN;
    }
}

const wsManager = new WebSocketManager();

wsManager.registerHandler('profile', (data) => {
    console.log('[WebSocket] Обновление профиля:', data);
    const { tab, count } = data;
    if (tab === 'balance') {
        const balanceElement = document.getElementById('balance-amount');
        if (balanceElement) {
            balanceElement.textContent = `${parseFloat(count).toFixed(2)} RUB`;
        }
    } else {
        const badge = document.querySelector(`.profile__badge[data-tab="${tab}"]`);
        if (badge) {
            badge.textContent = count;
        }
    }
});

if (document.body.dataset.authenticated === 'true') {
    wsManager.connect(
        '/ws/profile/',
        (socket) => console.log('[WebSocket] Профиль подключён'),
        (error) => console.error('[WebSocket] Ошибка профиля:', error),
        (event) => console.warn('[WebSocket] Профиль закрыт:', event)
    );
    wsManager.attachMessageHandler('/ws/profile/', 'profile');
}

export default wsManager;