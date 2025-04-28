document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('id_avatar');
    if (!input) return;
  
    input.addEventListener('change', function () {
      const file = this.files[0];
      if (!file) return;
  
      const reader = new FileReader();
      reader.onload = e => {
        document.getElementById('avatar-preview').src = e.target.result;
      };
      reader.readAsDataURL(file);
  
      const form = document.getElementById('avatar-form');
      const data = new FormData(form);
      fetch(form.action, {
        method: 'POST',
        body: data,
        headers: { 'X-CSRFToken': data.get('csrfmiddlewaretoken') }
      })
      .then(r => {
        if (!r.ok) throw new Error('Ошибка при загрузке');
        console.log('Аватар обновлён');
      })
      .catch(console.error);
    });
  });
  