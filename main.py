#!/usr/bin/env python3
"""
Application de découpage d'un rectangle en X=5 triangles.

Explore les possibilités de découper un rectangle en exactement 5 triangles
en utilisant une grille d'exploration H×V.

Usage : python triangle.py H V
  H = nombre de points horizontaux de la grille
  V = nombre de points verticaux  de la grille

Coins du rectangle :
  A1 = (0, 0)       coin supérieur gauche
  A2 = (H-1, 0)     coin supérieur droit
  A3 = (0, V-1)     coin inférieur gauche
  A4 = (H-1, V-1)   coin inférieur droit

Règles :
  - S1 va de A1 vers P1 (unique point intérieur).
  - S2 va de P1 vers P2 (sur le bord, ≠ A1).
  - S_n (n ≥ 3) va de P_{n-1} vers P_n (sur le bord,
    ≠ points déjà définis, pas sur le même bord que P_{n-1}).
  - Une forme Fx (x sommets) produit au minimum x-2 triangles.
  - Tmin = triangles actuels + Σ(x-2 pour chaque Fx).
  - GO si Tmin ≤ 5 ; STOP si Tmin > 5 ; SUCCESS si 5T exactement.
"""

import sys

X = 5  # nombre de triangles cible (fixé pour ce projet)


# ── Géométrie de la grille ─────────────────────────────────────────────

def bord_points(H, V):
    """Points du bord, ordre horaire en partant de A1(0,0), A1 inclus."""
    pts = []
    for x in range(H):
        pts.append((x, 0))            # haut  : A1 → A2
    for y in range(1, V):
        pts.append((H - 1, y))        # droit : A2 → A4
    for x in range(H - 2, -1, -1):
        pts.append((x, V - 1))        # bas   : A4 → A3
    for y in range(V - 2, 0, -1):
        pts.append((0, y))            # gauche: A3 → A1
    return pts


def interieur_points(H, V):
    """Points strictement intérieurs de la grille."""
    return [(x, y) for x in range(1, H - 1) for y in range(1, V - 1)]


def bords_de(pt, H, V):
    """Liste des bords du rectangle sur lesquels se trouve pt."""
    x, y = pt
    b = []
    if y == 0:      b.append('haut')
    if x == H - 1:  b.append('droit')
    if y == V - 1:  b.append('bas')
    if x == 0:      b.append('gauche')
    return b


def partagent_bord(p1, p2, H, V):
    """True si p1 et p2 sont sur un bord commun du rectangle."""
    return bool(set(bords_de(p1, H, V)) & set(bords_de(p2, H, V)))


# ── Outils polygones ───────────────────────────────────────────────────

def sur_segment(p, a, b):
    """True si le point p est sur le segment [a, b] (extrémités comprises)."""
    croix = (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])
    if croix != 0:
        return False
    prod = (p[0] - a[0]) * (b[0] - a[0]) + (p[1] - a[1]) * (b[1] - a[1])
    if prod < 0:
        return False
    long2 = (b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2
    return prod <= long2


def sur_bord_poly(pt, poly):
    """True si pt est sur le bord du polygone (sommet ou sur une arête)."""
    if pt in poly:
        return True
    n = len(poly)
    for i in range(n):
        if sur_segment(pt, poly[i], poly[(i + 1) % n]):
            return True
    return False


def inserer_point(poly, pt):
    """Insère pt dans la liste des sommets s'il est sur une arête.
    Retourne la nouvelle liste ou None si pt n'est pas sur le bord."""
    if pt in poly:
        return list(poly)
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        if sur_segment(pt, a, b) and pt != a and pt != b:
            return poly[:i + 1] + [pt] + poly[i + 1:]
    return None


def diviser_poly(poly, u, v):
    """Divise poly le long du segment u-v.
    u et v doivent être sur le bord du polygone.
    Retourne (poly1, poly2) ou None."""
    p = inserer_point(list(poly), u)
    if p is None:
        return None
    p = inserer_point(p, v)
    if p is None:
        return None
    if u not in p or v not in p:
        return None
    iu, iv = p.index(u), p.index(v)
    if iu == iv:
        return None
    if iu < iv:
        return p[iu:iv + 1], p[iv:] + p[:iu + 1]
    else:
        return p[iu:] + p[:iv + 1], p[iv:iu + 1]


# ── Découpage du rectangle après S1 + S2 ───────────────────────────────

def decouper_apres_s2(A1, A2, A3, A4, P1, P2, H, V):
    """
    Après S1(A1→P1) et S2(P1→P2), le chemin A1-P1-P2 divise le rectangle
    en deux polygones.
    Retourne [poly1, poly2] ou None.
    """
    bords = bords_de(P2, H, V)
    # Coins horaires : A1, A2, A4, A3
    # Priorité : haut > droit > bas > gauche  (pour traiter correctement les coins)
    if 'haut' in bords:
        cw, ccw = [], [A3, A4, A2]
    elif 'droit' in bords:
        cw, ccw = [A2], [A3, A4]
    elif 'bas' in bords:
        cw, ccw = [A2, A4], [A3]
    elif 'gauche' in bords:
        cw, ccw = [A2, A4, A3], []
    else:
        return None

    poly1 = [A1] + cw + [P2, P1]          # sens horaire : A1 → … → P2 → P1 → A1
    poly2 = [A1, P1, P2] + ccw[::-1]      # sens horaire : A1 → P1 → P2 → … → A1
    return [poly1, poly2]


# ── Statistiques et décision ───────────────────────────────────────────

def calculer_stats(polys):
    """Retourne (nb_triangles, liste_triée_des_tailles_des_autres_formes)."""
    nT = sum(1 for p in polys if len(p) == 3)
    autres = sorted(len(p) for p in polys if len(p) != 3)
    return nT, autres


def tmin(nT, autres):
    """Nombre minimum de triangles atteignables."""
    return nT + sum(x - 2 for x in autres)


def decider(nT, autres, cible=X):
    """GO / STOP / SUCCESS."""
    if not autres and nT == cible:
        return 'SUCCESS'
    if tmin(nT, autres) > cible:
        return 'STOP'
    return 'GO'


def fmt_stats(nT, autres):
    parts = []
    if nT > 0:
        parts.append(f"{nT}T")
    for x in autres:
        parts.append(f"F{x}")
    return " + ".join(parts) if parts else "0T"


def fmt_pt(p):
    return f"({p[0]},{p[1]})"


# ── Exploration récursive (S3, S4, S5) ─────────────────────────────────

def explorer(niveau, pt_courant, polys, definis, H, V):
    """
    Explore le segment S_{niveau+1} à partir de pt_courant.
      niveau = 2 → S3,  niveau = 3 → S4,  niveau = 4 → S5.
    """
    if niveau > 4:          # S5 au maximum (5 polygones = cible)
        return

    bord = bord_points(H, V)

    for p_suiv in bord:
        # --- contraintes sur P_n ---
        if p_suiv in definis:
            continue
        if partagent_bord(pt_courant, p_suiv, H, V):
            continue

        # --- chercher les polygones non-triangles contenant les deux points ---
        scissions = []
        for pi, poly in enumerate(polys):
            if len(poly) == 3:
                continue
            if not sur_bord_poly(pt_courant, poly):
                continue
            if not sur_bord_poly(p_suiv, poly):
                continue
            res = diviser_poly(poly, pt_courant, p_suiv)
            if res is not None:
                scissions.append((pi, res))

        if not scissions:
            continue

        for pi, (p1, p2) in scissions:
            nv_polys = polys[:pi] + [p1, p2] + polys[pi + 1:]
            nT, autres = calculer_stats(nv_polys)
            t = tmin(nT, autres)
            dec = decider(nT, autres)
            stats = fmt_stats(nT, autres)

            indent = "\t" * niveau
            sn = niveau + 1          # numéro du segment
            pn = niveau + 1          # numéro du point

            print(f"{indent}P{pn}{fmt_pt(p_suiv)} => "
                  f"S{sn}( {fmt_pt(pt_courant)},{fmt_pt(p_suiv)} ) : "
                  f"{stats} = {t}Tmin => {dec}")

            if dec == 'GO':
                explorer(niveau + 1, p_suiv, nv_polys,
                         definis | {p_suiv}, H, V)


# ── Programme principal ────────────────────────────────────────────────

def main(H, V):
    A1 = (0, 0)
    A2 = (H - 1, 0)
    A3 = (0, V - 1)
    A4 = (H - 1, V - 1)

    print("A1")

    pts_int = interieur_points(H, V)
    if not pts_int:
        print("# Pas de point intérieur (H<3 ou V<3) — impossible")
        return

    for p1 in pts_int:
        print(f"S1(A1,P1)")
        print(f"P1{fmt_pt(p1)}")

        bord = bord_points(H, V)
        definis = {A1, p1}

        for p2 in bord:
            if p2 in definis:
                continue

            polys = decouper_apres_s2(A1, A2, A3, A4, p1, p2, H, V)
            if polys is None:
                continue

            nT, autres = calculer_stats(polys)
            t = tmin(nT, autres)
            dec = decider(nT, autres)
            stats = fmt_stats(nT, autres)

            print(f"\tP2{fmt_pt(p2)} => "
                  f"S2( {fmt_pt(p1)},{fmt_pt(p2)} ) : "
                  f"{stats} = {t}Tmin => {dec}")

            if dec == 'GO':
                explorer(2, p2, polys, definis | {p2}, H, V)


if __name__ == "__main__":
    H = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    V = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    main(H, V)