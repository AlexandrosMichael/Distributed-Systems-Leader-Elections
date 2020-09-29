import sys
import argparse
import socket
import threading
import datetime
import csv
import os
import signal
import select
import time
from logger import *
from access_books import *
from node_messages import *

# settings
T_TIMEOUT = 10
HEADER = 128

# globals
COORDINATOR_FOUND = True
Q_LOCK = False
REQUEST_QUEUE = []
CLIENT_OPERATION_QUEUE = []
HOSTS = {}
SERVER = socket.gethostbyname(socket.gethostname())


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


# method which returns the hosts with a higher id than the node id.
# these are the nodes that will be sent an election message
def get_election_hosts(node_id):
    election_hosts = []
    for key in HOSTS.keys():
        if key > node_id:
            election_hosts.append(HOSTS[key])
    return election_hosts


# method which returns the details of all the other nodes
def get_all_hosts(node_id):
    hosts = []
    for key in HOSTS.keys():
        if key != node_id:
            hosts.append(HOSTS[key])
    return hosts


# method use to initiate an election
def initiate_election():
    global COORDINATOR_FOUND
    global COORDINATOR
    COORDINATOR_FOUND = False
    # get nodes that will be send an election message.
    election_hosts = get_election_hosts(ID)

    sockets = []

    # send election message.
    for host in election_hosts:

        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((host['hostname'], host['port']))
            msg_dict = {
                'id': ID,
                'msg_type': ELECTION_MESSAGE,
                'msg': ''
            }
            client.send(pickle.dumps(msg_dict))
            print(
                f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {ID} ] Send to {host['id']}: {ELECTION_MESSAGE}")
            sockets.append(client)
        except socket.error:
            print(
                f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {ID} ] Could not connect to {host['id']}")

    # watch the socket connections with the other nodes.
    readable, writable, exceptional = select.select(sockets, [], [], T_TIMEOUT)

    # if no-one replies withing T_TIMEOUT send COORDINATOR message to all sockets.
    if not (readable or writable or exceptional) or (len(election_hosts) == 0):
        hosts = get_all_hosts(ID)
        for host in hosts:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                client.connect((host['hostname'], host['port']))
                msg_dict = {
                    'id': ID,
                    'msg_type': COORDINATOR_MESSAGE,
                    'msg': ID
                }

                client.send(pickle.dumps(msg_dict))
                print(
                    f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {ID} ] Send to {host['id']}: {COORDINATOR_MESSAGE} {ID}")
                COORDINATOR_FOUND = True
                COORDINATOR = ID

            except socket.error:
                print(
                    f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {ID} ] Could not connect to {host['id']}")

    # some node responded with OK. We must wait for COORDINATOR_MESSAGE. If not received, initiate elections again
    for readableSocket in readable:
        msg = readableSocket.recv(HEADER)
        msg_dict = pickle.loads(msg)
        sender = msg_dict['id']
        msg = msg_dict['msg']
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {ID} ] Receive from {sender}: {msg}")

    # wait T_TIMEOUT for coordinator message
    t_wait = 0
    while not COORDINATOR_FOUND:
        time.sleep(0.25)
        t_wait += 0.25
        if t_wait == T_TIMEOUT:
            break

    # initiate another election if received OK but COORDINATOR message timed out
    if t_wait == 10 and not COORDINATOR_FOUND:
        initiate_election()


# method which carries out the ping operation.
# parameter is the node id of the node that will be pinged.
def ping(ping_id):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.settimeout(T_TIMEOUT)

    try:
        client.connect((HOSTS[ping_id]['hostname'], HOSTS[ping_id]['port']))

        msg_dict = {
            'id': ID,
            'msg_type': PING_MESSAGE,
            'msg': ping_id
        }

        client.send(pickle.dumps(msg_dict))

        print(
            f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {ID} ] Receive from Admin user: {PING_MESSAGE} {ping_id}")

        msg = client.recv(HEADER)

        if msg:
            msg_dict = pickle.loads(msg)
            sender = msg_dict['id']
            msg = msg_dict['msg']

            print(
                f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {ID} ] Receive from {sender}: {msg}")
    # if pinged node does not respond within T_TIMEOUT, initiate election
    except socket.timeout:
        print("[ADMIN INTERFACE] Timeout: initiate election.")
        initiate_election()
    # if any other exception occurs, initiate election again
    except socket.error:
        print("[ADMIN INTERFACE] Exception: initiate election.")
        initiate_election()


# Method which provides the text interface to the admin
def admin_interface():

    while True:
        print("[ADMIN INTERFACE] Choose option: Ping Node(1), Election(2), Disconnect(3)")
        admin_choice = input()
        admin_choice = int(admin_choice)

        # if admin chooses to ping another node
        if admin_choice == 1:

            ping_id = ID
            # prompt until we get a valid node id to ping
            while ping_id == ID:
                print("[ADMIN INTERFACE] Enter ID of node you would like to ping")
                admin_in = input()
                ping_id = int(admin_in)
                if ping_id == ID:
                    print("[ADMIN INTERFACE] You can't ping yourself. Enter another value.")

            ping(ping_id)

        # if admin chooses to initiate election
        elif admin_choice == 2:

            initiate_election()

        # if admin chooses to disconnect node. Can be used to simulate crash
        elif admin_choice == 3:
            print(
                f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {ID} ] Receive from Admin user: {DISCONNECT_MESSAGE}")
            os.kill(os.getpid(), signal.SIGKILL)

# method which makes the resource request to the coordinator
def make_request():
    coordinator = HOSTS[COORDINATOR]
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((coordinator['hostname'], coordinator['port']))
        msg_dict = {
            'id': ID,
            'msg_type': REQUEST_MESSAGE,
            'msg': 'Q'
        }
        client.send(pickle.dumps(msg_dict))

        print(
            f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {ID} ] Send to {coordinator['id']}: {REQUEST_MESSAGE}")
    except socket.error:
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {ID} ] Could not connect to {coordinator['id']}")


# method which notifies the coordinator that the node is releasing the resource Q
def release_resource():
    coordinator = HOSTS[COORDINATOR]
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((coordinator['hostname'], coordinator['port']))
        msg_dict = {
            'id': ID,
            'msg_type': RELEASE_MESSAGE,
            'msg': 'Q'
        }
        client.send(pickle.dumps(msg_dict))
        print(
            f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {ID} ] Send to {coordinator['id']}: {RELEASE_MESSAGE}")
    except socket.error:
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {ID} ] Could not connect to {coordinator['id']}")


# method used by the coordinator to grant resource Q access to node with node_id
def grant_access(node_id):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        client.connect((HOSTS[node_id]['hostname'], HOSTS[node_id]['port']))

        msg_dict = {
            'id': ID,
            'msg_type': REQUEST_OK,
            'msg': node_id
        }

        client.send(pickle.dumps(msg_dict))

        print(
            f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {ID} ] Send to {node_id}: {REQUEST_OK}")

    # if any other exception occurs, initiate election again
    except socket.error:
        print(
            f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {ID} ] Could not connect to {node_id}")


# method which performs the next operation in the queue of the node.
def perform_client_operation():
    operation = CLIENT_OPERATION_QUEUE[0]
    CLIENT_OPERATION_QUEUE.remove(operation)

    if operation[0] == 'borrow':
        msg_dict = operation[1]
        conn = operation[2]
        perform_borrow(msg_dict, conn)
    elif operation[0] == 'return':
        msg_dict = operation[1]
        conn = operation[2]
        perform_return(msg_dict, conn)


# method which carries out the borrow functionality
def perform_borrow(msg_dict, conn):
    sender = msg_dict['id']
    msg_type = msg_dict['msg_type']
    msg = msg_dict['msg']

    # check if borrow operation is valid
    if borrow_book(sender, int(msg)):
        borrow_response = "Borrow Successful"

        msg_dict = {
            'id': ID,
            'msg_type': BORROW_SUCCESS,
            'msg': borrow_response
        }
        conn.send(pickle.dumps(msg_dict))

        print(
            f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {ID} ] Update Q - Book {msg}: On loan.")
    else:
        borrow_response = "Borrow Unsuccessful"

        msg_dict = {
            'id': ID,
            'msg_type': BORROW_FAIL,
            'msg': borrow_response
        }
        conn.send(pickle.dumps(msg_dict))


# method which carries out the return functionality.
def perform_return(msg_dict, conn):
    sender = msg_dict['id']
    msg_type = msg_dict['msg_type']
    msg = msg_dict['msg']

    # check if return operation is valid
    if return_book(sender, int(msg)):
        return_response = "Return Successful"

        msg_dict = {
            'id': ID,
            'msg_type': RETURN_SUCCESS,
            'msg': return_response
        }
        conn.send(pickle.dumps(msg_dict))

        print(
            f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {ID} ] Update Q - Book {msg}: Returned.")
    else:
        borrow_response = "Return Unsuccessful"

        msg_dict = {
            'id': ID,
            'msg_type': RETURN_FAIL,
            'msg': borrow_response
        }
        conn.send(pickle.dumps(msg_dict))


# method called by thread spawned after a client has connected to the node.
# it listens for messages and it executes the appropriate functionality
def handle_client(conn, addr):
    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {ID} ] {addr[0]}:{addr[1]} connected.")

    global COORDINATOR_FOUND
    global COORDINATOR
    global ACCESS
    global Q_LOCK

    msg = conn.recv(HEADER)
    if msg:
        msg_dict = pickle.loads(msg)

        sender = msg_dict['id']
        msg_type = msg_dict['msg_type']
        msg = msg_dict['msg']

        print(
            f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {ID} ] Receive from {sender}: {msg_type} {msg}")

        # if ping request made
        if msg_type == PING_MESSAGE:
            ping_response = "Hello from Node " + str(ID)

            msg_dict = {
                'id': ID,
                'msg_type': PING_RESPONSE,
                'msg': ping_response
            }
            conn.send(pickle.dumps(msg_dict))

            print(
                f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {ID} ] Send to {sender}: {PING_RESPONSE} {msg}")

            conn.close()

        # if election message send
        elif msg_type == ELECTION_MESSAGE:
            COORDINATOR_FOUND = False
            election_response = 'OK ' + str(ID)
            msg_dict = {
                'id': ID,
                'msg_type': OK_MESSAGE,
                'msg': election_response
            }
            conn.send(pickle.dumps(msg_dict))
            print(
                f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {ID} ] Send to {sender}: {OK_MESSAGE} {msg}")

            # initiate election
            initiate_election()
            conn.close()

        # if new coordinator message sent
        elif msg_type == COORDINATOR_MESSAGE:
            COORDINATOR = int(msg)
            COORDINATOR_FOUND = True
            conn.close()

        # if a node makes a request for resource Q
        elif msg_type == REQUEST_MESSAGE:
            # make sure we are the coordinator
            if int(COORDINATOR) == int(ID):
                # if request queue is empty, give OK right away
                if not Q_LOCK:
                    grant_access(sender)
                    ACCESS = sender
                    Q_LOCK = True
                # if queue non empty, add the request to the end of the queue
                else:
                    REQUEST_QUEUE.append(sender)
            conn.close()

        # if a node releases resource Q
        elif msg_type == RELEASE_MESSAGE:
            # make sure we are the coordinator
            if COORDINATOR == ID:
                Q_LOCK = False
                # if some request is in the queue
                if len(REQUEST_QUEUE) > 0:
                    next_grant = REQUEST_QUEUE[0]
                    REQUEST_QUEUE.remove(next_grant)
                    ACCESS = next_grant
                    # grant access to the node next in queue
                    grant_access(next_grant)
                    Q_LOCK = True
                # if request queue is empty give access back to coordinator
                else:
                    ACCESS = COORDINATOR
            conn.close()

        # if the node receives access to resource Q
        elif msg_type == REQUEST_OK:
            # perform opertaion
            perform_client_operation()
            # release resource
            release_resource()
            conn.close()

        # if the node receives a borrow update request from client
        elif msg_type == BORROW_UPDATE:
            client_conn = conn
            # if the node has access, perform operation right away
            if int(ACCESS) == int(ID):
                perform_borrow(msg_dict, client_conn)
            # if the node is the coordinator, perform operation right away
            elif COORDINATOR == ID:
                perform_borrow(msg_dict, client_conn)
            else:
                # add operation on the operation queue of the node
                CLIENT_OPERATION_QUEUE.append(('borrow', msg_dict, client_conn))
                # send a request to the coordinator node
                make_request()

        # if the node returns a return update request from client
        elif msg_type == RETURN_UPDATE:
            client_conn = conn
            # if the node has access, perform operation right away
            if int(ACCESS) == int(ID):
                perform_return(msg_dict, client_conn)
            # if the node is the coordinator, perform operation right away
            elif COORDINATOR == ID:
                perform_return(msg_dict, client_conn)
            else:
                # add operation on the operation queue of the node
                CLIENT_OPERATION_QUEUE.append(('return', msg_dict, client_conn))
                # send a request to the coordinator node
                make_request()


# main method of the module. The node will listen for connections and spawn a new thread for each client.
# it will also spawn an additional thread for the admin interface functionality.
def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(ADDR)
    server.listen()

    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {ID} ] Listening on {SERVER}:{PORT}")

    admin_interface_thread = threading.Thread(target=admin_interface)
    admin_interface_thread.start()
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-i', '--id', dest='id', required=True, type=int)
    parser.add_argument('-p', '--port', dest='port', required=True, type=int)
    parser.add_argument('-c', '--coordinator', dest='coordinator', default=5, type=int)

    args = parser.parse_args()
    print(args)

    HOSTS = read_hosts()
    COORDINATOR = args.coordinator
    ACCESS = COORDINATOR
    ID = args.id
    PORT = args.port
    ADDR = (SERVER, PORT)

    sys.stdout = NodeLogger(ID)

    main()
