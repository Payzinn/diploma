document.addEventListener('DOMContentLoaded', () => {
  const modal     = document.getElementById('confirm-modal');
  const msgEl     = document.getElementById('confirm-modal-message');
  const btnYes    = document.getElementById('confirm-yes');
  const btnNo     = document.getElementById('confirm-no');
  let   targetForm = null;

  function openConfirm(message, form) {
      msgEl.textContent = message;
      targetForm = form;
      modal.classList.add('modal--show');
  }

  function closeConfirm() {
      modal.classList.remove('modal--show');
      targetForm = null;
  }

  document.querySelectorAll('.js-confirm-action').forEach(el => {
      el.addEventListener('click', e => {
          e.preventDefault();
          const form = el.closest('form');
          if (form) {
              openConfirm(el.dataset.confirmMessage, form);
          }
      });
  });

  btnYes.addEventListener('click', () => {
      if (targetForm) {
          targetForm.submit();
      }
  });

  btnNo.addEventListener('click', closeConfirm);

  // Закрыть по клику вне контента
  modal.addEventListener('click', e => {
      if (e.target === modal) closeConfirm();
  });
});