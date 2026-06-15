import dicesapi
from . import logger


class Metrics(object):

    ERROR_VALUE = "CoolrooWasHere"

    def __init__(self, api):
        if api is None or not isinstance(api, dicesapi.DicesAPI):
            raise ValueError
        else:
            logger.info("Metrics object created")

    #Cluster Functions

    #Int values
    def countInterruptions(self, cluster):
        '''Count the number of interruptions in a cluster'''

        logger.debug("Counting Interruptions from a cluster")
        if not isinstance(cluster, dicesapi.SpeechCluster):
            logger.critical("Could not count interruptions as a SpeechCluster was not provided")
            return self.ERROR_VALUE
        speeches = self.api.getSpeeches(cluster_id=cluster.id)
        interruptions = 0
        prevAddr = []
        for speech in speeches:
            if not any(responder in speech.spkr for responder in prevAddr):
                interruptions += 1
            prevAddr = speech.addr
        return interruptions

    def countReplies(self, cluster):
        '''Count the number of replies in a cluster'''

        logger.debug("Counting Replies from a cluster")
        if not isinstance(cluster, dicesapi.SpeechCluster):
            logger.critical("Could not count replies as a SpeechCluster was not provided")
            return self.ERROR_VALUE
        speeches = self.api.getSpeeches(cluster_id=cluster.id)
        interruptions = 0
        prevAddr = []
        for speech in speeches:
            if not any(responder in speech.spkr for responder in prevAddr):
                interruptions += 1
            prevAddr = speech.addr
        return interruptions

    def countSpeakers(self, cluster):
        '''Count the number of speakers in a cluster'''

        logger.debug("Counting speakers in a cluster")
        if not isinstance(cluster, dicesapi.SpeechCluster):
            logger.critical("Could not count speakers as a SpeechCluster was not provided")
            return self.ERROR_VALUE
        speeches = self.api.getSpeeches(cluster_id=cluster.id)
        speakers = 0
        for speech in speeches:
            speakers += len(speech.spkr)
        return speakers
    
    def countAddresees(self, cluster):
        '''Count the total number of addressees across speeches in a cluster'''

        logger.debug("Counting speakers in a cluster")
        if not isinstance(cluster, dicesapi.SpeechCluster):
            logger.critical("Could not count replies as a SpeechCluster was not provided")
            return self.ERROR_VALUE
        speeches = self.api.getSpeeches(cluster_id=cluster.id)
        addressees = 0
        for speech in speeches:
            addressees += len(speech.addr)
        return addressees

    #Boolean Returns

    def isOneSided(self, cluster):
        '''True if no speaker in the cluster has previously been addressed'''

        logger.debug("Determining whether conversation is one sided")
        if not isinstance(cluster, dicesapi.SpeechCluster):
            logger.critical("Could not determine one sidedness as a SpeechCluster was not provided")
            return self.ERROR_VALUE
        addressees = []
        speeches = self.api.getSpeeches(cluster_id=cluster.id)
        for speech in speeches:
            if any(speaker in speech.spkr for speaker in addressees):
                return False
            addressees.extend(speech.addr)
            addressees = list(set(addressees))
        return True

    def isMonologue(self, cluster):
        '''True if every speech in the cluster has the same single speaker'''

        logger.debug("Determining whether conversation is a monologue")
        if not isinstance(cluster, dicesapi.SpeechCluster):
            logger.critical("Could not determine if cluster is a monologue as a SpeechCluster was not provided")
            return self.ERROR_VALUE
        speeches = self.api.getSpeeches(cluster_id=cluster.id)
        if(len(speeches) == 0):
            logger.warning("Cluster did not contain any speeches")
            return False
        if(len(speeches[0].spkr) != 1):
            return False
        speaker = speeches[0].spkr[0]
        for speech in speeches:
            if len(speech.spkr) != 1 or speech.spkr[0] is not speaker:
                return False
        return True

    def doesInterruption(self, cluster, character):
        '''True if `character` speaks a speech in the cluster that is an interruption'''

        logger.debug("Checking if speaker interrupts")
        if not isinstance(cluster, dicesapi.SpeechCluster):
            logger.critical("Could not check if speaker interrupts as a SpeechCluster was not provided")
            return self.ERROR_VALUE
        if not isinstance(character, dicesapi.CharacterInstance):
            logger.critical("Could not check if speaker interrupts as a Character Instance was not provided")
            return self.ERROR_VALUE
        speeches = self.api.getSpeeches(cluster_id=cluster.id)
        for speech in speeches:
            if character in speech.spkr and speech.isInterruption():
                return True
        return False

        

    #Float Values

    def speakerPriority(self, cluster, speaker):
        '''Return the fraction of speeches in the cluster spoken by `speaker`'''

        logger.debug("Checking speaker priority")
        if not isinstance(cluster, dicesapi.SpeechCluster):
            logger.critical("Could not get speaker priority as a SpeechCluster was not provided")
            return self.ERROR_VALUE
        if not isinstance(speaker, dicesapi.CharacterInstance):
            logger.critical("Could not get speaker priority as a Character Instance was not provided")
            return self.ERROR_VALUE
        speeches = self.api.getSpeeches(cluster_id=cluster.id)
        speaking = 0
        for speech in speeches:
            speaking += 1 if speaker in speech.spkr else 0
        return speaking/len(speeches)


    #Speech Functions
    
    def speechBalance(self, speech):
        '''Return the ratio of speakers to addressees for a speech'''

        logger.debug("Determining speech balance")
        if not isinstance(speech, dicesapi.Speech):
            logger.critical("Could not get speech balance as a Speech was not provided")
            return self.ERROR_VALUE
        return len(speech.spkr)/len(speech.addr)