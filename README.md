Pour l’optimisation du modèle MILT (Mixed Integer Linear Programming), nous avons utilisé IBM CPLEX. Dans un premier temps, nous avons installé CPLEX_Studio_Community2211 sur
un ordinateur équipé de Windows 10 avec un processeur Intel Core i5.

Ensuite, nous avons créé un environnement Python en version 3.10, dans lequel nous avons installé les bibliothèques nécessaires, notamment :

python
 
- import numpy as np  
- from docplex.mp.model import Model

      2️⃣ Installation de CPLEX (solveur)
Option A : IBM ILOG CPLEX Optimization Studio

Télécharge ici : IBM CPLEX Optimization Studio

Crée un compte IBM gratuit si nécessaire.

Installe-le sur ton PC.

Par défaut sur Windows, le dossier est :

C:\Program Files\IBM\ILOG\CPLEX_StudioXXX


(où XXX est la version, ex. 22.1.1).

Vérifie que CPLEX est ajouté à la variable PATH :

Dans Windows :

Panneau de configuration → Système → Paramètres avancés → Variables d’environnement.

Ajoute :

C:\Program Files\IBM\ILOG\CPLEX_StudioXXX\cplex\bin\x64_win64
C:\Program Files\IBM\ILOG\CPLEX_StudioXXX\python


Redémarre ton terminal pour appliquer.

3️⃣ Installation de docplex
Option A : Avec pip
pip install docplex

Option B : Avec conda (si tu utilises Anaconda)
conda install -c conda-forge docplex

4️⃣ Vérification de l’installation

Teste dans Python (Spyder, Jupyter, ou console) :

from docplex.mp.model import Model

m = Model(name="test")
x = m.binary_var(name="x")
y = m.binary_var(name="y")
m.maximize(x + y)

sol = m.solve(log_output=True)
print(sol)


👉 Résultat attendu : CPLEX doit renvoyer une solution avec x=1, y=1.

5️⃣ Cas où CPLEX n’est pas trouvé

Si m.solve() renvoie None, cela veut dire que docplex est installé, mais CPLEX solveur n’est pas détecté.

Solutions :

Vérifie ton PATH (voir étape 2).

Sinon, utilise le solveur DOcplexcloud (cloud gratuit limité) :

from docplex.mp.model import Model

m = Model(name="demo")
x = m.integer_var(name="x")
y = m.integer_var(name="y")
m.maximize(2*x + 3*y)
m.add_constraint(x + y <= 10)

m.solve(url="https://api-oaas.docloud.ibmcloud.com/job_manager/rest/v1", 
        key="ta_clé_API")


⚠️ Pour ça, tu dois créer un compte IBM Cloud et obtenir une clé API.

6️⃣ Vérifier la version installée
pip show docplex

Un fichier JSON a été créé afin de séparer les données du programme. Deux fichiers de données ont été utilisés :

datay.json associé au programme principal Cplex_SCKONAN.py, et

data.json utilisé pour un programme de test SupplyChainYAO.py permettant de valider que le modèle fonctionne effectivement avec CPLEX.

Les fichiers Cplex_SCKONAN.py et supply_chain_model.py contiennent l’implémentation complète du modèle de planification de la chaîne logistique.
Cependant, nous avons rencontré une limitation importante liée à l’édition communautaire de CPLEX : celle-ci restreint la taille du problème à 1000 variables et 1000 contraintes. Or, notre modèle dépasse largement ces limites, ce qui empêche son exécution complète dans cette version gratuite de CPLEX.
