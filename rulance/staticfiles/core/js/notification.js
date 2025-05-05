import WSManager from './websocket.js';

function showNotification(message, type='success') {
  const notification = document.getElementById('notification');
  notification.textContent = message;
  notification.className = 'notification ' + type;
  notification.style.right = '20px';
  setTimeout(() => {
    notification.style.right = '-300px';
  }, 3000);
}

document.addEventListener('DOMContentLoaded', () => {
  const toggle   = document.getElementById('notif-toggle');
  const dropdown = document.querySelector('.dropdown--notif');
  const badge    = document.getElementById('notif-badge');
  const list     = document.getElementById('notif-list');

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
    showNotification(data.verb, 'success');

    const li = document.createElement('li');
    li.className = 'notification-item notification-item--new';
    li.dataset.id = data.id;
    li.innerHTML = `
      <a href="${data.link}" class="notification-link">
        ${data.verb}
        <small class="notification-time">${data.created_at}</small>
      </a>`;
    const empty = list.querySelector('.notification-empty');
    if (empty) empty.remove();
    list.prepend(li);

    let count = parseInt(badge.textContent) || 0;
    badge.textContent = ++count;
    badge.style.display = '';
  });

  list.addEventListener('click', e => {
    const a = e.target.closest('a.notification-link');
    if (!a) return;
    e.preventDefault();
    const li = a.closest('li.notification-item');
    const id = li.dataset.id;
    fetch(`/notifications/mark_read/${id}/`, {
      method: 'POST',
      headers: { 'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value }
    }).then(() => {
      li.classList.remove('notification-item--new');
      let count = parseInt(badge.textContent) || 1;
      badge.textContent = count > 1 ? count - 1 : '';
      if (count <= 1) badge.style.display = 'none';
      window.location = a.href;
    });
  });
});
