import socket
import json
import configparser
import logging
import os
import sys

# ----------------------------
# Load Configuration
# ----------------------------
config = configparser.ConfigParser()
config_file = "serverconfig.ini"
if not os.path.exists(config_file):
    print(f"Error: Configuration file '{config_file}' not found.")
    sys.exit(1)

config.read(config_file)

server_host = config.get("project3", "serverHost", fallback="127.0.0.1")
server_port = config.getint("project3", "serverPort", fallback=7188)

log_file = config.get("logging", "logFile", fallback="project3-server.log")
log_level = config.get("logging", "logLevel", fallback="INFO").upper()
log_mode = config.get("logging", "logFileMode", fallback="a")

# ----------------------------
# Setup Logging
# ----------------------------
logging.basicConfig(
    filename=log_file,
    level=getattr(logging, log_level, logging.INFO),
    format="%(asctime)s: %(levelname)s %(message)s",
    filemode=log_mode
)
logging.info("Project3 Server starting")
print("Server starting...")

# ----------------------------
# Server State Initialization
# ----------------------------
lists = {}  # Holds all created lists
current_list = None
saved_file = "saved_list.json"

# Try loading saved list
if os.path.exists(saved_file):
    with open(saved_file, 'r') as f:
        try:
            data = json.load(f)
            lists = data.get("lists", {})
            current_list = data.get("current_list", None)
            logging.info("Loaded saved list from previous session.")
        except Exception as e:
            logging.warning(f"Failed to load saved list: {e}")

# ----------------------------
# Create Server Socket
# ----------------------------
try:
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # For Errno 98
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((server_host, server_port))
    server_socket.listen(5)
    logging.info(f"Server listening on {server_host}:{server_port}")
    print(f"Listening on {server_host}:{server_port}")
except Exception as e:
    logging.error(f"Socket error: {e}")
    print(f"Server could not start: {e}")
    sys.exit(1)

# ----------------------------
# Accept Connections
# ----------------------------
while True:
    client_socket, client_address = server_socket.accept()
    logging.info(f"Accepted connection from {client_address}")
    print(f"Accepted connection from {client_address}")

    try:
        while True:
              #read and decode incoming data from the connected client
            data = client_socket.recv(2048).decode("utf-8")
            if not data:
                logging.warning("Received empty data.")
                break

            try:
                 #parse command and parameter from the JSON-encoded client request
                request = json.loads(data)
                command = request.get("command", "").upper()
                parameter = request.get("parameter", "").strip()
            except json.JSONDecodeError:
                logging.error("Invalid JSON format.")
                break

            logging.info(f"Received: {command} {parameter}")
            response = {"response": "", "parameter": ""}


            # ----------------------------
            # Command Handling
            # ----------------------------
            if command == "CREATE":
                #Validate and create new list, if the list does not exist already
                if not parameter:
                    response["response"] = "ERROR"
                    response["parameter"] = "Missing list name for CREATE."
                elif parameter in lists:
                    response["response"] = "WARNING"
                    response["parameter"] = f"List '{parameter}' already exists. You cannot create a duplicate."
                elif current_list:
                    response["response"] = "ERROR"
                    response["parameter"] = f"List '{current_list}' is currently active. DELETE it before creating a new one."
                else:
                    lists[parameter] = []
                    current_list = parameter
                    response["response"] = "CREATE"
                    response["parameter"] = f"List '{parameter}' created and selected."

            elif command == "ADD":
                  #add an item to the currently selected list
                if not current_list:
                    response["response"] = "ERROR"
                    response["parameter"] = "No list selected. Use CREATE first."
                elif not parameter:
                    response["response"] = "ERROR"
                    response["parameter"] = "Missing item to ADD."
                elif parameter in lists[current_list]:
                    response["response"] = "WARNING"
                    response["parameter"] = f"'{parameter}' already exists in list."
                else:
                    lists[current_list].append(parameter)
                    response["response"] = "ADD"
                    response["parameter"] = f"'{parameter}' added to list '{current_list}'."

            elif command == "REMOVE":
                 #remove an item from the currently selected list
                if not current_list:
                    response["response"] = "ERROR"
                    response["parameter"] = "No list selected."
                elif not parameter:
                    response["response"] = "ERROR"
                    response["parameter"] = "Missing item to REMOVE."
                elif parameter not in lists[current_list]:
                    response["response"] = "WARNING"
                    response["parameter"] = f"'{parameter}' not found in list."
                else:
                    lists[current_list].remove(parameter)
                    response["response"] = "REMOVE"
                    response["parameter"] = f"'{parameter}' removed from list."

            elif command == "DELETE":
                #delete a list only if there is an list
                if not parameter:
                    response["response"] = "ERROR"
                    response["parameter"] = "Missing list name for DELETE."
                elif parameter not in lists:
                    response["response"] = "WARNING"
                    response["parameter"] = f"List '{parameter}' does not exist."
                else:
                    del lists[parameter]
                    if current_list == parameter:
                        current_list = None
                    response["response"] = "DELETE"
                    response["parameter"] = f"List '{parameter}' deleted."

            elif command == "SHOW":
                #show what is in the list
                if not current_list:
                    response["response"] = "ERROR"
                    response["parameter"] = "No list selected."
                elif not lists[current_list]:
                    response["response"] = "SHOW"
                    response["parameter"] = "(list is empty)"
                else:
                    formatted = "; ".join(lists[current_list])
                    response["response"] = "SHOW"
                    response["parameter"] = formatted

            elif command == "QUIT":
                if current_list:
                    try:
                        with open(saved_file, 'w') as f:
                            json.dump({
                                "lists": lists,
                                "current_list": current_list
                            }, f)
                        logging.info("Saved list state to disk.")
                    except Exception as e:
                        logging.warning(f"Could not save list: {e}")
                else:
                    if os.path.exists(saved_file):
                        try:
                            os.remove(saved_file)
                            logging.info("Deleted saved_list.json because no active list remains.")
                        except Exception as e:
                            logging.warning(f"Could not delete saved list file: {e}")
                    
                response["response"] = "SHUTDOWN"
                response["parameter"] = "Server shutting down."
                client_socket.sendall(json.dumps(response).encode("utf-8"))
                logging.info("Shutting down server.")
                client_socket.close()
                server_socket.close()
                sys.exit(0)

            else:
                # Handle unrecognized commands
                response["response"] = "ERROR"
                response["parameter"] = f"Unsupported command: {command}"

            # ----------------------------
            # Send Response
            # ----------------------------
            try:
                client_socket.sendall(json.dumps(response).encode("utf-8"))
            except Exception as e:
                logging.error(f"Error sending response: {e}")
                break

        client_socket.close()
        logging.info("Closed client socket.")

    except Exception as e:
        logging.error(f"Client handling error: {e}")
        client_socket.close()