import sc2reader
from collections import defaultdict
from sc2reader.events import PlayerStatsEvent
import json
import math

### Storage unit class ###

class SC2Snapshot:

    def __init__(self, inLost, inVespeneCurrent, inMineralsCurrent, inVespeneCollectionRate, inMineralsCollectionRate, inWorkersActiveCount, inSupplyUsed, inSupplyTotal):
        self.lost = inLost
        self.vespeneCurrent = inVespeneCurrent
        self.mineralsCurrent = inMineralsCurrent
        self.vespeneCollectionRate = inVespeneCollectionRate
        self.mineralsCollectionRate = inMineralsCollectionRate
        self.workersActiveCount = inWorkersActiveCount
        self.supplyUsed = inSupplyUsed
        self.supplyTotal = inSupplyTotal

### From sc2plugins.py ###


def get_unit_type(unit):
    is_building = unit.is_building and 'Crawler' not in unit.name  # Crawlers are like units
    # Overseers,BroodLords,Ravagers and Lurkers morph but they are their own units
    if unit.name in ('Overseer', 'BroodLord', 'Ravager', 'Lurker') or is_building:
        unit_type = unit.name.lower()
    elif unit.name in ('Viking', 'VikingAssault'):
        unit_type = 'viking'
    elif unit.name in ('Hellion', 'BattleHellion'):
        unit_type = 'hellion'
    else:
        #print hex(unit.id), unit.name, "->", unit.type_history.values()[0].name.lower()
        if len(unit.type_history.values()) > 0:
            unit_type = unit.type_history.values()[0].name.lower()
        else:
            unit_type = None

    return unit_type


def get_plugin_army_map():


    # TODO: Once the sc2reader:new_data branch is finished we won't need this.
    # Include buildings for ownership tracking but don't include them in army tracking
    unit_data = {'WoL':
             {'Protoss': [
                 (False, 'probe', [50, 0, 1]),
                 (True, 'zealot', [100, 0, 2]),
                 (True, 'sentry', [50, 100, 2]),
                 (True, 'stalker', [125, 50, 2]),
                 (True, 'hightemplar', [50, 150, 2]),
                 (True, 'darktemplar', [125, 125, 2]),
                 (True, 'immortal', [250, 100, 4]),
                 (True, 'colossus', [300, 200, 6]),
                 # Can't know the cost, split the difference.
                 (True, 'archon', [175, 275, 4]),
                 (True, 'observer', [25, 75, 1]),
                 (True, 'warpprism', [200, 0, 2]),
                 (True, 'phoenix', [150, 100, 2]),
                 (True, 'voidray', [250, 150, 3]),
                 (True, 'carrier', [350, 250, 6]),
                 (True, 'mothership', [400, 400, 8]),
                 (True, 'photoncannon', [150, 0, 0]),
                 # (True,'interceptor', [25,0,0]), # This is technically a army unit

             ], 'Terran': [
                 (False, 'scv', [50, 0, 1]),
                 (True, 'marine', [50, 0, 1]),
                 (True, 'marauder', [100, 25, 2]),
                 (True, 'reaper', [50, 50, 2]),
                 (True, 'ghost', [200, 100, 2]),
                 (True, 'hellion', [100, 0, 2]),
                 (True, 'siegetank', [150, 125, 2]),
                 (True, 'thor', [300, 200, 6]),
                 (True, 'viking', [150, 75, 2]),
                 (True, 'medivac', [100, 100, 2]),
                 (True, 'banshee', [150, 100, 3]),
                 (True, 'raven', [100, 200, 2]),
                 (True, 'battlecruiser', [400, 300, 6]),
                 (True, 'planetaryfortress', [150, 150, 0]),
                 (True, 'missileturret', [100, 0, 0]),

             ], 'Zerg': [
                 # Cumulative costs, including drone costs
                 (False, 'drone', [50, 0, 1]),  # 0
                 (True, 'zergling', [25, 0, .5]),
                 (True, 'queen', [150, 0, 2]),
                 (True, 'baneling', [50, 25, .5]),
                 (True, 'roach', [75, 25, 2]),
                 (False, 'overlord', [100, 0, 0]),  # 5
                 # dont include the overlord cost
                 (True, 'overseer', [50, 50, 0]),
                 (True, 'hydralisk', [100, 50, 2]),
                 (True, 'spinecrawler', [150, 0, 0]),
                 (True, 'sporecrawler', [125, 0, 0]),
                 (True, 'mutalisk', [100, 100, 2]),  # 10
                 (True, 'corruptor', [150, 100, 2]),
                 (True, 'broodlord', [300, 250, 4]),
                 (True, 'broodling', [0, 0, 0]),
                 (True, 'infestor', [100, 150, 2]),
                 (True, 'infestedterran', [0, 0, 0]),
                 (True, 'ultralisk', [300, 200, 6]),
                 (False, 'nydusworm', [100, 100, 0]),
             ]},
             'HotS':    {'Protoss': [
                 (False, 'probe', [50, 0, 1]),
                 (True, 'zealot', [100, 0, 2]),
                 (True, 'sentry', [50, 100, 2]),
                 (True, 'stalker', [125, 50, 2]),
                 (True, 'hightemplar', [50, 150, 2]),
                 (True, 'darktemplar', [125, 125, 2]),  # 5
                 (True, 'immortal', [250, 100, 4]),
                 (True, 'colossus', [300, 200, 6]),
                 # Can't know the cost, split the difference.
                 (True, 'archon', [175, 275, 4]),
                 (True, 'observer', [25, 75, 1]),
                 (True, 'warpprism', [200, 0, 2]),  # 10
                 (True, 'phoenix', [150, 100, 2]),
                 (True, 'voidray', [250, 150, 4]),
                 (True, 'carrier', [350, 250, 6]),
                 # includes mothershipcore cost
                 (True, 'mothership', [400, 400, 8]),
                 (True, 'photoncannon', [150, 0, 0]),  # 15
                 (True, 'oracle', [150, 150, 3]),
                 (True, 'tempest', [300, 200, 4]),
                 (True, 'mothershipcore', [100, 100, 2]),
                 # (True,'interceptor', [25,0,0]), # This is technically a army unit

             ], 'Terran': [
                 (False, 'scv', [50, 0, 1]),  # 0
                 (True, 'marine', [50, 0, 1]),
                 (True, 'marauder', [100, 25, 2]),
                 (True, 'reaper', [50, 50, 1]),
                 (True, 'ghost', [200, 100, 2]),
                 (True, 'hellion', [100, 0, 2]),  # 5
                 (True, 'siegetank', [150, 125, 2]),
                 (True, 'thor', [300, 200, 6]),
                 (True, 'viking', [150, 75, 2]),
                 (True, 'medivac', [100, 100, 2]),
                 (True, 'banshee', [150, 100, 3]),  # 10
                 (True, 'raven', [100, 200, 2]),
                 (True, 'battlecruiser', [400, 300, 6]),
                 (True, 'planetaryfortress', [150, 150, 0]),
                 (True, 'missileturret', [100, 0, 0]),
                 (True, 'widowmine', [75, 25, 2]),  # 15

             ], 'Zerg': [
                 # Cumulative costs, including drone costs
                 (False, 'drone', [50, 0, 1]),
                 (True, 'zergling', [25, 0, .5]),
                 (True, 'queen', [150, 0, 2]),
                 (True, 'baneling', [50, 25, .5]),
                 (True, 'roach', [75, 25, 2]),
                 (False, 'overlord', [100, 0, 0]),
                 # dont include the overlord cost because we arent including costs of pylons or supply depots
                 (True, 'overseer', [50, 50, 0]),
                 (True, 'hydralisk', [100, 50, 2]),
                 (True, 'spinecrawler', [150, 0, 0]),
                 (True, 'sporecrawler', [125, 0, 0]),
                 (True, 'mutalisk', [100, 100, 2]),
                 (True, 'corruptor', [150, 100, 2]),
                 (True, 'broodlord', [300, 250, 4]),
                 (True, 'broodling', [0, 0, 0]),
                 (True, 'infestor', [100, 150, 2]),
                 (True, 'infestedterran', [0, 0, 0]),
                 (True, 'ultralisk', [300, 200, 6]),
                 (False, 'nydusworm', [100, 100, 0]),
                 (True, 'swarmhost', [200, 100, 3]),
                 (True, 'viper', [100, 200, 3]),

             ]},
             'LotV':    {'Protoss': [
                 (False, 'probe', [50, 0, 1]),
                 (True, 'zealot', [100, 0, 2]),
                 (True, 'sentry', [50, 100, 2]),
                 (True, 'stalker', [125, 50, 2]),
                 (True, 'hightemplar', [50, 150, 2]),
                 (True, 'darktemplar', [125, 125, 2]),  # 5
                 (True, 'immortal', [250, 100, 4]),
                 (True, 'colossus', [300, 200, 6]),
                 # Can't know the cost, split the difference.
                 (True, 'archon', [175, 275, 4]),
                 (True, 'observer', [25, 75, 1]),
                 (True, 'warpprism', [200, 0, 2]),  # 10
                 (True, 'phoenix', [150, 100, 2]),
                 (True, 'voidray', [250, 150, 4]),
                 (True, 'carrier', [350, 250, 6]),
                 # includes mothershipcore cost
                 (True, 'mothership', [400, 400, 8]),
                 (True, 'photoncannon', [150, 0, 0]),  # 15
                 (True, 'oracle', [150, 150, 3]),
                 (True, 'tempest', [300, 200, 4]),
                 (True, 'mothershipcore', [100, 100, 2]),
                 (True, 'disruptor', [100, 100, 2]),
                 (True, 'adept', [100, 25, 2]),  # 20
                 # (True,'interceptor', [25,0,0]), # This is technically a army unit

             ], 'Terran': [
                 (False, 'scv', [50, 0, 1]),  # 0
                 (True, 'marine', [50, 0, 1]),
                 (True, 'marauder', [100, 25, 2]),
                 (True, 'reaper', [50, 50, 1]),
                 (True, 'ghost', [200, 100, 2]),
                 (True, 'hellion', [100, 0, 2]),  # 5
                 (True, 'siegetank', [150, 125, 2]),
                 (True, 'thor', [300, 200, 6]),
                 (True, 'viking', [150, 75, 2]),
                 (True, 'medivac', [100, 100, 2]),
                 (True, 'banshee', [150, 100, 3]),  # 10
                 (True, 'raven', [100, 200, 2]),
                 (True, 'battlecruiser', [400, 300, 6]),
                 (True, 'planetaryfortress', [150, 150, 0]),
                 (True, 'missileturret', [100, 0, 0]),
                 (True, 'widowmine', [75, 25, 2]),  # 15
                 (True, 'cyclone', [150, 150, 3]),
                 (True, 'liberator', [150, 150, 3]),

             ], 'Zerg': [
                 # Cumulative costs, including drone costs
                 (False, 'drone', [50, 0, 1]),  # 0
                 (True, 'zergling', [25, 0, .5]),
                 (True, 'queen', [150, 0, 2]),
                 (True, 'baneling', [50, 25, .5]),
                 (True, 'roach', [75, 25, 2]),
                 (False, 'overlord', [100, 0, 0]),  # 5
                 # dont include the overlord cost because we arent including costs of pylons or supply depots
                 (True, 'overseer', [50, 50, 0]),
                 (True, 'hydralisk', [100, 50, 2]),
                 (True, 'spinecrawler', [150, 0, 0]),
                 (True, 'sporecrawler', [125, 0, 0]),
                 (True, 'mutalisk', [100, 100, 2]),  # 10
                 (True, 'corruptor', [150, 100, 2]),
                 (True, 'broodlord', [300, 250, 4]),
                 (True, 'broodling', [0, 0, 0]),
                 (True, 'infestor', [100, 150, 2]),
                 (True, 'infestedterran', [0, 0, 0]),  # 15
                 (True, 'ultralisk', [300, 200, 6]),
                 (False, 'nydusworm', [100, 100, 0]),
                 (True, 'swarmhost', [200, 100, 3]),
                 (True, 'viper', [100, 200, 3]),
                 (True, 'lurker', [150, 150, 3]),  # 20
                 (True, 'ravager', [100, 100, 3]),
             ]}}

    ARMY_MAP, ARMY_INFO, COUNTS_AS_ARMY, UNITS = {}, {}, {}, {}
    MAX_NUM_UNITS = 0
    for expansion, expansion_data in unit_data.items():
            ARMY_INFO[expansion] = {}
            for race, unit_list in expansion_data.items():
                if len(unit_list) > MAX_NUM_UNITS:
                    MAX_NUM_UNITS = len(unit_list)
                if race not in UNITS:
                    UNITS[race] = list()
                for index, (army, name, info) in enumerate(unit_list):
                    ARMY_INFO[expansion][name] = info
                    if name not in UNITS[race]:
                        UNITS[race].append(name)
                        ARMY_MAP[name] = index
                        COUNTS_AS_ARMY[name] = army

    return ARMY_MAP


### From sc2reader_to_esdb.py ###
# https://github.com/dsjoerg/ggpyjobs/blob/master/sc2parse/sc2reader_to_esdb.py

def populateBlobWithSummaryData(matchblob, replay, playerToIdentityId):
    # Tracker only useful for post 2.0.8 replays
    if replay.build < 25446:
        return replay

    identityIdToPlayer = dict([(v, k) for k, v in playerToIdentityId.items()])

    blob_names = ['Lost', 'VespeneCurrent', 'MineralsCurrent', 'VespeneCollectionRate',
                  'MineralsCollectionRate', 'WorkersActiveCount', 'SupplyUsage']
    for blob_name in blob_names:
        matchblob[blob_name] = defaultdict(list)

    players_we_track = [
        player for player in playerToIdentityId if playerToIdentityId[player] > 0]
    expected_player_count = len(players_we_track)

    def gatherstats(now, stats, matchblob):
        if len(stats) == expected_player_count:
            for ident_id, pstats in stats.items():
                matchblob['Lost'][ident_id].append(pstats.resources_lost)
                matchblob['VespeneCurrent'][ident_id].append(
                    pstats.vespene_current)
                matchblob['MineralsCurrent'][ident_id].append(
                    pstats.minerals_current)
                # starting with 3.2 the resource collection rates were reported as faster numbers.
                # we shift them back so that we dont have to make changes everywhere else and deal with a discontinuity
                matchblob['VespeneCollectionRate'][ident_id].append(
                    pstats.vespene_collection_rate / 1.36)
                matchblob['MineralsCollectionRate'][ident_id].append(
                    pstats.minerals_collection_rate / 1.36)
                matchblob['WorkersActiveCount'][ident_id].append(
                    pstats.workers_active_count)
                matchblob['SupplyUsage'][ident_id].append(
                    (pstats.food_used, pstats.food_made))
        else:
            print "Ignoring stats at loop {}, there were only {} but we needed {}".format(
                now, len(stats), expected_player_count)

    now = 0
    stats = dict()

    def efilter(e): return isinstance(e, PlayerStatsEvent)
    for event in filter(efilter, replay.tracker_events):
        # The events are sent in blocks ever 10seconds, 1 per player.
        if event.frame != now:
            if stats:
                gatherstats(now, stats, matchblob)
                stat = dict()
            now = event.frame

        # TODO: Get the ident_id instead
        if event.player in players_we_track:
            stats[playerToIdentityId[event.player]] = event

    # Gather that last set of stats
    gatherstats(now, stats, matchblob)

    for blob_name, attr_name in dict(
        VespeneCurrent='average_unspent_vespene',
        MineralsCurrent='average_unspent_minerals',
        VespeneCollectionRate='average_vespene_collection_rate',
        MineralsCollectionRate='average_minerals_collection_rate',
    ).iteritems():
        for ident_id, values in matchblob[blob_name].items():
            player = identityIdToPlayer[ident_id]

            # for the purpose of computing averages, we dont want
            # the first value of these arrays, which is the
            # observation at time 0
            values = values[1:]

            setattr(player, attr_name, sum(values)/len(values))

    for player in players_we_track:
        player.average_resource_collection_rate = (
            player.average_vespene_collection_rate + player.average_minerals_collection_rate)
        player.average_unspent_resources = player.average_unspent_minerals + \
            player.average_unspent_vespene
        player.workers_created = len(
            [u for u in player.units if (u.is_worker and u.finished_at is not None)])

        # we dont want to count beacons, larva and broodlings as units for the purposes of units_trained
        # what they have in common is that they have no mineral + vespene cost
        # subtract six because the initial workers dont count as units trained
        player.units_trained = len([u for u in player.units if (
            not u.is_building and u.finished_at is not None and (u.minerals + u.vespene > 0))]) - 6

        # subtract one because the initial base doesnt count as a structure built
        player.structures_built = len([u for u in player.units if (
            u.is_building and u.finished_at is not None)]) - 1
        player.workers_killed = len(
            [u for u in player.killed_units if u.is_worker])

        # we dont want to count larva or broodlings as units for the purposes of units_killed
        # what they have in common is that they have no mineral + vespene cost
        player.units_killed = len(
            [u for u in player.killed_units if not u.is_building and u.owner is not None and (u.minerals + u.vespene > 0)])

        player.structures_razed = len(
            [u for u in player.killed_units if u.is_building and u.owner is not None])

    if False:
        for player in players_we_track:
            print player, '\n', '='*30, '\n'
            for attr_name in ['time_supply_capped', 'average_resource_collection_rate', 'average_unspent_resources', 'workers_created', 'units_trained', 'structures_built', 'workers_killed', 'units_killed', 'structures_razed']:
                print "{0: <33}:\t{1}".format(
                    attr_name, getattr(player, attr_name))
            print
            for blob_name in blob_names:
                print "{0}:\n{1}\n".format(
                    blob_name, matchblob[blob_name][player.pid])
            print


def populateBlobWithSummaryDataCustom(matchblob, replay, playerToIdentityId):
    # Tracker only useful for post 2.0.8 replays
    if replay.build < 25446:
        return replay

    identityIdToPlayer = dict([(v, k) for k, v in playerToIdentityId.items()])

    blob_names = ['Lost', 'VespeneCurrent', 'MineralsCurrent', 'VespeneCollectionRate',
                  'MineralsCollectionRate', 'WorkersActiveCount', 'SupplyUsage']

    players_we_track = [
        player for player in playerToIdentityId if playerToIdentityId[player] > 0]
    expected_player_count = len(players_we_track)

    def gatherstats(now, stats, matchblob):
        if len(stats) == expected_player_count:
            for ident_id, pstats in stats.items():

                newSnapshot = SC2Snapshot(pstats.resources_lost,pstats.vespene_current,pstats.minerals_current,
                (pstats.vespene_collection_rate / 1.36), (pstats.minerals_collection_rate / 1.36), pstats.workers_active_count,pstats.food_used, pstats.food_made).__dict__

                if not pstats.frame in matchblob:
                    matchblob[pstats.frame] = dict()

                if not ident_id in matchblob[pstats.frame]:
                    matchblob[pstats.frame][ident_id] = newSnapshot

                matchblob[pstats.frame][ident_id]['units'] = defaultdict(int)
    
        else:
            print "Ignoring stats at loop {}, there were only {} but we needed {}".format(
                now, len(stats), expected_player_count)

    now = 0
    stats = dict()

    def efilter(e): return isinstance(e, PlayerStatsEvent)
    for event in filter(efilter, replay.tracker_events):
        # The events are sent in blocks ever 10seconds, 1 per player.
        if event.frame != now:
            if stats:
                gatherstats(now, stats, matchblob)
                stat = dict()
            now = event.frame

        # TODO: Get the ident_id instead
        if event.player in players_we_track:
            stats[playerToIdentityId[event.player]] = event

    # Gather that last set of stats
    gatherstats(now, stats, matchblob)

def army_map(replay, ptoi):

    """Creates a map of player-identity-id => array of army units in this format:
    [ [unit type, finished_at, died_at], [unit type, finished_at, died_at], ... ]
    """
    army_map = dict()
    ARMY_MAP = get_plugin_army_map()
    for player in [p for p in replay.players if p in ptoi]:
        player_army = list()
        for unit in player.units:
            unit_type = get_unit_type(unit)

            if unit_type in ARMY_MAP and unit.finished_at is not None and unit.died_at is not None and not unit.hallucinated:
                if unit_type == 'planetaryfortress':
                    # Its not a PF until it finishes upgrading!
                    for frame, utype in unit.type_history.items():
                        if utype.name == 'PlanetaryFortress':
                            player_army.append(
                                ('planetaryfortress', frame, unit.died_at))
                            break
                elif unit_type == 'overseer':
                    # The overseer spends part of its life as a overlord, split the time
                    for frame, utype in unit.type_history.items():
                        if utype.name == 'Overseer':
                            player_army.append(
                                ('overlord', unit.finished_at, frame))
                            player_army.append(
                                ('overseer', frame, unit.died_at))
                            break
                elif unit_type == 'broodlord':
                    # The broodlord spends part of its life as a corruptor, split the time
                    for frame, utype in unit.type_history.items():
                        if utype.name == 'BroodLord':
                            player_army.append(
                                ('corruptor', unit.finished_at, frame))
                            player_army.append(
                                ('broodlord', frame, unit.died_at))
                            break
                else:
                    # Everyone else gets full credit
                    player_army.append(
                        (unit_type, unit.finished_at, unit.died_at))

        army_map[ptoi[player]] = player_army
    return army_map

### Custom created function ###

def getPlayerInfo(blob,replay,playerToIdentityId):
    for player in replay.players:
        blob[playerToIdentityId[player]] = dict()
        blob[playerToIdentityId[player]]['race'] = player.pick_race

def writeToFile(dataBlob, outFileName):
    with open(outFileName, 'w') as outfile:
        json.dump(dataBlob, outfile)

def getOutputFolderFromRaces(player1Race,player2Race):
    isProtoss = False
    isTerran = False
    isZerg = False

    returnValue = "undefined"

    racesList = [player1Race,player2Race]

    for race in racesList:
        if race == "Zerg":
            isZerg = True
        elif race == "Terran":
            isTerran = True
        elif race == "Protoss":
            isProtoss = True

    if isZerg and isTerran: 
        returnValue = "ZvT"
    elif isZerg and isProtoss:
        returnValue = "ZvP"
    elif isProtoss and isTerran:
        returnValue = "TvP"
    elif isTerran:
        returnValue = "TvT"
    elif isZerg:
        returnValue = "ZvZ"
    elif isProtoss:
        returnValue = "PvP"

    if returnValue == "undefined":
        print("Erorr here!")

    print("Saving as a: ",returnValue, " with: {} , {}".format(player1Race,player2Race))

    return returnValue

def generateReport(filePath, fileName):

    replayReader = sc2reader.SC2Reader()
    replay = replayReader.load_replay(filePath + fileName)

    playerToIdentityId = {}

    idCount = 1

    for player in replay.players:
        playerToIdentityId[player] = idCount
        idCount = idCount + 1

    blob = dict()

    blob['frameinfo'] = dict()
    blob['playerinfo'] = dict()

    getPlayerInfo(blob['playerinfo'],replay, playerToIdentityId)
    populateBlobWithSummaryDataCustom(blob['frameinfo'], replay, playerToIdentityId)
    populateUnitData(blob['frameinfo'], replay, playerToIdentityId)

    outputFolderFromRaceInfo = getOutputFolderFromRaces(blob['playerinfo'][1]['race'],blob['playerinfo'][2]['race'])

    outputFileString = './dataOutput/' + outputFolderFromRaceInfo + '/' + fileName.split('.')[0] + '-data.json'

    writeToFile(blob, outputFileString)


def populateUnitData(blob, replay, playerToIdentityId):
    army_by_frame = army_map(replay, playerToIdentityId)
    sortedFrameList = sorted(blob)

    for player in army_by_frame:
        for unit in army_by_frame[player]:
            name = unit[0]
            startTime = unit[1]
            endTime = unit[2]

            startIndex = int(math.floor(startTime / 160))
            if (startIndex >= len(sortedFrameList)):
                startIndex = len(sortedFrameList) - 1

            endIndex = int(math.floor(endTime / 160))
            if (endIndex >= len(sortedFrameList)):
                endIndex = len(sortedFrameList) - 1

            visitingIndex = startIndex

            while visitingIndex < endIndex:
                visitingFrame = sortedFrameList[visitingIndex]
                if name in blob[visitingFrame][player]['units']:
                    blob[visitingFrame][player]['units'][name] += 1
                else: 
                    blob[visitingFrame][player]['units'][name] = 1
                visitingIndex += 1

def testUnitStorageStart(fileName):
    blob = dict()

    replayReader = sc2reader.SC2Reader()
    replay = replayReader.load_replay(fileName)

    playerToIdentityId = {}

    idCount = 1

    for player in replay.players:
        playerToIdentityId[player] = idCount
        idCount = idCount + 1

    blob["armies_by_frame"] = army_map(replay, playerToIdentityId)
    testUnitStorage2(blob, replay)


def testUnitStorage(blob, replay):
    event_names = set([event.name for event in replay.events])
    events_of_type = {name: [] for name in event_names}
    for event in replay.events:
        events_of_type[event.name].append(event)

    unit_sum_events = events_of_type["UnitBornEvent"] + \
        events_of_type["UnitDiedEvent"]

    unit_sum_events.sort(key=lambda x: x.second)

    unit_sum_dictionary = dict()

    for ube in unit_sum_events:
        if (type(ube) is sc2reader.events.UnitBornEvent):
            timing = int(math.floor(ube.second / 10) * 10)
            deltaSum = 0
            print("{} created {} at second {}".format(ube.unit_controller,
                                                      ube.unit.name,
                                                      ube.second))
            deltaSum = 1
        elif (type(ube) is sc2reader.events.UnitDiedEvent):
            print("{} died {} at second {}".format(ube.unit.owner,
                                                   ube.unit.name,
                                                   ube.second))
            deltaSum = -1

        if (ube.unit.name in unit_sum_dictionary):
            if (timing in unit_sum_dictionary[ube.unit.name]):
                unit_sum_dictionary[ube.unit.name][timing] = unit_sum_dictionary[ube.unit.name][timing] + deltaSum
            else:
                unit_sum_dictionary[ube.unit.name][timing] = deltaSum
        else:
            unit_sum_dictionary[ube.unit.name] = dict()
            unit_sum_dictionary[ube.unit.name][timing] = deltaSum
            if (ube.unit.name == "Drone"):
                print("Breakpoint")

def testUnitStorage2(blob, replay):
    for player in blob['armies_by_frame']:
        print(player)


if __name__ == "__main__":
    generateReport('./','replay2.SC2Replay')
