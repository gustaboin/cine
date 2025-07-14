
document.addEventListener('DOMContentLoaded', () =>
{
    const buttons = document.querySelectorAll('.mark-watched-btn');

    buttons.forEach(button =>
    {
        button.addEventListener('click', () =>
        {
            const movieId = button.getAttribute('data-movie-id');

            fetch(`/mark_watched/${movieId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            })
                .then(response =>
                {
                    if (response.ok)
                    {
                        // ✅ Actualizar DOM al marcar como vista
                        const watchedText = button.closest('.card-body').querySelector('.watched-status');
                        if (watchedText)
                        {
                            watchedText.innerHTML = '✔️ Vista';
                        }

                        // 🔒 Ocultar el botón
                        button.style.display = 'none';
                    } else
                    {
                        alert('Error al marcar como vista.');
                    }
                })
                .catch(() => alert('Error de red'));
        });
    });
});

