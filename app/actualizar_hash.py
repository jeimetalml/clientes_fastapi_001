import cx_Oracle
import bcrypt

def get_conexion():
    try:
        dsn = cx_Oracle.makedsn("localhost", 1521, service_name="XE")
        conexion = cx_Oracle.connect(user="integracion", password="integracion", dsn=dsn)
        return conexion
    except Exception as e:
        print("Error al conectar a BD:", e)
        raise

def es_hash_bcrypt(password):
    # Un hash bcrypt siempre comienza con $2b$ o $2a$, tiene longitud fija de 60 chars
    if password is None:
        return False
    return (password.startswith("$2b$") or password.startswith("$2a$")) and len(password) == 60

def actualizar_contrasenas():
    try:
        conexion = get_conexion()
        cursor = conexion.cursor()
        
        # Obtener RUT y contrasena actual de todos los clientes
        cursor.execute("SELECT RUT, CONTRASENIA FROM CLIENTES")
        clientes = cursor.fetchall()

        for rut, contrasenia in clientes:
            if contrasenia is None:
                print(f"[{rut}] Contraseña vacía, saltando...")
                continue

            # Verificar si la contraseña es hash bcrypt válido
            if es_hash_bcrypt(contrasenia):
                # Verificamos que el hash sea válido tratando de validar la contraseña con el hash
                # Aquí no tenemos la contraseña original para probar, solo validamos formato
                print(f"[{rut}] Contraseña parece hash bcrypt válido, no se cambia.")
                continue
            else:
                # Contraseña no tiene formato bcrypt válido, asumimos que está en texto plano
                print(f"[{rut}] Contraseña sin hash válido, se aplicará hash bcrypt.")

                # Aquí tenemos que hashéar la contraseña
                # Si la contraseña está guardada en texto plano: 
                # Si es el hash viejo, no se puede saber la contraseña original, pero suponemos que sí es texto plano
                password_bytes = contrasenia.encode('utf-8')
                hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
                hashed_str = hashed.decode('utf-8')

                # Actualizamos la contraseña con el hash correcto
                try:
                    cursor.execute("UPDATE CLIENTES SET CONTRASENIA = :p_hash WHERE RUT = :p_rut",
                                   {"p_hash": hashed_str, "p_rut": rut})
                    conexion.commit()
                    print(f"[{rut}] Contraseña actualizada a hash bcrypt correctamente.")
                except Exception as e:
                    print(f"[{rut}] ERROR al actualizar contraseña: {e}")

    except Exception as e:
        print("Error general:", e)
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conexion' in locals():
            conexion.close()

if __name__ == "__main__":
    actualizar_contrasenas()
