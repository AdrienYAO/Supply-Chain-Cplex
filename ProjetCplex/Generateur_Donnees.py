# -*- coding: utf-8 -*-
import json
import os
import numpy as np
import traceback


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
output_dat = os.path.join(BASE_DIR, "DataFinal.dat")
output_json = os.path.join(BASE_DIR, "DataFinal.json")

try:

   # --- PARAMÈTRES DE DEMANDE ---
    params = {
        'P1': {'moyenne': 80, 'ecart_type': 10},
        'P2': {'moyenne': 50, 'ecart_type': 7},
        'P3': {'moyenne': 85, 'ecart_type': 15},
        'P4': {'moyenne': 190, 'ecart_type': 3},
    }

    # Autres paramètres fixes
    INT = [5, 7, 4]
    MC = [100, 150, 75]
    SetCost = [100, 140, 200]
    MCIM = [
        [1, 1, 1],
        [0, 0, 1],
        [0, 1, 1],
        [1, 0, 0]
    ]
    OP = [
        [7, 7, 7],
        [12, 12, 12],
        [4, 4, 4],
        [0, 0, 0],
        [0, 0, 0],
        [5, 5, 5],
        [0, 0, 0],
        [9, 9, 9],
        [4.6, 4.6, 4.6],
        [8, 8, 8],
        [0, 0, 0],
        [0, 0, 0]
    ]
    Pdef = [
        [20, 0],
        [30, 0],
        [45, 0],
        [60, 0]
    ]
    IntrCost = [3, 5, 4, 7]
    InterCost = [2, 6, 4, 6]
    HoldCost = [4, 3.5, 3, 2.4]
    Tlot = [15, 10, 8, 15]
    SalCost = [6800, 10200, 6000]
    Mcost = [8000, 12000, 7500]
    SubCost = [50, 14, 20, 18]
    SubCapacity = [100, 50, 60, 120]
    BigM = 10000000
    LP = 0
    CL = 30

    # --- FONCTIONS D'ÉCRITURE ---
    def write_matrix_dat(name, matrix, f, end_semicolon=True):
        f.write(f"{name} = \n")
        for row in matrix:
            f.write(" ".join(map(str, row)) + "\n")
        if end_semicolon:
            f.write(";\n\n")
        else:
            f.write("\n\n")

    def write_list_dat(name, values, f, end_semicolon=True):
        line = f"{name} = " + " ".join(map(str, values))
        if end_semicolon:
            line += ";"
        f.write(line + "\n\n")

    # --- GÉNÉRATION DES DEMANDES ALÉATOIRES ---
    def generer_demande(periods=2):
        Dem = []
        for p in params.keys():
            Dem.append([max(0, int(np.random.normal(params[p]['moyenne'], params[p]['ecart_type'])))
                        for _ in range(periods)])
        return Dem

    # Générer Dem une seule fois
    Dem = generer_demande(periods=2)

    # --- GÉNÉRATION DU FICHIER .DAT ---
    with open(output_dat, "w") as f:
        write_matrix_dat("Dem", Dem, f)
        write_list_dat("INT", INT, f)
        write_list_dat("MC", MC, f)
        write_list_dat("SetCost", SetCost, f)
        write_matrix_dat("MCIM", MCIM, f)
        write_matrix_dat("OP", OP, f)
        write_matrix_dat("Pdef", Pdef, f)
        write_list_dat("IntrCost", IntrCost, f)
        write_list_dat("InterCost", InterCost, f)
        write_list_dat("HoldCost", HoldCost, f)
        write_list_dat("Tlot", Tlot, f)
        write_list_dat("SalCost", SalCost, f)
        write_list_dat("Mcost", Mcost, f)
        write_list_dat("SubCost", SubCost, f)
        write_list_dat("SubCapacity", SubCapacity, f)
        write_list_dat("BigM", [BigM], f)
        write_list_dat("LP", [LP], f)
        write_list_dat("CL", [CL], f, end_semicolon=False)

    print(f"[OK] Fichier .dat généré : {output_dat}")

    # --- GÉNÉRATION DU FICHIER JSON ---
    data_json = {
        "products": [1, 2, 3, 4],
        "machines": [1, 2, 3],
        "periods": [1, 2],
        "cells": [1, 2],
        "operations": OP,
        "machineN": [1, 2, 3, 4, 5, 6, 7],
        "subcontractors": [1, 2, 3, 4],
        "params": {k: {"moyenne": Dem[i], "ecart_type": params[k]["ecart_type"]}
                   for i, k in enumerate(params)},
        "MC": MC,
        "set_cost": SetCost,
        "big_m": BigM,
        "hold_cost": HoldCost,
        "intr_cost": IntrCost,
        "inter_cost": InterCost,
        "sub_capacity": SubCapacity,
        "pdef": Pdef,
        "tlot": Tlot,
        "sal_cost": SalCost,
        "mcost": Mcost,
        "sub_cost": SubCost,
        "CL": CL,
        "LP": LP,
        "INT": INT,
        "mcim": MCIM
    }

    with open(output_json, "w") as f_json:
        json.dump(data_json, f_json, indent=4)

    print(f"[OK] Fichier JSON généré avec succès : {output_json}")

except Exception as e:
    print(f"[ERREUR] Générateur de données a échoué : {e}")
    traceback.print_exc()

