# -*- coding: utf-8 -*-
"""
Created on Wed Jul 30 10:58:22 2025

@author: yadri_000
"""

import os
import json
import time
from docplex.mp.model import Model

#  Chargement des données depuis le fichier JSON
with open('data.json') as f:
    data = json.load(f)

# ✅ Conversion des clés chaînes "(1, 1)" en tuples (1, 1)
def convert_keys(d):
    return {eval(k): v for k, v in d.items()}

#  Paramètres
products = data['products']
machines = data['machines']
periods = data['periods']
cells = data['cells']
operations = data['operations']
machineN = data['machineN']
subcontractors = data['subcontractors']

demand = convert_keys(data['demand'])
machine_capacity = {int(k): v for k, v in data['machine_capacity'].items()}
setup_cost = {int(k): v for k, v in data['setup_cost'].items()}
Tlot = {int(k): v for k, v in data['Tlot'].items()}
BigM = data['BigM']
HoldCost = {int(k): v for k, v in data['HoldCost'].items()}
SubCapacity = {int(k): v for k, v in data['SubCapacity'].items()}
Pdef = convert_keys(data['Pdef'])
Mcost = {int(k): v for k, v in data['Mcost'].items()}
SalCost = {int(k): v for k, v in data['SalCost'].items()}
IntrCost = {int(k): v for k, v in data['IntrCost'].items()}
InterCost = {int(k): v for k, v in data['InterCost'].items()}
INT = {int(k): v for k, v in data['INT'].items()}
CL = data['CL']
LP = data['LP']
MCIM = convert_keys(data['MCIM'])

# Création du modèle
model = Model(name='ProductionModel')

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
Q1 = model.sum(setup_cost[m] / Tlot[p] * x[o, p, m, f, c, t]
    for o in operations for p in products for m in machines
    for f in machineN for c in cells for t in periods)

Q2 = model.sum(operation_cost[p, m, o] * x[o, p, m, f, c, t]
    for o in operations for p in products for m in machines
    for f in machineN for c in cells for t in periods)

Q3 = model.sum((Mcost[m] * NAJ[m, c, t]) - (SalCost[m] * NRE[m, c, t])
    for m in machines for c in cells for t in periods)

Q4 = model.sum(B[p, t] * HoldCost[p] for p in products for t in periods)
Q5 = model.sum(Y[p, l, t] * SubCapacity[l] for p in products for l in subcontractors for t in periods)

Q6 = model.sum(
    IntrCost[p] * x[o, p, m, f, c, t] for c in cells for t in periods for m in machines for f in machineN for p in
    products for o in operations if o < 3)

Q7 = model.sum(
    InterCost[p] * x[o, p, m, f, c, t] for c in cells for t in periods for m in machines for f in machineN for p in
    products for o in operations if o < 3)

model.minimize(Q1 + Q2 + Q3 + Q4 + Q5 + Q6 + Q7)

# Contraintes

# Demande
for p in products:
    for t in periods:
        denom = sum(MCIM.get((p, m), 0) for m in machines)
        model.add_constraint(
            model.sum(x[o, p, m, f, c, t]
                      for o in operations for m in machines
                      for f in machineN for c in cells) / denom
            + model.sum(Y[p, l, t] for l in subcontractors)
            + B[p, t] >= demand[p, t]
        )

# Capacité machine
for m in machines:
    for f in machineN:
        for c in cells:
            for t in periods:
                model.add_constraint(
                    model.sum(x[o, p, m, f, c, t]
                              for o in operations for p in products) <= machine_capacity[m]
                )

# BigM & Tlot
for o in operations:
    for p in products:
        for m in machines:
            for f in machineN:
                for c in cells:
                    for t in periods:
                        model.add_constraint(x[o, p, m, f, c, t] <= Tlot[p])
                        model.add_constraint(x[o, p, m, f, c, t] <= Z[o, p, m, f, c, t] * BigM)

# Sous-traitance
for l in subcontractors:
    for t in periods:
        model.add_constraint(
            model.sum(Y[p, l, t] for p in products) <= SubCapacity[l]
        )

#Backlog
for p in products:
    for t in periods:
        model.add_constraint(B[p, t] <= Pdef[p, t])

# Machines installées
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

# 📤 Résultats
if solution:
    print("✅ Solution trouvée")
    print("Statut:", model.solve_details.status)
    print(f"Fonction objectif = {model.objective_value}")
    print(f"Temps d'exécution : {elapsed_time:.4f} secondes")
    print(f"Nombre d'itérations : {model.get_solve_details().nb_iterations}")
    print()

    for name, var_dict in [("B", B), ("X", x), ("Z", Z), ("Y", Y), ("NAJ", NAJ), ("NRE", NRE)]:
        print(f"\nVariables {name} :")
        found = False
        for k, var in var_dict.items():
            val = var.solution_value
            if val is not None and val > 1e-5:
                print(f"{name}[{k}] = {val}")
                found = True
        if not found:
            print(f"Aucune valeur significative non nulle pour {name}.")
else:
    print("❌ Aucune solution trouvée.")

# Statistiques
print("Statistiques du modèle :")
print(f"Variables totales : {model.number_of_variables}")
print(f"Contraintes totales : {model.number_of_constraints}")
