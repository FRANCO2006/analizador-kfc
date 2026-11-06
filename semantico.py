"""
Análisis semántico de los pedidos (se aplica a los pedidos sintácticamente válidos).

Reglas de significado del negocio:
  R1) La cantidad de cada producto debe estar entre 1 y 50 unidades.
  R2) Un mismo producto no debe repetirse en el pedido (se suman en un solo ítem).
"""

CANTIDAD_MIN = 1
CANTIDAD_MAX = 50

REGLAS = [
    ("R1", f"La cantidad de cada producto debe estar entre {CANTIDAD_MIN} y {CANTIDAD_MAX} unidades."),
    ("R2", "Un mismo producto no debe repetirse en el pedido."),
]


def analizar(tokens):
    """tokens: lista de (lexema, token) de un pedido sintácticamente válido."""
    items = [(tokens[i][0], int(tokens[i + 1][0])) for i in range(0, len(tokens) - 1, 2)]
    pago = tokens[-1][0]
    errores, vistos = [], set()
    for producto, cantidad in items:
        if not CANTIDAD_MIN <= cantidad <= CANTIDAD_MAX:
            errores.append(f"Error semántico (R1): la cantidad {cantidad} de {producto} "
                           f"debe estar entre {CANTIDAD_MIN} y {CANTIDAD_MAX}.")
        if producto in vistos:
            errores.append(f"Error semántico (R2): el producto {producto} se repite; "
                           "suma sus cantidades en un solo ítem.")
        vistos.add(producto)
    return {
        "valida": not errores,
        "errores": errores,
        "items": items,
        "pago": pago,
        "unidades": sum(c for _, c in items),
    }
