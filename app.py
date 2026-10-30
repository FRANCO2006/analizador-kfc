import os
from flask import Flask, render_template, request, jsonify

from automatas import procesar, EJEMPLO, PRODUCTOS, PAGOS
import sintactico

app = Flask(__name__)

ENUNCIADO = (
    "Sistema de registro y validación de pedidos de un restaurante KFC. "
    "Se define un nuevo lenguaje formal en el que cada pedido se escribe en una línea "
    "con la estructura PRODUCTO CANTIDAD ... PAGO (por ejemplo: POLLO 2 EFECTIVO). "
    "El sistema recibe el texto del pedido (digitado o desde un archivo .txt), "
    "identifica sus LEXEMAS y los clasifica en TOKENS; luego, para cada lexema, "
    "genera su Expresión Regular, el AFND, el AFD equivalente, la tabla de "
    "transiciones, las transiciones y la quíntupla. Finalmente, valida cada pedido "
    "con un analizador sintáctico LR y construye su árbol sintáctico."
)


def analizar_texto(texto):
    """Análisis léxico + autómatas + análisis sintáctico LR de cada línea."""
    lexemas, automatas = procesar(texto)
    pedidos = []
    for num, linea in enumerate(texto.upper().splitlines(), start=1):
        if not linea.strip():
            continue
        toks = [(l["lexema"], l["token"]) for l in lexemas if l["linea"] == num]
        r = sintactico.analizar(toks)
        pedidos.append({
            "linea": num, "texto": linea.strip(), "valida": r["valida"],
            "error": r["error"], "pasos": r["pasos"], "dot_arbol": r["dot"],
            "derivacion": sintactico.derivacion(toks) if r["valida"] else [],
        })
    return lexemas, automatas, pedidos


@app.route("/", methods=["GET", "POST"])
def index():
    texto = EJEMPLO
    lexemas = automatas = pedidos = None
    error = ""

    if request.method == "POST":
        archivo = request.files.get("archivo")
        if archivo and archivo.filename:
            try:
                texto = archivo.read().decode("utf-8")
            except UnicodeDecodeError:
                error = "El archivo debe ser de texto (.txt) en UTF-8."
        else:
            texto = request.form.get("texto", "")

        if not error:
            if texto.strip():
                lexemas, automatas, pedidos = analizar_texto(texto)
            else:
                error = "Escribe un pedido o sube un archivo."

    cols_a, cols_g, filas_lr = sintactico.tabla_lr()
    return render_template(
        "index.html", enunciado=ENUNCIADO, texto=texto, error=error,
        lexemas=lexemas, automatas=automatas, pedidos=pedidos,
        productos=sorted(PRODUCTOS), pagos=sorted(PAGOS),
        producciones=sintactico.PRODUCCIONES, cols_a=cols_a, cols_g=cols_g,
        filas_lr=filas_lr, coleccion=sintactico.coleccion_lr0(),
    )


@app.route("/api/analizar", methods=["POST"])
def api_analizar():
    """API JSON usada por las pruebas automatizadas (Postman/Newman)."""
    datos = request.get_json(silent=True) or {}
    texto = datos.get("texto", "")
    if not texto.strip():
        return jsonify({"error": "Escribe un pedido."}), 400
    lexemas, automatas, pedidos = analizar_texto(texto)
    return jsonify({
        "lexemas": lexemas,
        "expresiones": {a["lexema"]: a["er"] for a in automatas},
        "afd": {a["lexema"]: {"estados": len(a["tabla"]), "quintupla": a["quintupla"]} for a in automatas},
        "pedidos": [{"linea": p["linea"], "texto": p["texto"], "valida": p["valida"],
                     "error": p["error"], "pasos": len(p["pasos"])} for p in pedidos],
        "resumen": {"total": len(pedidos), "validos": sum(p["valida"] for p in pedidos)},
    })


if __name__ == "__main__":
    puerto = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=puerto, debug=True)
