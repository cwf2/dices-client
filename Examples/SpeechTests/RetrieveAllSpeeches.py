from dicesapi import DicesAPI

api = DicesAPI() #Create a new connection to the database 

speeches = api.getSpeeches() #Fetch ALL the speeches from the database

for speech in speeches:
    print(speech.getCTS().text) #Print all of the text from the speeches