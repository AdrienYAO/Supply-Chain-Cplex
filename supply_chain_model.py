import os

# 👉 Remplace bien ce chemin si tu as installé ailleurs
os.environ['CPLEX_STUDIO_DIR2211'] = r"C:\Program Files\IBM\ILOG\CPLEX_Studio_Community2211"


from docplex.mp.model import Model


# from docplex.mp.data import DataReader

# Créer un modèle
model = Model(name='supply_chain_model')

# Lire le fichier de données
# data_file = r'C:\Users\yadri_000\Desktop\These\supply_chain\CMS\These_final\code_2023\CPLEX\ModeleProduction\DataFinal.dat'
# data_reader = DataReader(model)
# data_reader.read(data_file)

# Définir les ensembles
products = [1, 2, 3, 4]
machines = [1, 2, 3]
periods = [1, 2]
machineN = list(range(1, 8))
cells = [1, 2]
operations = [1, 2, 3]
subcontractors = [1, 2, 3, 4]

# Déclaration des paramètres
demand = {(1, 1): 80, (1, 2): 107,
          (2, 1): 59, (2, 2): 44,
          (3, 1): 73, (3, 2): 98,
          (4, 1): 186, (4, 2): 184}

machine_capacity = {1: 100, 2: 150, 3: 75}  # Capacités des machines
setup_cost = {1: 100, 2: 140, 3: 200}  # Coûts d'installation
operation_cost = {(p, m, o): 0 for p in products for m in machines for o in operations}  # À définir si nécessaire
Tlot = {1: 15, 2: 10, 3: 8, 4: 15}  # Lots de production
BigM = 10000000  # Valeur de BigM
SubCapacity = {1: 100, 2: 50, 3: 60, 4: 120}  # Capacités des sous-traitants
Pdef = {(1, 1): 20, (1, 2): 0,
        (2, 1): 30, (2, 2): 0,
        (3, 1): 45, (3, 2): 0,
        (4, 1): 60, (4, 2): 0}

SetCost = {1: 6800, 2: 10200, 3: 6000}  # Coûts de mise en place 
HoldCost = {1: 4, 2: 3.5, 3: 3, 4: 2.4}  # Coûts de maintien
Mcost = {1: 8000, 2: 12000, 3: 7500}  # Coûts d'achats des machines
SalCost = {1: 6800, 2: 10200, 3: 6000}  # Coûts de vente machines
IntrCost = {1: 3, 2: 5, 3: 4, 4: 7}  # Coûts des mouvements  interne des cellules
InterCost = {1: 2, 2: 6, 3: 4, 4: 6}  # Coûts des mouvements externe des cellules
INT = {1: 5, 2: 7, 3: 4}
# Définir les limites
CL = 30  # Capacité maximale
LP = 10  # Production minimale

# Paramètres MCIM et OP
MCIM = {
    (1, 1): 1, (1, 2): 1, (1, 3): 1,
    (2, 1): 0, (2, 2): 0, (2, 3): 1,
    (3, 1): 0, (3, 2): 1, (3, 3): 1,
    (4, 1): 1, (4, 2): 0, (4, 3): 0
}

OP = {
    (1, 1): 7, (1, 2): 7, (1, 3): 7,
    (2, 1): 12, (2, 2): 12, (2, 3): 12,
    (3, 1): 4, (3, 2): 4, (3, 3): 4,
    (4, 1): 0, (4, 2): 0, (4, 3): 0,
    (5, 1): 0, (5, 2): 0, (5, 3): 0,
    (6, 1): 5, (6, 2): 5, (6, 3): 5,
    (7, 1): 0, (7, 2): 0, (7, 3): 0,
    (8, 1): 9, (8, 2): 9, (8, 3): 9,
    (9, 1): 4.6, (9, 2): 4.6, (9, 3): 4.6,
    (10, 1): 8, (10, 2): 8, (10, 3): 8
}

# Déclaration des variables de décision
B = model.continuous_var_dict(((p, t) for p in products for t in periods), name='B')  # Produits reportés
Y = model.continuous_var_dict(((p, l, t) for p in products for l in subcontractors for t in periods),
                              name='Y')  # Sous-traitance
NAJ = model.integer_var_dict(((m, c, t) for m in machines for c in cells for t in periods),
                             name='NAJ')  # Machine ajoutée
NRE = model.integer_var_dict(((m, c, t) for m in machines for c in cells for t in periods),
                             name='NRE')  # Machine retirée
x = model.continuous_var_dict(
    ((o, p, m, f, c, t) for o in operations for p in products for m in machines for f in machineN for c in cells for t
     in periods), name='x')
Z = model.continuous_var_dict(
    ((o, p, m, f, c, t) for o in operations for p in products for m in machines for f in machineN for c in cells for t
     in periods), name='Z')
MN = model.integer_var_dict(((m, c, t) for m in machines for c in cells for t in periods),
                            name='MN')  # Machine existante

# Fonction objectif : Minimiser les coûts
Q1 = model.sum(setup_cost[m] / Tlot[p] * x[o, p, m, f, c, t]
               for c in cells for t in periods for m in machines for f in machineN for p in products for o in
               operations)

Q2 = model.sum(operation_cost[p, m, o] * x[o, p, m, f, c, t]
               for c in cells for t in periods for m in machines for f in machineN for p in products for o in
               operations)

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

for t in periods[1:]:  # Pour t >= 2
    for p in products:
        denom = sum(MCIM[p, m] for m in machines)  # pré-calculé une fois

        model.add_constraint(
            model.sum(
                x.get((o, p, m, f, c, t), 0)
                for o in operations
                for m in machines
                for f in machineN
                for c in cells
            ) / denom
            + model.sum(Y[p, l, t] for l in subcontractors)
            + B[p, t] - B[p, 1]
            >= demand[p, t],
            f"DemandConstraint_t{t}_p{p}"
        )


# Contrainte de demande pour les périodes t >= 2
for t in periods[1:]:
    for p in products:
        denom = sum(MCIM[p, m] for m in machines)  # Précalcule une constante

        if denom == 0:
            raise ValueError(f"MCIM denominator is zero for product {p}")

        model.add_constraint(
            model.sum(
                x[o, p, m, f, c, t]
                for o in operations
                for m in machines
                for f in machineN
                for c in cells
            ) / denom
            + model.sum(Y[p, l, t] for l in subcontractors)
            + B[p, t] - B[p, 1]
            >= demand[p, t],
            f"DemandConstraint_t{t}_p{p}"
        )


# Contraintes de capacités des machines
for m in machines:
    for f in machineN:
        for c in cells:
            for t in periods:
                model.add_constraint(
                    model.sum(x[o, p, m, f, c, t] for p in products for o in operations) <= machine_capacity[m],
                    f"MachineCapacityConstraint_m{m}_f{f}_c{c}_t{t}"
                )

# Contraintes sur les quantités produites
for o in operations:
    for p in products:
        for m in machines:
            for f in machineN:
                for c in cells:
                    for t in periods:
                        model.add_constraint(
                            x[o, p, m, f, c, t] <= Tlot[p],
                            f"TlotConstraint_o{o}_p{p}_m{m}_f{f}_c{c}_t{t}"
                        )

                        model.add_constraint(
                            x[o, p, m, f, c, t] <= Z[o, p, m, f, c, t] * BigM,
                            f"BigMConstraint_o{o}_p{p}_m{m}_f{f}_c{c}_t{t}"
                        )

# Capacités des sous-traitants
for l in subcontractors:
    for t in periods:
        model.add_constraint(
            model.sum(Y[p, l, t] for p in products) <= SubCapacity[l],
            f"SubcontractorCapacityConstraint_l{l}_t{t}"
        )

# Contraintes sur les produits reportés
for p in products:
    for t in periods:
        model.add_constraint(
            B[p, t] <= Pdef[p, t],
            f"BacklogConstraint_p{p}_t{t}"
        )

# Contraintes sur les machines
for o in operations:
    for p in products:
        for f in machineN:
            for c in cells:
                for t in periods:
                    model.add_constraint(
                        model.sum(x[o, p, m, f, c, t] for m in machines) <= NAJ[m, c, t] * BigM,
                        f"MachineUsageConstraint_o{o}_p{p}_f{f}_c{c}_t{t}"
                    )
# Contrainte sur l'utilisation de x
for o in operations:
    for p in products:
        for m in machines:
            for c in cells:
                for t in periods:
                    model.add_constraint(
                        model.sum(
                            x[o, p, m, f, c, t] for f in machineN if f >= 5
                        ) == 0, ctname=f"constraint_x_{o}_{p}_{m}_{c}_{t}_f_ge_5"
                    )

                for t in periods:
                    model.add_constraint(
                        model.sum(
                            x[o, p, m, f, c, t] for f in machineN if f >= 7
                        ) == 0, ctname=f"constraint_x_{o}_{p}_{m}_{c}_{t}_f_ge_7"
                    )

                for t in periods:
                    model.add_constraint(
                        model.sum(
                            x[o, p, m, f, c, t] for f in machineN if f >= 4
                        ) == 0, ctname=f"constraint_x_{o}_{p}_{m}_{c}_{t}_f_ge_4"
                    )

# Contrainte sur Z
for o in operations:
    for p in products:
        for m in machines:
            for c in cells:
                for t in periods:
                    model.add_constraint(
                        model.sum(
                            Z[o, p, m, f, c, t] for f in machineN if f >= 5
                        ) == 0, ctname=f"constraint_Z_{o}_{p}_{m}_{c}_{t}_f_ge_5"
                    )

                for t in periods:
                    model.add_constraint(
                        model.sum(
                            Z[o, p, m, f, c, t] for f in machineN if f >= 7
                        ) == 0, ctname=f"constraint_Z_{o}_{p}_{m}_{c}_{t}_f_ge_7"
                    )

                for t in periods:
                    model.add_constraint(
                        model.sum(
                            Z[o, p, m, f, c, t] for f in machineN if f >= 4
                        ) == 0, ctname=f"constraint_Z_{o}_{p}_{m}_{c}_{t}_f_ge_4"
                    )

# Contrainte sur les machines existantes
for c in cells:
    for m in machines:
        model.add_constraint(
            NAJ[m, c, 1] - NRE[m, c, 1] + INT[m] == MN[m, c, 1],
            ctname=f"machine_purchase_sale_constraint_{m}_{c}_1"
        )

# Pour les périodes t > 1
for m in machines:
    for c in cells:
        for t in periods[1:]:
            model.add_constraint(
                NAJ[m, c, t] - NRE[m, c, t] + MN[m, c, t - 1] == MN[m, c, t],
                ctname=f"machine_purchase_sale_constraint_{m}_{c}_{t}"
            )
# Contrainte sur la capacité minimum
for c in cells:
    for t in periods:
        model.add_constraint(
            LP <= model.sum(MN[m, c, t] for m in machines),
            ctname=f"cell_capacity_min_constraint_{c}_{t}"
        )

# Contrainte sur la capacité maximum
for c in cells:
    for t in periods:
        model.add_constraint(
            model.sum(MN[m, c, t] for m in machines) <= CL,
            ctname=f"cell_capacity_max_constraint_{c}_{t}"
        )
# Contrainte sur la capacité de production des machines
for m in machines:
    for t in periods:
        model.add_constraint(
            model.sum(
                model.sum(
                    model.sum(
                        model.sum(
                            x[o, p, m, f, c, t] for o in operations
                        ) for p in products
                    ) for f in machineN
                ) for c in cells
            ) <= machine_capacity[m] * model.sum(MN[m, c, t] for c in cells)
        )

# Résoudre le modèle
solution = model.solve()


# Afficher les résultats
if solution:
    # Utilisation de model.solve_details pour obtenir le statut de la solution
    solve_details = model.solve_details
    print("Status:", solve_details.status)

    for p in products:
        for t in periods:
            # Assurez-vous que B[p, t] est une variable de décision
            if (p, t) in B:
                print(f"Product {p}, Period {t}: {B[p, t].solution_value}")
            else:
                print(f"B[{p}, {t}] n'est pas défini dans le modèle.")
else:
    print("No solution found")
    
# Création d’un petit modèle test
model = Model(name='test_cplex')
x = model.continuous_var(name='x')
model.maximize(x)
solution = model.solve()

if solution:
    print("Solution trouvée :", solution.get_value(x))
else:
    print("Aucune solution trouvée")

