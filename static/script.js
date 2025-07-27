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


// mensajes flash efimeros 5 sec

setTimeout(function ()
{
    var flashMessage = document.getElementById('flash-message');
    if (flashMessage)
    {
        flashMessage.style.display = 'none'; // Oculta el mensaje
    }
}, 2500);


// logout por inactividad 
/*
let inactivityTime = function ()
{
    let timer;
    const timeoutDuration = 60000; // 10 minutos en milisegundos

    const resetTimer = () =>
    {
        clearTimeout(timer);
        timer = setTimeout(() =>
        {
            // Cerrar sesión por inactividad
            window.location.href = '/logout';
        }, timeoutDuration);
    };

    // Eventos para reiniciar el temporizador
    window.onload = resetTimer;
    window.onmousemove = resetTimer;
    window.onkeydown = resetTimer;
};
inactivityTime();
*/

/****** quiero ocultar un actor en la version celular ****/


/************** subselect para menues de genero ************/
/*
function showSubSelect()
{
    const mainSelect = document.getElementById('genero');
    const subSelectDrama = document.getElementById('Drama');
    const subSelectCommedy = document.getElementById('Comedia');
    const subSelectCrime = document.getElementById('Crimen');
    const subSelectAction = document.getElementById('Acción');
    const subSelectHorror = document.getElementById('Horror');
    const subSelectAll = document.getElementById('Todas');

    // Oculta todos los subselects
    subSelectDrama.style.display = 'none';
    subSelectCommedy.style.display = 'none';
    subSelectCrime.style.display = 'none';
    subSelectAction.style.display = 'none';
    subSelectHorror.style.display = 'none';
    subSelectAll.style.display = 'none';

    // Muestra el subselect correspondiente según la opción seleccionada
    switch (mainSelect.value)
    {
        case 'drama':
            subSelectDrama.style.display = 'block';
            break;
        case 'comedy':
            subSelectCommedy.style.display = 'block';
            break;
        case 'crime':
            subSelectCrime.style.display = 'block';
            break;
        case 'action':
            subSelectAction.style.display = 'block';
            break;
        case 'horror':
            subSelectHorror.style.display = 'block';
            break;
        case 'all':
            subSelectAll.style.display = 'block';
            break;
        default:
            break; // No hacer nada si no hay opción seleccionada
    }
}
*/
function showSubSelect()
{
    const mainSelect = document.getElementById('orderBy');
    const genreSelect = document.getElementById('genreSelect');

    // Oculta el subselect de género por defecto
    genreSelect.style.display = 'none';

    // Muestra el subselect de género si se selecciona "Género"
    if (mainSelect.value === 'genre')
    {
        genreSelect.style.display = 'block';
    }
}

/************** chart de progreso de saga **********/

document.addEventListener('DOMContentLoaded', function ()
{
    const sagas = window.sagas;
    const renderedCharts = new Set();

    // Plugin para mostrar el porcentaje
    const percentagePlugin = {
        id: 'percentageLabel',
        beforeDraw: (chart) =>
        {
            const { ctx, data, chartArea } = chart;
            const total = data.datasets[0].data.reduce((a, b) => a + b, 0);
            const value = data.datasets[0].data[0]; // Vistas
            const percentage = ((value / total) * 100).toFixed(0); // Calcula el porcentaje

            ctx.save();
            ctx.font = 'bold 30px Arial'; // Tamaño y la fuente
            ctx.fillStyle = '#000'; // Color del texto
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(percentage + '%', chartArea.left + (chartArea.right - chartArea.left) / 2, chartArea.top + (chartArea.bottom - chartArea.top) / 2);
            ctx.restore();
        }
    };

    function renderChart(saga)
    {
        if (renderedCharts.has(saga.id)) return;

        const canvas = document.getElementById('progressChart-' + saga.id);
        if (!canvas || canvas.offsetParent === null) return;

        const ctx = canvas.getContext('2d');

        // Calcula el porcentaje y define el color
        const total = saga.total;
        const watched = saga.watched;
        const percentage = (total > 0) ? (watched / total) * 100 : 0;

        let backgroundColor = '#28a745'; // Verde por defecto
        if (percentage < 25)
        {
            backgroundColor = '#dc3545'; // Rojo
        } else if (percentage < 50)
        {
            backgroundColor = '#ffc107'; // Amarillo
        } else if (percentage < 75)
        {
            backgroundColor = '#fd7e14'; // Naranja (ejemplo de color)
        }
        // else if the percentage is 75 or greater, it remains green.

        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Vistas', 'Restantes'],
                datasets: [{
                    data: [watched, Math.max(0, total - watched)],
                    backgroundColor: [backgroundColor, '#e9ecef'], // Cambia el color según el porcentaje
                    borderWidth: 1
                }]
            },
            options: {
                cutout: '70%',
                responsive: true,
                plugins: {
                    legend: { display: false },
                    percentageLabel: {} // Añade el plugin aquí
                }
            },
            plugins: [percentagePlugin] // Registra el plugin
        });

        renderedCharts.add(saga.id);
    }

    // Render los visibles al inicio
    sagas.forEach(renderChart);

    // Detectar cuando cambia el slide
    const carousel = document.getElementById('sagaCarousel');
    if (carousel)
    {
        carousel.addEventListener('slid.bs.carousel', () =>
        {
            sagas.forEach(renderChart); // intenta renderizar todos (saltea los que ya están)
        });
    }
});


