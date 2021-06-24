from dicesapi import DicesAPI

def filterFunc(thing):
    return len(thing.spkr) == 1 and len(thing.addr) == 1 and thing.spkr[0] is not thing.addr[0]

api = DicesAPI()

speeches = api.getSpeeches().advancedFilter(filterFunc)

print("Number of speeches between two people is " + str(len(speeches)))