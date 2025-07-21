document.addEventListener('DOMContentLoaded', () =>
{
    //   Marcar película como vista
    const buttons = document.querySelectorAll('.mark-watched-btn');

    buttons.forEach(button =>
    {
        button.addEventListener('click', function ()
        {
            const movieId = this.dataset.movieId;

            fetch(`/mark_watched/${movieId}`, {
                method: 'POST'
            })
                .then(response =>
                {
                    if (!response.ok)
                    {
                        throw new Error(`HTTP status ${response.status}`);
                    }
                    return response.json();
                })
                .then(data =>
                {
                    if (data.success)
                    {
                        //Cambiar clase visual de la tarjeta
                        const cardBody = this.closest('.movie-card').querySelector('.card-body');
                        cardBody.classList.remove('not-watched');
                        cardBody.classList.add('watched');
                        // Cambiar texto si hay un span con estado
                        const watchedText = cardBody.querySelector('.watched-status');
                        if (watchedText) watchedText.innerText = '✔️ Vista';
                        // Reemplazar el botón
                        this.outerHTML = '<button class="btn btn-sm btn-outline-dark" disabled>✔️ Vista</button>';
                    } else
                    {
                        alert(' Error del servidor al marcar como vista.');
                    }
                })
                .catch(err =>
                {
                    console.error(' Error de red o backend:', err);
                    alert('Error de red al marcar como vista.');
                });
        });
    });

    // 📽️ Resetear trailer al cerrar modal
    const trailerModal = document.getElementById('trailerModal');
    const trailerFrame = document.getElementById('trailerFrame');

    if (trailerModal && trailerFrame)
    {
        trailerModal.addEventListener('hidden.bs.modal', () =>
        {
            const src = trailerFrame.getAttribute('src');
            trailerFrame.setAttribute('src', src); // Reset
        });
    }
});
