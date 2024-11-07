import cv2
import os
import numpy as np
import time
import json
import dlib
from database import insertar_pasajero, insertar_imagen, insertar_comparacion

# Configuraciones de archivos y rutas
ruta_json = "interfaz/paradas.json"
estado_file_path = "estado.txt"

# Variables para evitar capturas duplicadas
recent_faces = []  # Almacena (descriptor, tiempo) para rostros recientes
recent_evasor_descriptors = []  # Almacena descriptores de evasores recientes
TIME_THRESHOLD = 10  # En segundos
POSITION_THRESHOLD = 20  # Tolerancia en píxeles para posición

# Variables globales
last_face_position = None
known_faces_images = []  # Lista global para almacenar rostros conocidos

# Funciones de registro en JSON
def registrar_evasion_json(id_parada):
    with open(ruta_json, "r") as archivo:
        paradas = json.load(archivo)
    for parada in paradas:
        if parada["id_parada"] == id_parada:
            parada["evasiones"] += 1
            print(f"Evasión registrada en: {id_parada}, Total Evasiones: {parada['evasiones']}")
            break
    with open(ruta_json, "w") as archivo:
        json.dump(paradas, archivo, indent=4)

def leer_estado():
    if os.path.exists(estado_file_path):
        with open(estado_file_path, "r") as archivo:
            return int(archivo.read().strip())
    return -1

def escribir_estado(indice):
    with open(estado_file_path, "w") as archivo:
        archivo.write(str(indice))

def manejar_evasor():
    last_index = leer_estado()
    last_index += 1
    with open(ruta_json, "r") as archivo:
        paradas = json.load(archivo)
    if last_index >= len(paradas):
        last_index = 0
    paradero_actual = paradas[last_index]
    registrar_evasion_json(paradero_actual["id_parada"])
    escribir_estado(last_index)

# Crear carpetas si no existen
if not os.path.exists('base_de_datos'):
    os.makedirs('base_de_datos/pagadores')
    os.makedirs('base_de_datos/evasores')

# Inicializar detector de rostros con dlib
face_detector = dlib.get_frontal_face_detector()

# Inicializar ORB detector para características
orb = cv2.ORB_create()

# Contadores para nombres de archivo
pagador_counter = 0
evasor_counter = 0

# Función para comparar rostros con ORB
def compare_faces(orb, img1, img2, min_good_matches=20):
    kp1, des1 = orb.detectAndCompute(img1, None)
    kp2, des2 = orb.detectAndCompute(img2, None)
    if des1 is None or des2 is None:
        return False
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = bf.match(des1, des2)
    good_matches = [m for m in matches if m.distance < 50]
    return len(good_matches) > min_good_matches

# Función para verificar si un rostro es nuevo en base al tiempo y similitud
def is_new_face(descriptor):
    current_time = time.time()
    for (recent_descriptor, last_seen) in recent_faces:
        if current_time - last_seen < TIME_THRESHOLD:
            if compare_faces(orb, descriptor, recent_descriptor):
                return False
    # Agregar el nuevo descriptor a recent_faces
    recent_faces.append((descriptor, current_time))
    # Limpiar recent_faces para evitar crecimiento excesivo
    recent_faces[:] = [(desc, t) for (desc, t) in recent_faces if current_time - t < TIME_THRESHOLD]
    return True

# Función para verificar si la posición es diferente de la última registrada
def is_different_position(current_position):
    global last_face_position
    if last_face_position is None:
        last_face_position = current_position
        return True
    x1, y1, w1, h1 = last_face_position
    x2, y2, w2, h2 = current_position
    distance = abs(x1 - x2) + abs(y1 - y2)
    if distance > POSITION_THRESHOLD:
        last_face_position = current_position
        return True
    return False

# Función para guardar la imagen y registrar en la base de datos
def guardar_imagen_y_registrar(id_viaje, face_resized, es_pagador=True):
    global pagador_counter, evasor_counter
    tipo = "pagadores" if es_pagador else "evasores"
    contador = pagador_counter if es_pagador else evasor_counter
    imagen_path = f"base_de_datos/{tipo}/{tipo}_{contador}.png"
    cv2.imwrite(imagen_path, face_resized)
    id_pasajero = insertar_pasajero()
    id_imagen = insertar_imagen(id_pasajero, id_viaje, imagen_path)
    if id_imagen is None:
        print("Error al insertar la imagen en la base de datos.")
        return
    if not es_pagador:
        insertar_comparacion(id_imagen, resultado=0)
        print(f"Evasor guardado en: {imagen_path}")
    else:
        print(f"Pagador guardado en: {imagen_path}")
    if es_pagador:
        pagador_counter += 1
    else:
        evasor_counter += 1

# Función para capturar y registrar rostros en la cámara de pago
def capture_paying_faces(cap):
    global pagador_counter, known_faces_images
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        faces = face_detector(frame, 1)
        for face in faces:
            x, y, w, h = face.left(), face.top(), face.width(), face.height()
            face_region = frame[y:y + h, x:x + w]
            if face_region.size == 0:
                continue
            face_resized = cv2.resize(face_region, (150, 150))
            if is_different_position((x, y, w, h)) and is_new_face(face_resized):
                known_faces_images.append(face_resized)
                guardar_imagen_y_registrar("101-I-L-B02", face_resized, es_pagador=True)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.imshow('Camara de Pago', frame)
        key = cv2.waitKey(1)
        if key == ord('q'):
            return 'general'
        elif key == 27:
            return 'exit'

# Función para verificar los rostros en la cámara general
def check_fare_evaders(cap):
    global evasor_counter, last_evasor_capture_time, known_faces_images, recent_evasor_descriptors
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        faces = face_detector(frame, 1)
        for face in faces:
            x, y, w, h = face.left(), face.top(), face.width(), face.height()
            face_region = frame[y:y + h, x:x + w]
            if face_region.size == 0:
                continue
            face_resized = cv2.resize(face_region, (150, 150))
            if is_different_position((x, y, w, h)) and is_new_face(face_resized):
                if any(compare_faces(orb, face_resized, known_face) for known_face in known_faces_images):
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                else:
                    guardar_imagen_y_registrar("101-I-L-B02", face_resized, es_pagador=False)
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                    print("Posible evasor capturado")
                    recent_evasor_descriptors.append(face_resized)
                    last_evasor_capture_time = time.time()
                    manejar_evasor()
        cv2.imshow('Camara General', frame)
        key = cv2.waitKey(1)
        if key == ord('q'):
            return 'payment'
        elif key == 27:
            return 'exit'

if __name__ == "__main__":
    cap_payment = cv2.VideoCapture(0)  # Cámara 1 para pagos
    cap_general = cv2.VideoCapture(2)  # Cámara 2 para detección general
    mode = 'payment'
    while True:
        if mode == 'payment':
            mode = capture_paying_faces(cap_payment)
        elif mode == 'general':
            mode = check_fare_evaders(cap_general)
        if mode == 'exit':
            break
    cap_payment.release()
    cap_general.release()
    cv2.destroyAllWindows()
