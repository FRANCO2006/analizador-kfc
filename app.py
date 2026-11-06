import os
from flask import Flask, render_template, request, jsonify, Response, abort

from automatas import procesar, procesar_tokens, a_jflap, TOKENS, EJEMPLO, PRODUCTOS, PAGOS
import sintactico
import semantico

app = Flask(__name__)

ENUNCIADO = (
    "Sistema de registro y validación de pedidos de un restaurante KFC. Cada pedido se "
    "escribe en una línea con la estructura PRODUCTO CANTIDAD ... PAGO (por ejemplo: "
    "POLLO 2 EFECTIVO) y pasa por las tres fases de un compilador antes de enviarse a cocina."
)
FASES = [
    ("Análisis léxico",
     "Lee el pedido, lo separa en lexemas y asigna a cada uno su token (PRODUCTO, CANTIDAD o PAGO) "
     "con expresiones regulares y autómatas finitos (AFND → AFD). Lo que no pertenece al lenguaje "
     "se marca como DESCONOCIDO."),
    ("Análisis sintáctico",
     "Verifica con un analizador LR (SLR) que los tokens sigan el orden de la gramática: uno o más "
     "pares producto cantidad y al final un pago. Si cumple, construye el árbol sintáctico."),
    ("Análisis semántico",
     "Revisa que el pedido tenga sentido para el negocio: la cantidad de cada producto debe estar "
     "entre 1 y 50 y un producto no puede repetirse en el mismo pedido."),
]


def analizar_texto(texto):
    """Análisis léxico + autómatas + análisis sintáctico LR de cada línea."""
    lexemas, automatas = procesar(texto)
    pedidos = []
    for num, linea in enumerate(texto.upper().splitlines(), start=1):
        if not linea.strip():
            continue
        toks = [(l["lexema"], l["token"]) for l in lexemas if l["linea"] == num]
        r = sintactico.analizar(toks)
        sem = semantico.analizar(toks) if r["valida"] else None
        valida = r["valida"] and sem["valida"]
        error = r["error"] or (" ".join(sem["errores"]) if sem else "")
        fase = "" if valida else ("léxica" if error.startswith("Error léxico")
                                  else "sintáctica" if error.startswith("Error sintáctico") else "semántica")
        pedidos.append({
            "linea": num, "texto": linea.strip(), "valida": valida, "sintaxis_ok": r["valida"],
            "error": error, "fase": fase, "pasos": r["pasos"], "dot_arbol": r["dot"],
            "derivacion": sintactico.derivacion(toks) if r["valida"] else [],
            "semantico": sem,
        })
    return lexemas, automatas, pedidos


@app.route("/", methods=["GET", "POST"])
def index():
    texto = EJEMPLO
    lexemas = automatas = pedidos = tokens = desconocidos = None
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
                tokens, desconocidos = procesar_tokens(lexemas)
            else:
                error = "Escribe un pedido o sube un archivo."

    cols_a, cols_g, filas_lr = sintactico.tabla_lr()
    return render_template(
        "index.html", enunciado=ENUNCIADO, fases=FASES, reglas=semantico.REGLAS,
        tokens=tokens, desconocidos=desconocidos, texto=texto, error=error,
        lexemas=lexemas, automatas=automatas, pedidos=pedidos,
        productos=sorted(PRODUCTOS), pagos=sorted(PAGOS),
        producciones=sintactico.PRODUCCIONES, cols_a=cols_a, cols_g=cols_g,
        filas_lr=filas_lr, coleccion=sintactico.coleccion_lr0(),
    )


@app.route("/jflap/<token>_<tipo>.jff")
def jflap(token, tipo):
    """Descarga el AFND o el AFD de un token en formato JFLAP para validarlo."""
    if token not in [t["token"] for t in TOKENS] or tipo not in ("afnd", "afd"):
        abort(404)
    return Response(a_jflap(token, tipo), mimetype="application/xml",
                    headers={"Content-Disposition": f"attachment; filename={token}_{tipo.upper()}.jff"})


@app.route("/ejemplo.txt")
def ejemplo():
    return Response(EJEMPLO + "\n", mimetype="text/plain",
                    headers={"Content-Disposition": "attachment; filename=pedidos_ejemplo.txt"})


@app.route("/api/analizar", methods=["POST"])
def api_analizar():
    """API JSON usada por las pruebas automatizadas (Postman/Newman)."""
    datos = request.get_json(silent=True) or {}
    texto = datos.get("texto", "")
    if not texto.strip():
        return jsonify({"error": "Escribe un pedido."}), 400
    lexemas, automatas, pedidos = analizar_texto(texto)
    tokens, _ = procesar_tokens(lexemas)
    return jsonify({
        "lexemas": lexemas,
        "expresiones": {a["lexema"]: a["er"] for a in automatas},
        "afd": {a["lexema"]: {"estados": len(a["tabla"]), "quintupla": a["quintupla"]} for a in automatas},
        "tokens": {t["token"]: {"er": t["er"], "lenguaje": t["lenguaje"], "notacion": t["notacion"],
                                "afnd_estados": t["afnd_estados"], "afd_estados": t["afd_estados"]} for t in tokens},
        "pedidos": [{"linea": p["linea"], "texto": p["texto"], "valida": p["valida"], "fase": p["fase"],
                     "error": p["error"], "pasos": len(p["pasos"])} for p in pedidos],
        "resumen": {"total": len(pedidos), "validos": sum(p["valida"] for p in pedidos)},
    })


if __name__ == "__main__":
    puerto = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=puerto, debug=True)
