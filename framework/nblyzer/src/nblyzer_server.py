# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import socket
import json
from events import *
from nblyzer import NBlyzer

hostname = 'localhost'
port_no = 9999

def parse_client_message(msg):
    msg_json = json.loads(msg)
    try:
        event = msg_json["event"]
    except:
        return Exception("Invalid message format")

    try:
        params = msg_json["params"]
    except:
        params = None
    try:
        notebook_name = msg_json["notebook_name"]
    except:
        notebook_name = None

    return event, params, notebook_name

def serve():
    nblyzer_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM, proto=0, fileno=None)
    nblyzer_socket.bind((hostname, port_no))
    nblyzer_socket.listen(5)
    nblyzer = defaultdict(NBlyzer)
    shutdown_condition = False

    while True:
        client, client_addr = nblyzer_socket.accept()
        client_message = client.recv(1048576).decode()
        event_str, params, notebook_name = parse_client_message(client_message)
        event = get_event(event_str, params)
        if event:
            result = nblyzer[notebook_name].execute_event(event)
        else:
            client.send("Server is stopping...\n".encode())
            nblyzer_socket.close()
            break
        if result and result.dumps():
            server_message = '{"status":"success","result":' + result.dumps() + '}'
        else:
            server_message = '{"status":"success"}'

        if event_str == "open_notebook":
            shutdown_condition = True

        if event_str == "close_notebook":
            nblyzer.pop(notebook_name)
            if shutdown_condition and not len(nblyzer.keys()):
                client.send('{"status":"terminated"}'.encode())
                nblyzer_socket.close()
                break
                
        client.send(server_message.encode())

def get_event(event_str, params):
    if event_str == "run_cell":
        try:
            return RunCellEvent(params["changed_cell_id"])
        except:
            Exception("Wrong parameters were given")
    elif event_str == "open_notebook":
        try:
            return OpenNotebookEvent(params["notebook_json"])
        except:
            Exception("Wrong parameters were given")
    elif event_str == "add_active_analyses":
        try:
            return AddActiveAnalysesEvent(params["active_analyses"])
        except:
            Exception("Wrong parameters were given")
    elif event_str == "add_cell":
        try:
            return AddCellEvent(params["position"], params["kind"], params["content"])
        except:
            Exception("Wrong parameters were given")
    elif event_str == "remove_cell":
        try:
            return RemoveCellEvent(params["position"])
        except:
            Exception("Wrong parameters were given")
    elif event_str == "change_cell":
        try:
            return ChangeCellCodeEvent(str(params["new_code"]), int(params["cell_index"]), bool(params["with_result"]))
        except:
            Exception("Wrong parameters were given")
    elif event_str == "close_notebook":
        try:
            return CloseNotebookEvent()
        except:
            Exception("Wrong parameters were given")
    else:
        return

if __name__ == "__main__":
    serve()