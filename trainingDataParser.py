import os
import json
import csv

def getReplayFilesFromInput():
    fileNamesList = []
    for root, directories, filenames in os.walk('./dataOutput/ZvZ'):
        for filename in filenames:
            fileNamesList.append([root + '/', filename])

    return fileNamesList


def flattenjson(b, delim):
    val = {}
    for i in b.keys():
        if isinstance(b[i], dict):
            get = flattenjson(b[i], delim)
            for j in get.keys():
                val[i + delim + j] = get[j]
        else:
            val[i] = b[i]

    return val


def oldMain():
    fileNameList = getReplayFilesFromInput()

    data = []

    with open(fileNameList[0][0]+fileNameList[0][1]) as f:
        for line in f:
            data.append(json.loads(line))

    flattenedJson = flattenjson(data[0], ",")

    processedCounter = 0

    totalToBeProcessed = len(fileNameList)

    print(totalToBeProcessed)

def generateDataHeaders():
    generalHeaders = ['lost','mineralsCollectionRate','mineralsCurrent','supplyTotal','supplyUsed','vespeneCollectionRate','vespeneCurrent','workersActiveCount']
    unitHeaders = ['drone','zergling','queen','baneling','roach','overlord','overseer','hydralisk','spinecrawler','sporecrawler','mutalisk','corruptor','broodlord','broodling','infestor'\
        ,'infestedterran','ultralisk','nydusworm','swarmhost','viper']
    
    returnDictionary = {'generalHeaders':generalHeaders,'unitHeaders':unitHeaders}

    return returnDictionary

def playerGameTickToCSVLine(gameTick, replayJSON, playerValue):
    returnCSVValues = []
    gameTickFrame = replayJSON['frameinfo'][gameTick][str(playerValue)]

    dataHeaders = generateDataHeaders()

    for header in dataHeaders['generalHeaders']:
        returnCSVValues.append(gameTickFrame[header])

    for unit in dataHeaders['unitHeaders']:
        if unit in gameTickFrame['units']:
            returnCSVValues.append(gameTickFrame['units'][unit])
        else:
            returnCSVValues.append(0)

    return returnCSVValues


def gameTickToCSVLine(gameTick, replayJSON):

    resultCSVLine = []

    player1Tick = playerGameTickToCSVLine(gameTick, replayJSON, 1)
    player2Tick = playerGameTickToCSVLine(gameTick, replayJSON, 2)

    # Merge the arrays
    resultCSVLine = [gameTick] + player1Tick + player2Tick

    # Add Game Winner
    gameWinner = 0
    if replayJSON['playerinfo']['1']['won']:
        gameWinner = 1
    elif replayJSON['playerinfo']['2']['won']:
        gameWinner = 2
    else:
        print("Error! Undefined game winner!")

    resultCSVLine = resultCSVLine + [gameWinner]

    return resultCSVLine


def main():

    fileNameList = getReplayFilesFromInput()

    csvWriter = csv.writer(open("./outputData.csv","w"))

    dataHeaderStrings = generateDataHeaders()

    headerLine = dataHeaderStrings['generalHeaders'] + dataHeaderStrings['unitHeaders']

    csvHeaderLine1 = []
    csvHeaderLine2 = []

    for headerValue in headerLine:
        csvHeaderLine1.append(headerValue + "1")
        csvHeaderLine2.append(headerValue + "2")

    csvWriter.writerow(csvHeaderLine1 + csvHeaderLine2)

    processedCounter = 0
    totalToBeProcessed = len(fileNameList)

    for fileRoot, fileName in fileNameList:
        with open(fileRoot+fileName) as json_file:
            replayJSON = json.load(json_file)
            for gameTick in replayJSON['frameinfo']:
                CSVfileLine = gameTickToCSVLine(gameTick, replayJSON)
                csvWriter.writerow(CSVfileLine)
        processedCounter += 1
        print("{}/{}".format(processedCounter,totalToBeProcessed))

    # For each game
    # Take the json data
    # For each 'tick' of the game
    # Put that JSON data into a csv row
    # write all the rows to a giant csv file


if __name__ == "__main__":
    main()
