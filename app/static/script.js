let miNombre = null;
let juegoActual = null;
let misNumeros = {};

function campoValido(id) {
  return document.getElementById(id).reportValidity();
}

function soloDigitos(campo) {
  campo.value = campo.value.replace(/[^0-9]/g, "");
}

function soloLetras(campo) {
  campo.value = campo.value.replace(/[^A-Za-zÁÉÍÓÚáéíóúÑñÜü ]/g, "");
}

function mostrar(texto) {
  document.getElementById("mensaje").textContent = texto;
}

function limpiar(texto) {
  const div = document.createElement("div");
  div.textContent = texto === null ? "-" : String(texto);
  return div.innerHTML;
}

async function llamar(metodo, url, cuerpo) {
  const opciones = { method: metodo, headers: { "Content-Type": "application/json" } };
  if (cuerpo) opciones.body = JSON.stringify(cuerpo);
  const respuesta = await fetch(url, opciones);
  const datos = await respuesta.json();
  if (!respuesta.ok) {
    const error = typeof datos.detail === "string" ? datos.detail : JSON.stringify(datos.detail);
    throw new Error(error);
  }
  return datos;
}

async function login() {
  if (!campoValido("nombre")) return;
  try {
    const nombre = document.getElementById("nombre").value;
    const datos = await llamar("POST", "/login", { nombre: nombre });
    miNombre = datos.nombre;
    document.getElementById("usuario").textContent = "Jugador: " + miNombre;
    mostrar(datos.mensaje);
  } catch (e) { mostrar("Error: " + e.message); }
}

async function crearJuego() {
  if (!miNombre) { mostrar("Primero haga login"); return; }
  if (!campoValido("secreto")) return;
  try {
    const numero = document.getElementById("secreto").value;
    const datos = await llamar("POST", "/juego", { nombre: miNombre, numero: numero });
    misNumeros[datos.juego.id] = numero;
    juegoActual = datos.juego.id;
    mostrar(datos.mensaje + " (juego " + juegoActual + ")");
    actualizar();
  } catch (e) { mostrar("Error: " + e.message); }
}

async function unirse(id) {
  if (!miNombre) { mostrar("Primero haga login"); return; }
  if (!campoValido("secreto")) return;
  try {
    const numero = document.getElementById("secreto").value;
    const datos = await llamar("PUT", "/juego/" + id, { nombre: miNombre, numero: numero });
    misNumeros[id] = numero;
    juegoActual = id;
    mostrar(datos.mensaje);
    actualizar();
  } catch (e) { mostrar("Error: " + e.message); }
}

function verJuego(id) {
  juegoActual = id;
  actualizar();
}

async function jugar() {
  if (!campoValido("intento")) return;
  try {
    const numero = document.getElementById("intento").value;
    const datos = await llamar("POST", "/juego/" + juegoActual + "/jugar", { nombre: miNombre, numero: numero });
    mostrar(datos.mensaje);
    document.getElementById("intento").value = "";
    actualizar();
  } catch (e) { mostrar("Error: " + e.message); }
}

async function cargarJuegos() {
  const datos = await llamar("GET", "/juego");
  let filas = "";
  for (const j of datos.juegos) {
    let boton = "<button onclick='verJuego(" + j.id + ")'>Ver</button>";
    if (j.estado === "por_iniciar" && j.creador !== miNombre) {
      boton += " <button onclick='unirse(" + j.id + ")'>Unirse</button>";
    }
    filas += "<tr><td>" + j.id + "</td><td>" + limpiar(j.creador) + "</td><td>" + j.estado +
             "</td><td>" + limpiar(j.jugadores.join(", ")) + "</td><td>" + limpiar(j.ganador) +
             "</td><td>" + boton + "</td></tr>";
  }
  document.getElementById("tablaJuegos").innerHTML = filas;
}

async function cargarJuego() {
  if (juegoActual === null) return;
  const j = await llamar("GET", "/juego/" + juegoActual);
  document.getElementById("panelJuego").classList.remove("oculto");
  document.getElementById("idJuego").textContent = j.id;
  document.getElementById("estadoJuego").textContent = j.estado;
  document.getElementById("turnoJuego").textContent = j.turno || "-";
  document.getElementById("ganadorJuego").textContent = j.ganador || "-";
  document.getElementById("miNumero").textContent = misNumeros[j.id] || "-";
  let filas = "";
  for (const i of j.intentos) {
    filas += "<tr><td>" + limpiar(i.jugador) + "</td><td>" + i.numero + "</td><td>" + i.fijas +
             "</td><td>" + i.picas + "</td><td>" + i.hora + "</td></tr>";
  }
  document.getElementById("tablaIntentos").innerHTML = filas;
  if (j.numeros_secretos) {
    let lista = "";
    for (const nombre in j.numeros_secretos) {
      const nombreBonito = nombre.charAt(0).toUpperCase() + nombre.slice(1);
      lista += "<li>" + limpiar(nombreBonito) + ": " + j.numeros_secretos[nombre] + "</li>";
    }
    document.getElementById("secretos").innerHTML = "<p>Números secretos:</p><ul>" + lista + "</ul>";
  } else {
    document.getElementById("secretos").innerHTML = "";
  }
}

async function actualizar() {
  try {
    await cargarJuegos();
    await cargarJuego();
    const s = await llamar("GET", "/salud");
    document.getElementById("pod").textContent = s.pod;
  } catch (e) { console.log(e); }
}

setInterval(actualizar, 2000);
actualizar();