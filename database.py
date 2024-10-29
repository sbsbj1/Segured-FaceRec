import pyodbc
from datetime import date

def conectar_sql():
    try:
        connection = pyodbc.connect(
            "DRIVER={ODBC Driver 17 for SQL Server};"
            "SERVER=servidor-segured.database.windows.net;"
            "DATABASE=segured-db;"
            "UID=segured;"
            "PWD=password2024!;"
            "Encrypt=yes;"
            "TrustServerCertificate=no;"
            "Connection Timeout=30;"
        )
        return connection
    except pyodbc.Error as e:
        print(f"Error al conectar a SQL Server: {e}")
        raise

def insertar_pasajero():
    connection = conectar_sql()
    cursor = connection.cursor()
    try:
        # Modificada la consulta para usar OUTPUT
        cursor.execute("""
            INSERT INTO Pasajeros 
            OUTPUT INSERTED.id_pasajero 
            DEFAULT VALUES
        """)
        
        # Obtener el ID insertado
        id_pasajero = cursor.fetchval()
        connection.commit()
        
        print(f"Pasajero insertado con ID: {id_pasajero}")
        return id_pasajero
        
    except pyodbc.Error as e:
        print(f"Error al insertar en la tabla Pasajeros: {e}")
        connection.rollback()
        return None
    finally:
        cursor.close()
        connection.close()

def insertar_imagen(id_pasajero, id_viaje, url_imagen):
    if id_pasajero is None:
        print("Error: No se puede insertar imagen sin id_pasajero")
        return None
        
    connection = conectar_sql()
    cursor = connection.cursor()
    fecha_captura = date.today()
    
    try:
        print(f"Insertando imagen: id_pasajero={id_pasajero}, id_viaje={id_viaje}, fecha_captura={fecha_captura}, url_imagen={url_imagen}")
        cursor.execute("""
            INSERT INTO Imagen (id_pasajero, id_viaje, fecha_captura, URL_imagen)
            OUTPUT INSERTED.id_imagen
            VALUES (?, ?, ?, ?)
        """, (id_pasajero, id_viaje, fecha_captura, url_imagen))
        
        id_imagen = cursor.fetchval()
        connection.commit()
        
        print(f"Imagen insertada con id: {id_imagen}")
        return id_imagen
        
    except pyodbc.Error as e:
        print(f"Error al insertar en la tabla Imagen: {e}")
        connection.rollback()
        return None
    finally:
        cursor.close()
        connection.close()

def insertar_comparacion(id_imagen, resultado):
    if id_imagen is None:
        print("Error: id_imagen es None, no se puede insertar en la tabla Comparacion.")
        return
        
    connection = conectar_sql()
    cursor = connection.cursor()
    fecha_verificacion = date.today()
    
    try:
        cursor.execute("""
            INSERT INTO Comparacion (id_imagen, fecha_verificacion, resultado) 
            VALUES (?, ?, ?)
        """, (id_imagen, fecha_verificacion, resultado))
        connection.commit()
        print(f"Comparación insertada para imagen {id_imagen}")
        
    except pyodbc.Error as e:
        print(f"Error al insertar en la tabla Comparacion: {e}")
        connection.rollback()
    finally:
        cursor.close()
        connection.close()
