import pickle
import socket
import os
import sys
import struct
import time
import zipfile
import shutil
from Repository import Repository


class Client:
    def __init__(self):
        self.isUserLogedIn = False
        self.gitDir = ""
        self.repository = None
        self.currenUser = ""
        self.commands = [
            "help",
            "login",
            "signup",
            "changeDir",
            "commit",
            "printCommits",
            "selectRepo",
            "addContributer",
            "createRepo",
            "deleteRepo",
            "push",
            "clone",
            "pull",
            "sync",
            "getAllRepos",
            "exit"
        ]
        self.repoName = 'gitRepo'
        self.gitIgnorPatterns = {self.repoName}
        self.getDirectory()
        self.initLocalRepo()

    def initLocalRepo(self):
        self.repository = Repository(os.path.join(self.gitDir, self.repoName), self.repoName, False)

        path = os.path.join(self.gitDir, self.repoName)
        if os.path.exists(path):
            repoFile = open(os.path.join(path, self.repoName), 'rb')
            self.repository = pickle.load(repoFile)
            repoFile.close()
        else:
            os.makedirs(path, exist_ok=True)
            repoFilePath = os.path.join(path, self.repoName)
            repoFile = open(repoFilePath, 'wb')
            pickle.dump(self.repository, repoFile)
            repoFile.close()

    def gitInit(self):
        self.initLocalRepo()

    def getDirectory(self):
        directory = ""
        while not os.path.isdir(directory):
            print('Enter directory to commit : ', end='')
            directory = input()
        self.gitDir = directory

    def socket_client(self):
        host = socket.gethostname()
        port = 123
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.connect((host, port))

        message = ""
        decoded_data = ""
        while message != "quit" and decoded_data != "quit":
            try:
                message, command = self.getCommand()
                while command not in self.commands:
                    print('Command not found! try again.')
                    message, command = self.getCommand()

                if command == "commit":
                    self.commit(message.split()[1])
                elif command == "printCommits":
                    self.printCommits()
                elif command == "changeDir":
                    self.getDirectory()
                elif command == "help":
                    self.help()
                else:
                    if command == "push":
                        conn.sendall(message.encode())
                        self.push(conn)
                    elif command == "clone":
                        conn.sendall(message.encode())
                        self.getFiles(conn, type='clone')
                    elif command == "pull":
                        conn.sendall(message.encode())
                        self.getFiles(conn, type='pull')
                    elif command == "sync":
                        conn.sendall(message.encode())
                        self.sync(conn, message)
                    elif command == "exit":
                        conn.sendall(message.encode())
                        conn.close()
                    else:
                        conn.sendall(message.encode())

                    data = conn.recv(1024).decode()

                    if not self.isUserLogedIn:
                        splittedData = data.split('-')
                        commandSuccess = splittedData[0]
                        severMessage = splittedData[1]
                        if commandSuccess == "True":
                            self.isUserLogedIn = True
                            currentUser = splittedData[2]
                            self.currenUser = currentUser
                        print('+ ' + severMessage)
                    else:
                        if command == 'login' or command == 'signup':
                            splittedData = data.split('-')
                            severMessage = splittedData[0]
                            if len(splittedData) == 2:
                                self.currenUser = splittedData[1]
                            print('+ ' + severMessage)
                        else:
                            print('+ ' + data)

            except socket.error:
                conn.close()
                print("Error Occured.")
                break
        conn.close()

    def push(self, s):
        self.compressFiles()
        while True:
            zipFilePath = os.path.join(os.path.curdir, 'Cmp.zip')
            if os.path.isfile(zipFilePath):
                fileinfo_size = struct.calcsize('128sl')
                fhead = struct.pack('128sl', self.repository.getLastCommitName().encode(),
                                    os.stat(zipFilePath).st_size)
                s.send(fhead)
                print('client filepath: {}'.format(zipFilePath))
                fp = open(zipFilePath, 'rb')
                while True:
                    data = fp.read()
                    if not data:
                        print('{} file send over...'.format(zipFilePath))
                        break
                    s.send(data)
                fp.close()
            else:
                print("file not exists!")
                break
            os.remove(zipFilePath)
            break

    def compressFiles(self):
        dir_name = self.repository.getLastCommitPath()

        filePaths = self.retrieve_file_paths(dir_name)

        zip_file = zipfile.ZipFile('Cmp' + '.zip', 'w')
        with zip_file:
            for filename in filePaths:
                zip_file.write(filename,
                               arcname=filename.replace(os.path.join(self.gitDir, self.repoName) + '\\', '', 1))

    def retrieve_file_paths(self, dirName):
        filePaths = []

        for root, directories, files in os.walk(dirName):
            for filename in files:
                filePath = os.path.join(root, filename)
                filePaths.append(filePath)

        return filePaths

    def commit(self, message):
        self.repository.createCommit(message)
        src = self.gitDir
        dest = self.repository.getLastCommitPath()
        shutil.copytree(src, dest, symlinks=False, ignore=shutil.ignore_patterns('gitRepo'), copy_function=shutil.copy2,
                        ignore_dangling_symlinks=False, dirs_exist_ok=True)
        print("commit successfully created.")

    def printCommits(self):
        if self.repository == None:
            print("First select a directory!")
        if len(self.repository.commits) == 0:
            print("No Commits!")
        else:
            for commit in self.repository.commitsWithMessages.keys():
                commitPath = self.repository.getCommitPath(commit)
                ti_c = os.path.getctime(commitPath)
                c_ti = time.ctime(ti_c)
                print(str.format('{}\t ------>>>> \t{}\t{}', commit, self.repository.commitsWithMessages[commit], c_ti))

    def pullLocaly(self):
        filePathes = self.retrieve_file_paths(self.gitDir)
        for filePath in filePathes:
            if self.repoName not in filePath:
                os.remove(filePath)

        src = self.repository.getLastCommitPath()
        dest = self.gitDir
        shutil.copytree(src, dest, symlinks=False, ignore=shutil.ignore_patterns('gitRepo'), copy_function=shutil.copy2,
                        ignore_dangling_symlinks=False, dirs_exist_ok=True)

    def getFiles(self, conn, type='clone'):
        while 1:
            fileinfo_size = struct.calcsize('128sl')
            buf = conn.recv(fileinfo_size)
            if buf:
                if type == 'pull':
                    filePathes = self.retrieve_file_paths(self.gitDir)
                    for filePath in filePathes:
                        if self.repoName not in filePath:
                            os.remove(filePath)

                filename, filesize = struct.unpack('128sl', buf)
                filename = filename.decode('utf-8')
                fn = filename.strip('\00')
                new_filename = os.path.join(self.gitDir, fn)
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
                shutil.unpack_archive(filename=new_filename, extract_dir=self.gitDir, format="zip")
                os.remove(new_filename)

                print('end receive...')

            print("files received successfully!")
            break

    def sync(self, conn, message):
        lastLocalModifiedTime = int(os.path.getmtime(os.path.join(self.gitDir, self.repoName)))
        fhead = struct.pack('iq', 1, lastLocalModifiedTime)
        conn.send(fhead)

        fileinfo_size = struct.calcsize('iq')
        buf = conn.recv(fileinfo_size)
        lastCommitName, lastRepoModifiedTime = struct.unpack('iq', buf)

        if lastLocalModifiedTime < lastRepoModifiedTime:
            self.getFiles(conn, type='pull')
        else:
            self.push(conn)

    def help(self):
        print("\nhelp")
        print("login\t[username]\t[password]")
        print("signup\t[username]\t[password]")
        print("changeDir")
        print("commit\t[message]")
        print("printCommits")
        print("selectRepo\t[reponame]")
        print("createRepo\t[reponame]\t[isprivate]")
        print("addContributer\t[username]")
        print("push")
        print("clone")
        print("pull")
        print("sync")
        print("getAllRepos\n")

    def getCommand(self):
        if self.currenUser!="":
            print(str.format('{} ({}) > ', self.gitDir,self.currenUser), end='')
        else:
            print(str.format('{} > ', self.gitDir), end='')
        message = input()
        splittedMessage = message.split(' ')
        command = splittedMessage[0]

        return message, command


if __name__ == '__main__':
    client = Client()
    client.socket_client()
