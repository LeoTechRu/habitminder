document.addEventListener('DOMContentLoaded', () => {
    // Обработка кликов по дням календаря
    document.querySelectorAll('.day').forEach(day => {
        day.addEventListener('click', async function() {
            const habitId = this.closest('.habit-calendar').dataset.habitId;
            const date = this.dataset.date;
            const currentStatus = this.classList.contains('bg-success');
            
            try {
                const response = await fetch(`/habit/${habitId}/update`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: `date=${date}&status=${!currentStatus}`
                });

                if (response.ok) {
                    this.classList.toggle('bg-success');
                    this.classList.toggle('bg-danger');
                    this.classList.toggle('text-white');
                }
            } catch (error) {
                console.error('Ошибка обновления:', error);
            }
        });
    });
});