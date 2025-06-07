document.addEventListener('DOMContentLoaded', function() {
    function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

    const csrfToken = getCookie('csrftoken');
        if (!csrfToken) {
    console.error('CSRF token not found');
    return; 
}
    const sphereModal = document.getElementById('myModal');
    const sphereBtn = document.getElementById('sphere_modal');
    if (sphereModal && sphereBtn) {
        const closeBtn = sphereModal.querySelector('.close');
        const backBtn = document.getElementById('backBtn');
        const sphereItems = sphereModal.querySelectorAll('.sphere-block');

        sphereBtn.addEventListener('click', e => {
            e.preventDefault();
            sphereModal.classList.add('modal--show');
        });

        closeBtn.addEventListener('click', () => {
            sphereModal.classList.remove('modal--show');
            resetSpheres();
        });

        window.addEventListener('click', e => {
            if (e.target === sphereModal) {
                sphereModal.classList.remove('modal--show');
                resetSpheres();
            }
        });

        backBtn.addEventListener('click', resetSpheres);

        sphereItems.forEach(block => {
            const heading = block.querySelector('h3');
            const list = block.querySelector('ul');

            heading.addEventListener('click', () => {
                sphereItems.forEach(b => {
                    b.style.display = 'block';
                    b.querySelector('ul').style.display = 'none';
                });
                block.style.display = 'block';
                list.style.display = 'block';
                backBtn.style.display = 'inline-block';
            });

            list.querySelectorAll('li').forEach(li => {
                li.addEventListener('click', () => {
                    document.getElementById('chosen_sphere').value = li.dataset.stid;
                    document.getElementById('sphere_chosen_name').textContent = 'Вы выбрали: ' + li.textContent.trim();
                    sphereModal.classList.remove('modal--show');
                    resetSpheres();
                });
            });
        });

        function resetSpheres() {
            sphereItems.forEach(b => {
                b.style.display = 'block';
                b.querySelector('ul').style.display = 'none';
            });
            backBtn.style.display = 'none';
        }
    } else {
        console.warn('Модалка #myModal или кнопка #sphere_modal не найдены');
    }

    // Код для #orderModal (выбор заказа)
    const orderModal = document.getElementById('orderModal');
    const orderBtn = document.querySelector('.js-open-invitation-modal');
    if (orderModal && orderBtn) {
        const closeBtn = orderModal.querySelector('.close');

        orderBtn.addEventListener('click', e => {
            e.preventDefault();
            orderModal.classList.add('modal--show');
            console.log('Модалка #orderModal открыта');
        });

        closeBtn.addEventListener('click', () => {
            orderModal.classList.remove('modal--show');
            console.log('Модалка #orderModal закрыта');
        });

        window.addEventListener('click', e => {
            if (e.target === orderModal) {
                orderModal.classList.remove('modal--show');
            }
        });

        // Обработка клика по заголовкам заказов
        const orderHeadings = orderModal.querySelectorAll('.js-send-invitation');
        if (orderHeadings.length === 0) {
            console.warn('Заголовки заказов .js-send-invitation не найдены в #orderModal');
        } else {
            orderHeadings.forEach(heading => {
                heading.addEventListener('click', async () => {
                    const freelancerId = heading.getAttribute('data-freelancer-id');
                    const orderId = heading.getAttribute('data-order-id');

                    if (!freelancerId || !orderId) {
                        alert('Ошибка: данные приглашения отсутствуют.');
                        return;
                    }

                    try {
                        const response = await fetch(`/profile/${freelancerId}/send-invitation/`, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/x-www-form-urlencoded',
                                'X-CSRFToken': csrfToken
                            },
                            body: `order_id=${orderId}`
                        });

                        const data = await response.json();
                        if (data.success) {
                            alert(data.message);
                            orderModal.classList.remove('modal--show');
                        } else {
                            alert(data.error || 'Ошибка отправки приглашения.');
                        }
                    } catch (error) {
                        console.error('Ошибка запроса:', error);
                        alert('Произошла ошибка при отправке приглашения.');
                    }
                });
            });
        }
    } else {
        console.warn('Модалка #orderModal или кнопка .js-open-invitation-modal не найдены');
    }
});