# Pondremos una libreria (minuscula es la libreria y mayusculas son los metodos que tiene la libreria):
from fastapi import FastAPI, HTTPException  # HTTPException es un error de tipo petición
from pydantic import BaseModel, Field  # Para validar y estructurar datos de entrada; Field lo uso para definir opcionales xd
import cx_Oracle  # libreria que conecta python con ORACLE
import bcrypt  # libreria para hashear y validar contraseñas
from typing import Optional  # para campos opcionales en PATCH
import re #Para la validación del rut

# Valida que el RUT tenga el formato chileno sin puntos y con guion (ej: 12345678-9)
def validar_formato_rut(rut: str) -> bool:
    return bool(re.match(r"^\d{7,8}-[\dkK]$", rut))

#Validar que el digito verificador y el rut correspondan
def validar_rut_con_dv(rut: str) -> bool:
    if not validar_formato_rut(rut):
        return False

    cuerpo, dv_ingresado = rut.upper().split("-")
    suma = 0
    multiplicador = 2

    for digito in reversed(cuerpo):
        suma += int(digito) * multiplicador
        multiplicador += 1
        if multiplicador > 7:
            multiplicador = 2

    resto = suma % 11
    dv_calculado = 11 - resto

    if dv_calculado == 11:
        dv_correcto = "0"
    elif dv_calculado == 10:
        dv_correcto = "K"
    else:
        dv_correcto = str(dv_calculado)

    return dv_ingresado == dv_correcto

# Importamos middleware para manejar CORS (control de acceso desde distintos dominios)
from fastapi.middleware.cors import CORSMiddleware  

# crearé una variable de la API:
api = FastAPI()  # Instanciamos la aplicación FastAPI

# Definimos lista con orígenes permitidos para acceder a la API (solo estos podrán hacer peticiones)
origins = [
    "http://localhost",      # Permitir el localhost básico
    "http://localhost:8100", # Puerto común para Ionic en el desarrollo
    # aqui abajito le podemos agregar otros adicionales
]

# Agregamos middleware CORS a la API para controlar accesos desde distintos dominios
api.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       # Aquí le decimos que sólo estos orígenes podrán acceder
    allow_credentials=True,      # Permitir envío de cookies y headers con credenciales
    allow_methods=["*"],         # Permitir todos los métodos HTTP (GET, POST, PUT, DELETE, etc)
    allow_headers=["*"],         # Permitir todos los headers
)

# Modelo para validar datos de login (estructura que espera el endpoint):
class LoginData(BaseModel):
    email: str  # Email del cliente
    contrasenia: str  # Contraseña del cliente

# Modelo para validar datos de cliente al crear o actualizar:
class Cliente(BaseModel):
    rut: str  # RUT único del cliente
    nombre_completo: str  # Nombre completo del cliente
    email: str  # Email del cliente
    contrasenia: str  # Contraseña (en texto plano para hashear al guardar)
    region: str  # Región de residencia
    comuna: str  # Comuna de residencia
    direccion: str  # Dirección del cliente

# Modelo para PATCH: todos los campos son opcionales (excepto rut, que se recibe en path)
class ClientePatch(BaseModel):
    nombre_completo: Optional[str] = None  # Nombre completo opcional para actualización parcial
    email: Optional[str] = None  # Email opcional
    contrasenia: Optional[str] = None  # Contraseña opcional
    region: Optional[str] = None  # Región opcional
    comuna: Optional[str] = None  # Comuna opcional
    direccion: Optional[str] = None  # Dirección opcional

# Haremos la conexión con ORACLE:
def get_conexion():  # variable de conexion
    try:
        dsn = cx_Oracle.makedsn("localhost", 1521, service_name="XE")  # Aqui va el DSN (Data Source Name) con host, puerto y servicio de la base de datos
        conexion = cx_Oracle.connect(user="integracion", password="integracion", dsn=dsn)  # Aqui va la conexión usando usuario, contraseña y DSN
        return conexion  # Devolvemos conexión activa
    except Exception as ex:
        print("Error al conectar:", ex)  # Mostramos error en consola
        raise  # Re-lanzamos error para manejarlo afuera

# Ahora Haré algunos endpoints:

# GET para listar los clientes
@api.get("/clientes")  # Ruta para listar clientes
def get_clientes():
    try:
        cone = get_conexion()  # se crea variable y se le entrega a cone
        cursor = cone.cursor()  # cursor es un elemento ejecutable que permite ejecutar comandos sql de una bd
        sql1 = "SELECT RUT, NOMBRE_COMPLETO, EMAIL, CONTRASENIA, REGION, COMUNA, DIRECCION FROM CLIENTES"  # Consulta para obtener todos los campos relevantes de la tabla CLIENTES
        cursor.execute(sql1)  # ejecuto la variable de la petición
        rows = cursor.fetchall()  # Con esto tomo todo el resultado del select
        lista1 = []  # creamos lista para guardar todos los clientes de la bd uno por uno
        for c in rows:  # creo c de clientes
            cliente = {"RUT": c[0], "NOMBRE_COMPLETO": c[1], "EMAIL": c[2], "CONTRASENIA": c[3], "REGION": c[4], "COMUNA": c[5], "DIRECCION": c[6]}  # Aqui va el diccionario con los datos de cada cliente, usando índices de columnas
            lista1.append(cliente)  # agregamos el diccionario a la lista
        return lista1  # Aqui devuelve la lista con todos los clientes
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener usuarios: {str(e)}")  # Si ocurre error devolvemos código 500 con detalle del error
    finally:
        if 'cursor' in locals():  # Esto cierra el cursor
            cursor.close()
        if 'cone' in locals(): #Esto cierra la conexión
            cone.close()

# POST para login, validando contraseña con hash
@api.post("/login")  # Ruta para login
def login(datos: LoginData):  # recibe un JSON con email y contrasenia validado con LoginData
    try:
        cone = get_conexion()  # se crea variable y se le entrega a cone
        cursor = cone.cursor()  # cursor es un elemento ejecutable que permite ejecutar comandos sql de una bd
        sql = "SELECT CONTRASENIA FROM CLIENTES WHERE EMAIL = :email"  # Consulta para obtener contraseña hasheada almacenada para ese email
        cursor.execute(sql, {"email": datos.email})  # ejecuto la variable de la petición
        resultado = cursor.fetchone()  # Tomamos primer resultado (único)

        if resultado is None:
            raise HTTPException(status_code=401, detail="Email o contraseña incorrectos") # Este error es en caso de que no exista ese email en la BD, error 401

        password_hash_db = resultado[0]  # contraseña almacenada en la BD (hash)
        if bcrypt.checkpw(datos.contrasenia.encode('utf-8'), password_hash_db.encode('utf-8')): # Aqui se valida el password ingresado con el hash almacenado
            return {"mensaje": "Login exitoso"}  # Login correcto
        else:
            raise HTTPException(status_code=401, detail="Email o contraseña incorrectos")  # Error login por datos incorrectos

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en login: {str(e)}")  # Error general de servidor en login
    finally:
        if 'cursor' in locals(): # Esto cierra el cursor
            cursor.close()
        if 'cone' in locals(): # Esto cierra la conexión
            cone.close()

# POST para crear un nuevo cliente
@api.post("/clientes")  # Ruta para crear cliente
def crear_cliente(cliente: Cliente):
        # Validar formato del RUT
    if not validar_rut_con_dv(cliente.rut):
        raise HTTPException(status_code=400, detail="El RUT ingresado no es válido o tiene un dígito verificador incorrecto. Ejemplo correcto: 12345678-9")
    # Validar que el nombre no sea solo números
    if re.fullmatch(r'\d+', cliente.nombre_completo):
        raise HTTPException(status_code=400, detail="El nombre no puede contener solo números")

    try:
        cone = get_conexion()  # conexion
        cursor = cone.cursor()  # cursor
        hashed_password = bcrypt.hashpw(cliente.contrasenia.encode('utf-8'), bcrypt.gensalt()).decode('utf-8') # Hasheamos la contraseña antes de guardarla para seguridad
        sql = """
        INSERT INTO CLIENTES (RUT, NOMBRE_COMPLETO, EMAIL, CONTRASENIA, REGION, COMUNA, DIRECCION) 
        VALUES (:rut, :nombre, :email, :contrasenia, :region, :comuna, :direccion) 
        """ # Insert SQL con bind variables para evitar inyección SQL
        cursor.execute(sql, {
            "rut": cliente.rut,
            "nombre": cliente.nombre_completo,
            "email": cliente.email,
            "contrasenia": hashed_password,
            "region": cliente.region,
            "comuna": cliente.comuna,
            "direccion": cliente.direccion
        })
        cone.commit()  # Confirmamos cambios en la base de datos
        return {"mensaje": "Cliente creado exitosamente"}  # Mensaje de éxito
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear cliente: {str(e)}") # Error al crear cliente
    finally:
        if 'cursor' in locals(): #Esto cierra el cursor
            cursor.close()
        if 'cone' in locals(): # Esto cierra la conexión
            cone.close()

# PUT para actualizar un cliente existente (por rut)
@api.put("/clientes/{rut}")  # Ruta para actualizar cliente completo
def actualizar_cliente(rut: str, cliente: Cliente):
        # Validar formato del RUT recibido
    if not validar_rut_con_dv(rut):
        raise HTTPException(status_code=400, detail="El RUT ingresado no es válido o tiene un dígito verificador incorrecto. Ejemplo correcto: 12345678-9")

    try:
        cone = get_conexion()  # conexión
        cursor = cone.cursor()  # cursor
        hashed_password = bcrypt.hashpw(cliente.contrasenia.encode('utf-8'), bcrypt.gensalt()).decode('utf-8') # Hasheamos la contraseña antes de actualizar para seguridad

        cursor.execute("SELECT RUT FROM CLIENTES WHERE RUT = :rut", {"rut": rut}) # Con esto validamos que el cliente exista antes de actualizar
        if cursor.fetchone() is None:
            raise HTTPException(status_code=404, detail="Cliente no encontrado") # Este error se usa en caso que el cliente no exista, error 404

        # Actualizamos todos los campos del cliente
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
        cone.commit()  # Confirmamos cambios
        return {"mensaje": "Cliente actualizado exitosamente"}  # Mensaje éxito
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar cliente: {str(e)}") # Error general al actualizar cliente
    finally:
        if 'cursor' in locals(): # Esto cierra el cursor
            cursor.close()
        if 'cone' in locals(): # Esto ciera la conexión
            cone.close()

# DELETE para eliminar un cliente por rut
@api.delete("/clientes/{rut}")  # Ruta para eliminar cliente
def eliminar_cliente(rut: str):
        # Validar formato del RUT recibido
    if not validar_rut_con_dv(rut):
        raise HTTPException(status_code=400, detail="El RUT ingresado no es válido o tiene un dígito verificador incorrecto. Ejemplo correcto: 12345678-9")

    try:
        cone = get_conexion()  # conexión
        cursor = cone.cursor()  # cursor
        cursor.execute("SELECT RUT FROM CLIENTES WHERE RUT = :rut", {"rut": rut}) # Verificamos que exista el cliente antes de eliminar
        if cursor.fetchone() is None:
            raise HTTPException(status_code=404, detail="Cliente no encontrado") # Este error se usa si el cliente no se encuentra, error 404
        cursor.execute("DELETE FROM CLIENTES WHERE RUT = :rut", {"rut": rut}) # Aquí ejecutamos la eliminación
        cone.commit()  # Confirmamos cambios
        return {"mensaje": "Cliente eliminado exitosamente"}  # Mensaje de éxito
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar cliente: {str(e)}") # Error general al eliminar cliente
    finally:
        if 'cursor' in locals(): # Esto cierra el cursor
            cursor.close()
        if 'cone' in locals(): # Esto cierra la conexión
            cone.close()

# PATCH para actualizar parcialmente un cliente (por rut)
@api.patch("/clientes/{rut}")  # Ruta para actualización parcial
def actualizar_cliente_parcial(rut: str, cliente: ClientePatch):  # Recibe rut por path y datos parciales en body
        # Validar formato del RUT recibido
    if not validar_rut_con_dv(rut):
        raise HTTPException(status_code=400, detail="El RUT ingresado no es válido o tiene un dígito verificador incorrecto. Ejemplo correcto: 12345678-9")

    try:
        cone = get_conexion()  # Creamos conexión
        cursor = cone.cursor()  # Creamos cursor

        cursor.execute("SELECT RUT FROM CLIENTES WHERE RUT = :rut", {"rut": rut}) # Verificamos que el cliente exista antes de actualizar
        if cursor.fetchone() is None:
            raise HTTPException(status_code=404, detail="Cliente no encontrado") # Este eror se usa si el cliente no se encuentra, error 404

        campos_a_actualizar = []  # Lista que almacenará los campos a actualizar en SQL
        valores = {}  # Diccionario para los valores bind del execute

        # Por cada campo opcional que venga en el JSON, se agrega a la lista y al diccionario
        if cliente.nombre_completo is not None:
            campos_a_actualizar.append("NOMBRE_COMPLETO = :nombre")
            valores["nombre"] = cliente.nombre_completo
        if cliente.email is not None:
            campos_a_actualizar.append("EMAIL = :email")
            valores["email"] = cliente.email
        if cliente.contrasenia is not None:
            hashed_password = bcrypt.hashpw(cliente.contrasenia.encode('utf-8'), bcrypt.gensalt()).decode('utf-8') # Hasheamos la contraseña si viene para actualizar
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
            raise HTTPException(status_code=400, detail="No se enviaron campos para actualizar") # Si no se envió ningún campo para actualizar, devolvemos error 400

        valores["rut"] = rut  # agregamos el rut para la cláusula WHERE

        sql = f"UPDATE CLIENTES SET {', '.join(campos_a_actualizar)} WHERE RUT = :rut" # Construimos la consulta SQL dinámicamente con los campos a actualizar

        cursor.execute(sql, valores)  # Ejecutamos la consulta con los valores bind
        cone.commit()  # Confirmamos los cambios en la base de datos

        return {"mensaje": "Cliente actualizado parcialmente exitosamente"}  # Mensaje de éxito

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar cliente parcialmente: {str(e)}") # Manejo de error general en actualización parcial
    finally:
        if 'cursor' in locals(): # Esto cierra el cursor
            cursor.close()
        if 'cone' in locals(): #Esto cierra la conexión
            cone.close()
