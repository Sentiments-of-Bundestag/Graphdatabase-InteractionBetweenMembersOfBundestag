# Graphdatabase-InteractionBetweenMembersOfBundestag
This project is about data of the "Deutscher Bundestag". This repository demonstrates an approach to transform data from mongodb to neo4j.

Collaborators:
 - Rico Stucke [rico-stucke](https://github.com/rico-stucke)
 - Florian Thom [FlorianTh2](https://github.com/FlorianTh2)
 - Jennifer Vormann [FrauMauz](https://github.com/fraumauz)

## Learned
- graphdatabas
- graphdatabase schema
- neo4j
- neomodel
- mongodb
- pymongo

## Prerequisites
The prerequisites are defined below. Here is assumed you have a running mongodb and a running neo4j-db. The given skript has the following requirements (requirements for pip)
- python3
- pip
- Flask
- alive-progress
- neomodel
- pymongo

## Getting Started
- How to start the neo4j-database?
```
sudo docker run \
    --name testneo4j \
    -d \
    --publish=7474:7474 --publish=7687:7687 \
    --env NEO4J_AUTH=neo4j/<your-password> \
    neo4j:latest
# userId: neo4j
# pw: <your-password>
# name of graphdatabase: neo4j - default
# url: neo4j://<your-server-ip>
```

- Trigger refetching and rebuild of the database with possible new data of the mongodb
```
HTTP-GET: <your-server-ip>:5000/api/v1/notify
```

- Start flask-server
```
pip install -r requirements.txt
export FLASK_APP=./remoteNeo4j/neo4jCreator.py
python3 -m flask run -h 0.0.0.0
HTTP:GET (e.g. via web-browser): http://<your-server-ip>:5000/api/v1/notify
```

## Additional informations
- After you started the skript, you just started the flask-server but not the actual neo4j-skript -> if you want to start the neo4j-skript, you have to HTTP-GET (e.g. just open the proper url in your web-browser), since its executed with each HTTP-GET at the proper route (described above)
- runs much faster if neo4j-db and flask-server (which runs the actual skript) are on the same host
  - on same host: around 30min (for around 250k comments between persons)
  - on different hosts: around 10h (for around 250k comments between persons)
- runtime: around 25min (neo4j-db and flask-server on same host)

## Build with
- Flask
- alive-progress
- neomodel
- pymongo