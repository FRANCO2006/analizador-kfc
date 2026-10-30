"""
Análisis sintáctico LR (SLR(1)) de los pedidos.

Gramática libre de contexto G = (N, T, P, S):
  N = {S', PEDIDO, ITEMS, ITEM}
  T = {producto, cantidad, pago}
  S = PEDIDO
  P:
    0) S'     -> PEDIDO
    1) PEDIDO -> ITEMS pago
    2) ITEMS  -> ITEMS ITEM
    3) ITEMS  -> ITEM
    4) ITEM   -> producto cantidad
"""

INICIAL = "S'"
FIN = "$"
PRODUCCIONES = [
    ("S'", ["PEDIDO"]),
    ("PEDIDO", ["ITEMS", "pago"]),
    ("ITEMS", ["ITEMS", "ITEM"]),
    ("ITEMS", ["ITEM"]),
    ("ITEM", ["producto", "cantidad"]),
]
NO_TERMINALES = ["S'", "PEDIDO", "ITEMS", "ITEM"]
TERMINALES = ["producto", "cantidad", "pago"]
TOKEN_A_TERMINAL = {"PRODUCTO": "producto", "CANTIDAD": "cantidad", "PAGO": "pago"}


# ---------------------------------------------------------------
# Construcción de la colección LR(0) y de la tabla SLR(1)
# ---------------------------------------------------------------
def _cerradura(items):
    res = set(items)
    cambio = True
    while cambio:
        cambio = False
        for (p, punto) in list(res):
            der = PRODUCCIONES[p][1]
            if punto < len(der) and der[punto] in NO_TERMINALES:
                for i, (izq, _) in enumerate(PRODUCCIONES):
                    if izq == der[punto] and (i, 0) not in res:
                        res.add((i, 0))
                        cambio = True
    return frozenset(res)


def _ir_a(items, x):
    mov = {(p, d + 1) for (p, d) in items
           if d < len(PRODUCCIONES[p][1]) and PRODUCCIONES[p][1][d] == x}
    return _cerradura(mov) if mov else None


def _primeros_y_siguientes():
    prim = {n: set() for n in NO_TERMINALES}
    cambio = True
    while cambio:
        cambio = False
        for izq, der in PRODUCCIONES:
            x = der[0]
            nuevo = {x} if x in TERMINALES else prim[x]
            if not nuevo <= prim[izq]:
                prim[izq] |= nuevo
                cambio = True
    sig = {n: set() for n in NO_TERMINALES}
    sig[INICIAL].add(FIN)
    cambio = True
    while cambio:
        cambio = False
        for izq, der in PRODUCCIONES:
            for i, x in enumerate(der):
                if x not in NO_TERMINALES:
                    continue
                if i + 1 < len(der):
                    y = der[i + 1]
                    nuevo = {y} if y in TERMINALES else prim[y]
                else:
                    nuevo = sig[izq]
                if not nuevo <= sig[x]:
                    sig[x] |= nuevo
                    cambio = True
    return prim, sig


def construir_tabla():
    estados = [_cerradura({(0, 0)})]
    trans = {}
    i = 0
    while i < len(estados):
        for x in TERMINALES + NO_TERMINALES:
            dest = _ir_a(estados[i], x)
            if dest is None:
                continue
            if dest not in estados:
                estados.append(dest)
            trans[(i, x)] = estados.index(dest)
        i += 1

    _, sig = _primeros_y_siguientes()
    accion, ir_a = {}, {}
    for i, items in enumerate(estados):
        for x in TERMINALES:
            if (i, x) in trans:
                accion[(i, x)] = f"d{trans[(i, x)]}"
        for x in NO_TERMINALES:
            if (i, x) in trans:
                ir_a[(i, x)] = trans[(i, x)]
        for (p, d) in items:
            if d == len(PRODUCCIONES[p][1]):
                if p == 0:
                    accion[(i, FIN)] = "acc"
                else:
                    for a in sig[PRODUCCIONES[p][0]]:
                        if (i, a) in accion:
                            raise ValueError("Conflicto SLR")
                        accion[(i, a)] = f"r{p}"
    return estados, accion, ir_a, sig


ESTADOS, ACCION, IR_A, SIGUIENTES = construir_tabla()


def tabla_lr():
    """Filas de la tabla ACCIÓN / IR_A para mostrar en pantalla."""
    cols_a = TERMINALES + [FIN]
    cols_g = NO_TERMINALES[1:]
    filas = []
    for i in range(len(ESTADOS)):
        filas.append({
            "estado": i,
            "accion": [ACCION.get((i, a), "") for a in cols_a],
            "ir_a": [str(IR_A[(i, n)]) if (i, n) in IR_A else "" for n in cols_g],
        })
    return cols_a, cols_g, filas


def item_texto(p, d):
    izq, der = PRODUCCIONES[p]
    der = list(der)
    der.insert(d, "•")
    return f"{izq} → {' '.join(der)}"


def coleccion_lr0():
    return [{"estado": i, "items": [item_texto(p, d) for (p, d) in sorted(it)]}
            for i, it in enumerate(ESTADOS)]


# ---------------------------------------------------------------
# Análisis LR de una línea (lista de tokens)
# ---------------------------------------------------------------
def analizar(tokens):
    """tokens: lista de (lexema, TOKEN). Devuelve dict con pasos, válido, árbol DOT y error."""
    entrada = []
    for lex, tok in tokens:
        if tok not in TOKEN_A_TERMINAL:
            return {"valida": False, "pasos": [], "dot": None,
                    "error": f"Error léxico: '{lex}' no pertenece al lenguaje."}
        entrada.append((TOKEN_A_TERMINAL[tok], lex))
    entrada.append((FIN, FIN))

    pila = [0]
    simbolos = []
    nodos = []          # pila paralela de nodos del árbol: (id, etiqueta, hijos)
    contador = [0]

    def nodo(etq, hijos=()):
        contador[0] += 1
        return (contador[0], etq, list(hijos))

    pasos, k = [], 0
    while True:
        estado = pila[-1]
        a, lex = entrada[k]
        act = ACCION.get((estado, a))
        paso = {"pila": " ".join(str(x) for x in pila),
                "simbolos": " ".join(simbolos),
                "entrada": " ".join(t for t, _ in entrada[k:])}
        if act is None:
            esperados = [t for t in TERMINALES + [FIN] if (estado, t) in ACCION]
            paso["accion"] = "error"
            pasos.append(paso)
            return {"valida": False, "pasos": pasos, "dot": None,
                    "error": f"Error sintáctico: se encontró '{lex if a != FIN else 'fin de línea'}' "
                             f"y se esperaba {' o '.join(esperados)}."}
        if act == "acc":
            paso["accion"] = "aceptar"
            pasos.append(paso)
            return {"valida": True, "pasos": pasos, "dot": _dot_arbol(nodos[-1]), "error": ""}
        if act.startswith("d"):
            paso["accion"] = f"desplazar {act[1:]}"
            pasos.append(paso)
            pila.append(int(act[1:]))
            simbolos.append(a)
            hoja = nodo(f"{a}\\n{lex}")
            nodos.append(hoja)
            k += 1
        else:
            p = int(act[1:])
            izq, der = PRODUCCIONES[p]
            paso["accion"] = f"reducir {p}: {izq} → {' '.join(der)}"
            pasos.append(paso)
            hijos = nodos[-len(der):]
            del pila[-len(der):]
            del simbolos[-len(der):]
            del nodos[-len(der):]
            simbolos.append(izq)
            nodos.append(nodo(izq, hijos))
            pila.append(IR_A[(pila[-1], izq)])


def _dot_arbol(raiz):
    lineas = ["digraph Arbol {", 'node [fontname="Arial", shape=box, style="rounded"];']

    def rec(n):
        nid, etq, hijos = n
        forma = "" if hijos else ', style="rounded,filled", fillcolor="#eeeeee"'
        lineas.append(f'n{nid} [label="{etq}"{forma}];')
        for h in hijos:
            lineas.append(f"n{nid} -> n{h[0]};")
            rec(h)
    rec(raiz)
    lineas.append("}")
    return "\n".join(lineas)


def derivacion(tokens):
    """Derivación por la derecha (la que reconstruye el análisis LR) de una línea válida."""
    n_items = (len(tokens) - 1) // 2
    sufijo = ["pago"]
    pasos = ["PEDIDO", "ITEMS pago"]
    for _ in range(n_items - 1):
        pasos.append(" ".join(["ITEMS", "ITEM"] + sufijo))
        sufijo = ["producto", "cantidad"] + sufijo
        pasos.append(" ".join(["ITEMS"] + sufijo))
    pasos.append(" ".join(["ITEM"] + sufijo))
    pasos.append(" ".join(["producto", "cantidad"] + sufijo))
    return pasos
