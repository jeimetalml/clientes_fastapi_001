#Pondremos una libreria (minuscula es la libreria y mayusculas son los metodos que tiene la libreria):
from fastapi import FastAPI, HTTPException #HTTPException es un error de tipo petición
import cx_Oracle #libreria que conecta python con ORACLE
#creamos una variable de la API:
api = FastAPI()

#Haremos la conexión con ORACLE:
def get_conexion(): #variable de conexion
    try:
        dsn = cx_Oracle.makedsn("localhost", 1521, service_name="XE") # con dsn l edigo de donde vienen los datos para la conexion / se llama a cx_Oracle para crear el origen de datos y se le entrega: nombre o número del host, puerto, nombre del servidor(en cada pc es diferente)
        conexion = cx_Oracle.connect(user="integracion", password="integracion", dsn=dsn) #con esto creamos la conexion y entregamos 3 cosas: usuario de BD, clave usuario BD, donde se va a conectar
        return conexion
    except Exception as ex:
        print("Error al conectar:",ex)
        raise

#Ahora haremos endpoints:

#GET
@api.get("/clientes") # en / va la ruta en la que aparecerán los datos
def get_clientes():
    try:
        cone = get_conexion() #se crea variable y se le entrega a cone
        cursor = cone.cursor() #cursor es un elemento ejecutable que permite ejecutar comandos sql de una bd
        sql1 = "SELECT RUT, NOMBRE_COMPLETO, EMAIL, CONTRASENIA, REGION, COMUNA, DIRECCION FROM CLIENTES" #Creo la variable de la petición y escrivo el SELECT de la bd
        cursor.execute(sql1) #ejecuto la variable de la petición
        rows = cursor.fetchall() #Con esto tomo todo el resultado del select
        lista1 = [] #creamos lista para guardar todos los clientes de la bd uno por uno
        for c in rows: # creo c de clientes
            cliente = {"RUT": c[0], "NOMBRE_COMPLETO": c[1], "EMAIL": c[2], "CONTRASENIA": c[3], "REGION": c[4], "COMUNA": c[5], "DIRECCION": c[6]} #creo variable/diccionario y le pongo los atributos del select
            lista1.append(cliente) #esto recorre cliente por cliente buscando todos los datos solicitados
        return lista1 #Aqui devuelve la lista con todos los clientes
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obetener usuarios: {str(e)}") #Error de tipo petición y se le entregan: codigo de rror, mensaje a entregar con ese codigo y se convierte a string la variable
    finally: 
        if 'cone' in locals(): #Esto cierra la conexión
            cone.close()
        if 'cursor' in locals(): #Esto cierra el cursor
            cursor.close()
