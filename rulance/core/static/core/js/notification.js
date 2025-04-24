document.addEventListener('DOMContentLoaded', function() {
    function showNotification(message, type) {
      const notification = document.getElementById('notification');
      notification.textContent = message;
      notification.className = 'notification ' + type;
      notification.style.right = '20px';
      setTimeout(function() {
        notification.style.right = '-300px';
      }, 3000);
    }

    const urlParams = new URLSearchParams(window.location.search);
    const status    = urlParams.get('status');
    const message   = urlParams.get('message');
    if (status === 'success') {
      showNotification('Заказ успешно размещён!', 'success');
    } else if (status === 'error' && message) {
      showNotification('Ошибка: ' + message, 'error');
    }
  });