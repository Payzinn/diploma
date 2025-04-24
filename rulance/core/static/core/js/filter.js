document.addEventListener('DOMContentLoaded', () => {
    const sphereButtons = document.querySelectorAll('.orders_control__toggle-btn[data-sphere-id]');
    const subsphereGroups = document.querySelectorAll('.sphere_types_group');
  
    sphereButtons.forEach(btn => {
      const input = btn.querySelector('input[type="radio"]');
      btn.addEventListener('click', () => {
        sphereButtons.forEach(b => b.classList.remove('active'));
        subsphereGroups.forEach(g => g.style.display = 'none');
  
        input.checked = true;
        btn.classList.add('active');
  
        const sid = btn.dataset.sphereId;
        document.querySelectorAll(`.sphere_types_group[data-sphere-id="${sid}"]`)
                .forEach(g => g.style.display = 'block');
      });
      if (input.checked) btn.click();
    });
  
    const subsphereButtons = document.querySelectorAll(
        '.orders_control__toggle-btn:not([data-sphere-id])'
      );
      subsphereButtons.forEach(btn => {
        const input = btn.querySelector('input[type="checkbox"]');
      
        const update = () => {
          if (input.checked) {
            btn.classList.add('active');
          } else {
            btn.classList.remove('active');
          }
        };
      
        btn.addEventListener('click', e => {
          e.preventDefault();
          input.checked = !input.checked;
          update();
        });
      
        update();
      });
    })