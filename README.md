# Picas y Fijas - version distribuida en Kubernetes

Trabajo de Sistemas Distribuidos - Universidad de los Llanos.

API REST (JSON) del juego Picas y Fijas hecha en Python con FastAPI, con un frontend basico
y desplegable en Kubernetes. Los datos se guardan en memoria (no usa base de datos).

## Endpoints

| Metodo | Ruta | Que hace | Cuerpo JSON |
|---|---|---|---|
| POST | /login | Registra el nombre del jugador | `{"nombre":"ana"}` |
| POST | /juego | Crea un juego con el numero secreto del creador | `{"nombre":"ana","numero":"8135"}` |
| PUT | /juego/{id} | Se une a un juego; al unirse el segundo jugador el juego inicia y el primer turno es aleatorio | `{"nombre":"beto","numero":"4271"}` |
| POST | /juego/{id}/jugar | Envia un intento (solo si es su turno) y devuelve picas y fijas | `{"nombre":"beto","numero":"1234"}` |
| GET | /juego/{id} | Estado del juego: por_iniciar, en_juego o terminado (con ganador) | - |
| GET | /juego | Lista los juegos con su creador, estado y ganador. Filtro opcional `?estado=terminado` | - |
| GET | /salud | Revision de salud usada por Kubernetes; devuelve el nombre del pod | - |
| GET | / | Frontend basico | - |

Reglas del numero: exactamente 4 caracteres, solo digitos del 0 al 9 y sin digitos repetidos.
Se envia como texto (`"0123"`) para no perder el cero inicial.

Documentacion interactiva generada por FastAPI: `/docs`

## Ejecutar en local

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
# abrir http://localhost:8000
bash pruebas/pruebas.sh
```

## Docker

```bash
docker build -t bahamong/picas-fijas:1.1 .
docker run -p 8000:8000 bahamong/picas-fijas:1.1
docker login
docker push bahamong/picas-fijas:1.1
```

## Kubernetes (Killercoda)

```bash
git clone https://github.com/bahamong/picas-y-fijas-k8s.git
cd picas-y-fijas-k8s
kubectl apply -f k8s/namespace.yml
kubectl apply -f k8s/deployment.yml
kubectl apply -f k8s/service.yml
kubectl get all -n unillanos
kubectl port-forward -n unillanos service/picas-fijas-service --address 0.0.0.0 80:80
```

En otra terminal: `bash pruebas/pruebas.sh http://localhost`.
En el navegador: menu de Killercoda "Traffic / Ports", puerto 80.

## Por que una sola replica

Los juegos viven en la memoria del proceso. Si hubiera 3 replicas, cada pod tendria su
propia copia de los datos y el Service repartiria las peticiones entre ellos, asi que un
juego creado en un pod no existiria en los otros. Para escalar a varias replicas habria que
sacar el estado a un almacenamiento compartido (por ejemplo Redis).