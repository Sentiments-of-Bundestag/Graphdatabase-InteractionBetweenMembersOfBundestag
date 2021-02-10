#!/usr/bin/env python
# coding: utf-8

# In[ ]:
import pymongo
from pymongo import MongoClient
pymongo.version

import pprint
import collections

from neomodel import *
from neomodel import db
from alive_progress import alive_bar

from alive_progress import alive_bar
from itertools import islice

from flask import Flask

class Person(StructuredNode):
    speakerId = StringProperty()
    name = StringProperty()
    role = StringProperty()
    faction = Relationship('Faction', 'MEMBER')
    madeComment = RelationshipTo('Commentary', 'SENDER')
    recievedComment = RelationshipFrom('Commentary', 'RECEIVER')

class ParliamentSession(StructuredNode):
    sessionId = IntegerProperty()
    startDateTime = StringProperty()
    endDateTime = StringProperty()
    legislative_period = IntegerProperty()

class Faction(StructuredNode):
    factionId = StringProperty()
    name = StringProperty()
    madeComment = RelationshipTo('Commentary', 'FROMFACTION')
    recievedComment = RelationshipFrom('Commentary', 'TOFACTION')

class Commentary(StructuredNode):
    sentiment = FloatProperty()
    applause = BooleanProperty() 
    message = StringProperty()
    dateString = StringProperty()
    sender = RelationshipFrom('Person', 'SENDER')
    receiver = RelationshipTo('Person', 'RECEIVER')
    receiverFaction = RelationshipTo('Faction', 'TOFACTION')
    senderFaction = RelationshipFrom('Faction', 'FROMFACTION')
    session = Relationship('ParliamentSession', 'SESSION')

def find_relevant_title(text) -> title:
    if 'a. D.' in text and 'Bundesminster' in text:
        return 'Bundesminster a. D.'
    if 'Bundesminster' in text:
        return 'Bundesminster'
    if 'Vizepräsident' in text:
        return 'Vizepräsident'
    if 'Bundeskanzler' in text:
        return 'Bundeskanzler'
    if 'Bundestagspräsident' in text:
        return 'Bundestagspräsident'
    if 'Bundespräsident' in text:
        return 'Bundespräsident'


def test_function():
    print("Started build up of neo4j")
    db_name_mongo = "sentiment"
    mongo_url = "mongodb://readonly:r34d0nly!@141.45.146.163:27017"
    mongo = MongoClient(mongo_url)
    databaseMongo = mongo.sentiment

    collection_names = databaseMongo.list_collection_names()

    unique_persons = {}
    unique_factions = {}
    unique_sessions = {}
    unique_interactions = []

    for i in collection_names:
        queryResult = databaseMongo.get_collection(i).find_one()

        """
        'speakers' : {'faction', 'first_name', 'last_name', job_title}
        'person' : {'speakerId', 'name', 'role'}
        """

        neo4j_persons = []

        for keyString in queryResult['speakers']:
            speaker = queryResult['speakers'][keyString]
            role = ''

            if 'job_title' in speaker:
                role = find_relevant_title(speaker['job_title'])

            neo4j_persons.append({'speakerId' : keyString, 'name' : (speaker['forename'] + ' ' + speaker['surname']).strip(), 'role' : role, 'factionId': queryResult['speakers'][keyString]['memberships'][-1][2]})

        #loop um doppelte Namen zu entfernen
        sorted_persons = collections.OrderedDict()
        for obj in neo4j_persons:
            if obj['speakerId'] not in sorted_persons:
                sorted_persons[obj['speakerId']] = obj

        for key in sorted_persons:
            if key not in unique_persons:
                unique_persons[key] = sorted_persons[key]

        faction_dictionary = queryResult['factions']
        faction_list = []
        for keyString in faction_dictionary:
            faction = faction_dictionary[keyString]
            faction_list.append({'id' : keyString, 'name' : faction})

        for faction in faction_list:
            if faction['id'] not in unique_factions:
                unique_factions[faction['id']] = faction

        parliamentSession = {'session_id' : queryResult['session_no'], 'startDateTime' : queryResult['start'], 'endDateTime' : queryResult['end'],
              'legislative_period' : queryResult['legislative_period']}

        unique_sessions[parliamentSession['session_id']] = parliamentSession

        interaction_list = queryResult['interactions']

        for interaction in interaction_list:
            if interaction['sender'].startswith('F') and interaction['receiver'].startswith('F'):
                inter = interaction
            else:
                interaction['dateString'] = parliamentSession['startDateTime']
                interaction['psessionId'] = parliamentSession['session_id']
                unique_interactions.append(interaction)

    mongo.close()

    ### neomodel class setup


    config.DATABASE_URL = 'bolt://neo4j:super-super-secret-password@141.45.146.164:7687'

    ### neo4j inserts



    clear_neo4j_database(db)

    all_comments = []
    all_persons = {}
    all_factions = {}
    all_psession = {}

    print('Creating Faction nodes')
    
    noFaction = None

    with alive_bar(len(unique_factions)) as bar:
        for factionKey in unique_factions:
            with db.transaction:
                factionDBO = Faction(factionId = unique_factions[factionKey]['id'], name = unique_factions[factionKey]['name']).save()
                factionDBO.refresh()
                all_factions[factionDBO.factionId] = factionDBO

                if factionDBO.name == 'Fraktionslos':
                    noFaction = factionDBO
            bar()

    print('Creating Person nodes')

    with db.transaction:
        with alive_bar(len(unique_persons)) as bar:
            for personKey in unique_persons:

                personDBO = Person(speakerId = unique_persons[personKey]['speakerId'], name = unique_persons[personKey]['name'], role = unique_persons[personKey]['role']).save()
                personDBO.refresh()

                if all_factions.get(unique_persons[personKey]['factionId'], None) is not None:
                    relation = personDBO.faction.connect(all_factions[unique_persons[personKey]['factionId']]) #relationship person to faction
                else:
                    relation = personDBO.faction.connect(noFaction)
                all_persons[personDBO.speakerId] = personDBO
                bar()

    print('Creating parliament session nodes')

    with alive_bar(len(unique_sessions)) as bar:
        for psessionKey in unique_sessions:
            with db.transaction:
                psessionDBO = ParliamentSession(sessionId = unique_sessions[psessionKey]['session_id'], startDateTime = unique_sessions[psessionKey]['startDateTime'], endDateTime = unique_sessions[psessionKey]['endDateTime'],      legislative_period = unique_sessions[psessionKey]['legislative_period']).save()
                psessionDBO.refresh()
                all_psession[psessionDBO.sessionId] = psessionDBO
            bar()

    print('Creating interaction nodes')

    with alive_bar(len(unique_interactions)) as bar:
        for interaction in unique_interactions:
            with db.transaction:

                if 'polarity' in interaction:
                    polarity = interaction['polarity']
                else:
                    polarity = 0.0

                if 'applause' in interaction:
                    applause = interaction['applause']
                else:
                    applause = False

                commentDBO = Commentary(sentiment = polarity, message = interaction['message'], dateString = interaction['dateString'], applause = applause).save()
                relation = commentDBO.session.connect(all_psession[interaction['psessionId']])
                all_comments.append(commentDBO)

                #relationship faction to comment
                if interaction['sender'].startswith('F'):
                    relation = all_factions[interaction['sender']].madeComment.connect(commentDBO)
                #relationship person to comment
                else:
                    relation = all_persons[interaction['sender']].madeComment.connect(commentDBO)    

                #relationship comment to faction        
                if interaction['receiver'].startswith('F'):
                    relation = commentDBO.receiverFaction.connect(all_factions[interaction['receiver']])
                #relationship comment to person
                else:
                    relation = commentDBO.receiver.connect(all_persons[interaction['receiver']])
            bar()

# test_function()
app = Flask(__name__)
@app.route('/api/v1/notify')
def notify_get():
    return test_function()

