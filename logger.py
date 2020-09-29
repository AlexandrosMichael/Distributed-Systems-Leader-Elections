import sys


# logger which prints the output in a logfile. it also prints the output on terminal
# adapted from https://stackoverflow.com/questions/14906764/how-to-redirect-stdout-to-both-file-and-console-with-scripting
class NodeLogger(object):
    def __init__(self, node_id):
        self.terminal = sys.stdout
        file_name = "node_" + str(node_id) + ".log"
        self.log = open("logs/" + file_name, "a")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        pass


class ClientLogger(object):
    def __init__(self, node_id):
        self.terminal = sys.stdout
        file_name = "client_" + str(node_id) + ".log"
        self.log = open("logs/" + file_name, "a")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        pass
