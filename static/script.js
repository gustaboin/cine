
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


// modal para que se cierre la reproduccion del trailer

document.addEventListener('DOMContentLoaded', function ()
{
    const trailerModal = document.getElementById('trailerModal');
    const trailerFrame = document.getElementById('trailerFrame');

    trailerModal.addEventListener('hidden.bs.modal', function ()
    {
        // Detener el video reiniciando el src
        const src = trailerFrame.getAttribute('src');
        trailerFrame.setAttribute('src', src);
    });
});
