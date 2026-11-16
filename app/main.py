import os
import random
import socket
import threading
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI(title="Picas y Fijas distribuid")

jugadores = {}
juegos = {}
siguiente_id = 1

candado = threading.Lock()

POR_INICIAR = "por iniciar"
EN_JUEGO = "en juego"
TERMINADO = "terminado"

class Login(BaseModel):
    nombre: str

class JugadorNumero(BaseModel):
    nombre: str
    numero: str

def validar_numero(numero):
    numero = numero.strip()
    if numero == "":
        raise HTTPException(status_code=400, detail="Debe enviar un número.")
    for c in numero:
        if c not in "0123456789":
            raise HTTPException(status_code=400, detail="El número solo puede tener dígitos del 0 al 9.")
    if len(numero) != 4:
        raise HTTPException(status_code=400, detail="El número debe tener exactamente 4 dígitos.")
    if len(set(numero)) != 4:
        raise HTTPException(status_code=400, detail="El número no puede tener dígitos repetidos.")
    return numero

def calcular_picas_fijas(secreto, intento):
    fijas = 0
    picas = 0
    for i in range(4):
        if intento[i] == secreto[i]:
            fijas += 1
        elif intento[i] in secreto:
            picas += 1
    return picas, fijas

def validar_jugador(nombre):
    nombre = nombre.strip()
    if nombre not in jugadores:
        raise HTTPException(status_code=404, detail="El jugador '" + nombre + "' no existe. Por favor, primero haga /login para registrarse.")
    return nombre

def buscar_juego(id_juego):
    if id_juego not in juegos:
        raise HTTPException(status_code=404, detail="El juego " + str(id_juego) + " no existe.")
    return juegos[id_juego]

def ver_juego(juego):
    datos = {
        "id": juego["id"],
        "creador": juego["creador"],
        "estado": juego["estado"],
        "jugadores": juego["jugadores"],
        "turno": juego["turno"],
        "ganador": juego["ganador"],
        "intentos": juego["intentos"],
        "creado": juego["creado"],
    }
    if juego["estado"] == TERMINADO:
        datos["numeros_secretos"] = juego["numeros"]
    return datos

def hora_actual():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@app.post("/login")
def login(datos: Login):
    nombre = datos.nombre.strip()
    if nombre == "":
        raise HTTPException(status_code=400, detail="El nombre no puede estar vacío.")
    if len(nombre) > 20:
        raise HTTPException(status_code=400, detail="El nombre no puede tener más de 20 caracteres.")
    for c in nombre:
        if not (c.isalpha() or c == " "):
            raise HTTPException(status_code=400, detail="El nombre solo puede tener letras y espacios.")
    with candado:
        if nombre in jugadores:
            return {"mensaje": "Bienvenido de nuevo " + nombre, "nombre": nombre}
        jugadores[nombre] = hora_actual()
    return {"mensaje": "Jugador " + nombre + " registrado correctamente.",
            "nombre": nombre
            }

@app.post("/juego", status_code=201)
def crear_juego(datos: JugadorNumero):
    global siguiente_id
    nombre = validar_jugador(datos.nombre)
    numero = validar_numero(datos.numero)
    with candado:
        id_juego = siguiente_id
        siguiente_id += 1
        juegos[id_juego] = {
            "id": id_juego,
            "creador": nombre,
            "estado": POR_INICIAR,
            "jugadores": [nombre],
            "numeros": {nombre: numero},
            "turno": None,
            "ganador": None,
            "intentos": [],
            "creado": hora_actual(),
        }
        return {"mensaje": "Juego creado, esperando al otro jugador.",
                "juego": ver_juego(juegos[id_juego])
                }

@app.put("/juego/{id_juego}")
def unirse_juego(id_juego: int, datos: JugadorNumero):
    nombre = validar_jugador(datos.nombre)
    numero = validar_numero(datos.numero)
    with candado:
        juego = buscar_juego(id_juego)
        if juego["estado"] != POR_INICIAR:
            raise HTTPException(status_code=409, detail="El juego ya ha comenzado o ha terminado.")
        if nombre == juego["creador"]:
            raise HTTPException(status_code=400, detail="El creador del juego no puede unirse como jugador.")
        juego["jugadores"].append(nombre)
        juego["numeros"][nombre] = numero
        juego["estado"] = EN_JUEGO
        juego["turno"] = random.choice(juego["jugadores"])
        return {"mensaje": "El juego ha comenzado, empieza " + juego["turno"],
                "juego": ver_juego(juego)}

@app.post("/juego{id_juego}/jugar")
def jugar(id_juego: int, datos: JugadorNumero):
    nombre = validar_jugador(datos.nombre)
    with candado:
        juego = buscar_juego(id_juego)
        if juego["estado"] == POR_INICIAR:
            raise HTTPException(status_code=409, detail="El juego aún no ha comenzado, espera a que se una otro jugador.")
        if juego["estado"] == TERMINADO:
            raise HTTPException(status_code=409, detail="El juego ya ha terminado.")
        if nombre not in juego["jugadores"]:
            raise HTTPException(status_code=403, detail="El jugador '" + nombre + "' no está en este juego.")
        if juego["turno"] != nombre:
            raise HTTPException(status_code=409, detail="No es tu turno de jugar, es el turno de " + juego["turno"] + ".")

        intento = validar_numero(datos.numero)

        if juego["jugadores"][0] == nombre:
            oponente = juego["jugadores"][1]
        else:
            oponente = juego["jugadores"][0]

        picas, fijas = calcular_picas_fijas(juego["numeros"][oponente], intento)
        juego["intentos"].append({
            "jugador": nombre,
            "numero": intento,
            "picas": picas,
            "fijas": fijas,
            "hora": hora_actual(),
        })

        if fijas == 4:
            juego["estado"] = TERMINADO
            juego["ganador"] = nombre
            juego["turno"] = None
            mensaje = "¡Felicidades " + nombre + "! Has ganado el juego."
        else:
            juego["turno"] = oponente
            mensaje = str(picas) + " picas y " + str(fijas) + " fijas. Ahora es el turno de " + oponente + "."

        return {"mensaje": mensaje,
                "picas": picas,
                "fijas": fijas,
                "juego": ver_juego(juego)
        }

@app.get("/juego/{id_juego}")
def estado_juego(id_juego: int):
    with candado:
        juego = buscar_juego(id_juego)
        return ver_juego(juego)

@app.get("/juego")
def listar_juegos(estado: str = None):
    with candado:
        lista = []
        for juego in juegos.values():
            if estado is not None and juego["estado"] != estado:
                continue
            lista.append({
                "id": juego["id"],
                "creador": juego["creador"],
                "estado": juego["estado"],
                "jugadores": juego["jugadores"],
                "ganador": juego["ganador"],
            })
        return {"total": len(lista),
                "juegos": lista}

@app.get("/salud")
def salud():
    return {"estado": "ok",
            "pod": socket.gethostname(),
    }
@app.get("/")
def inicio():
    ruta = os.path.join(os.path.dirname(__file__), "static", "index.html")
    return FileResponse(ruta)