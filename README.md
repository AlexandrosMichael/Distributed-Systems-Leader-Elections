# Leader elections and mutual exclusion - Distributed Systems

## Virtual environment

This part along with the installation instructions are optional because as of now, the distributed system is implemented with modules from the Python standard library only. They were included for following 'best practices'.

Create a virtual environment
```bash
python3 -m venv virtualenv
```

Activate the virtual environment

```bash
source virtualenv/bin/activate
```

## Installation

Installing all the pip packages

```bash
pip3 install -r requirements.txt
```

## Initialise book library

In order to initialise the resource representing the library, run the following in the command line:

```bash
python create_books.py
```
This will create 10 books with ID's from 1 to 10, and it will save them as a file in the resources directory. Run this just once as running it restores the state of the library to the initial state, erasing all of the library records of borrows and returns.

## Node Settings

Within the nodes.csv file, we provide the details of each node, including the id, hostname and port on which they'll be listening on. In order to run these on your personal machine for testing, change the hostname to match your inet address. This can be found by running the following command:

```bash
ifconfig
```

## Running Nodes

After the right node settings have been set, we are ready to get the nodes running. They can be run as follows:

```bash
python node.py -i <node_id> -p <port_number>
```
It is important that we follow the same id-port mapping found in the nodes.csv file. For example node with id=1 should be listening on port=5001, node with id=2 should be listening on port=5002 and so on until the node with id=5. 

At this point the node will be up and running and it will also provide an admin interface, as required.

## Running Clients

To run the client and connect it to a node run the following:

```bash
python client.py -u <username> -n <designated_node_id>
```
Where <username> is used to identify a client within the library records and <designated_node_id> is the id  of the node to  which the client will connect and make requests. 

At this point the client will be able to make requests and the distributed system will fulfil them.

## Logs

Logs are automatically created and stored within the logs directory.

