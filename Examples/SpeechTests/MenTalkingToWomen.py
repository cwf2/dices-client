from dicesapi import DicesAPI, FilterParams

def filterFunc(thing):
    return any(man.gender == FilterParams.CHARACTER_GENDER_MALE for man in thing.spkr) and any(woman.gender == FilterParams.CHARACTER_GENDER_FEMALE for woman in thing.addr)

api = DicesAPI()

speeches = api.getSpeeches().advancedFilter(filterFunc)

print("Number of men talking to women " + str(len(speeches)))