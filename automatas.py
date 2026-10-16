"""
Lógica de lenguajes formales del proyecto:
  1. Analizador léxico  -> LEXEMAS y TOKENS
  2. Expresión Regular (ER) de cada lexema
  3. AFND (método de Thompson) a partir de cada ER
  4. AFD  (construcción de subconjuntos) a partir del AFND
  5. Tabla de transiciones, transiciones δ, quíntupla y gráficos (DOT)
"""
import re

# ---------------------------------------------------------------
# 1. DICCIONARIO DEL LENGUAJE (pedidos de KFC)
# ---------------------------------------------------------------
PRODUCTOS = {"POLLO", "ALITAS", "HAMBURGUESA", "PAPAS", "GASEOSA",
             "COMBO", "NUGGETS", "ENSALADA", "HELADO", "POPCORN"}
PAGOS = {"EFECTIVO", "TARJETA", "YAPE", "PLIN"}

DIGITO = "[0-9]"          # clase de caracteres usada como un solo símbolo

EJEMPLO = """POLLO 2 PAPAS 1 EFECTIVO
HAMBURGUESA 3 GASEOSA 3 TARJETA
ALITAS 12 YAPE"""


def clasificar(lexema):
    """Devuelve el TOKEN al que pertenece un lexema."""
    if lexema in PRODUCTOS:
        return "PRODUCTO"
    if lexema in PAGOS:
        return "PAGO"
    if lexema.isdigit():
        return "CANTIDAD"
    return "DESCONOCIDO"


def analizar_lexico(texto):
    """Separa el texto en lexemas y les asigna su token."""
    resultado = []
    for num_linea, linea in enumerate(texto.upper().splitlines(), start=1):
        for lexema in linea.split():
            resultado.append({"linea": num_linea, "lexema": lexema,
                              "token": clasificar(lexema)})
    return resultado


# ---------------------------------------------------------------
# 2. EXPRESIÓN REGULAR DE CADA LEXEMA
# ---------------------------------------------------------------
def generar_er(lexema, token):
    """PRODUCTO / PAGO -> concatenación de sus letras.
       CANTIDAD        -> [0-9]+ (uno o más dígitos)."""
    if token == "CANTIDAD":
        return DIGITO + "+"
    return lexema


# ---------------------------------------------------------------
# 3. AFND con el método de Thompson
# ---------------------------------------------------------------
EPS = "ε"


def _tokens_er(er):
    """Convierte la ER en una lista de símbolos y operadores."""
    items, i = [], 0
    while i < len(er):
        c = er[i]
        if c == "[":
            fin = er.index("]", i)
            items.append(("SIM", er[i:fin + 1]))
            i = fin + 1
            continue
        if c in "()|*+":
            items.append(("OP", c))
        else:
            items.append(("SIM", c))
        i += 1
    # insertar la concatenación explícita "."
    con_concat = []
    for k, it in enumerate(items):
        con_concat.append(it)
        if k + 1 < len(items):
            a, b = it, items[k + 1]
            izq = a[0] == "SIM" or a[1] in ")*+"
            der = b[0] == "SIM" or b[1] == "("
            if izq and der:
                con_concat.append(("OP", "."))
    return con_concat


def _a_postfija(items):
    prioridad = {"|": 1, ".": 2, "*": 3, "+": 3}
    salida, pila = [], []
    for tipo, val in items:
        if tipo == "SIM":
            salida.append((tipo, val))
        elif val == "(":
            pila.append(val)
        elif val == ")":
            while pila[-1] != "(":
                salida.append(("OP", pila.pop()))
            pila.pop()
        else:
            while pila and pila[-1] != "(" and prioridad[pila[-1]] >= prioridad[val]:
                salida.append(("OP", pila.pop()))
            pila.append(val)
    while pila:
        salida.append(("OP", pila.pop()))
    return salida


def er_a_afnd(er):
    """Construye el AFND-ε de Thompson. Estados numerados 0, 1, 2, ..."""
    trans = []                 # (origen, símbolo, destino)
    contador = [0]

    def nuevo():
        contador[0] += 1
        return contador[0] - 1

    pila = []
    for tipo, val in _a_postfija(_tokens_er(er)):
        if tipo == "SIM":
            s, f = nuevo(), nuevo()
            trans.append((s, val, f))
            pila.append((s, f))
        elif val == ".":
            b, a = pila.pop(), pila.pop()
            trans.append((a[1], EPS, b[0]))
            pila.append((a[0], b[1]))
        elif val == "|":
            b, a = pila.pop(), pila.pop()
            s, f = nuevo(), nuevo()
            trans += [(s, EPS, a[0]), (s, EPS, b[0]),
                      (a[1], EPS, f), (b[1], EPS, f)]
            pila.append((s, f))
        elif val in "*+":
            a = pila.pop()
            s, f = nuevo(), nuevo()
            trans += [(s, EPS, a[0]), (a[1], EPS, a[0]), (a[1], EPS, f)]
            if val == "*":
                trans.append((s, EPS, f))
            pila.append((s, f))

    inicio, final = pila.pop()
    return {"estados": list(range(contador[0])), "inicio": inicio,
            "finales": [final], "trans": trans}


# ---------------------------------------------------------------
# 4. AFD por construcción de subconjuntos
# ---------------------------------------------------------------
def _cerradura(estados, trans):
    pila, res = list(estados), set(estados)
    while pila:
        e = pila.pop()
        for o, s, d in trans:
            if o == e and s == EPS and d not in res:
                res.add(d)
                pila.append(d)
    return frozenset(res)


def afnd_a_afd(afnd):
    alfabeto = []
    for _, s, _ in afnd["trans"]:
        if s != EPS and s not in alfabeto:
            alfabeto.append(s)

    inicial = _cerradura({afnd["inicio"]}, afnd["trans"])
    nombres = {inicial: "q0"}
    pendientes, trans = [inicial], {}
    while pendientes:
        actual = pendientes.pop(0)
        for a in alfabeto:
            mover = {d for o, s, d in afnd["trans"] if o in actual and s == a}
            if not mover:
                continue
            destino = _cerradura(mover, afnd["trans"])
            if destino not in nombres:
                nombres[destino] = f"q{len(nombres)}"
                pendientes.append(destino)
            trans[(nombres[actual], a)] = nombres[destino]

    finales_afnd = set(afnd["finales"])
    estados = list(nombres.values())
    finales = [n for c, n in nombres.items() if c & finales_afnd]
    subconjuntos = {n: sorted(c) for c, n in nombres.items()}
    return {"estados": estados, "alfabeto": alfabeto, "inicio": "q0",
            "finales": finales, "trans": trans, "subconjuntos": subconjuntos}


# ---------------------------------------------------------------
# 5. TABLA, TRANSICIONES, QUÍNTUPLA Y GRÁFICOS (DOT)
# ---------------------------------------------------------------
def tabla_afd(afd):
    filas = []
    for q in afd["estados"]:
        marca = ("→" if q == afd["inicio"] else "") + ("*" if q in afd["finales"] else "")
        celdas = [afd["trans"].get((q, a), "—") for a in afd["alfabeto"]]
        filas.append({"marca": marca, "estado": q, "celdas": celdas,
                      "subconjunto": afd["subconjuntos"][q]})
    return filas


def lista_transiciones(afd):
    return [f"δ({o}, {a}) = {d}" for (o, a), d in afd["trans"].items()]


def quintupla(afd):
    return {
        "Q": "{" + ", ".join(afd["estados"]) + "}",
        "Σ": "{" + ", ".join(afd["alfabeto"]) + "}",
        "δ": "Q × Σ → Q (ver tabla de transiciones)",
        "q0": afd["inicio"],
        "F": "{" + ", ".join(afd["finales"]) + "}",
    }


def _esc(texto):
    return texto.replace('"', '\\"')


def dot_afnd(afnd):
    lineas = ['digraph AFND {', 'rankdir=LR;', 'node [shape=circle, fontname="Arial"];',
              'inicio [shape=point];']
    for f in afnd["finales"]:
        lineas.append(f'{f} [shape=doublecircle];')
    lineas.append(f'inicio -> {afnd["inicio"]};')
    for o, s, d in afnd["trans"]:
        lineas.append(f'{o} -> {d} [label="{_esc(s)}"];')
    lineas.append("}")
    return "\n".join(lineas)


def dot_afd(afd):
    lineas = ['digraph AFD {', 'rankdir=LR;', 'node [shape=circle, fontname="Arial"];',
              'inicio [shape=point];']
    for f in afd["finales"]:
        lineas.append(f'{f} [shape=doublecircle];')
    lineas.append(f'inicio -> {afd["inicio"]};')
    for (o, a), d in afd["trans"].items():
        lineas.append(f'{o} -> {d} [label="{_esc(a)}"];')
    lineas.append("}")
    return "\n".join(lineas)


# ---------------------------------------------------------------
# PROCESO COMPLETO PARA CADA LEXEMA ÚNICO
# ---------------------------------------------------------------
def procesar(texto):
    lexemas = analizar_lexico(texto)
    automatas, vistos = [], set()
    for item in lexemas:
        lex, tok = item["lexema"], item["token"]
        if tok == "DESCONOCIDO" or lex in vistos:
            continue
        vistos.add(lex)
        er = generar_er(lex, tok)
        afnd = er_a_afnd(er)
        afd = afnd_a_afd(afnd)
        automatas.append({
            "lexema": lex, "token": tok, "er": er,
            "afnd_estados": len(afnd["estados"]),
            "dot_afnd": dot_afnd(afnd), "dot_afd": dot_afd(afd),
            "alfabeto": afd["alfabeto"], "tabla": tabla_afd(afd),
            "transiciones": lista_transiciones(afd),
            "quintupla": quintupla(afd),
        })
    return lexemas, automatas
