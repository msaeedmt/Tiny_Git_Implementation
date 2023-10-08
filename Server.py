import re
import shutil
import zipfile

from Git import Git
import pickle
import os
import socket
import threading
import time
import sys
import struct


class Server:
    def __init__(self):
        self.location = "E:\\PythonGit"
        self.fileName = "gitFile"
        self.localRepoName = 'gitRepo'

        self.isUserLogedIn = False
        self.currentUser = None
        self.currenRepository = None
        self.currentUsername = ""

        self.git = Git(self.location)

        self.path = os.path.join(self.location, self.fileName)
        if os.path.exists(self.path):
            gitFile = open(self.path, 'rb')
            self.git = pickle.load(gitFile)
            print(self.git.users)
            gitFile.close()

        self.SEPARATOR = "<SEPARATOR>"
        self.BUFFER_SIZE = 4096

    def socket_service(self):
        host = ''
        port = 123
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((host, port))

        s.listen(10)
        conn, addr = s.accept()

        while True:

            try:
                data = conn.recv(1024).decode()
                if not self.isUserLogedIn:
                    response = self.loginAndSignup(data)
                    response = str.format("{}-{}", self.isUserLogedIn, response)
                else:
                    response = self.callCommand(data, conn, addr)
                conn.sendall(response.encode())

            except socket.error:
                conn.close()
                print("Error Occured.")
                break

        conn.close()

    def saveGitConfig(self):
        gitFile = open(self.path, 'wb')
        pickle.dump(self.git, gitFile)
        gitFile.close()

    def loginAndSignup(self, data):
        splited_data = data.split(' ')
        command = splited_data[0]

        if command == "login":
            username = splited_data[1]
            password = splited_data[2]
            isLoginSuccessful = self.git.login(username, password)
            if not isLoginSuccessful:
                print("login failed!")
                return "Login failed!"
            else:
                self.isUserLogedIn = True
                self.currentUser = self.git.getUserObject(username)
                print("successfuly loged in")
                return str.format('"LogedIn successfully."-{}', self.currentUser.username)
        elif command == 'signup':
            username = splited_data[1]
            password = splited_data[2]
            isSignupSuccessful = self.git.addUser(username, password)
            if not isSignupSuccessful:
                print("signup failed!")
                return "SignUp failed!"
            else:
                self.isUserLogedIn = True
                self.currentUser = self.git.getUserObject(username)
                self.saveGitConfig()
                print("successfuly signed up in")
                return str.format('"SignedUp successfully."-{}', self.currentUser.username)

        return "You should login first to have access!"

    def callCommand(self, data, conn, addr):
        command = (data.split(' '))[0]
        if command == "push":
            return self.commitAndPushFiles(conn, data)
        elif command == "clone":
            return self.sendFile(conn, 'clone')
        elif command == "pull":
            return self.sendFile(conn, 'pull')
        elif command == "getAllRepos":
            return self.getAllRepos()
        elif command == "selectRepo":
            return self.selectRepo(data)
        elif command == "createRepo":
            return self.createRepo(data)
        elif command == "sync":
            return self.sync(conn, data)
        elif command == "addContributer":
            return self.addContributer(data)
        elif command == "login" or command == "signup":
            return self.loginAndSignup(data)
        elif command == "exit":
            conn.close()

    def createRepo(self, data):
        splittedData = data.split(' ')
        repoName = splittedData[1]
        if splittedData[2] == 'True':
            isPrivate = True
        else:
            isPrivate = False

        isCreated = self.currentUser.createRepo(repoName, isPrivate)
        self.git.repositories[repoName] = self.currentUser.username
        self.saveGitConfig()
        self.currenRepository = self.currentUser.getRepo(repoName)

        if isCreated:
            return "Repository has been made successfully."
        else:
            return "Unable to make repository!"

    def selectRepo(self, data):
        splittedData = data.split(' ')
        repoName = splittedData[1]

        repoOwner = self.git.repositories[repoName]
        oRepoOwner = self.git.getUserObject(repoOwner)
        foundedRepo = oRepoOwner.getRepo(repoName)

        if foundedRepo == None:
            return "Repo not found!"
        if foundedRepo.isPirvate and self.currentUser.username not in foundedRepo.contributers:
            print('Unauthorized')
            return "Unauthorized. this repository in private!"

        self.currenRepository = foundedRepo
        return "seccessfully selected repository."

    def commitAndPushFiles(self, conn, data):
        if self.currentUser.username not in self.currenRepository.contributers:
            return "Unauthorized. You are not a contributer!"
        while 1:
            fileinfo_size = struct.calcsize('128sl')
            buf = conn.recv(fileinfo_size)
            if buf:
                filename, filesize = struct.unpack('128sl', buf)
                filename = filename.decode('utf-8')
                filename = filename.strip('\00')
                new_filename = os.path.join(self.currenRepository.location, "Cms.zip")
                print('file new name is {0}, filesize if {1}'.format(new_filename, filesize))

                recvd_size = 0

                with open(new_filename, 'wb') as fp:
                    print('start receiving...')

                    while not recvd_size == filesize:
                        if filesize - recvd_size > 1024:
                            print("Processing:{0}%".format(round((recvd_size) * 100 / filesize)), end="\r")
                            data = conn.recv(1024)
                            recvd_size += len(data)
                        else:
                            data = conn.recv(filesize - recvd_size)
                            recvd_size = filesize
                        fp.write(data)
                    fp.close()
                shutil.unpack_archive(filename=new_filename, extract_dir=self.currenRepository.location, format="zip")
                os.remove(new_filename)

                commit = self.currenRepository.getCommit(filename)
                self.currenRepository.addCommit(commit.name, commit.message)

                print('end receive...')
            else:
                return "file has problem!"
            return "files pushed successfully!"

    def getAllRepos(self):
        allRepos = "AllRepositories"
        for repo in self.git.repositories.keys():
            repoPath = os.path.join(self.location, self.git.repositories[repo], repo)
            ti_c = os.path.getctime(repoPath)
            c_ti = time.ctime(ti_c)
            allRepos += str.format('\n{}\t ------>>>> \t{}\t{}', repo, self.git.repositories[repo], c_ti)
        return allRepos

    def sendFile(self, s, type="clone"):
        if self.currenRepository == None:
            return "no repository selected!"
        if type == "pull" and self.currentUser.username not in self.currenRepository.contributers:
            return "Unauthorized. You are not a contributer!"
        self.compressFiles(type)
        while True:
            zipFilePath = os.path.join(os.path.curdir, 'Cmp.zip')
            if os.path.isfile(zipFilePath):
                fileinfo_size = struct.calcsize('128sl')
                fhead = struct.pack('128sl', os.path.basename(zipFilePath).encode('utf-8'),
                                    os.stat(zipFilePath).st_size)
                s.send(fhead)
                print('server filepath: {}'.format(zipFilePath))
                fp = open(zipFilePath, 'rb')
                while True:
                    data = fp.read()
                    if not data:
                        print('{} file send over...'.format(zipFilePath))
                        break
                    s.send(data)
                fp.close()
            else:
                return "file not exists!"
            os.remove(zipFilePath)
            return "files successfully Sent."

    def compressFiles(self, type):
        dir_name = self.currenRepository.getLastCommitPath()
        filePaths = self.retrieve_file_paths(dir_name)

        zip_file = zipfile.ZipFile('Cmp' + '.zip', 'w')
        with zip_file:
            for filename in filePaths:
                if not re.findall(str.format("{}\Z", self.currenRepository.getLastCommitName()), filename):
                    rootPath = ''
                    if type == "clone":
                        rootPath = self.currenRepository.repoName

                    zip_file.write(filename,
                                   arcname=filename.replace(os.path.join(self.currenRepository.location,
                                                                         self.currenRepository.getLastCommitName()),
                                                            rootPath, 1))

    def retrieve_file_paths(self, dirName):

        filePaths = []

        for root, directories, files in os.walk(dirName):
            for filename in files:
                filePath = os.path.join(root, filename)
                filePaths.append(filePath)

        return filePaths

    def sync(self, conn, data):
        fileinfo_size = struct.calcsize('iq')
        buf = conn.recv(fileinfo_size)
        lastCommitName, lastLocalModifiedTime = struct.unpack('iq', buf)

        lastRepoModifiedTime = int(os.path.getmtime(self.currenRepository.location))
        fhead = struct.pack('iq', 1, lastRepoModifiedTime)
        conn.send(fhead)

        if lastLocalModifiedTime < lastRepoModifiedTime:
            result = self.sendFile(conn, 'pull')
        else:
            result = self.commitAndPushFiles(conn, data)
        return result + " (synced)"

    def addContributer(self, data):
        splittedData = data.split(' ')
        username = splittedData[1]

        if self.currentUser.username == self.currenRepository.owner:
            self.currenRepository.addContributer(username)
            print('Successfully added contributer.')
            return 'Successfully added contributer.'
        else:
            print('Just repo onwer can add Contributer!')
            return 'Just repo onwer can add Contributer!'


if __name__ == '__main__':
    server = Server()
    server.socket_service()
