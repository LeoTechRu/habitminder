document.addEventListener('DOMContentLoaded', () => {
    // Инициализация тултипов
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    const tooltipList = [...tooltipTriggerList].map(el => new bootstrap.Tooltip(el, {
        boundary: 'window',
        customClass: 'habit-tooltip'
    }));

    // Наблюдатель за изменениями в календаре
    const observer = new MutationObserver(mutations => {
        mutations.forEach(mutation => {
            if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                const habitId = mutation.target.closest('.habit-calendar').dataset.habitId;
                updateProgressBar(habitId);
            }
        });
    });

    // Функция обновления прогресс-бара
    const updateProgressBar = (habitId) => {
        const card = document.querySelector(`.habit-calendar[data-habit-id="${habitId}"]`).closest('.card');
        const progressBar = card.querySelector('.progress-bar');
        const completedDays = card.querySelectorAll('.day.bg-success').length;
        const totalDays = card.querySelectorAll('.day').length;
        
        if (totalDays > 0) {
            const percentage = (completedDays / totalDays) * 100;
            progressBar.style.width = `${percentage}%`;
            progressBar.textContent = `${Math.round(percentage)}%`;
        }
    };

    // Инициализация наблюдателя для всех календарей
    document.querySelectorAll('.habit-calendar').forEach(calendar => {
        observer.observe(calendar, {
            attributes: true,
            subtree: true,
            attributeFilter: ['class']
        });
    });
});