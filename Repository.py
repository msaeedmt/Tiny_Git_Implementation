import os
import pickle
import random
from Commit import Commit


class Repository:
    def __init__(self, location, repoName, isPrivate, owner=""):
        self.owner = owner
        self.location = location
        self.repoName = repoName
        self.contributers = []
        self.isPirvate = isPrivate
        self.commits = []
        self.commitsWithMessages = {}
        self.contributers.append(self.owner)

    def createCommit(self, message):
        commitName = self.generateRandomCode()
        # commitName = str.format("commit-{}", self.generateRandomCode())

        self.commits.append(commitName)
        self.commitsWithMessages[commitName] = message

        repoFilePath = os.path.join(self.location, self.repoName)

        repoFile = open(repoFilePath, 'wb')
        pickle.dump(self, repoFile)
        repoFile.close()

        path = os.path.join(self.location, commitName)
        os.makedirs(path, exist_ok=True)

        oCommit = Commit(commitName, message)
        commitFilePath = os.path.join(path, commitName)
        commitFile = open(commitFilePath, 'wb')
        pickle.dump(oCommit, commitFile)
        commitFile.close()

        return True

    def addCommit(self, commitName, message):
        self.commits.append(commitName)
        # self.commitsWithMessages[commitName] = message

        repoFilePath = os.path.join(self.location, self.repoName)

        repoFile = open(repoFilePath, 'wb')
        pickle.dump(self, repoFile)
        repoFile.close()

    def generateRandomCode(self):

        random_number = random.randint(0, 16777215)
        hex_number = str(hex(random_number))

        return hex_number

    def getCommitPath(self, commitName):
        if commitName not in self.commits:
            print("commit not exists")
            return None

        path = os.path.join(self.location, commitName)
        return path

    def getLastCommitPath(self):
        path = os.path.join(self.location, self.commits[len(self.commits) - 1])
        return path

    def getLastCommitName(self):
        return self.commits[-1]

    def getCommit(self, commitName):
        commitFilePath = os.path.join(self.location, commitName, commitName)
        commitFile = open(commitFilePath, 'rb')
        commit = pickle.load(commitFile)
        commitFile.close()

        return commit

    def addContributer(self,username):
        self.contributers.append(username)

        repoFilePath = os.path.join(self.location, self.repoName)

        repoFile = open(repoFilePath, 'wb')
        pickle.dump(self, repoFile)
        repoFile.close()