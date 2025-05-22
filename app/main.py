#Pondremos una libreria (minuscula es la libreria y mayusculas son los metodos que tiene la libreria):
from fastapi import FastAPI

#creamos una variable de la API:
api = FastAPI()

#ahora creamos los metodos de la API:
@api.get("/")
def inicial():
    return {"mensaje": "Hola mundo 2"}

@api.get("/usuarios/{id}")
def get_usuario(id: int):
    usuarios = {
        1: {"nombre": "lalo cura", "email": "lalo.cura@gmail.com"}
    }
    return usuarios.get(id)
