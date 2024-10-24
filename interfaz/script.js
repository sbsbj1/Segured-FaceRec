document.addEventListener('DOMContentLoaded', function () {
    var map = L.map('map').setView([-33.4489, -70.6693], 13);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    // Cargar los datos de paradas
    fetch('paradas.json')
        .then(response => response.json())
        .then(data => {
            data.forEach(parada => {
                // Crear un marcador para cada parada
                const marker = L.marker([parada.lat_parada, parada.lon_parada]).addTo(map);
                // Agregar un popup con información
                marker.bindPopup(`<strong>${parada.nombre_parada}</strong><br>Evasiones: ${parada.evasiones}`);
            });
        })
        .catch(error => console.error('Error al cargar las paradas:', error));

    // Mostrar el card deck de bootstrap
    const btnEstadisticas = document.getElementById('btnEstadisticas');

    btnEstadisticas.addEventListener('click', function () {
        console.log('Botón de estadísticas clicado');
        fetch('paradas.json')
            .then(response => {
                console.log('Respuesta recibida');
                return response.json();
            })
            .then(data => {
                console.log('Datos JSON:', data);
                let totalEvasiones = 0;
                let paraderoEvasiones = {};

                data.forEach(parada => {
                    totalEvasiones += parada.evasiones;
                    if (paraderoEvasiones[parada.id_parada]) {
                        paraderoEvasiones[parada.id_parada] += parada.evasiones;
                    } else {
                        paraderoEvasiones[parada.id_parada] = parada.evasiones;
                    }
                });

                let paraderoCritico = Object.keys(paraderoEvasiones).reduce((a, b) => paraderoEvasiones[a] > paraderoEvasiones[b] ? a : b);

                document.getElementById('totalEvasiones').textContent = `${totalEvasiones} evasiones`;
                document.getElementById('paraderoCritico').textContent = paraderoCritico;

                const cardDeck = document.getElementById('cardDeck');
                cardDeck.style.display = 'flex';
            })
            .catch(error => console.error('Error al cargar el JSON:', error));
    });
});