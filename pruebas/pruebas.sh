#!/bin/bash

BASE=${1:-http://localhost:8000}
JSON="Content-Type: application/json"

titulo() { echo; echo "=== $1 ==="; }

titulo "Login de ana y beto"
curl -s -X POST $BASE/login -H "$JSON" -d '{"nombre":"ana"}'; echo
curl -s -X POST $BASE/login -H "$JSON" -d '{"nombre":"beto"}'; echo

titulo "Validaciones del numero (todas deben fallar)"
curl -s -X POST $BASE/juego -H "$JSON" -d '{"nombre":"ana","numero":"12a4"}'; echo
curl -s -X POST $BASE/juego -H "$JSON" -d '{"nombre":"ana","numero":"123"}'; echo
curl -s -X POST $BASE/juego -H "$JSON" -d '{"nombre":"ana","numero":"1123"}'; echo
curl -s -X POST $BASE/juego -H "$JSON" -d '{"nombre":"ana","numero":"12345"}'; echo
curl -s -X POST $BASE/juego -H "$JSON" -d '{"nombre":"pedro","numero":"1234"}'; echo

titulo "ana crea un juego con el numero 8135"
RESP=$(curl -s -X POST $BASE/juego -H "$JSON" -d '{"nombre":"ana","numero":"8135"}')
echo $RESP
ID=$(echo $RESP | python3 -c "import sys, json; print(json.load(sys.stdin)['juego']['id'])")
echo "ID del juego: $ID"

titulo "Listar juegos"
curl -s $BASE/juego; echo

titulo "ana intenta unirse a su propio juego (debe fallar)"
curl -s -X PUT $BASE/juego/$ID -H "$JSON" -d '{"nombre":"ana","numero":"4271"}'; echo

titulo "beto se une con el numero 4271 (el juego inicia)"
RESP=$(curl -s -X PUT $BASE/juego/$ID -H "$JSON" -d '{"nombre":"beto","numero":"4271"}')
echo $RESP
TURNO=$(echo $RESP | python3 -c "import sys, json; print(json.load(sys.stdin)['juego']['turno'])")
if [ "$TURNO" = "ana" ]; then OTRO="beto"; SECRETO_OTRO="4271"; else OTRO="ana"; SECRETO_OTRO="8135"; fi
echo "Empieza: $TURNO"

titulo "Un tercer jugador intenta unirse (debe fallar, el juego ya inicio)"
curl -s -X POST $BASE/login -H "$JSON" -d '{"nombre":"carlos"}' > /dev/null
curl -s -X PUT $BASE/juego/$ID -H "$JSON" -d '{"nombre":"carlos","numero":"9876"}'; echo

titulo "$OTRO intenta jugar sin ser su turno (debe fallar)"
curl -s -X POST $BASE/juego/$ID/jugar -H "$JSON" -d "{\"nombre\":\"$OTRO\",\"numero\":\"1234\"}"; echo

titulo "$TURNO juega 1234"
curl -s -X POST $BASE/juego/$ID/jugar -H "$JSON" -d "{\"nombre\":\"$TURNO\",\"numero\":\"1234\"}"; echo

titulo "$OTRO juega 1234"
curl -s -X POST $BASE/juego/$ID/jugar -H "$JSON" -d "{\"nombre\":\"$OTRO\",\"numero\":\"1234\"}"; echo

titulo "$TURNO adivina el numero $SECRETO_OTRO y gana"
curl -s -X POST $BASE/juego/$ID/jugar -H "$JSON" -d "{\"nombre\":\"$TURNO\",\"numero\":\"$SECRETO_OTRO\"}"; echo

titulo "Jugar despues de terminado (debe fallar)"
curl -s -X POST $BASE/juego/$ID/jugar -H "$JSON" -d "{\"nombre\":\"$OTRO\",\"numero\":\"1234\"}"; echo

titulo "Estado final del juego"
curl -s $BASE/juego/$ID; echo

titulo "Listar solo juegos terminados"
curl -s "$BASE/juego?estado=terminado"; echo

titulo "Salud y pod que respondio"
curl -s $BASE/salud; echo