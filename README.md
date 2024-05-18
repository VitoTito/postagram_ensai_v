README --- Général --- (2024-05-19) 

# INFORMATIONS GÉNÉRALES

## Fonctionnement

Dans un premier temps, se placer dans le dossier `terraform/`, puis :

```bash
pipenv sync
pipenv shell
```

Ensuite :

```bash
cdktf deploy
```

Récupérer les id correspondant au bucket et à DynamoDB, puis les coller dans le fichier `main_server.py` au début du fichier respectivement
dans les variables `your_bucket` et `your_dynamo_table`. Les insérer également dans le fichier `.env` dans le dossier `webservice/`

Ensuite, changer dans le `cdktf.json` le `main_serverless.py` en `main_server.py`, puis :

```bash
cdktf deploy
```

Récupérer une nouvelle fois l'adresse du LB (Load Balancer), et l'insérer dans le fichier `index.js` dans `webapp/src/` (ligne 12 : `axios.defaults.baseURL`)

Enfin, lancer l'interface en se plaçant dans le dossier `webapp/`, puis :

```bash
npm install
npm start
```

Se connecter ensuite. Il est notamment possible de créer une publication, de voir l'ensemble des publications de tous les utilisateurs, de poster une image.

