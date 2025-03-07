document.addEventListener('DOMContentLoaded', () => {
    // Инициализация тултипов
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    const tooltipList = [...tooltipTriggerList].map(el => new bootstrap.Tooltip(el, {
        boundary: 'window',
        customClass: 'habit-tooltip'
    }));

    // Обработчик кликов по дням календаря
    document.querySelectorAll('.day').forEach(day => {
        day.addEventListener('click', async function(event) {
            if (this.classList.contains('bg-danger') || 
                this.style.pointerEvents === 'none') {
                event.stopPropagation();
                return;
            }

            const habitId = this.closest('.habit-calendar').dataset.habitId;
            const date = this.dataset.date;
            
            try {
                const response = await fetch(`/habit/${habitId}/update`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ date })
                });
                
                if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                
                const result = await response.json();
                
                if (result.status === 'success') {
                    this.classList.toggle('bg-success');
                    this.classList.toggle('bg-light');
                    
                    // Обновление тултипа
                    const tooltip = bootstrap.Tooltip.getInstance(this);
                    tooltip.setContent({
                        '.tooltip-inner': 
                            `${date.split('-').reverse().join('.')}\nСтатус: ${result.new_status ? '✅ Выполнено' : '❌ Пропущено'}`
                    });
                }
            } catch (error) {
                console.error('Update error:', error);
                alert(error.message || 'Ошибка обновления статуса');
            }
        });
    });

    // Обновление прогресс-баров при изменении
    const observer = new MutationObserver(mutations => {
        mutations.forEach(mutation => {
            if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                const habitId = mutation.target.closest('.habit-calendar').dataset.habitId;
                updateProgressBar(habitId);
            }
        });
    });

    document.querySelectorAll('.habit-calendar').forEach(calendar => {
        observer.observe(calendar, {
            attributes: true,
            subtree: true,
            attributeFilter: ['class']
        });
    });

    function updateProgressBar(habitId) {
        const progressBar = document.querySelector(`[data-habit-id="${habitId}"] .progress-bar`);
        const completedDays = document.querySelectorAll(`[data-habit-id="${habitId}"] .bg-success`).length;
        const totalDays = document.querySelectorAll(`[data-habit-id="${habitId}"] .day`).length;
        
        if (totalDays > 0) {
            const percentage = (completedDays / totalDays) * 100;
            progressBar.style.width = `${percentage}%`;
            progressBar.textContent = `${Math.round(percentage)}%`;
        }
    }
});