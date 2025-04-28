document.addEventListener('DOMContentLoaded', function() {
    const modal       = document.getElementById('myModal');
    const sphereBtn   = document.getElementById('sphere_modal');
    const closeBtn    = modal.querySelector('.close');
    const backBtn     = document.getElementById('backBtn');
    const sphereItems = modal.querySelectorAll('.sphere-block');
  
    sphereBtn.addEventListener('click', e => {
      e.preventDefault();
      modal.classList.add('modal--show');
    });
    closeBtn.addEventListener('click', () => {
      modal.classList.remove('modal--show');
      resetSpheres();
    });
    window.addEventListener('click', e => {
      if (e.target === modal) {
        modal.classList.remove('modal--show');
        resetSpheres();
      }
    });
    backBtn.addEventListener('click', resetSpheres);
  
    sphereItems.forEach(block => {
      const heading = block.querySelector('h3');
      const list    = block.querySelector('ul');
  
      heading.addEventListener('click', () => {
        sphereItems.forEach(b => {
          b.style.display                     = 'block';
          b.querySelector('ul').style.display = 'none';
        });
        block.style.display      = 'block';
        list.style.display       = 'block';
        backBtn.style.display    = 'inline-block';
      });
  
      list.querySelectorAll('li').forEach(li => {
        li.addEventListener('click', () => {
          document.getElementById('chosen_sphere').value =
            li.dataset.stid;
          document.getElementById('sphere_chosen_name').textContent =
            'Вы выбрали: ' + li.textContent.trim();
          modal.classList.remove('modal--show');
          resetSpheres();
        });
      });
    });
  
    function resetSpheres() {
      sphereItems.forEach(b => {
        b.style.display                     = 'block';
        b.querySelector('ul').style.display = 'none';
      });
      backBtn.style.display = 'none';
    }
  });