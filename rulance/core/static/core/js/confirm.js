document.addEventListener('DOMContentLoaded', () => {
  const modal     = document.getElementById('confirm-modal');
  const msgEl     = document.getElementById('confirm-modal-message');
  const btnYes    = document.getElementById('confirm-yes');
  const btnNo     = document.getElementById('confirm-no');
  let   targetAction = null; 

  function openConfirm(message, action) {
      msgEl.textContent = message;
      targetAction = action;
      modal.classList.add('modal--show');
  }

  function closeConfirm() {
      modal.classList.remove('modal--show');
      targetAction = null;
  }

  document.querySelectorAll('.js-confirm-action').forEach(el => {
      el.addEventListener('click', e => {
          e.preventDefault();
          const form = el.closest('form');
          if (form) {
              openConfirm(el.dataset.confirmMessage, { type: 'form', element: form });
          } else if (el.href) {
              openConfirm(el.dataset.confirmMessage, { type: 'link', href: el.href });
          }
      });
  });

  btnYes.addEventListener('click', () => {
      if (targetAction) {
          if (targetAction.type === 'form') {
              targetAction.element.submit();
          } else if (targetAction.type === 'link') {
              window.location.href = targetAction.href;
          }
      }
  });

  btnNo.addEventListener('click', closeConfirm);

  modal.addEventListener('click', e => {
      if (e.target === modal) closeConfirm();
  });
});