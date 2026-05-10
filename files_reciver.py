import os
def get_consulta(ruta):
    contenido = ""
    if isinstance(ruta,str) and os.path.isfile(ruta):
        try:
            with open(ruta,'r',encoding='utf-8')as file:
                contenido = file.read()
        except Exception as e:
            return f"Error: {e}"
    else:
        contenido = ruta
    
    return contenido
ruta = "./texto.txt"
print(get_consulta(ruta))