# Analizador Léxico de Pedidos KFC

Proyecto de Teoría de la Computación (USIL). Aplicación web en Flask que:

1. Muestra el enunciado del proyecto.
2. Recibe el lenguaje inicial (digitado o subiendo un `.txt`).
3. Genera los **TOKENS** y **LEXEMAS** (PRODUCTO, CANTIDAD, PAGO).
4. Genera la **Expresión Regular** de cada lexema.
5. Construye el **AFND** (método de Thompson).
6. Lo convierte a **AFD** (construcción de subconjuntos).
7. Muestra la **tabla de transiciones**.
8. Lista las **transiciones** δ.
9. Muestra la **quíntupla** M = (Q, Σ, δ, q0, F).

Los gráficos de los autómatas se generan desde el código (lenguaje DOT) y se dibujan en el navegador con viz.js.

## Archivos

- `app.py` — servidor Flask (rutas y formulario)
- `automatas.py` — análisis léxico, ER, AFND, AFD, tabla y quíntupla
- `templates/index.html` — interfaz
- `static/estilos.css` — estilos
- `ejemplo.txt` — archivo de prueba

## Ejecutar en local

```
pip install -r requirements.txt
python app.py
```

Abrir http://127.0.0.1:8080

## Publicar en Render

- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn app:app`
