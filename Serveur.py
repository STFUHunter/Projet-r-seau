import socket
import threading
import time

# Server configuration
HOST = "127.0.0.1"
PORT = 5555
clients = [None, None]
game_state = [" "] * 9
current_turn = 0
game_active = False
lock = threading.Lock()

def send_game_state(player_id):
    if clients[player_id]:
        state_msg = "STATE:" + ",".join(game_state) + ":" + str(current_turn)
        try:
            clients[player_id].send(state_msg.encode())
        except:
            print(f"Failed to send state to Player {player_id + 1}")

def broadcast_game_state():
    for i in range(2):
        send_game_state(i)

def check_winner():
    for i in range(0, 9, 3):
        if game_state[i] != " " and game_state[i] == game_state[i+1] == game_state[i+2]:
            return game_state[i]
    for i in range(3):
        if game_state[i] != " " and game_state[i] == game_state[i+3] == game_state[i+6]:
            return game_state[i]
    if game_state[0] != " " and game_state[0] == game_state[4] == game_state[8]:
        return game_state[0]
    if game_state[2] != " " and game_state[2] == game_state[4] == game_state[6]:
        return game_state[2]
    if all(cell != " " for cell in game_state):
        return "TIE"
    return None

def handle_client(client, player_id):
    global current_turn, game_active
    print(f"Thread started for Player {player_id + 1}")
    other_id = 1 - player_id
    symbol = "X" if player_id == 0 else "O"

    try:
        while not all(clients):
            time.sleep(0.1)

        with lock:
            if player_id == 0 and not game_active:
                game_active = True
                print("Game starts!")
                broadcast_game_state()

        while True:
            try:
                data = client.recv(4096).decode().strip()
                if not data:
                    print(f"Player {player_id + 1} disconnected.")
                    break

                print(f"Received from Player {player_id + 1}: {data}")

                if data.startswith("MOVE:") and current_turn == player_id:
                    try:
                        position = int(data.split(":")[1])
                        with lock:
                            if 0 <= position <= 8 and game_state[position] == " ":
                                game_state[position] = symbol
                                winner = check_winner()
                                if winner:
                                    if winner == "TIE":
                                        broadcast_message("RESULT:TIE")
                                    else:
                                        winning_player = 0 if winner == "X" else 1
                                        broadcast_message(f"RESULT:WIN:{winning_player}")
                                    game_active = False
                                else:
                                    current_turn = other_id
                                broadcast_game_state()
                    except ValueError:
                        print(f"Invalid move format from Player {player_id + 1}")

                elif data == "RESET" and not game_active:
                    with lock:
                        if player_id == 0:
                            reset_game()
                            broadcast_message("RESET")
                            broadcast_game_state()

            except Exception as e:
                print(f"Error with Player {player_id + 1}: {e}")
                break

    finally:
        with lock:
            if clients[player_id] == client:
                clients[player_id] = None
                broadcast_message(f"DISCONNECT:{player_id}")
                game_active = False
        client.close()
        print(f"Connection closed for Player {player_id + 1}")

def broadcast_message(message):
    for i in range(2):
        if clients[i]:
            try:
                clients[i].send(message.encode())
            except:
                print(f"Failed to send message to Player {i + 1}")

def reset_game():
    global game_state, current_turn, game_active
    game_state = [" "] * 9
    current_turn = 0
    game_active = True
    print("Game reset")

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server_socket.bind((HOST, PORT))
        server_socket.listen(2)
        print(f"Server started on {HOST}:{PORT}. Waiting for players...")

        while True:
            client, addr = server_socket.accept()
            player_id = None
            with lock:
                for i in range(2):
                    if clients[i] is None:
                        clients[i] = client
                        player_id = i
                        break
            if player_id is not None:
                print(f"Player {player_id + 1} connected from {addr}")
                client.send(f"ID:{player_id}".encode())
                thread = threading.Thread(target=handle_client, args=(client, player_id), daemon=True)
                thread.start()
            else:
                client.send("FULL".encode())
                client.close()
                print(f"Rejected connection from {addr}: game full")
    except Exception as e:
        print(f"Server error: {e}")
    finally:
        for c in clients:
            if c:
                try:
                    c.close()
                except:
                    pass
        server_socket.close()
        print("Server stopped.")

if __name__ == "__main__":
    start_server()
