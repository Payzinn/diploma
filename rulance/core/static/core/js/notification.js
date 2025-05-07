import WSManager from './websocket.js';

function showPopup(message, type = 'success') {
  const notification = document.getElementById('notification');
  notification.textContent = message;
  notification.className = 'notification ' + type;
  notification.style.right = '20px';
  setTimeout(() => {
    notification.style.right = '-300px';
  }, 3000);
}

function updateSeparators(list) {
  list.querySelectorAll('hr').forEach(hr => hr.remove());
  const items = list.querySelectorAll('li.notification-item');
  items.forEach((item, index) => {
    if (index < items.length - 1) {
      item.after(document.createElement('hr'));
    }
  });
}

document.addEventListener('DOMContentLoaded', () => {
  const params = new URLSearchParams(window.location.search);
  if (params.get('status') === 'success') {
    showPopup('Заказ успешно размещён!', 'success');
  } else if (params.get('status') === 'error' && params.get('message')) {
    showPopup(`Ошибка: ${params.get('message')}`, 'error');
  }

  const chatPage = document.getElementById('chat-page');
  const currentChatId = chatPage?.dataset.chatId;

  const toggle   = document.getElementById('notif-toggle');
  const dropdown = document.querySelector('.dropdown--notif');
  const badge    = document.getElementById('notif-badge');
  const list     = document.getElementById('notif-list');

  const initialUnreadCount = parseInt(badge.textContent) || 0;
  badge.textContent = initialUnreadCount > 0 ? initialUnreadCount : '';
  badge.style.display = initialUnreadCount > 0 ? '' : 'none';

  toggle.addEventListener('click', () => {
    dropdown.classList.toggle('open');
  });

  const WS_URL = '/ws/notifications/';
  WSManager.connect(
    WS_URL,
    () => WSManager.attachMessageHandler(WS_URL, 'notif_message'),
    null,
    null
  );

  WSManager.registerHandler('notif_message', data => {
    if (currentChatId && data.link.includes(`/chat/${currentChatId}/`)) {
      console.log(`Auto-marking notification ${data.id} as read (in chat ${currentChatId})`);
      fetch(`/notifications/mark_read/${data.id}/`, {
        method: 'POST',
        headers: { 'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value }
      }).catch(err => console.error('Error auto-marking notification:', err));
      return;
    }

    showPopup(data.verb, 'success');

    const li = document.createElement('li');
    li.className = 'notification-item notification-item--new';
    li.dataset.id = data.id;
    li.innerHTML = `
      <a href="${data.link}" class="notification-link profile__link">
        ${data.verb}
        <small class="notification-time">${data.created_at}</small>
      </a>
      <button class="notification-delete" data-id="${data.id}">×</button>`;
    const empty = list.querySelector('.notification-empty');
    if (empty) empty.remove();
    list.prepend(li);
    updateSeparators(list);

    let count = parseInt(badge.textContent) || 0;
    badge.textContent = ++count;
    badge.style.display = '';
  });

  list.addEventListener('click', e => {
    const a = e.target.closest('a.notification-link');
    if (a) {
      e.preventDefault();
      e.stopPropagation();
      const li = a.closest('li.notification-item');
      const id = li.dataset.id;
      console.log(`Marking notification ${id} as read`);
      const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
      if (!csrfToken) {
        console.error('CSRF token not found');
        li.remove();
        updateSeparators(list);
        let cnt = parseInt(badge.textContent) || 0;
        let newCnt = cnt > 0 ? cnt - 1 : 0;
        badge.textContent = newCnt > 0 ? newCnt : '';
        badge.style.display = newCnt > 0 ? '' : 'none';
        if (!list.querySelector('li.notification-item')) {
          list.innerHTML = '<li class="notification-empty">У вас пока нет уведомлений.</li>';
        }
        setTimeout(() => window.location = a.href, 100);
        return;
      }
      fetch(`/notifications/mark_read/${id}/`, {
        method: 'POST',
        headers: {
          'X-CSRFToken': csrfToken,
          'Content-Type': 'application/json'
        }
      }).then(response => {
        if (!response.ok) throw new Error(`HTTP error ${response.status}`);
        console.log(`Notification ${id} marked as read`);
        li.remove();
        updateSeparators(list);
        let cnt = parseInt(badge.textContent) || 0;
        let newCnt = cnt > 0 ? cnt - 1 : 0;
        badge.textContent = newCnt > 0 ? newCnt : '';
        badge.style.display = newCnt > 0 ? '' : 'none';
        if (!list.querySelector('li.notification-item')) {
          list.innerHTML = '<li class="notification-empty">У вас пока нет уведомлений.</li>';
        }
        setTimeout(() => window.location = a.href, 100);
      }).catch(err => {
        console.error('Error marking notification as read:', err);
        li.remove();
        updateSeparators(list);
        let cnt = parseInt(badge.textContent) || 0;
        let newCnt = cnt > 0 ? cnt - 1 : 0;
        badge.textContent = newCnt > 0 ? newCnt : '';
        badge.style.display = newCnt > 0 ? '' : 'none';
        if (!list.querySelector('li.notification-item')) {
          list.innerHTML = '<li class="notification-empty">У вас пока нет уведомлений.</li>';
        }
        setTimeout(() => window.location = a.href, 100);
      });
      return;
    }

    if (e.target.classList.contains('notification-delete')) {
      const id = e.target.dataset.id;
      console.log(`Deleting notification ${id}`);
      const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
      if (!csrfToken) {
        console.error('CSRF token not found');
        return;
      }
      fetch(`/notifications/delete/${id}/`, {
        method: 'POST',
        headers: {
          'X-CSRFToken': csrfToken,
          'Content-Type': 'application/json'
        }
      }).then(response => {
        if (!response.ok) throw new Error(`HTTP error ${response.status}`);
        console.log(`Notification ${id} deleted`);
        const li = e.target.closest('li.notification-item');
        li.remove();
        updateSeparators(list);
        let cnt = parseInt(badge.textContent) || 0;
        let newCnt = cnt > 0 ? cnt - 1 : 0;
        badge.textContent = newCnt > 0 ? newCnt : '';
        badge.style.display = newCnt > 0 ? '' : 'none';
        if (!list.querySelector('li.notification-item')) {
          list.innerHTML = '<li class="notification-empty">У вас пока нет уведомлений.</li>';
        }
      }).catch(err => console.error('Error deleting notification:', err));
    }
  });

  updateSeparators(list);
});