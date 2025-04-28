document.addEventListener('DOMContentLoaded', () => {
    const modal     = document.getElementById('confirm-modal');
    const msgEl     = document.getElementById('confirm-modal-message');
    const btnYes    = document.getElementById('confirm-yes');
    const btnNo     = document.getElementById('confirm-no');
    let   targetHref = null;
  
    function openConfirm(message, href) {
      msgEl.textContent = message;
      targetHref = href;
      modal.classList.add('modal--show');
    }
  
    function closeConfirm() {
      modal.classList.remove('modal--show');
      targetHref = null;
    }
  
    document.querySelectorAll('.js-confirm-action').forEach(el => {
      el.addEventListener('click', e => {
        e.preventDefault();
        openConfirm(el.dataset.confirmMessage, el.href);
      });
    });
  
    btnYes.addEventListener('click', () => {
      if (targetHref) window.location.href = targetHref;
    });
    btnNo.addEventListener('click', closeConfirm);
  
    // закрыть по клику вне контента
    modal.addEventListener('click', e => {
      if (e.target === modal) closeConfirm();
    });
  });
  