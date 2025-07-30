# -*- coding: utf-8 -*-
"""
@author: yadri_000
"""

import json
import numpy as np
import time
from docplex.mp.model import Model

# Charger les données depuis le fichier JSON
with open('datay.json') as f:
    data = json.load(f)

# Générer la demande aléatoire selon la loi normale
def generer_demande(params, periods):
    demande = {}
    for i, (periode, valeurs) in enumerate(params.items(), start=1):
        for t in periods:
            val = max(0, int(np.random.normal(valeurs["moyenne"], valeurs["ecart_type"])))
            demande[(i, t)] = val
    return demande

# Initialiser ensembles et paramètres
# Initialisation des ensembles pour le modèle
products = range(1, 5)         # P1 à P4 (4 produits)
machines = range(1, 4)         # 3 machines
periods = range(1, 3)          # 2 périodes
cells = range(1, 3)            # 2 cellules (à adapter si besoin)
machineN = range(1, 8)         # nombre d’unités/machines (idem machines ici)
subcontractors = range(1, 5)   # 4 sous-traitants (exemple)
operations = range(1, 4) # 12 opérations

# Générer demande
demande = generer_demande(data["params"], periods)

# Extraire paramètres
products = data['products']
machines = data['machines']
periods = data['periods']
cells = data['cells']
machineN = data['machineN']
subcontractors = data['subcontractors']

MC = data['MC']  # capacités machines
set_cost = data['set_cost']
big_m = data['big_m']
hold_cost = data['hold_cost']
intr_cost = data['intr_cost']
inter_cost = data['inter_cost']
sub_capacity = data['sub_capacity']
pdef = data['pdef']  # liste de listes (produit, périodes)
tlot = data['tlot']
sal_cost = data['sal_cost']
mcost = data['mcost']
sub_cost = data['sub_cost']
CL = data['CL']
LP = data['LP']

mcim = data['mcim']  # matrice 4x3

# Fonction pour accéder à mcim : mcim[produit_index][machine_index]
def mcim_val(p, m):
    return mcim[p-1][m-1]  # indices décalés

# Modèle
model = Model("Production")

#  Variables
x = model.continuous_var_dict(((o, p, m, f, c, t)
                               for o in operations for p in products
                               for m in machines for f in machineN
                               for c in cells for t in periods), name='x')

Z = model.binary_var_dict(((o, p, m, f, c, t)
                           for o in operations for p in products
                           for m in machines for f in machineN
                           for c in cells for t in periods), name='Z')

B = model.continuous_var_dict(((p, t) for p in products for t in periods), name='B')
Y = model.continuous_var_dict(((p, l, t) for p in products for l in subcontractors for t in periods), name='Y')
NAJ = model.integer_var_dict(((m, c, t) for m in machines for c in cells for t in periods), name='NAJ')
NRE = model.integer_var_dict(((m, c, t) for m in machines for c in cells for t in periods), name='NRE')
MN = model.integer_var_dict(((m, c, t) for m in machines for c in cells for t in periods), name='MN')

# Coût d'opération arbitraire
operation_cost = {(p, m, o): 5 for p in products for m in machines for o in operations}

# 🎯 Fonction objectif
Q1 = model.sum(set_cost[m-1] / tlot[p-1] * x[o, p, m, f, c, t]
    for o in operations for p in products for m in machines
    for f in machineN for c in cells for t in periods)

Q2 = model.sum(operation_cost[p, m, o] * x[o, p, m, f, c, t]
    for o in operations for p in products for m in machines
    for f in machineN for c in cells for t in periods)

Q3 = model.sum((mcost[m-1] * NAJ[m, c, t]) - (sal_cost[m-1] * NRE[m, c, t])
    for m in machines for c in cells for t in periods)

Q4 = model.sum(B[p, t] * hold_cost[p-1] for p in products for t in periods)
Q5 = model.sum(Y[p, l, t] * sub_cost[l-1] for p in products for l in subcontractors for t in periods)

Q6 = model.sum(
    intr_cost[p-1] * x[o, p, m, f, c, t]
    for c in cells for t in periods for m in machines for f in machineN
    for p in products for o in operations if o < 3)

Q7 = model.sum(
    inter_cost[p-1] * x[o, p, m, f, c, t]
    for c in cells for t in periods for m in machines for f in machineN
    for p in products for o in operations if o < 3)

model.minimize(Q1 + Q2 + Q3 + Q4 + Q5 + Q6 + Q7)


# Contraintes

for p in products:
    for t in periods:
        denom = sum(mcim_val(p, m) for m in machines)
        model.add_constraint(
            model.sum(x[o, p, m, f, c, t]
                      for o in operations for m in machines
                      for f in machineN for c in cells) / denom
            + model.sum(Y[p, l, t] for l in subcontractors)
            + B[p, t] >= demande[(p, t)]
        )


for m in machines:
    for f in machineN:
        for c in cells:
            for t in periods:
                model.add_constraint(
                    model.sum(x[o, p, m, f, c, t]
                              for o in operations for p in products) <= MC[m-1]
                )


for o in operations:
    for p in products:
        for m in machines:
            for f in machineN:
                for c in cells:
                    for t in periods:
                        model.add_constraint(x[o, p, m, f, c, t] <= tlot[p-1])
                        model.add_constraint(x[o, p, m, f, c, t] <= Z[o, p, m, f, c, t] * big_m)



# Sous-traitance
for l in subcontractors:
    for t in periods:
        model.add_constraint(
    model.sum(Y[p, l, t] for p in products) <= sub_capacity[l-1]
)


#Backlog
for p in products:
    for t in periods:
        model.add_constraint(B[p, t] <= pdef[p-1][t-1])

INT = {m: 0 for m in machines}  # initialisation par défaut, à adapter si tu as une vraie donnée

for m in machines:
    for c in cells:
        for t in periods:
            model.add_constraint(MN[m, c, t] == NAJ[m, c, t] - NRE[m, c, t] + INT[m])


# Capacité cellulaire
for c in cells:
    for t in periods:
        model.add_constraint(model.sum(MN[m, c, t] for m in machines) >= LP)
        model.add_constraint(model.sum(MN[m, c, t] for m in machines) <= CL)

# Résolution avec mesure du temps
start_time = time.time()
solution = model.solve()
end_time = time.time()
elapsed_time = end_time - start_time

# Résultats
if solution:
    print("✅ Solution trouvée")
    print("Statut:", model.solve_details.status)
    print(f"Fonction objectif = {model.objective_value}")
    print(f"Temps d'exécution : {end_time - start_time:.4f} secondes\n")

    for name, var_dict in [("B", B), ("X", x), ("Z", Z), ("Y", Y), ("NAJ", NAJ), ("NRE", NRE)]:
        print(f"Variables {name}:")
        found = False
        for k, var in var_dict.items():
            val = var.solution_value
            if val is not None and val > 1e-5:
                print(f"  {name}{k} = {val}")
                found = True
        if not found:
            print(f"  Aucune valeur significative non nulle pour {name}.")
else:
    print("❌ Aucune solution trouvée.")

