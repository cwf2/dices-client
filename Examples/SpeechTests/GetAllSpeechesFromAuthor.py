from dicesapi import DicesAPI

api = DicesAPI() #Create a link to the dicesAPI

speeches = api.getSpeeches(author_name="Homer") #Get all speeches from Homer

print(len(speeches)) #Print how many speeches there are