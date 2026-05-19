# TCP List Manager

A client-server list management application built with Python sockets. Commands are exchanged as JSON over a persistent TCP connection.

Built for **CSE 3421** — Introduction to Computer Networking.

## Overview

The server maintains named lists in memory and processes commands from a connected client. The client validates user input locally, sends well-formed JSON requests over TCP, and displays the server's response. If a list is active when the server shuts down, its state is saved to disk and restored on the next launch.

## Architecture

```
┌──────────────┐     JSON over TCP      ┌──────────────┐
│   p3c.py     │ ◄──────────────────► │   p3s.py     │
│   (Client)   │    port 7188          │   (Server)   │
│              │                       │              │
│ • Input      │   { "command": "ADD", │ • List CRUD  │
│   validation │     "parameter": "" } │ • State      │
│ • Display    │                       │   persistence│
└──────────────┘                       └──────────────┘
```

**Request format:**
```json
{ "command": "ADD", "parameter": "milk" }
```

**Response format:**
```json
{ "response": "ADD", "parameter": "'milk' added to list 'groceries'." }
```

## Commands

| Command | Usage | Description |
|---------|-------|-------------|
| `create` | `create <name>` | Create a new list and set it as active |
| `add` | `add <item>` | Add an item to the active list |
| `remove` | `remove <item>` | Remove an item from the active list |
| `show` | `show` | Display all items in the active list |
| `delete` | `delete <name>` | Delete a list by name |
| `help` | `help` | Show available commands |
| `quit` | `quit` | Save state and shut down the server |

## Getting Started

### 1. Start the server

```bash
python p3s.py
```

The server reads from `serverconfig.ini` and begins listening on the configured host and port (default `127.0.0.1:7188`).

### 2. Connect the client

```bash
python p3c.py
```

The client reads from `clientconfig.ini` and connects to the server.

### 3. Try it out

```
Enter a command: create groceries
List 'groceries' created and selected.

Enter a command: add milk
'milk' added to list 'groceries'.

Enter a command: add eggs
'eggs' added to list 'groceries'.

Enter a command: show
List Items:
  1. milk
  2. eggs

Enter a command: remove milk
'milk' removed from list.

Enter a command: quit
Server requested shutdown. Closing client.
```

## Configuration

Both the server and client are configured through `.ini` files:

**serverconfig.ini / clientconfig.ini**
```ini
[project3]
serverHost = 127.0.0.1
serverPort = 7188

[logging]
logFile = project3-server.log
logLevel = INFO
logFileMode = a
```

## Project Structure

```
├── p3s.py              # Server — listens for connections and processes commands
├── p3c.py              # Client — takes user input and communicates with server
├── serverconfig.ini    # Server configuration
├── clientconfig.ini    # Client configuration
└── README.md
```

## Key Concepts Demonstrated

- Persistent TCP socket connections (`socket.AF_INET`, `socket.SOCK_STREAM`)
- JSON-based application-layer protocol over raw sockets
- Client-side input validation before network transmission
- Server-side state management with disk persistence
- Configurable logging with Python's `logging` module
- Graceful shutdown with state serialization

## Built With

- Python 3
- `socket` — TCP networking
- `json` — message serialization
- `configparser` — configuration management
- `logging` — structured logging
