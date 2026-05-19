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
config_file = "clientconfig.ini"

if not os.path.exists(config_file):
    print(f"Error: Configuration file '{config_file}' not found.")
    sys.exit(1)

config.read(config_file)

server_host = config.get("project3", "serverHost", fallback="127.0.0.1")
server_port = config.getint("project3", "serverPort", fallback=7188)

log_file = config.get("logging", "logFile", fallback="project3-client.log")
log_level = config.get("logging", "logLevel", fallback="INFO").upper()
log_mode = config.get("logging", "logFileMode", fallback="a")

# ----------------------------
# Set Up Logging
# ----------------------------
logging.basicConfig(
    filename=log_file,
    level=getattr(logging, log_level, logging.INFO),
    format="%(asctime)s: %(levelname)s %(message)s",
    filemode=log_mode
)
logging.info("Project3 Client starting")

# ----------------------------
# Valid Commands and Help
# ----------------------------
COMMANDS_REQUIRING_PARAMETER = {"ADD", "CREATE", "DELETE", "REMOVE"}
VALID_COMMANDS = {"ADD", "CREATE", "DELETE", "HELP", "QUIT", "REMOVE", "SHOW"}

#help command
USAGE = """usage:
  add <item>         - Add list item
  create <list name> - Create list
  delete <list name> - Delete list
  help               - Help
  quit               - Quit
  remove <item>      - Remove list item
  show               - Show items"""

# ----------------------------
# Connect to Server
# ----------------------------
try:
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server_host, server_port))
    print(f"Connected to server {server_host}:{server_port}")
    logging.info(f"Connected to server {server_host}:{server_port}")
except Exception as e:
    logging.error(f"Connection failed: {e}")
    print(f"Error: Could not connect to the server: {e}")
    sys.exit(1)

# ----------------------------
# Main Loop
# ----------------------------
while True:
    #prompt user for commands and interact with server
    user_input = input("Enter a command: ").strip()
    logging.info(f"User input: {user_input}")

    if not user_input:
        #no empty input
        print("Error: No command entered.")
        logging.warning("Empty command entered.")
        continue

    tokens = user_input.split()
    command = tokens[0].upper()
    parameter = " ".join(tokens[1:]) if len(tokens) > 1 else ""

    #only server can use this, client use quit
    if command == "SHUTDOWN":
        print("Command error: SHUTDOWN is an invalid command")
        logging.warning("User attempted forbidden SHUTDOWN command.")
        continue

    if command not in VALID_COMMANDS:
        #Handle unknown commands
        print(f"Invalid command entered: {command}\n\n{USAGE}")
        logging.warning(f"Invalid command: {command}")
        continue

    if command in COMMANDS_REQUIRING_PARAMETER and not parameter:
         #reject valid commands with missing arguments
        print(f"Missing element in command: {command}\n\n{USAGE}")
        logging.warning(f"Missing parameter for command: {command}")
        continue

    if command == "HELP":
        print(USAGE)
        logging.info("Displayed HELP usage message.")
        continue

    # ----------------------------
    # Send request to server
    # ----------------------------
    request_json = json.dumps({"command": command, "parameter": parameter})
    try:
        client_socket.sendall(request_json.encode('utf-8'))
        logging.info(f"Sent request: {request_json}")
    except Exception as e:
        logging.error(f"Failed to send request: {e}")
        print(f"Error sending request to server: {e}")
        break

    # ----------------------------
    # Receive and handle server response
    # ----------------------------
    try:
        response_data = client_socket.recv(2048).decode('utf-8')
        response = json.loads(response_data)
        logging.info(f"Received response: {response}")
    except Exception as e:
        logging.error(f"Failed to receive response: {e}")
        print(f"Error receiving response from server: {e}")
        break

    response_type = response.get("response", "").upper()
    response_param = response.get("parameter", "")

    if response_type == "SHOW":
          #display current list items with numbering
        items = response_param.split(";")
        print("List Items:")
        for i, item in enumerate(items, start=1):
            print(f"  {i}. {item.strip()}")
    elif response_type in {"WARNING", "ERROR"}:
          #print and log server-side warning or error
        print(f"{response_type}: {response_param}")
        logging.warning(response_param)
    elif response_type == "SHUTDOWN":
        print("Server requested shutdown. Closing client.")
        break
    else:
        print(response_param)

# ----------------------------
# Cleanup
# ----------------------------
client_socket.close()
logging.info("Client application terminated.")
print("Client terminated.")



