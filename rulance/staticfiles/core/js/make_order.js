document.addEventListener('DOMContentLoaded', () => {
    const negotiableCheckbox = document.getElementById('id_is_negotiable');
    const priceField         = document.getElementById('id_price');
  
    function updatePriceField() {
      if (negotiableCheckbox.checked) {
        priceField.disabled = true;
        priceField.style.opacity = '0.5';
        priceField.style.cursor  = 'not-allowed';
      } else {
        priceField.disabled = false;
        priceField.style.opacity = '';
        priceField.style.cursor  = '';
      }
    }
  
    negotiableCheckbox.addEventListener('change', updatePriceField);
  
    updatePriceField();
  });