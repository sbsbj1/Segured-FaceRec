import cv2
import os
import numpy as np
import time

# Crear carpetas si no existen
if not os.path.exists('base_de_datos'):
    os.makedirs('base_de_datos/pagadores')
    os.makedirs('base_de_datos/evasores')

# Inicializar YOLO y cargar pesos, configuración y nombres de clases
net = cv2.dnn.readNet("yolo/yolov3-tiny.weights", "yolo/yolov3-tiny.cfg")
layer_names = net.getLayerNames()
output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]

with open("yolo/coco.names", "r") as f:
    classes = [line.strip() for line in f.readlines()]

# Inicializar ORB detector para características
orb = cv2.ORB_create()

# Listas para almacenar descriptores de los rostros de pagadores y evasores
known_face_descriptors = []
known_faces_images = []
recent_evasor_descriptors = []

# Contadores para nombres de archivo
pagador_counter = 0
evasor_counter = 0

# Tiempo mínimo entre capturas del mismo rostro (en segundos)
TIME_THRESHOLD = 5  # 5 segundos
last_evasor_capture_time = time.time()  # Control de tiempo entre capturas


# Función para comparar características con ORB
def compare_faces(orb, img1, img2):
    kp1, des1 = orb.detectAndCompute(img1, None)
    kp2, des2 = orb.detectAndCompute(img2, None)

    if des1 is None or des2 is None:
        return False

    # Comparar usando un matcher de Hamming
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = bf.match(des1, des2)

    # Filtrar buenos matches
    good_matches = [m for m in matches if m.distance < 50]

    return len(good_matches) > 15  # Umbral de coincidencias


# Función para capturar y registrar rostros en la cámara de pago
def capture_paying_faces(cap):
    global pagador_counter
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        height, width, channels = frame.shape
        blob = cv2.dnn.blobFromImage(frame, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
        net.setInput(blob)
        outs = net.forward(output_layers)

        class_ids = []
        confidences = []
        boxes = []

        for out in outs:
            for detection in out:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]

                if class_id == 0 and confidence > 0.5:  # Solo detecta personas
                    center_x = int(detection[0] * width)
                    center_y = int(detection[1] * height)
                    w = int(detection[2] * width)
                    h = int(detection[3] * height)

                    x = int(center_x - w / 2)
                    y = int(center_y - h / 2)

                    # Recortar la detección para solo centrarse en el rostro
                    y = y + int(h / 4)  # Subir la coordenada Y (parte superior del cuadro)
                    h = int(h / 2)  # Limitar el cuadro a la mitad superior

                    boxes.append([x, y, w, h])
                    confidences.append(float(confidence))
                    class_ids.append(class_id)

        indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)
        if len(indexes) > 0:
            for i in indexes.flatten():
                x, y, w, h = boxes[i]
                face = frame[y:y + h, x:x + w]

                # Evitar que un rostro vacío o mal detectado cause error
                if face.size == 0:
                    continue

                # Redimensionar el rostro al tamaño estándar
                face_resized = cv2.resize(face, (150, 150))

                # Comprobar si el rostro ya fue registrado usando ORB
                if any(compare_faces(orb, face_resized, known_face) for known_face in known_faces_images):
                    continue  # Saltar si el rostro ya está registrado

                # Guardar descriptores del rostro y la imagen
                known_faces_images.append(face_resized)

                # Guardar el rostro en la carpeta de pagadores
                pagador_path = f"base_de_datos/pagadores/pagador_{pagador_counter}.png"
                cv2.imwrite(pagador_path, face_resized)
                print(f"Rostro guardado en: {pagador_path}")
                pagador_counter += 1

                # Dibujar el cuadro verde alrededor del rostro
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        cv2.imshow('Camara de Pago', frame)

        # Cambiar al modo de detección de evasores con 'q' o cerrar con 'Esc'
        key = cv2.waitKey(1)
        if key == ord('q'):
            return 'general'
        elif key == 27:  # Tecla 'Esc' para salir
            return 'exit'


# Función para verificar los rostros en la cámara general
def check_fare_evaders(cap):
    global evasor_counter, last_evasor_capture_time
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        height, width, channels = frame.shape
        blob = cv2.dnn.blobFromImage(frame, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
        net.setInput(blob)
        outs = net.forward(output_layers)

        class_ids = []
        confidences = []
        boxes = []

        for out in outs:
            for detection in out:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]

                if class_id == 0 and confidence > 0.5:  # Solo detecta personas
                    center_x = int(detection[0] * width)
                    center_y = int(detection[1] * height)
                    w = int(detection[2] * width)
                    h = int(detection[3] * height)

                    x = int(center_x - w / 2)
                    y = int(center_y - h / 2)

                    # Recortar la detección para solo centrarse en el rostro
                    y = y + int(h / 4)  # Subir la coordenada Y (parte superior del cuadro)
                    h = int(h / 2)  # Limitar el cuadro a la mitad superior

                    boxes.append([x, y, w, h])
                    confidences.append(float(confidence))
                    class_ids.append(class_id)

        indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)
        if len(indexes) > 0:
            for i in indexes.flatten():
                x, y, w, h = boxes[i]
                face = frame[y:y + h, x:x + w]

                # Evitar errores con rostros vacíos o mal detectados
                if face.size == 0:
                    continue

                # Redimensionar el rostro al tamaño estándar
                face_resized = cv2.resize(face, (150, 150))

                # Verificar si el rostro ha sido capturado recientemente
                if time.time() - last_evasor_capture_time < TIME_THRESHOLD:
                    if any(compare_faces(orb, face_resized, known_face) for known_face in recent_evasor_descriptors):
                        continue  # Saltar si el rostro fue capturado recientemente

                # Comparar con los rostros registrados usando ORB
                if any(compare_faces(orb, face_resized, known_face) for known_face in known_faces_images):
                    # Dibujar cuadro verde sin texto para los pagadores
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                else:
                    # Guardar el rostro en la carpeta de evasores
                    evasor_path = f"base_de_datos/evasores/evasor_{evasor_counter}.png"
                    cv2.imwrite(evasor_path, face_resized)
                    print(f"Evasor guardado en: {evasor_path}")
                    evasor_counter += 1

                    # Dibujar cuadro rojo sin texto para los evasores
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                    print("Posible evasor capturado")

                    # Actualizar la lista de evasores recientes y el tiempo
                    recent_evasor_descriptors.append(face_resized)
                    last_evasor_capture_time = time.time()

        cv2.imshow('Camara General', frame)

        # Cambiar al modo de captura de pagadores con 'q' o cerrar con 'Esc'
        key = cv2.waitKey(1)
        if key == ord('q'):
            return 'payment'
        elif key == 27:  # Tecla 'Esc' para salir
            return 'exit'


if __name__ == "__main__":
    cap = cv2.VideoCapture(0)  # Usamos solo una cámara
    mode = 'payment'

    while True:
        if mode == 'payment':
            mode = capture_paying_faces(cap)
        elif mode == 'general':
            mode = check_fare_evaders(cap)
        if mode == 'exit':
            break

    cap.release()
    cv2.destroyAllWindows()
