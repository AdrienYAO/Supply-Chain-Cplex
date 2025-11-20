# CMS_Optimization.py
# -*- coding: utf-8 -*-
from docplex.mp.model import Model
import os
import json
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(BASE_DIR, "DataFinal.json")
OUT_TXT = os.path.join(BASE_DIR, "resultats_optimisation.txt")

# --- Chargement JSON ---
if not os.path.exists(JSON_PATH):
    raise FileNotFoundError(f"Le fichier DataFinal.json est introuvable : {JSON_PATH}")

with open(JSON_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

def load_demande_from_json(params, periods):
    """Créer le dict demande[(p,t)] à partir de data['params']"""
    demande = {}
    keys_sorted = sorted(params.keys(), key=lambda k: int(k.lstrip("P")))
    for i, pkey in enumerate(keys_sorted, start=1):
        moy = params[pkey].get("moyenne")
        if isinstance(moy, list):
            moy_list = [float(x) for x in moy]
        else:
            moy_list = [float(moy)] * len(periods)
        # padding/trimming si nécessaire
        if len(moy_list) < len(periods):
            moy_list += [moy_list[-1]] * (len(periods) - len(moy_list))
        elif len(moy_list) > len(periods):
            moy_list = moy_list[:len(periods)]
        for idx, t in enumerate(periods):
            demande[(i, t)] = max(0, int(round(moy_list[idx])))
    return demande

def run_cms_optimization():
    mdl = Model(name="CMS_Optimization")

    # --- Ensembles ---
    P = data.get('products')
    M = data.get('machines')
    T = data.get('periods')
    C = data.get('cells')
    L = data.get('subcontractors')
    operations = data.get('operations')
    
    
    # --- Paramètres ---
    params = data.get("params", {})
    demande = load_demande_from_json(params, T)
    MC = data.get('MC', [])
    set_cost = data.get('set_cost', [])
    big_m = data.get('big_m')
    hold_cost = data.get('hold_cost', [])
    intr_cost = data.get('intr_cost', [])
    inter_cost = data.get('inter_cost', [])
    sub_capacity = data.get('sub_capacity', [])
    pdef = data.get('pdef', [])
    tlot = data.get('tlot', [])
    sal_cost = data.get('sal_cost', [])
    mcost = data.get('mcost', [])
    sub_cost = data.get('sub_cost', [])
    CL = data.get('CL', None)
    LP = data.get('LP', None)
    INT = data.get('INT', [])
    mcim = data.get('mcim', [])

    # --- Variables de décision ---
    X = mdl.integer_var_dict(((p, mi, mj, ci, cj, t) 
                              for p in P for mi in M for mj in M for ci in C for cj in C for t in T),
                             name="X")
    Z = mdl.binary_var_dict(((p, mi, mj, ci, cj, t)
                             for p in P for mi in M for mj in M for ci in C for cj in C for t in T),
                            name="Z")
    Y = mdl.integer_var_dict(((p, l, t) for p in P for l in L for t in T), name="Y")
    B = mdl.integer_var_dict(((p, t) for p in P for t in T), name="B")
    NAJ = mdl.integer_var_dict(((m, c, t) for m in M for c in C for t in T), name="NAJ")
    NRE = mdl.integer_var_dict(((m, c, t) for m in M for c in C for t in T), name="NRE")
    MN = mdl.integer_var_dict(((m, c, t) for m in M for c in C for t in T), name="MN")

    # --- Fonction objectif (simplifiée Q1, Q4, Q5) ---
    Q1 = mdl.sum((set_cost[mi-1] / tlot[p-1]) * X[p, mi, mj, ci, cj, t]
                 for (p, mi, mj, ci, cj, t) in X)
    Q2 = mdl.sum(mcim[p, mj] * operations[p][mj] * X[p, mi, mj, ci, cj, t] 
                 for (p, mi, mj, ci, cj, t) in X if p < len(operations) and mj < len(operations[p]) and (p, mj) in mcim)
    Q3 = mdl.sum((mcost[mi] if mi in mcost else 0) * NAJ[mi, c, t] - (sal_cost[mi] if mi in sal_cost else 0) * NRE[mi, c, t] 
                 for mi in M for c in C for t in T)
    Q4 = mdl.sum(sub_cost[l-1] * Y[p, l, t] for p in P for l in L for t in T)
    Q5 = mdl.sum(hold_cost[p-1] * B[p, t] for p in P for t in T)
    Q6 = mdl.sum(intr_cost[p-1] * X[p, mi, mj, c, c, t] for p in P for mi in M for mj in M for c in C for t in T)
    Q7 = mdl.sum(inter_cost[p-1] * X[p, mi, mj, ci, cj, t] for p in P for mi in M for mj in M for ci in C for cj in C for t in T if ci != cj)

    mdl.minimize(Q1 + Q2 + Q3 + Q4 + Q5 + Q6 + Q7)

    # --- Contraintes principales ---
    # 1️⃣ Satisfaction demande
    for p in P:
      for t in T:
        # B_{p,t-1} = 0 si t=1
        prev_B = B[p, t-1] if t > 1 else 0
        
        mdl.add_constraint(
            mdl.sum(X[p, mi, mj, ci, cj, t] for mi in M for mj in M for ci in C for cj in C)
            + mdl.sum(Y[p, l, t] for l in L)
            + B[p, t] >= demande[p, t] + prev_B,
                    ctname=f"satisf_dem_{p}_{t}")

    #for p in P:
       # for t_index, t in enumerate(T):
            #lhs = mdl.sum(X[p, mi, mj, ci, cj, t] for mi in M for mj in M for ci in C for cj in C) + \
                #  mdl.sum(Y[p, l, t] for l in L) + B[p, t]
            #rhs = demande.get((p, t), 0) + (B.get((p, T[t_index-1]), 0) if t_index > 0 else 0)
            #mdl.add_constraint(lhs >= rhs, f"Demand_p{p}_t{t}")
            
            
    #for p in P:
       #for mi in M:
        # for mj in M:
           # for ci in C:
              #  for cj in C:
                    #for t in T:
                       # mdl.add_constraint(
                           # X[p, mi, mj, ci, cj, t] * (1 - MCIM[p, mj]) <= 0,
                             # ctname=f"ct_X_MCIM_{p}_{mi}_{mj}_{c}_{cj}_{t}")
            
            
    for p, mi, mj, ci, cj, t in X:
            # Index ajusté pour accéder à mcim
            if 0 <= p-1 < len(mcim) and 0 <= mj-1 < len(mcim[0]):
                val_mcim = mcim[p-1][mj-1]
            else:
                val_mcim = 0  # ou tu peux lever une exception ici si nécessaire

            # 1. Interdire les transferts si machine non autorisée
            mdl.add_constraint(X[p, mi, mj, ci, cj, t] * (1 - val_mcim) <= 0)

            # 2. Respect du lot max
            mdl.add_constraint(X[p, mi, mj, ci, cj, t] <= tlot[p-1])

            # 3. Activation via Z
            mdl.add_constraint(X[p, mi, mj, ci, cj, t] <= Z[p, mi, mj, ci, cj, t] * big_m)

    # 2️⃣ Sous-traitance ≤ capacité
    for l in L:
        for t in T:
            mdl.add_constraint(mdl.sum(Y[p, l, t] for p in P) <= sub_capacity[l-1], f"SubCap_l{l}_t{t}")

    # 3️⃣ Stock ≤ pdef
    for p in P:
     for t in T:
        mdl.add_constraints(B[p, t] <= pdef[p-1][t-1] for p in P for t in T)
        
    for m in M:
       for c in C:
          mdl.add_constraint(MN[m, c, 1] == INT[m-1], f"Equilibrage_init_{m}_{c}")

    # 4️⃣ Machines (NAJ/NRE/MN)
# --- Contrainte d’équilibrage dynamique des machines ---
    for m in M:
       for c in C:
        for t in T:
            if t > 1:
                mdl.add_constraint(
                    NAJ[m, c, t] - NRE[m, c, t] + MN[m, c, t-1] == MN[m, c, t],
                    ctname=f"Equilibrage_M_{m}_{c}_{t}"
                )
            else:
                # Pour t = 1, il n’y a pas de période précédente (on peut supposer MN[m,c,0] = 0)
                mdl.add_constraint(
                    NAJ[m, c, t] - NRE[m, c, t] == MN[m, c, t],
                    ctname=f"Equilibrage_init_M_{m}_{c}_{t}"
                )
    # 5️⃣ LP et CL
    for c in C:
        for t in T:
            mdl.add_constraint(LP <= mdl.sum(MN[m, c, t] for m in M), f"LP_c{c}_t{t}")
            mdl.add_constraint(mdl.sum(MN[m, c, t] for m in M) <= CL, f"CL_c{c}_t{t}")

    # 6️⃣ Utilisation machine
    for t in T:
        for mi in M:
            mdl.add_constraint(
                mdl.sum(X[p, mi, mj, ci, cj, t] for p in P for mj in M for c in C for cp in C) 
                <= MC[m-1] * mdl.sum(MN[m, c, t] for c in C),
                f"MachineUtilization_m{m}_t{t}"
            )

    # 7️⃣ Flux intra-cellulaire
    for t in T:
        for mi in M:
            for c in C:
                lhs = mdl.sum(X[p, mi, mj, c, cp, t] for p in P for mj in M for cp in C)
                rhs = mdl.sum(X[p, mk, mi, cp, c, t] for p in P for mk in M for cp in C)
                mdl.add_constraint(lhs <= rhs, f"FlowBalance_m{mi}_c{c}_t{t}")
                
    # --- Résolution ---
    start_time = time.time()
    solution = mdl.solve(log_output=False)
    elapsed_time = time.time() - start_time

    # --- Écriture fichier sortie ---
    with open(OUT_TXT, "w", encoding="utf-8") as f:
        f.write("Demande :\n")
        for k in sorted(demande.keys()):
            f.write(f"{k} {demande[k]}\n")

        if solution:
            f.write("\n✅ Solution trouvée\n")
            f.write(f"Statut: {mdl.solve_details.status}\n")
            f.write(f"Fonction objectif = {mdl.objective_value}\n")
            f.write(f"Nombre d'itérations = {mdl.solve_details.nb_iterations}\n")
            f.write(f"Temps d'exécution : {elapsed_time:.4f} s\n\n")
            
            tol = 1e-6
            for name, var_dict in [("X", X), ("Z", Z), ("Y", Y), ("B", B), ("NAJ", NAJ), ("NRE", NRE), ("MN", MN)]:
                f.write(f"\n--- Variables {name} ---\n")
                found = False
                for k, var in var_dict.items():
                    val = var.solution_value
                    if val is not None and abs(val) > tol:
                        f.write(f"{name}{k} = {val}\n")
                        found = True
                if not found:
                    f.write(f"Aucune valeur significative non nulle pour {name}.\n")
        else:
            f.write("\n❌ Aucune solution trouvée.\n")
            f.write(f"Temps écoulé: {elapsed_time:.4f} s\n")
        
        f.write("\nLP ET CL (depuis JSON si présents):\n")
        f.write(f"LP = {LP}\n")
        f.write(f"CL = {CL}\n")

        f.write("\nStatistiques du modèle :\n")
        f.write(f"Variables totales : {mdl.number_of_variables}\n")
        f.write(f"Contraintes totales : {mdl.number_of_constraints}\n")
        try:
            f.write(f"nonzeros : {mdl.number_of_nonzeros}\n")
        except Exception:
            pass

    print(f"Résultats écrits dans {OUT_TXT}")

if __name__ == "__main__":
    run_cms_optimization()
