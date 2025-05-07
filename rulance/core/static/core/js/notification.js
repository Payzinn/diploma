import WSManager from './websocket.js';

function showPopup(message, type = 'success') {
  const notification = document.getElementById('notification');
  notification.textContent = message;
  notification.className = 'notification ' + type;
  notification.style.right = '20px';
  setTimeout(() => notification.style.right = '-300px', 3000);
}

async function markRead(id) {
  await fetch(`/notifications/mark_read/${id}/`, {
    method: 'POST',
    headers: { 'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value }
  });
}

document.addEventListener('DOMContentLoaded', () => {
  const params = new URLSearchParams(location.search);
  if (params.get('status') === 'success') showPopup('Заказ успешно размещён!');
  else if (params.get('status') === 'error' && params.get('message'))
    showPopup(`Ошибка: ${params.get('message')}`, 'error');

  const chatPage = document.getElementById('chat-page');
  const currentChatId = chatPage?.dataset.chatId;

  const toggle   = document.getElementById('notif-toggle');
  const dropdown = document.querySelector('.dropdown--notif');
  const badge    = document.getElementById('notif-badge');
  const list     = document.getElementById('notif-list');

  function updateBadge(delta) {
    let cnt = parseInt(badge.textContent) || 0;
    cnt = Math.max(0, cnt + delta);
    badge.textContent = cnt > 0 ? cnt : '';
    badge.style.display = cnt > 0 ? '' : 'none';
  }

  toggle.addEventListener('click', async () => {
    dropdown.classList.toggle('open');
    if (dropdown.classList.contains('open')) {
      const unread = Array.from(list.querySelectorAll('li.notification-item--new'));
      for (const li of unread) {
        const id = li.dataset.id;
        await markRead(id);
        li.classList.remove('notification-item--new');
      }
      updateBadge(-unread.length);
    }
  });

  function injectCloseButtons() {
    list.querySelectorAll('li.notification-item').forEach(li => {
      if (!li.querySelector('.notif-close')) {
        const btn = document.createElement('button');
        btn.className = 'notif-close';
        btn.textContent = '×';
        li.appendChild(btn);
      }
    });
  }
  injectCloseButtons();

  WSManager.connect('/ws/notifications/',
    () => WSManager.attachMessageHandler('/ws/notifications/', 'notif_message'),
    null, null
  );
  WSManager.registerHandler('notif_message', data => {
    if (currentChatId && data.link.includes(`/chat/${currentChatId}/`)) {
      markRead(data.id);
      return;
    }

    showPopup(data.verb);

    const li = document.createElement('li');
    li.className = 'notification-item notification-item--new';
    li.dataset.id = data.id;
    li.innerHTML = `
      <a href="${data.link}" class="notification-link">
        ${data.verb}
        <small class="notification-time">${data.created_at}</small>
      </a>`;
    list.prepend(li);
    injectCloseButtons();
    updateBadge(+1);
  });

  list.addEventListener('click', async e => {
    if (e.target.matches('.notif-close')) {
      const li = e.target.closest('li.notification-item');
      const id = li.dataset.id;
      await markRead(id);
      li.remove();
      updateBadge(-1);
      return;
    }
    const a = e.target.closest('a.notification-link');
    if (!a) return;
    e.preventDefault();
    const li = a.closest('li.notification-item');
    const id = li.dataset.id;
    await markRead(id);
    li.remove();
    updateBadge(-1);
    setTimeout(() => window.location = a.href, 100);
  });
});
