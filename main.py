import sc2reportgenerator
import os


def getReplayFilesFromInput():
    fileNamesList = []
    for root, directories, filenames in os.walk('./dataInput/'):
        for filename in filenames:
            # fileNamesList.append(os.path.join(root, filename))
            fileNamesList.append([root + '/',filename])

    return fileNamesList


def main():

    fileNameList = getReplayFilesFromInput()
    processedCounter = 0
    totalToBeProcessed = len(fileNameList)

    for root,fileName in fileNameList:
        try:
            sc2reportgenerator.generateReport(root,fileName)
        except Exception as e:
            print("Ran into an exception, skipping this test: ",e)
        processedCounter += 1
        print("{}/{}".format(processedCounter,totalToBeProcessed))

if __name__ == "__main__":
    main()
