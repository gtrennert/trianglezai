#!/usr/bin/env python3
"""
Application de découpage d'un rectangle en X=5 triangles.

Usage : python triangle.py H V
  H = nombre de points horizontaux de la grille
  V = nombre de points verticaux  de la grille

Modes :
  - Exploration (yes) : Génère un fichier texte avec l'arbre complet des possibilités.
  - Dessin (no)       : Affiche les configurations réussies sous forme de dessins ASCII par lots de 9.
"""

import sys
from datetime import datetime

X = 5  # nombre de triangles cible (fixé pour ce projet)

# ── Géométrie de la grille ─────────────────────────────────────────────

def bord_points(H, V):
    pts = []
    for x in range(H):
        pts.append((x, 0))
    for y in range(1, V):
        pts.append((H - 1, y))
    for x in range(H - 2, -1, -1):
        pts.append((x, V - 1))
    for y in range(V - 2, 0, -1):
        pts.append((0, y))
    return pts

def interieur_points(H, V):
    return [(x, y) for x in range(1, H - 1) for y in range(1, V - 1)]

def bords_de(pt, H, V):
    x, y = pt
    b = []
    if y == 0:      b.append('haut')
    if x == H - 1:  b.append('droit')
    if y == V - 1:  b.append('bas')
    if x == 0:      b.append('gauche')
    return b

def partagent_bord(p1, p2, H, V):
    return bool(set(bords_de(p1, H, V)) & set(bords_de(p2, H, V)))

# ── Outils polygones et intersections ──────────────────────────────────

def remove_duplicates(p):
    if not p: return []
    res = []
    for pt in p:
        if not res or res[-1] != pt:
            res.append(pt)
    if len(res) > 1 and res[0] == res[-1]:
        res.pop()
    return res

def true_vertex_count(poly):
    if len(poly) < 3: return 0
    count = 0
    n = len(poly)
    for i in range(n):
        prev = poly[(i-1)%n]
        curr = poly[i]
        nxt = poly[(i+1)%n]
        cross = (curr[0] - prev[0]) * (nxt[1] - curr[1]) - (curr[1] - prev[1]) * (nxt[0] - curr[0])
        if cross != 0:
            count += 1
    return count

def clean_collinear(poly):
    """Supprime les sommets alignés pour ne garder que les vrais coins."""
    if len(poly) < 3: return poly
    res = []
    n = len(poly)
    for i in range(n):
        prev = poly[(i-1)%n]
        curr = poly[i]
        nxt = poly[(i+1)%n]
        cross = (curr[0] - prev[0]) * (nxt[1] - curr[1]) - (curr[1] - prev[1]) * (nxt[0] - curr[0])
        if cross != 0:
            res.append(curr)
    return remove_duplicates(res)

def sur_segment(p, a, b):
    croix = (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])
    if croix != 0:
        return False
    prod = (p[0] - a[0]) * (b[0] - a[0]) + (p[1] - a[1]) * (b[1] - a[1])
    if prod < 0:
        return False
    long2 = (b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2
    return prod <= long2

def seg_intersect(p1, q1, p2, q2):
    def o(p, q, r):
        val = (q[1] - p[1]) * (r[0] - q[0]) - (q[0] - p[0]) * (r[1] - q[1])
        if val == 0: return 0
        return 1 if val > 0 else 2
    o1 = o(p1, q1, p2)
    o2 = o(p1, q1, q2)
    o3 = o(p2, q2, p1)
    o4 = o(p2, q2, q1)
    if o1 != o2 and o3 != o4:
        return True
    return False

def inserer_point(poly, pt):
    if pt in poly:
        return list(poly)
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        if sur_segment(pt, a, b) and pt != a and pt != b:
            return poly[:i + 1] + [pt] + poly[i + 1:]
    return None

def diviser_poly(poly, u, v, all_polys):
    p = remove_duplicates(inserer_point(list(poly), u))
    if p is None: return None
    p = remove_duplicates(inserer_point(p, v))
    if p is None: return None
    
    for w in p:
        if w != u and w != v and sur_segment(w, u, v):
            return None
            
    for other_poly in all_polys:
        n = len(other_poly)
        for i in range(n):
            a = other_poly[i]
            b = other_poly[(i+1)%n]
            
            if other_poly is not poly:
                if sur_segment(u, a, b) and u != a and u != b:
                    return None
                if sur_segment(v, a, b) and v != a and v != b:
                    return None
                
            if sur_segment(u, a, b) or sur_segment(v, a, b):
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
    
    if true_vertex_count(poly1) < 3 or true_vertex_count(poly2) < 3:
        return None
        
    return [poly1, poly2]

def get_candidates(poly, H, V):
    cands = set(poly)
    n = len(poly)
    for i in range(n):
        a = poly[i]
        b = poly[(i+1)%n]
        if bords_de(a, H, V) and bords_de(b, H, V):
            if partagent_bord(a, b, H, V):
                x1, y1 = a
                x2, y2 = b
                if x1 == x2:
                    for y in range(min(y1, y2), max(y1, y2) + 1):
                        cands.add((x1, y))
                elif y1 == y2:
                    for x in range(min(x1, x2), max(x1, x2) + 1):
                        cands.add((x, y1))
    return list(cands)

def same_edge(poly, u, v):
    n = len(poly)
    for i in range(n):
        a = poly[i]
        b = poly[(i+1)%n]
        if sur_segment(u, a, b) and sur_segment(v, a, b):
            return True
    return False

def valid_diagonal(poly, u, v, all_polys):
    for w in poly:
        if w != u and w != v and sur_segment(w, u, v):
            return False
            
    for other_poly in all_polys:
        n = len(other_poly)
        for i in range(n):
            a = other_poly[i]
            b = other_poly[(i+1)%n]
            
            if other_poly is not poly:
                if sur_segment(u, a, b) and u != a and u != b:
                    return False
                if sur_segment(v, a, b) and v != a and v != b:
                    return False
                
            if sur_segment(u, a, b) or sur_segment(v, a, b):
                continue
                
            if seg_intersect(u, v, a, b):
                return False
    return True

# ── Découpage du rectangle après S1 + S2 ───────────────────────────────

def decouper_apres_s2(A1, A2, A3, A4, P1, P2, H, V):
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

# ── Signature Topologique (SGN) ────────────────────────────────────────

def get_signature(triangles, H, V):
    """Génère une signature topologique unique et invariante pour une famille de découpages."""
    all_pts = set()
    for t in triangles:
        for p in t:
            all_pts.add(p)
            
    pt_to_role = {}
    coins = {
        (0, 0): "A1",
        (H - 1, 0): "A2",
        (H - 1, V - 1): "A4",
        (0, V - 1): "A3"
    }
    for p in all_pts:
        if p in coins:
            pt_to_role[p] = coins[p]
        elif 0 < p[0] < H - 1 and 0 < p[1] < V - 1:
            pt_to_role[p] = "I"
            
    top_pts = sorted([p for p in all_pts if p[1] == 0 and p not in coins], key=lambda p: p[0])
    for i, p in enumerate(top_pts):
        pt_to_role[p] = f"T{i+1}"
        
    right_pts = sorted([p for p in all_pts if p[0] == H - 1 and p not in coins], key=lambda p: p[1])
    for i, p in enumerate(right_pts):
        pt_to_role[p] = f"R{i+1}"
        
    bottom_pts = sorted([p for p in all_pts if p[1] == V - 1 and p not in coins], key=lambda p: p[0], reverse=True)
    for i, p in enumerate(bottom_pts):
        pt_to_role[p] = f"B{i+1}"
        
    left_pts = sorted([p for p in all_pts if p[0] == 0 and p not in coins], key=lambda p: p[1], reverse=True)
    for i, p in enumerate(left_pts):
        pt_to_role[p] = f"L{i+1}"
        
    sig_parts = []
    for t in triangles:
        roles = sorted([pt_to_role[p] for p in t])
        sig_parts.append("-".join(roles))
        
    sig_parts.sort()
    return " | ".join(sig_parts)

# ── Mode 1 : Exploration ───────────────────────────────────────────────

def main_explore(H, V):
    A1, A2, A3, A4 = (0, 0), (H - 1, 0), (0, V - 1), (H - 1, V - 1)

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

        for p2 in bord:
            if p2 == A1:
                continue

            polys = decouper_apres_s2(A1, A2, A3, A4, p1, p2, H, V)
            if polys is None:
                continue

            nT, autres = calculer_stats(polys)
            t = tmin(nT, autres)
            dec = decider(nT, autres)
            stats = fmt_stats(nT, autres)
            
            dec_str = dec
            if dec == 'SUCCESS':
                sgn = get_signature([clean_collinear(p) for p in polys], H, V)
                dec_str = f"SUCCESS ({sgn})"

            print(f"\tP2{fmt_pt(p2)} => S2( {fmt_pt(p1)},{fmt_pt(p2)} ) : {stats} = {t}Tmin => {dec_str}")

            if dec == 'GO':
                explorer_explore(2, polys, H, V)


def explorer_explore(niveau, polys, H, V):
    if niveau > 4:
        return

    for pi, poly in enumerate(polys):
        cands = get_candidates(poly, H, V)
        for i in range(len(cands)):
            for j in range(i + 1, len(cands)):
                u = cands[i]
                v = cands[j]
                
                if u == v:
                    continue
                if partagent_bord(u, v, H, V):
                    continue
                if same_edge(poly, u, v):
                    continue
                if not valid_diagonal(poly, u, v, polys):
                    continue
                
                res = diviser_poly(poly, u, v, polys)
                if res is None:
                    continue
                    
                p1, p2 = res
                nv_polys = polys[:pi] + [p1, p2] + polys[pi + 1:]
                nT, autres = calculer_stats(nv_polys)
                t = tmin(nT, autres)
                dec = decider(nT, autres)
                stats = fmt_stats(nT, autres)
                
                dec_str = dec
                if dec == 'SUCCESS':
                    sgn = get_signature([clean_collinear(p) for p in nv_polys], H, V)
                    dec_str = f"SUCCESS ({sgn})"
                
                indent = "\t" * niveau
                sn = niveau + 1
                
                print(f"{indent}P{sn}{fmt_pt(v)} => S{sn}( {fmt_pt(u)},{fmt_pt(v)} ) : {stats} = {t}Tmin => {dec_str}")

                if dec == 'GO':
                    explorer_explore(niveau + 1, nv_polys, H, V)


# ── Mode 2 : Dessin ASCII ──────────────────────────────────────────────

def explorer_gen(niveau, polys, H, V):
    if niveau > 4:
        return

    for pi, poly in enumerate(polys):
        cands = get_candidates(poly, H, V)
        for i in range(len(cands)):
            for j in range(i + 1, len(cands)):
                u = cands[i]
                v = cands[j]
                
                if u == v:
                    continue
                if partagent_bord(u, v, H, V):
                    continue
                if same_edge(poly, u, v):
                    continue
                if not valid_diagonal(poly, u, v, polys):
                    continue
                
                res = diviser_poly(poly, u, v, polys)
                if res is None:
                    continue
                    
                p1, p2 = res
                nv_polys = polys[:pi] + [p1, p2] + polys[pi + 1:]
                nT, autres = calculer_stats(nv_polys)
                dec = decider(nT, autres)

                if dec == 'SUCCESS':
                    yield nv_polys
                elif dec == 'GO':
                    yield from explorer_gen(niveau + 1, nv_polys, H, V)


def normalize_solution(polys):
    """Crée une représentation unique d'une solution en triant les sommets et les triangles."""
    sol = []
    for p in polys:
        p_clean = clean_collinear(p)
        sol.append(tuple(sorted(p_clean)))
    return tuple(sorted(sol))


def generate_all_successes(H, V):
    A1, A2, A3, A4 = (0, 0), (H - 1, 0), (0, V - 1), (H - 1, V - 1)
    
    pts_int = interieur_points(H, V)
    if not pts_int:
        return

    seen = set()
    for p1 in pts_int:
        bord = bord_points(H, V)
        for p2 in bord:
            if p2 == A1:
                continue

            polys = decouper_apres_s2(A1, A2, A3, A4, p1, p2, H, V)
            if polys is None:
                continue

            nT, autres = calculer_stats(polys)
            dec = decider(nT, autres)

            if dec == 'SUCCESS':
                clean_polys = [clean_collinear(p) for p in polys]
                norm = normalize_solution(clean_polys)
                if norm not in seen:
                    seen.add(norm)
                    yield clean_polys
            elif dec == 'GO':
                for nv_polys in explorer_gen(2, polys, H, V):
                    clean_polys = [clean_collinear(p) for p in nv_polys]
                    norm = normalize_solution(clean_polys)
                    if norm not in seen:
                        seen.add(norm)
                        yield clean_polys


def get_ascii_lines(H, V, segments):
    """Génère les lignes de texte ASCII pour un rectangle et ses segments."""
    SCALE_X = 12
    SCALE_Y = 6
    W = H * SCALE_X + 1
    H_grid = V * SCALE_Y + 1
    grid = [[' ' for _ in range(W)] for _ in range(H_grid)]

    for x in range(H):
        for y in range(V):
            grid[y * SCALE_Y][x * SCALE_X] = '+'

    def draw_line(x1, y1, x2, y2):
        orig_dx = x2 - x1
        orig_dy = y2 - y1
        if orig_dy == 0:
            char = '-'
        elif orig_dx == 0:
            char = '|'
        elif orig_dx * orig_dy > 0:
            char = '\\'
        else:
            char = '/'
            
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy

        cx, cy = x1, y1
        while True:
            if (cx, cy) == (x2, y2):
                grid[cy][cx] = '+'
            elif grid[cy][cx] == ' ':
                grid[cy][cx] = char
            
            if cx == x2 and cy == y2:
                break
                
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                cx += sx
            if e2 < dx:
                err += dx
                cy += sy

    for seg in segments:
        p1, p2 = seg
        draw_line(p1[0] * SCALE_X, p1[1] * SCALE_Y, p2[0] * SCALE_X, p2[1] * SCALE_Y)

    return [ "".join(row) for row in grid ]


def main_draw(H, V):
    print(f"Recherche des solutions pour {H}x{V}...")
    gen = generate_all_successes(H, V)
    batch_count = 0
    
    while True:
        batch = []
        try:
            for _ in range(9):
                batch.append(next(gen))
        except StopIteration:
            pass

        if not batch:
            if batch_count == 0:
                print("Aucune solution trouvée.")
            else:
                print("Plus aucune solution.")
            break

        for i, triangles in enumerate(batch):
            print(f"--- Solution {batch_count * 9 + i + 1} ---")
            
            segments = []
            for t in triangles:
                segments.append((t[0], t[1]))
                segments.append((t[1], t[2]))
                segments.append((t[2], t[0]))
                
            def fmt_triangle(t):
                pts = ",".join([fmt_pt(p) for p in t])
                return f"( {pts} )"
            list_str = " - ".join([fmt_triangle(t) for t in triangles])
            
            sgn = get_signature(triangles, H, V)
            
            print(f"{list_str} ({sgn})")
            
            ascii_lines = get_ascii_lines(H, V, segments)
            for line in ascii_lines:
                print(line)
            print()

        batch_count += 1

        if len(batch) < 9:
            print("Plus aucune solution.")
            break

        ans = input("continuer avec les 9 suivants yes/no: ").strip().lower()
        if ans != 'yes':
            break


# ── Programme principal ────────────────────────────────────────────────

if __name__ == "__main__":
    H = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    V = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    
    mode = input("mode exploration yes/no (defaut: yes): ").strip().lower()
    
    if mode == "no":
        main_draw(H, V)
    else:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        nom_fichier = f"resultat{timestamp}.txt"
        
        print(f"Calcul en cours... Les résultats seront écrits dans : {nom_fichier}")
        
        with open(nom_fichier, 'w', encoding='utf-8') as f:
            old_stdout = sys.stdout
            sys.stdout = f
            try:
                main_explore(H, V)
            finally:
                sys.stdout = old_stdout
                
        print(f"Terminé ! Les résultats ont été sauvegardés dans {nom_fichier}.")