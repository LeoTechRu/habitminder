document.addEventListener('DOMContentLoaded', () => {
    // Инициализация тултипов
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    const tooltipList = [...tooltipTriggerList].map(el => new bootstrap.Tooltip(el));

    // Обработчик кликов по дням календаря
    document.querySelectorAll('.day:not(.bg-danger)').forEach(day => {
        day.addEventListener('click', async function() {
            const habitId = this.closest('.habit-calendar').dataset.habitId;
            const date = this.dataset.date;
            const currentDate = new Date();
            const selectedDate = new Date(date);
            
            // Проверка на будущие и прошедшие даты
            if (selectedDate > currentDate) {
                alert('Нельзя отмечать будущие даты!');
                return;
            }
            
            try {
                const response = await fetch(`/habit/${habitId}/update`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                    body: `date=${date}`
                });
                
                const result = await response.json();
                
                if (result.status === 'success') {
                    // Обновление визуального состояния
                    this.classList.toggle('bg-success');
                    this.classList.toggle('bg-light');
                    
                    // Обновление тултипа
                    const tooltip = bootstrap.Tooltip.getInstance(this);
                    tooltip.setContent({'.tooltip-inner': 
                        `${date.split('-').reverse().join('.')}\nСтатус: ${result.new_status ? 'Выполнено' : 'Пропущено'}`
                    });
                    
                    // Обновление счетчиков прогресса
                    updateProgressBars(habitId);
                }
            } catch (error) {
                console.error('Ошибка обновления:', error);
                alert('Произошла ошибка при обновлении статуса');
            }
        });
    });

    // Функция обновления прогресс-баров
    function updateProgressBars(habitId) {
        document.querySelectorAll(`[data-habit-id="${habitId}"] .progress-bar`).forEach(bar => {
            const totalDays = Object.keys(bar.dataset).length;
            const completedDays = [...bar.parentNode.querySelectorAll('.bg-success')].length;
            const percentage = (completedDays / totalDays) * 100;
            bar.style.width = `${percentage}%`;
            bar.textContent = `${Math.round(percentage)}%`;
        });
    }
});
