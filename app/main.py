# Pondremos una libreria (minuscula es la libreria y mayusculas son los metodos que tiene la libreria):
from fastapi import FastAPI, HTTPException # HTTPException es un error de tipo petición
from pydantic import BaseModel, Field # Para validar y estructurar datos de entrada; Field se usará para definir opcionales
import cx_Oracle # libreria que conecta python con ORACLE
import bcrypt  # libreria para hashear y validar contraseñas
from typing import Optional # para campos opcionales en PATCH

# creamos una variable de la API:
api = FastAPI()

# Modelo para validar datos de login (estructura que espera el endpoint):
class LoginData(BaseModel):
    email: str
    contrasenia: str

# Modelo para validar datos de cliente al crear o actualizar:
class Cliente(BaseModel):
    rut: int
    nombre_completo: str
    email: str
    contrasenia: str
    region: str
    comuna: str
    direccion: str

# Modelo para PATCH: todos los campos son opcionales (excepto rut, que se recibe en path)
class ClientePatch(BaseModel):
    nombre_completo: Optional[str] = None
    email: Optional[str] = None
    contrasenia: Optional[str] = None
    region: Optional[str] = None
    comuna: Optional[str] = None
    direccion: Optional[str] = None

# Haremos la conexión con ORACLE:
def get_conexion(): # variable de conexion
    try:
        dsn = cx_Oracle.makedsn("localhost", 1521, service_name="XE") # con dsn le digo de donde vienen los datos para la conexion / se llama a cx_Oracle para crear el origen de datos y se le entrega: nombre o número del host, puerto, nombre del servidor(en cada pc es diferente)
        conexion = cx_Oracle.connect(user="integracion", password="integracion", dsn=dsn) # con esto creamos la conexion y entregamos 3 cosas: usuario de BD, clave usuario BD, donde se va a conectar
        return conexion
    except Exception as ex:
        print("Error al conectar:", ex)
        raise

# Ahora haremos endpoints:

# GET para listar los clientes
@api.get("/clientes") # en / va la ruta en la que aparecerán los datos
def get_clientes():
    try:
        cone = get_conexion() # se crea variable y se le entrega a cone
        cursor = cone.cursor() # cursor es un elemento ejecutable que permite ejecutar comandos sql de una bd
        sql1 = "SELECT RUT, NOMBRE_COMPLETO, EMAIL, CONTRASENIA, REGION, COMUNA, DIRECCION FROM CLIENTES" # Creo la variable de la petición y escribo el SELECT de la bd
        cursor.execute(sql1) # ejecuto la variable de la petición
        rows = cursor.fetchall() # Con esto tomo todo el resultado del select
        lista1 = [] # creamos lista para guardar todos los clientes de la bd uno por uno
        for c in rows: # creo c de clientes
            cliente = {"RUT": c[0], "NOMBRE_COMPLETO": c[1], "EMAIL": c[2], "CONTRASENIA": c[3], "REGION": c[4], "COMUNA": c[5], "DIRECCION": c[6]} # creo variable/diccionario y le pongo los atributos del select
            lista1.append(cliente) # esto recorre cliente por cliente buscando todos los datos solicitados
        return lista1 # Aqui devuelve la lista con todos los clientes
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener usuarios: {str(e)}") # Error de tipo petición y se le entregan: codigo de error, mensaje a entregar con ese codigo y se convierte a string la variable
    finally:
        if 'cursor' in locals(): # Esto cierra el cursor
            cursor.close()
        if 'cone' in locals(): # Esto cierra la conexión
            cone.close()

# POST para login, validando contraseña con hash
@api.post("/login")
def login(datos: LoginData): # recibe un JSON con email y contrasenia validado con LoginData
    try:
        cone = get_conexion() # se crea variable y se le entrega a cone
        cursor = cone.cursor() # cursor es un elemento ejecutable que permite ejecutar comandos sql de una bd
        sql = "SELECT CONTRASENIA FROM CLIENTES WHERE EMAIL = :email"  # buscamos la contraseña hash guardada en bd para ese email
        cursor.execute(sql, {"email": datos.email}) # ejecuto la variable de la petición
        resultado = cursor.fetchone()
        
        if resultado is None:
            # No existe ese email en la BD
            raise HTTPException(status_code=401, detail="Email o contraseña incorrectos")

        password_hash_db = resultado[0]  # contraseña almacenada en la BD (hash)
        # Validamos el password ingresado con el hash almacenado
        if bcrypt.checkpw(datos.contrasenia.encode('utf-8'), password_hash_db.encode('utf-8')):
            return {"mensaje": "Login exitoso"}
        else:
            raise HTTPException(status_code=401, detail="Email o contraseña incorrectos")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en login: {str(e)}") #Error de tipo petición y se le entregan: codigo de error, mensaje a entregar con ese codigo y se convierte a string la variable
    finally:
        if 'cursor' in locals(): #Esto cierra el cursor
            cursor.close()
        if 'cone' in locals(): #Esto cierra la conexión
            cone.close()

# POST para crear un nuevo cliente
@api.post("/clientes")
def crear_cliente(cliente: Cliente):
    try:
        cone = get_conexion() # conexion
        cursor = cone.cursor() # cursor
        # Hasheamos la contraseña antes de guardarla
        hashed_password = bcrypt.hashpw(cliente.contrasenia.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        # Insert SQL con bind variables para evitar inyección SQL
        sql = """
        INSERT INTO CLIENTES (RUT, NOMBRE_COMPLETO, EMAIL, CONTRASENIA, REGION, COMUNA, DIRECCION)
        VALUES (:rut, :nombre, :email, :contrasenia, :region, :comuna, :direccion)
        """
        cursor.execute(sql, {
            "rut": cliente.rut,
            "nombre": cliente.nombre_completo,
            "email": cliente.email,
            "contrasenia": hashed_password,
            "region": cliente.region,
            "comuna": cliente.comuna,
            "direccion": cliente.direccion
        })
        cone.commit()
        return {"mensaje": "Cliente creado exitosamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear cliente: {str(e)}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'cone' in locals():
            cone.close()

# PUT para actualizar un cliente existente (por rut)
@api.put("/clientes/{rut}")
def actualizar_cliente(rut: int, cliente: Cliente):
    try:
        cone = get_conexion()
        cursor = cone.cursor()
        # Hasheamos la contraseña antes de actualizar
        hashed_password = bcrypt.hashpw(cliente.contrasenia.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # Verificamos que el cliente exista
        cursor.execute("SELECT RUT FROM CLIENTES WHERE RUT = :rut", {"rut": rut})
        if cursor.fetchone() is None:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")

        # Actualizamos los datos
        sql = """
        UPDATE CLIENTES SET
            NOMBRE_COMPLETO = :nombre,
            EMAIL = :email,
            CONTRASENIA = :contrasenia,
            REGION = :region,
            COMUNA = :comuna,
            DIRECCION = :direccion
        WHERE RUT = :rut
        """
        cursor.execute(sql, {
            "nombre": cliente.nombre_completo,
            "email": cliente.email,
            "contrasenia": hashed_password,
            "region": cliente.region,
            "comuna": cliente.comuna,
            "direccion": cliente.direccion,
            "rut": rut
        })
        cone.commit()
        return {"mensaje": "Cliente actualizado exitosamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar cliente: {str(e)}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'cone' in locals():
            cone.close()

# DELETE para eliminar un cliente por rut
@api.delete("/clientes/{rut}")
def eliminar_cliente(rut: int):
    try:
        cone = get_conexion()
        cursor = cone.cursor()
        # Verificamos que exista el cliente antes de eliminar
        cursor.execute("SELECT RUT FROM CLIENTES WHERE RUT = :rut", {"rut": rut})
        if cursor.fetchone() is None:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
        # Ejecutamos delete
        cursor.execute("DELETE FROM CLIENTES WHERE RUT = :rut", {"rut": rut})
        cone.commit()
        return {"mensaje": "Cliente eliminado exitosamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar cliente: {str(e)}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'cone' in locals():
            cone.close()

# PATCH para actualizar parcialmente un cliente (por rut)
@api.patch("/clientes/{rut}")
def actualizar_cliente_parcial(rut: int, cliente: ClientePatch): # Recibe rut por path y datos parciales en body
    try:
        cone = get_conexion() # Creamos conexión
        cursor = cone.cursor() # Creamos cursor

        # Verificamos que el cliente exista antes de actualizar
        cursor.execute("SELECT RUT FROM CLIENTES WHERE RUT = :rut", {"rut": rut})
        if cursor.fetchone() is None:
            raise HTTPException(status_code=404, detail="Cliente no encontrado") # Si no existe, error 404

        campos_a_actualizar = [] # Lista que almacenará los campos a actualizar en SQL
        valores = {} # Diccionario para los valores bind del execute

        # Por cada campo opcional que venga en el JSON, se agrega a la lista y al diccionario
        if cliente.nombre_completo is not None:
            campos_a_actualizar.append("NOMBRE_COMPLETO = :nombre")
            valores["nombre"] = cliente.nombre_completo
        if cliente.email is not None:
            campos_a_actualizar.append("EMAIL = :email")
            valores["email"] = cliente.email
        if cliente.contrasenia is not None:
            # Hasheamos la contraseña si viene para actualizar
            hashed_password = bcrypt.hashpw(cliente.contrasenia.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            campos_a_actualizar.append("CONTRASENIA = :contrasenia")
            valores["contrasenia"] = hashed_password
        if cliente.region is not None:
            campos_a_actualizar.append("REGION = :region")
            valores["region"] = cliente.region
        if cliente.comuna is not None:
            campos_a_actualizar.append("COMUNA = :comuna")
            valores["comuna"] = cliente.comuna
        if cliente.direccion is not None:
            campos_a_actualizar.append("DIRECCION = :direccion")
            valores["direccion"] = cliente.direccion

        if not campos_a_actualizar:
            # Si no se envió ningún campo para actualizar, devolvemos error 400
            raise HTTPException(status_code=400, detail="No se enviaron campos para actualizar")

        valores["rut"] = rut # agregamos el rut para la cláusula WHERE

        # Construimos la consulta SQL dinámicamente
        sql = f"UPDATE CLIENTES SET {', '.join(campos_a_actualizar)} WHERE RUT = :rut"

        cursor.execute(sql, valores) # Ejecutamos la consulta con los valores bind
        cone.commit() # Confirmamos los cambios en la base de datos

        return {"mensaje": "Cliente actualizado parcialmente exitosamente"} # Mensaje de éxito

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar cliente parcialmente: {str(e)}") # Manejo de error
    finally:
        if 'cursor' in locals(): # Cerramos cursor si existe
            cursor.close()
        if 'cone' in locals(): # Cerramos conexión si existe
            cone.close()
