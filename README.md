# 🚀 FAST API de Clientes - FERREMAS

**FERREMAS Online: Transformación Digital**
Esta API fue desarrollada como parte del proyecto de digitalización de la empresa FERREMAS. Permite gestionar clientes a través de operaciones, así como autenticar usuarios mediante un sistema de login seguro. Se conecta con una base de datos Oracle y está preparada para integrarse con un frontend móvil o web (por ejemplo, Ionic).

---

🔄 Subir API a GitHub por primera vez

```bash
git config --global user.name "Tu Nombre"
git config --global user.email "tu.correo@duocuc.cl"

git init
git add .
git commit -m "Primer commit - estructura base"
git branch -M main
git remote add origin https://github.com/usuario/repositorio.git
git push -u origin main
```

🔄 Subir API a GitHub ya existente

```bash
git config --global user.name "Tu Nombre"
git config --global user.email "tu.correo@duocuc.cl"

git add .
git commit -m "Primer commit - estructura base"
git push
```

🔃 Descargar API desde GitHub

```bash
cd carpeta_destino
git clone https://github.com/usuario/repositorio.git
cd api-clientes-ferremas

python -m venv venv
source venv/Scripts/activate

pip install -r requirements.txt
code .
```

# Si es primera vez que usarás Oracle:

```bash
pip install cx_Oracle
pip freeze > requirements.txt
```

🔌 Conectar con Oracle
En Oracle SQL Developer como usuario `system`, ejecutar:

```sql
DROP USER integracion CASCADE;
ALTER SESSION SET "_ORACLE_SCRIPT" = TRUE;
CREATE USER integracion IDENTIFIED BY 1234;
GRANT CONNECT, RESOURCE, DBA TO integracion;
```

Luego iniciar sesión con ese usuario y ejecutar el script SQL para crear la tabla `CLIENTES`.

Asegúrate de actualizar el archivo `main.py` con los datos de conexión de tu equipo (usuario, clave, puerto y servicio).

🌐 Encontrar nombre del servicio y puerto Oracle
Ir al disco `C:\Oracle\...` o la carpeta donde esté instalada tu base de datos.
Buscar el archivo `tnsnames.ora`.
Allí encontrarás el nombre del servicio (XE, XEPDB1, etc.) y el puerto (normalmente 1521).

▶️ Levantar el servidor

```bash
uvicorn app.main:api --reload

# O en otro puerto si el 8000 está ocupado:
uvicorn app.main:api --reload --port 8080
```

🔄 Actualizar contraseñas antiguas a formato hash

```bash
python app/actualizar_hash.py
```

🗃️ Estructura del proyecto

```text
📆 api-clientes-ferremas
 ├️ 📂 app
 │ ├️ main.py
 │ └️ actualizar_hash.py
 ├️ requirements.txt
 └️ README.md
```

---

## 👨‍💻 Autores

* **Jeison Padilla Suarez**
  📧 [je.padilla@duocuc.cl](mailto:je.padilla@duocuc.cl)

* **Victoria Bahamondes Araya**
  📧 [vic.bahamondes@duocuc.cl](mailto:vic.bahamondes@duocuc.cl)

---

## 🧰 Tecnologías utilizadas

* [FastAPI](https://fastapi.tiangolo.com/)
* [Uvicorn](https://www.uvicorn.org/)
* [cx\_Oracle](https://oracle.github.io/python-cx_Oracle/)
* [bcrypt](https://pypi.org/project/bcrypt/)
* Oracle Database 21c XE
* Python 3.10+
* Postman / Insomnia / Thunder Client (para pruebas)
* Git

---

## ⚙️ Instalación y uso

### 🛠️ Crear API desde cero

```bash
# Crear carpeta del proyecto
cd ruta/deseada
mkdir api-clientes-ferremas
cd api-clientes-ferremas

# Crear entorno virtual y activarlo
python -m venv venv
source venv/Scripts/activate   # En Windows
# source venv/bin/activate     # En Linux/macOS

# Instalar dependencias principales
pip install fastapi uvicorn

# Guardar dependencias
pip freeze > requirements.txt

# Crear estructura de archivos
mkdir app
touch app/main.py

# Abrir en Visual Studio Code
code .
```

---

🔐 Seguridad
Las contraseñas de clientes se almacenan en formato cifrado usando bcrypt.

Las consultas a la base de datos están protegidas contra SQL Injection mediante variables bind.

CORS configurado para permitir acceso desde otras plataformas como Ionic o React.

---

🔁 Endpoints disponibles

🔐 **POST /login**
Autenticación del cliente.

```json
{
  "email": "cliente@correo.cl",
  "contrasenia": "clave123"
}
```

➕ **POST /clientes**
Crea un nuevo cliente.

```json
{
  "rut": 12345678,
  "nombre_completo": "Ana López",
  "email": "ana@correo.cl",
  "contrasenia": "miclave",
  "region": "Valparaíso",
  "comuna": "Viña del Mar",
  "direccion": "Calle 123"
}
```

📅 **GET /clientes**
Obtiene todos los clientes.

✏️ **PUT /clientes/{rut}**
Actualiza completamente los datos de un cliente.

🧹 **PATCH /clientes/{rut}**
Modifica campos específicos del cliente.

❌ **DELETE /clientes/{rut}**
Elimina un cliente por RUT.

---

📁 Documentación interactiva

* Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* Redoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

🧪 Pruebas recomendadas
Recomendamos utilizar:

* Postman
* Insomnia
* Thunder Client

Ejemplo de prueba con login:

```http
POST http://127.0.0.1:8000/login
Content-Type: application/json

{
  "email": "juan@correo.cl",
  "contrasenia": "clave123"
}
```

---

🔄 Buenas prácticas de desarrollo

* Mantén `requirements.txt` actualizado con `pip freeze > requirements.txt`.
* Usa `source venv/Scripts/activate` siempre antes de levantar el servidor.
* Evita dejar contraseñas visibles en el código, especialmente al subir a GitHub.
* Usa `.env` para variables sensibles si decides escalar la aplicación.

---

📬 Contacto
¿Tienes dudas, sugerencias o encontraste un bug? Contáctanos:

* **Jeison Padilla Suarez**
  📧 [je.padilla@duocuc.cl](mailto:je.padilla@duocuc.cl)

* **Victoria Bahamondes Araya**
  📧 [vic.bahamondes@duocuc.cl](mailto:vic.bahamondes@duocuc.cl)

---

📄 Licencia
Este proyecto fue desarrollado como parte del trabajo académico del curso de INtegración de plataformas en Duoc UC.
Está permitido su uso con fines educativos. Para otros fines, contactar a los autores.
