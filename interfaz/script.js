document.addEventListener('DOMContentLoaded', function () {
    var map = L.map('map').setView([-33.4489, -70.6693], 13);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    let marcadores = {};

    // Cargar los datos de paradas
    fetch('paradas.json')
        .then(response => response.json())
        .then(data => {
            data.forEach(parada => {
                // Crear un marcador para cada parada
                const marker = L.marker([parada.lat_parada, parada.lon_parada]).addTo(map);
                // Agregar un popup con información
                marker.bindPopup(`<strong>${parada.nombre_parada}</strong><br>
    Evasiones: ${parada.evasiones}<br><br>
    <strong><a href="evasiones.html" onclick="window.location.href='evasiones.html'; return false;">Ver Evasiones</a></strong>`);
                // Agregar el marcador al objeto de marcadores
                marcadores[parada.id_parada] = marker;
            });
        })
        .catch(error => console.error('Error al cargar las paradas:', error));
        
    const gallery = document.getElementById('gallery');

    const rutaImagenes = 'base_de_datos/evasores/';
    const imagenes = ['evasores_0.png', 'evasores_1.png', 'evasores_2.png', 'evasores_3.png', 'evasores_4.png'];
    imagenes.forEach(nombreImagen => {
        const col = document.createElement('div');
        col.classList.add('col-lg-4', 'col-md-6', 'mb-4'); //se añaden las clases de bootstrap
        
        const img = document.createElement('img');
        img.src = `${rutaImagenes}${nombreImagen}`;
        img.alt = nombreImagen;
        img.classList.add('img-fluid');

        col.appendChild(img);
        gallery.appendChild(col);
    })


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

    const btnGenerarReporte = document.getElementById('btnGenerarReporte');

    btnGenerarReporte.addEventListener('click', function () {
        fetch('paradas.json')
        .then(response => response.json())
        .then(data => {
            const fecha = new Date().toISOString();   //Se crea la fecha y se pasa al formato ISO de fechas
            const nombreArchivo = 'reporte-ruta101-' + fecha + '.json';   //se junta en el nombreArchivo
            const jsonStr = JSON.stringify(data, null, 4);         
            const blob = new Blob([jsonStr], {type: 'application/json'});


            //Para que se descargue:
            const a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = nombreArchivo;
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(a.href);
        })
    });

    const btnBuscarParadas = document.getElementById('btnBuscarParadas');
    const inputParadaID = document.getElementById('inputParadaID');
    btnBuscarParadas.addEventListener('click', function () {
        const paradaID = inputParadaID.value.trim();
        if (!paradaID) {
            alert('Debe ingresar un ID de parada');
            return;
        }

        const marcador = marcadores[paradaID];
        if (marcador) {
            marcador.openPopup();
            map.setView(marcador.getLatLng(), 15); //se centra el mapa en el marcador
        } else {
            alert('No se encontró una parada con ese ID');
        }
        
        });
    
    function updatefecha(){
        const date = new Date(); //creamos el objeto

        const fechaActual = date.toLocaleDateString(); //obtenemos la fecha actual como string

        document.querySelector('#datetime').textContent = fechaActual; //actualizamos el span del HTML

    }
    setInterval(updatefecha, 1000);  //aqui llamamos la funcion del tiempo cada segundo
});

