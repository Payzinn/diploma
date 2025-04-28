document.addEventListener('DOMContentLoaded', function() {
  
    const toggles    = document.querySelectorAll('.portfolio-form__toggle-btn');
    const yearsBlock = document.getElementById('years_block');
    const yearsInput = document.getElementById('id_years_experience');
  
    function updateToggles() {
      toggles.forEach(toggle => {
        const inp = toggle.querySelector('input[type="radio"]');
        if (inp.checked) {
          toggle.classList.add('portfolio-form__toggle-btn--active');
        } else {
          toggle.classList.remove('portfolio-form__toggle-btn--active');
        }
      });
    }
  
    toggles.forEach(toggle => {
      toggle.addEventListener('click', () => {
        const inp = toggle.querySelector('input[type="radio"]');
        inp.checked = true;
        updateToggles();
  
        if (inp.value === 'True') {
          yearsBlock.style.display = 'none';
          yearsInput.disabled      = true;
          yearsInput.value         = '';
        } else {
          yearsBlock.style.display = 'block';
          yearsInput.disabled      = false;
        }
      });
    });
  
    updateToggles();
    const initially = document.querySelector('.portfolio-form__toggle-btn input:checked');
    if (initially) {
      initially.closest('.portfolio-form__toggle-btn').click();
    }

    document.querySelectorAll('.portfolio-form__toggle-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.portfolio-form__toggle-btn').forEach(b => {
          b.classList.remove('portfolio-form__toggle-btn--active');
          b.querySelector('input').checked = false;
        });
        btn.classList.add('portfolio-form__toggle-btn--active');
        btn.querySelector('input').checked = true;
    
        const yearsBlock = document.getElementById('years_block');
        if (btn.dataset.value === 'True') {
          yearsBlock.style.display = 'none';
        } else {
          yearsBlock.style.display = 'flex';
        }
      });
    });
    window.addEventListener('DOMContentLoaded', () => {
      const active = document.querySelector('.portfolio-form__toggle-btn--active');
      if (active && active.dataset.value === 'True') {
        document.getElementById('years_block').style.display = 'none';
      }
    });
  });
  

