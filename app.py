import os
from flask import Flask, render_template, request

from automatas import procesar, EJEMPLO, PRODUCTOS, PAGOS

app = Flask(__name__)

ENUNCIADO = (
    "Sistema de registro y validación de pedidos de un restaurante KFC. "
    "Se define un nuevo lenguaje formal en el que cada pedido se escribe en una línea "
    "con la estructura PRODUCTO CANTIDAD ... PAGO (por ejemplo: POLLO 2 EFECTIVO). "
    "El sistema recibe el texto del pedido (digitado o desde un archivo .txt), "
    "identifica sus LEXEMAS y los clasifica en TOKENS; luego, para cada lexema, "
    "genera su Expresión Regular, el AFND, el AFD equivalente, la tabla de "
    "transiciones, las transiciones y la quíntupla."
)


@app.route("/", methods=["GET", "POST"])
def index():
    texto = EJEMPLO
    lexemas, automatas, error = None, None, ""

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
                lexemas, automatas = procesar(texto)
            else:
                error = "Escribe un pedido o sube un archivo."

    return render_template("index.html", enunciado=ENUNCIADO, texto=texto,
                           lexemas=lexemas, automatas=automatas, error=error,
                           productos=sorted(PRODUCTOS), pagos=sorted(PAGOS))


if __name__ == "__main__":
    puerto = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=puerto, debug=True)
