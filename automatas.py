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
LISTA_PRODUCTOS = ["POLLO", "ALITAS", "HAMBURGUESA", "PAPAS", "GASEOSA",
                   "COMBO", "NUGGETS", "ENSALADA", "HELADO", "POPCORN"]
LISTA_PAGOS = ["EFECTIVO", "TARJETA", "YAPE", "PLIN"]
PRODUCTOS = set(LISTA_PRODUCTOS)
PAGOS = set(LISTA_PAGOS)

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


def er_a_afnd(er, compacto=False):
    """Construye el AFND-ε de Thompson. Estados numerados 0, 1, 2, ...
    compacto=True une directamente los fragmentos concatenados (sin ε),
    lo que produce un AFND más pequeño y legible para los tokens."""
    trans = []                 # (origen, símbolo, destino)
    contador = [0]

    def nuevo():
        contador[0] += 1
        return contador[0] - 1

    pila, uniones = [], set()
    for tipo, val in _a_postfija(_tokens_er(er)):
        if tipo == "SIM":
            s, f = nuevo(), nuevo()
            trans.append((s, val, f))
            pila.append((s, f))
        elif val == ".":
            b, a = pila.pop(), pila.pop()
            if compacto:
                # el estado inicial de b se fusiona con el final de a
                trans[:] = [(a[1] if o == b[0] else o, sm, a[1] if d == b[0] else d)
                            for o, sm, d in trans]
                fin_b = a[1] if b[1] == b[0] else b[1]
                pila.append((a[0], fin_b))
            else:
                trans.append((a[1], EPS, b[0]))
                pila.append((a[0], b[1]))
        elif val == "|":
            b, a = pila.pop(), pila.pop()
            if compacto and a in uniones:
                # unión n-aria: la nueva alternativa se cuelga de la misma unión
                trans += [(a[0], EPS, b[0]), (b[1], EPS, a[1])]
                pila.append(a)
                continue
            s, f = nuevo(), nuevo()
            trans += [(s, EPS, a[0]), (s, EPS, b[0]),
                      (a[1], EPS, f), (b[1], EPS, f)]
            pila.append((s, f))
            uniones.add((s, f))
        elif val in "*+":
            a = pila.pop()
            s, f = nuevo(), nuevo()
            trans += [(s, EPS, a[0]), (a[1], EPS, a[0]), (a[1], EPS, f)]
            if val == "*":
                trans.append((s, EPS, f))
            pila.append((s, f))

    inicio, final = pila.pop()
    if not compacto:
        return {"estados": list(range(contador[0])), "inicio": inicio,
                "finales": [final], "trans": trans}
    # renumerar en orden de recorrido (BFS) desde el estado inicial
    orden, cola = [inicio], [inicio]
    while cola:
        e = cola.pop(0)
        for o, _, d in trans:
            if o == e and d not in orden:
                orden.append(d)
                cola.append(d)
    nuevo_id = {e: i for i, e in enumerate(orden)}
    trans = [(nuevo_id[o], sm, nuevo_id[d]) for o, sm, d in trans]
    return {"estados": list(range(len(orden))), "inicio": 0,
            "finales": [nuevo_id[final]], "trans": trans}


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


def dot_afnd(afnd, rankdir="LR"):
    lineas = ['digraph AFND {', f'rankdir={rankdir};', 'node [shape=circle, fontname="Arial"];',
              'inicio [shape=point];']
    for f in afnd["finales"]:
        lineas.append(f'{f} [shape=doublecircle];')
    lineas.append(f'inicio -> {afnd["inicio"]};')
    for o, s, d in afnd["trans"]:
        lineas.append(f'{o} -> {d} [label="{_esc(s)}"];')
    lineas.append("}")
    return "\n".join(lineas)


def dot_afd(afd, rankdir="LR"):
    lineas = ['digraph AFD {', f'rankdir={rankdir};', 'node [shape=circle, fontname="Arial"];',
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


# ---------------------------------------------------------------
# AUTÓMATAS POR TIPO DE TOKEN (agrupador)
# ---------------------------------------------------------------
TOKENS = [
    {"token": "PRODUCTO", "lexemas": LISTA_PRODUCTOS,
     "er": "(" + "|".join(LISTA_PRODUCTOS) + ")",
     "lenguaje": "P = {" + ", ".join(LISTA_PRODUCTOS) + "}",
     "notacion": "P", "prueba_ok": "POLLO", "prueba_mal": "PIZZA"},
    {"token": "CANTIDAD", "lexemas": ["1", "2", "3", "12", "…"],
     "er": DIGITO + "+",
     "lenguaje": "D = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9}",
     "notacion": "D+", "prueba_ok": "12", "prueba_mal": "DOS"},
    {"token": "PAGO", "lexemas": LISTA_PAGOS,
     "er": "(" + "|".join(LISTA_PAGOS) + ")",
     "lenguaje": "M = {" + ", ".join(LISTA_PAGOS) + "}",
     "notacion": "M", "prueba_ok": "YAPE", "prueba_mal": "BITCOIN"},
]


def automatas_token(nombre):
    """AFND (Thompson) y AFD (subconjuntos) de la ER de un tipo de token."""
    t = next(x for x in TOKENS if x["token"] == nombre)
    afnd = er_a_afnd(t["er"], compacto=True)
    afd = afnd_a_afd(afnd)
    return t, afnd, afd


def procesar_tokens(lexemas):
    """Tabla agrupada por token + AFND, AFD, tabla y quíntupla de cada token."""
    salida = []
    for t in TOKENS:
        _, afnd, afd = automatas_token(t["token"])
        encontrados = []
        for l in lexemas:
            if l["token"] == t["token"] and l["lexema"] not in encontrados:
                encontrados.append(l["lexema"])
        salida.append({
            **t, "encontrados": encontrados,
            "afnd_estados": len(afnd["estados"]), "afd_estados": len(afd["estados"]),
            "dot_afnd": dot_afnd(afnd, "LR" if t["token"] == "CANTIDAD" else "TB"),
            "dot_afd": dot_afd(afd, "LR" if t["token"] == "CANTIDAD" else "TB"),
            "alfabeto": afd["alfabeto"], "tabla": tabla_afd(afd),
            "transiciones": lista_transiciones(afd), "quintupla": quintupla(afd),
        })
    desconocidos = []
    for l in lexemas:
        if l["token"] == "DESCONOCIDO" and l["lexema"] not in desconocidos:
            desconocidos.append(l["lexema"])
    return salida, desconocidos


# ---------------------------------------------------------------
# EXPORTACIÓN A JFLAP (.jff) PARA VALIDAR LOS AUTÓMATAS
# ---------------------------------------------------------------
def _simbolos_jflap(simbolo):
    if simbolo == EPS:
        return [""]
    if simbolo == DIGITO:
        return [str(d) for d in range(10)]
    return [simbolo]


def _posiciones(estados, inicio, aristas):
    """Coloca los estados por niveles (BFS) para que se vean ordenados en JFLAP."""
    nivel, cola = {inicio: 0}, [inicio]
    while cola:
        e = cola.pop(0)
        for o, d in aristas:
            if o == e and d not in nivel:
                nivel[d] = nivel[e] + 1
                cola.append(d)
    usados, pos = {}, {}
    for e in estados:
        n = nivel.get(e, 0)
        fila = usados.get(n, 0)
        usados[n] = fila + 1
        pos[e] = (60 + n * 110, 60 + fila * 80)
    return pos


def a_jflap(nombre, tipo):
    """Devuelve el XML .jff del AFND o del AFD del token indicado."""
    from xml.sax.saxutils import escape
    _, afnd, afd = automatas_token(nombre)
    if tipo == "afnd":
        estados = afnd["estados"]
        ids = {e: i for i, e in enumerate(estados)}
        nombres = {e: f"q{e}" for e in estados}
        inicio, finales = afnd["inicio"], set(afnd["finales"])
        trans = afnd["trans"]
    else:
        estados = afd["estados"]
        ids = {e: i for i, e in enumerate(estados)}
        nombres = {e: e for e in estados}
        inicio, finales = afd["inicio"], set(afd["finales"])
        trans = [(o, a, d) for (o, a), d in afd["trans"].items()]
    pos = _posiciones(estados, inicio, [(o, d) for o, _, d in trans])
    x = ['<?xml version="1.0" encoding="UTF-8" standalone="no"?>',
         "<!--Generado por el Analizador de Pedidos KFC-->",
         "<structure>", "<type>fa</type>", "<automaton>"]
    for e in estados:
        x.append(f'<state id="{ids[e]}" name="{nombres[e]}"><x>{pos[e][0]}.0</x><y>{pos[e][1]}.0</y>'
                 + ("<initial/>" if e == inicio else "") + ("<final/>" if e in finales else "") + "</state>")
    for o, s, d in trans:
        for sim in _simbolos_jflap(s):
            leer = f"<read>{escape(sim)}</read>" if sim else "<read/>"
            x.append(f"<transition><from>{ids[o]}</from><to>{ids[d]}</to>{leer}</transition>")
    x += ["</automaton>", "</structure>"]
    return "\n".join(x)
