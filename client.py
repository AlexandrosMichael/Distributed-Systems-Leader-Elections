import sys
import argparse
import socket
import threading
import datetime
import csv
import pickle
import os
import signal
import time
from logger import *
from client_messages import *


# client settings
T_TIMEOUT = 10
HEADER = 128
HOSTS = {}


# method which loads and returns the details of all the hosts as found in the nodes.csv file
def read_hosts():
    hosts = {}
    with open('nodes.csv') as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            id = int(row['id'])
            host = row['hostname']
            port = int(row['port'])
            hosts[id] = {
                'id': id,
                'hostname': host,
                'port': port
            }
    return hosts


# method which makes the BORROW_UPDATE request to the client's server node
def borrow_book(book_id):
    host = HOSTS[DESIGNATED_NODE]
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((host['hostname'], host['port']))
        client.setblocking(True)
        msg_dict = {
            'id': ID,
            'msg_type': BORROW_UPDATE,
            'msg': book_id
        }
        client.send(pickle.dumps(msg_dict))
        print(
            f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {ID} ] Send to {host['id']}: {BORROW_UPDATE}")

        msg = client.recv(HEADER)
        while len(msg) == 0:
            time.sleep(0.25)
            msg = client.recv(HEADER)

        if msg:
            msg_dict = pickle.loads(msg)
            sender = msg_dict['id']
            msg = msg_dict['msg']

            print(
                f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {ID} ] Receive from {sender}: {msg}")

    except socket.error:
        print(
            f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {ID} ] Could not connect to {host['id']}")
    except socket.timeout:
        print(
            f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {ID} ] Timeout by host {host['id']}")


# method which makes the RETURN_UPDATE request to the client's server node
def return_book(book_id):
    host = HOSTS[DESIGNATED_NODE]
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((host['hostname'], host['port']))

        msg_dict = {
            'id': ID,
            'msg_type': RETURN_UPDATE,
            'msg': book_id
        }
        client.send(pickle.dumps(msg_dict))
        print(
            f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {ID} ] Send to {host['id']}: {RETURN_UPDATE}")

        msg = client.recv(HEADER)

        if msg:
            msg_dict = pickle.loads(msg)
            sender = msg_dict['id']
            msg = msg_dict['msg']

            print(
                f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {ID} ] Receive from {sender}: {msg}")

    except socket.error:
        print(
            f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {ID} ] Could not connect to {host['id']}")
    except socket.timeout:
        print(
            f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {ID} ] Timeout by host {host['id']}")


# Method which provides the text interface to the admin
def client_interface():
    while True:
        print("[CLIENT INTERFACE] Choose option: Borrow Book(1), Return Book(2), Disconnect(3)")
        client_choice = input()
        client_choice = int(client_choice)

        # if client chooses to borrow a book
        if client_choice == 1:

            book_id = -1

            # prompt client until they enter a valid book id
            while book_id > 10 or book_id < 1:
                print("[CLIENT INTERFACE] Enter ID of the book you would like to borrow.")
                book_id = input()
                book_id = int(book_id)
                if book_id > 10 or book_id < 1:
                    print("[CLIENT INTERFACE] Invalid book id.")

            borrow_book(book_id)

        # if client chooses to return a book
        elif client_choice == 2:

            book_id = -1

            # prompt client until they enter a valid book id
            while book_id > 10 or book_id < 1:
                print("[CLIENT INTERFACE] Enter ID of the book you would like to return.")
                book_id = input()
                book_id = int(book_id)
                if book_id > 10 or book_id < 1:
                    print("[CLIENT INTERFACE] Invalid book id.")

            return_book(book_id)

        elif client_choice == 3:
            print("[CLIENT INTERFACE] Disconnecting.")
            sys.stdout.flush()
            os.kill(os.getpid(), signal.SIGKILL)


# main method of the client. Spawns a thread to provide the client interface functionality.
def main():
    client_interface_thread = threading.Thread(target=client_interface())
    client_interface_thread.start()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-u', '--username', dest='id', required=True, type=str)
    parser.add_argument('-n', '--node', dest='node_id', required=True, type=int)

    args = parser.parse_args()
    print(args)

    HOSTS = read_hosts()
    ID = args.id

    DESIGNATED_NODE = args.node_id
    sys.stdout = ClientLogger(ID)

    main()
