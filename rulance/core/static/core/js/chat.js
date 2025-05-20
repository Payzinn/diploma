import WSManager from './websocket.js';

document.addEventListener('DOMContentLoaded', () => {
  const chatWindow = document.getElementById('chat-window');
  if (!chatWindow) return;

  const chatId = chatWindow.dataset.chatId;
  const CURRENT_USER_ID = parseInt(chatWindow.dataset.currentUserId, 10);
  const FREELANCER_ID   = parseInt(chatWindow.dataset.freelancerId, 10);

  let lastDate = null;
  const lastMsg = chatWindow.querySelector('[data-date]:last-of-type');
  if (lastMsg) lastDate = lastMsg.dataset.date;

  const wsUrl    = `/ws/chat/${chatId}/`;
  const groupName = `chat_${chatId}`;

  function escapeHTML(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  WSManager.registerHandler(groupName, data => {
    if (data.type === 'chat.update') {
      const actionsDiv = document.querySelector('.chat__actions');
      if (actionsDiv && data.status !== 'InWork') {
        actionsDiv.style.display = 'none';
      }
      return;
    }

    if (data.date !== lastDate) {
      const sep = document.createElement('div');
      sep.className = 'chat__date-separator';
      sep.textContent = data.date_readable || new Date(data.date).toLocaleDateString('ru-RU');
      chatWindow.appendChild(sep);
      lastDate = data.date;
    }

    if (data.is_system) {
      const sysEl = document.createElement('div');
      sysEl.className = 'chat__message chat__message--system';
      sysEl.dataset.date = data.date;

      let inner = `<div class="chat__body chat__body--system"><p>${escapeHTML(data.message)}</p>`;

      if ((data.message_type === 'cancel_request' || data.message_type === 'complete_request') &&
          CURRENT_USER_ID === FREELANCER_ID &&
          !data.extra_data?.response) {
        const action = data.message_type === 'cancel_request' ? 'cancel_response' : 'complete_response';
        inner += `
          <div class="chat__system-buttons">
            <button data-action="${action}" data-response="yes" class="button-small">Согласен</button>
            <button data-action="${action}" data-response="no" class="button-small button-small--danger">Не согласен</button>
          </div>`;
      }

      inner += '</div>';
      sysEl.innerHTML = inner;
      chatWindow.appendChild(sysEl);

      if (data.message_type === 'cancel_response' || data.message_type === 'complete_response') {
        const lastBtns = chatWindow.querySelector('.chat__system-buttons');
        if (lastBtns) lastBtns.remove();

        if (data.extra_data?.response === 'yes') {
          const form = document.getElementById('chat-form');
          if (form) {
            form.outerHTML = '<p class="chat__form">Чат завершён, отправка сообщений невозможна.</p>';
          }
          const actionsDiv = document.querySelector('.chat__actions');
          if (actionsDiv) {
            actionsDiv.style.display = 'none';
          }
        }
      }
    } else {
      const msgEl = document.createElement('div');
      msgEl.className = `chat__message ${data.sender_id === CURRENT_USER_ID ? 'chat__message--self' : ''}`;
      msgEl.dataset.date = data.date;

      let html = '';
      if (data.sender_id !== CURRENT_USER_ID) {
        html += `<img src="${escapeHTML(data.avatar_url)}" class="chat__avatar" alt="${escapeHTML(data.sender_full_name)}">`;
      }
      html += `
        <div class="chat__body">
          <strong>
            <a href="/profile/${data.sender_id}/" class="profile__link">
              ${escapeHTML(data.sender_full_name)}
            </a>
          </strong>
          <p>${escapeHTML(data.message)}</p>
          <small class="chat__time">${escapeHTML(data.time)}</small>
        </div>`;

      msgEl.innerHTML = html;
      chatWindow.appendChild(msgEl);
    }

    chatWindow.scrollTop = chatWindow.scrollHeight;
  });

  WSManager.connect(wsUrl,
    () => {
      console.log(`[chat] WebSocket подключён к ${wsUrl}`);
      WSManager.attachMessageHandler(wsUrl, groupName);
    },
    e => console.error(`[chat] WebSocket ошибка:`, e),
    e => console.warn(`[chat] WebSocket закрыт:`, e)
  );

  document.getElementById('chat-form')?.addEventListener('submit', e => {
    e.preventDefault();
    const input = document.getElementById('chat-input');
    const text = input.value.trim();
    if (!text) return;
    WSManager.send(wsUrl, { action: 'message', message: text });
    input.value = '';
  });

  document.querySelectorAll('.js-confirm-action').forEach(el => {
    el.addEventListener('click', e => {
      e.preventDefault();
      e.stopPropagation();
      const message = el.dataset.confirmMessage;
      const action  = el.dataset.action;

      const modal = document.getElementById('confirm-modal');
      const content = modal.querySelector('.modal-content');
      content.innerHTML = `
        <p id="confirm-modal-message">${message}</p>
        <div class="modal__buttons">
          <button id="confirm-yes" class="button-small">Да</button>
          <button id="confirm-no" class="button-small button-small--danger">Нет</button>
        </div>
      `;
      modal.classList.add('modal--show');

      const yes = document.getElementById('confirm-yes');
      const no  = document.getElementById('confirm-no');

      yes.onclick = () => {
        if (action === 'cancel_request') {
          content.innerHTML = `
            <p>Укажите причину отмены:</p>
            <textarea id="cancel-reason" rows="4" style="width:100%;" placeholder="Введите причину..."></textarea>
            <div class="modal__buttons">
              <button id="reason-submit" class="button-small">Отправить</button>
              <button id="reason-cancel" class="button-small button-small--danger">Отмена</button>
            </div>
          `;
          const submit = document.getElementById('reason-submit');
          const cancel = document.getElementById('reason-cancel');
          const textarea = document.getElementById('cancel-reason');

          submit.onclick = () => {
            const reason = textarea.value.trim();
            if (reason) {
              WSManager.send(wsUrl, { action, reason });
              modal.classList.remove('modal--show');
            } else {
              alert('Пожалуйста, укажите причину отмены.');
            }
          };
          cancel.onclick = () => modal.classList.remove('modal--show');
        } else {
          WSManager.send(wsUrl, { action });
          modal.classList.remove('modal--show');
        }
      };
      no.onclick = () => modal.classList.remove('modal--show');
      modal.onclick = ev => { if (ev.target === modal) modal.classList.remove('modal--show'); };
    });
  });

  chatWindow.addEventListener('click', e => {
    const btn = e.target.closest('.chat__system-buttons button');
    if (!btn) return;
    const action   = btn.dataset.action;
    const response = btn.dataset.response;
    WSManager.send(wsUrl, { action, response });
    btn.parentNode.remove();
  });
});