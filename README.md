Pour l’optimisation du modèle MILT (Mixed Integer Linear Programming), nous avons utilisé IBM CPLEX. Dans un premier temps, nous avons installé CPLEX_Studio_Community2211 sur
un ordinateur équipé de Windows 10 avec un processeur Intel Core i5.

Ensuite, nous avons créé un environnement Python en version 3.10, dans lequel nous avons installé les bibliothèques nécessaires, notamment :

python
 
- import numpy as np  
- from docplex.mp.model import Model
- 
Un fichier JSON a été créé afin de séparer les données du programme. Deux fichiers de données ont été utilisés :

datay.json associé au programme principal Cplex_SCKONAN.py, et

data.json utilisé pour un programme de test SupplyChainYAO.py permettant de valider que le modèle fonctionne effectivement avec CPLEX.

Les fichiers Cplex_SCKONAN.py et supply_chain_model.py contiennent l’implémentation complète du modèle de planification de la chaîne logistique.
Cependant, nous avons rencontré une limitation importante liée à l’édition communautaire de CPLEX : celle-ci restreint la taille du problème à 1000 variables et 1000 contraintes. Or, notre modèle dépasse largement ces limites, ce qui empêche son exécution complète dans cette version gratuite de CPLEX.
