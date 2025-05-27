# Pondremos una libreria (minuscula es la libreria y mayusculas son los metodos que tiene la libreria):
from fastapi import FastAPI, HTTPException # HTTPException es un error de tipo petición
from pydantic import BaseModel  # Para validar y estructurar datos de entrada
import cx_Oracle # libreria que conecta python con ORACLE
import bcrypt  # libreria para hashear y validar contraseñas

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

# GET
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
