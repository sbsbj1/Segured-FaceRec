// Esperar a que el DOM esté completamente cargado
document.addEventListener('DOMContentLoaded', function () {
    // Inicializar el mapa
    var map = L.map('map').setView([-33.4489, -70.6693], 13);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    let marcadores = {};
    let paradasData = []; // Para almacenar las paradas

    // Funcion para cargar los datos de paradas
    function cargarParadas() {
        return fetch('paradas.json')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                paradasData = data; // Guardar los datos globalmente
                data.forEach(parada => {
                    const marker = L.marker([parada.lat_parada, parada.lon_parada]).addTo(map);
                    marker.bindPopup(`
                        <strong>${parada.nombre_parada}</strong><br>
                        Evasiones: ${parada.evasiones}<br><br>
                        <a href="evasiones.html" class="btn btn-primary btn-sm">Ver Evasiones</a>
                    `);
                    marcadores[parada.id_parada] = marker;
                });
                return data;
            })
            .catch(error => {
                console.error('Error al cargar las paradas:', error);
                alert('Error al cargar los datos de paradas');
            });
    }

    // Función para actualizar estadísticas
    function actualizarEstadisticas() {
        if (paradasData.length === 0) {
            alert('No hay datos de paradas disponibles');
            return;
        }

        let totalEvasiones = 0;
        let maxEvasiones = 0;
        let paraderoCritico = '';

        paradasData.forEach(parada => {
            totalEvasiones += parada.evasiones;
            if (parada.evasiones > maxEvasiones) {
                maxEvasiones = parada.evasiones;
                paraderoCritico = parada.id_parada;
            }
        });

        document.getElementById('totalEvasiones').textContent = `${totalEvasiones} evasiones`;
        document.getElementById('paraderoCritico').textContent = `Parada ${paraderoCritico} (${maxEvasiones} evasiones)`;
        
        const cardDeck = document.getElementById('cardDeck');
        cardDeck.style.display = 'flex';
    }

    // Función para generar reporte
    function generarReporte() {
        if (paradasData.length === 0) {
            alert('No hay datos para generar el reporte');
            return;
        }

        const fecha = new Date().toISOString().split('T')[0];
        const nombreArchivo = `reporte-ruta101-${fecha}.json`;
        const jsonStr = JSON.stringify(paradasData, null, 2);
        const blob = new Blob([jsonStr], { type: 'application/json' });

        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = nombreArchivo;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(a.href);
    }

    // Función para buscar parada
    function buscarParada() {
        const paradaID = document.getElementById('inputParadaID').value.trim();
        if (!paradaID) {
            alert('Por favor ingrese un ID de parada');
            return;
        }

        const marcador = marcadores[paradaID];
        if (marcador) {
            map.setView(marcador.getLatLng(), 15);
            marcador.openPopup();
        } else {
            alert('No se encontró una parada con ese ID');
        }
    }

    // Función para actualizar fecha
    function actualizarFecha() {
        const fecha = new Date().toLocaleDateString();
        document.getElementById('datetime').textContent = fecha;
    }

    function mostrarBotonesFiltro() {
        const filterButtons = document.getElementById('filterButtons');
        if (filterButtons.style.display === 'none')
        { 
            filterButtons.style.display = 'block';
        }
        else
        {
            filterButtons.style.display = 'none';
        }
    }

    let altEvasiones = false;

    function ocultarEvasiones() {
        altEvasiones = !altEvasiones;

        paradasData.forEach(parada => {
            
            if (altEvasiones && parada.evasiones === 0) {
                marcadores[parada.id_parada].remove();
            }
            else {
                marcadores[parada.id_parada].addTo(map);
            }

        })
    }

    function mostrarMaxEvasiones() {
        altEvasiones = !altEvasiones;
        let maxEvasiones = 0;
        let paraderoCritico = '';

        paradasData.forEach(parada => {
            if (parada.evasiones > maxEvasiones) {
                maxEvasiones = parada.evasiones;
                paraderoCritico = parada.id_parada;
            }
        });


        
        paradasData.forEach(parada => {
            const marcador = marcadores[parada.id_parada];
            if (altEvasiones){
                if(parada.id_parada === paraderoCritico) {
                    marcador.addTo(map);
                    marcador.openPopup();
                } else {
                    marcador.remove();
                }
            } else {
                marcador.addTo(map);
            }
    });
}
    

    // Inicializar la aplicación
    cargarParadas().then(() => {
        // Configurar event listeners
        document.getElementById('btnEstadisticas').addEventListener('click', actualizarEstadisticas);
        document.getElementById('btnGenerarReporte').addEventListener('click', generarReporte);
        document.getElementById('btnBuscarParadas').addEventListener('click', buscarParada);
        document.getElementById('btnFilter').addEventListener('click', mostrarBotonesFiltro);
        document.getElementById('btnOcultar').addEventListener('click', ocultarEvasiones);
        document.getElementById('btnExclamacion').addEventListener('click', mostrarMaxEvasiones);
        
        // Iniciar actualización de fecha
        actualizarFecha();
        setInterval(actualizarFecha, 1000);
    });
});
