#!/usr/bin/env python3
"""
Application de découpage d'un rectangle en X=5 triangles.

Usage : python triangle.py H V
  H = nombre de points horizontaux de la grille
  V = nombre de points verticaux  de la grille

Règles :
  - S1 va de A1 vers P1 (unique point intérieur).
  - S2 va de P1 vers P2 (sur le bord, ≠ A1).
  - S_n (n ≥ 3) va de P_{n-1} vers P_n (sur le bord ou P1,
    ≠ points déjà définis, pas sur le même bord que P_{n-1}).
  - Une forme Fx (x sommets) produit au minimum x-2 triangles.
  - Tmin = triangles actuels + Σ(x-2 pour chaque Fx).
  - GO si Tmin ≤ 5 ; STOP si Tmin > 5 ; SUCCESS si 5T exactement.
"""

import sys
from datetime import datetime

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

# ── Outils polygones et intersections ──────────────────────────────────

def remove_duplicates(p):
    """Supprime uniquement les doublons consécutifs (garde les points alignés)."""
    if not p: return []
    res = []
    for pt in p:
        if not res or res[-1] != pt:
            res.append(pt)
    if len(res) > 1 and res[0] == res[-1]:
        res.pop()
    return res

def true_vertex_count(poly):
    """Compte le nombre de sommets ayant un angle non plat (vrais coins)."""
    if len(poly) < 3: return 0
    count = 0
    n = len(poly)
    for i in range(n):
        prev = poly[(i-1)%n]
        curr = poly[i]
        nxt = poly[(i+1)%n]
        # Produit en croix pour vérifier l'alignement
        cross = (curr[0] - prev[0]) * (nxt[1] - curr[1]) - (curr[1] - prev[1]) * (nxt[0] - curr[0])
        if cross != 0:
            count += 1
    return count

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

def orientation(p, q, r):
    val = (q[1] - p[1]) * (r[0] - q[0]) - (q[0] - p[0]) * (r[1] - q[1])
    if val == 0: return 0
    return 1 if val > 0 else 2

def seg_intersect(p1, q1, p2, q2):
    """Vrai si les segments [p1,q1] et [p2,q2] se croisent strictement."""
    o1 = orientation(p1, q1, p2)
    o2 = orientation(p1, q1, q2)
    o3 = orientation(p2, q2, p1)
    o4 = orientation(p2, q2, q1)
    if o1 != o2 and o3 != o4:
        return True
    return False

def inserer_point(poly, pt):
    """Insère pt dans la liste des sommets s'il est sur une arête."""
    if pt in poly:
        return list(poly)
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        if sur_segment(pt, a, b) and pt != a and pt != b:
            return poly[:i + 1] + [pt] + poly[i + 1:]
    return None

def diviser_poly(poly, u, v):
    """Divise poly le long du segment u-v en vérifiant la validité topologique."""
    p = remove_duplicates(inserer_point(list(poly), u))
    if p is None: return None
    p = remove_duplicates(inserer_point(p, v))
    if p is None: return None
    
    # 1. Empêcher le segment de passer exactement par un autre sommet
    for w in p:
        if w != u and w != v and sur_segment(w, u, v):
            return None
            
    # 2. Empêcher le segment de croiser les arêtes existantes du polygone
    n = len(p)
    for i in range(n):
        a = p[i]
        b = p[(i+1)%n]
        if u in (a, b) or v in (a, b):
            continue
        if seg_intersect(u, v, a, b):
            return None
            
    if u not in p or v not in p: return None
    iu, iv = p.index(u), p.index(v)
    if iu == iv: return None
    
    if iu < iv:
        poly1 = p[iu:iv + 1]
        poly2 = p[iv:] + p[:iu + 1]
    else:
        poly1 = p[iu:] + p[:iv + 1]
        poly2 = p[iv:iu + 1]
        
    poly1 = remove_duplicates(poly1)
    poly2 = remove_duplicates(poly2)
    
    # 3. Empêcher la création de formes dégénérées (lignes plates à 2 sommets)
    if true_vertex_count(poly1) < 3 or true_vertex_count(poly2) < 3:
        return None
        
    return [poly1, poly2]

# ── Découpage du rectangle après S1 + S2 ───────────────────────────────

def decouper_apres_s2(A1, A2, A3, A4, P1, P2, H, V):
    """Découpe le rectangle proprement en évitant les doublons de coins."""
    rect = [A1, A2, A4, A3]
    rect_avec_p2 = remove_duplicates(inserer_point(list(rect), P2))
    if rect_avec_p2 is None:
        return None
        
    i1 = rect_avec_p2.index(A1)
    i2 = rect_avec_p2.index(P2)
        
    if i1 < i2:
        bord1 = rect_avec_p2[i1:i2+1]
        bord2 = rect_avec_p2[i2:] + rect_avec_p2[:i1+1]
    else:
        bord1 = rect_avec_p2[i1:] + rect_avec_p2[:i2+1]
        bord2 = rect_avec_p2[i2:i1+1]
        
    poly1 = remove_duplicates(bord1 + [P1])
    poly2 = remove_duplicates(bord2 + [P1])
    
    if true_vertex_count(poly1) < 3 or true_vertex_count(poly2) < 3:
        return None
    return [poly1, poly2]

# ── Statistiques et décision ───────────────────────────────────────────

def calculer_stats(polys):
    nT = 0
    autres = []
    for p in polys:
        v_count = true_vertex_count(p)
        if v_count == 3:
            nT += 1
        else:
            autres.append(v_count)
    autres.sort()
    return nT, autres

def tmin(nT, autres):
    return nT + sum(x - 2 for x in autres)

def decider(nT, autres, cible=X):
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

# ── Exploration récursive ─────────────────────────────────────────────

def explorer(niveau, pt_courant, polys, definis, P1, H, V):
    if niveau > 4:
        return

    candidats = []
    if pt_courant != P1:
        candidats.append(P1)
        
    for p_suiv in bord_points(H, V):
        if p_suiv in definis:
            continue
        if partagent_bord(pt_courant, p_suiv, H, V):
            continue
        candidats.append(p_suiv)

    for p_suiv in candidats:
        scissions = []
        for pi, poly in enumerate(polys):
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
            sn = niveau + 1
            pn = niveau + 1

            print(f"{indent}P{pn}{fmt_pt(p_suiv)} => "
                  f"S{sn}( {fmt_pt(pt_courant)},{fmt_pt(p_suiv)} ) : "
                  f"{stats} = {t}Tmin => {dec}")

            if dec == 'GO':
                explorer(niveau + 1, p_suiv, nv_polys,
                         definis | {p_suiv}, P1, H, V)

# ── Programme principal ────────────────────────────────────────────────

def main(H, V):
    A1 = (0, 0)
    A2 = (H - 1, 0)
    A3 = (0, V - 1)
    A4 = (H - 1, V - 1)

    print(f"# Grille d'exploration : {H} points horizontaux (x=0..{H-1}), {V} points verticaux (y=0..{V-1})")
    print(f"# Coins du rectangle : A1{fmt_pt(A1)} A2{fmt_pt(A2)} A3{fmt_pt(A3)} A4{fmt_pt(A4)}")
    print(f"# Points strictement intérieurs possibles pour P1 : {interieur_points(H, V)}")
    print(f"# Points sur le bord : {bord_points(H, V)}")
    print("-" * 60)

    pts_int = interieur_points(H, V)
    if not pts_int:
        print("# Pas de point intérieur (H<3 ou V<3) — impossible")
        return

    print("A1")

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
                explorer(2, p2, polys, definis | {p2}, p1, H, V)

if __name__ == "__main__":
    H = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    V = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    nom_fichier = f"resultat{timestamp}.txt"
    
    print(f"Calcul en cours... Les résultats seront écrits dans : {nom_fichier}")
    
    with open(nom_fichier, 'w', encoding='utf-8') as f:
        old_stdout = sys.stdout
        sys.stdout = f
        try:
            main(H, V)
        finally:
            sys.stdout = old_stdout
            
    print(f"Terminé ! Les résultats ont été sauvegardés dans {nom_fichier}.")