import pygame
import sys
import socket
import threading
from queue import Queue

# Initialize pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 500, 500
SQUARE_SIZE = 120
MARGIN = 20
FONT = pygame.font.Font(None, 40)

# Load images
try:
    blank_image = pygame.image.load('Blank.png')
    x_image = pygame.image.load('x.png')
    o_image = pygame.image.load('o.png')
    Background = pygame.image.load('NewBackground.jpeg')
    Background = pygame.transform.scale(Background, (WIDTH, HEIGHT))
except pygame.error:
    print("Warning: Could not load one or more image files.")
    blank_image = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE))
    blank_image.fill((200, 200, 200))
    x_image = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE))
    x_image.fill((200, 200, 200))
    pygame.draw.line(x_image, (0, 0, 255), (20, 20), (SQUARE_SIZE-20, SQUARE_SIZE-20), 5)
    pygame.draw.line(x_image, (0, 0, 255), (SQUARE_SIZE-20, 20), (20, SQUARE_SIZE-20), 5)
    o_image = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE))
    o_image.fill((200, 200, 200))
    pygame.draw.circle(o_image, (255, 0, 0), (SQUARE_SIZE//2, SQUARE_SIZE//2), SQUARE_SIZE//2-20, 5)
    Background = pygame.Surface((WIDTH, HEIGHT))
    Background.fill((50, 50, 50))

# Create Pygame window
win = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Tic Tac Toe')
clock = pygame.time.Clock()

# Networking variables
HOST = '127.0.0.1'
PORT = 5555
client_socket = None
player_id = None
connected = False
game_started = False

# Queues for thread-safe communication
move_queue = Queue()
status_queue = Queue()

def connect_to_server():
    global client_socket, connected, player_id
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((HOST, PORT))
        connected = True
        print("Connected to server!")
        threading.Thread(target=receive_data, daemon=True).start()
    except Exception as e:
        print(f"Failed to connect: {e}")
        status_queue.put(f"Connection failed: {e}")

def receive_data():
    global player_id, game_started, connected
    while connected:
        try:
            if client_socket:
                data = client_socket.recv(1024*4).decode().strip()
                if not data:
                    status_queue.put("Disconnected from server")
                    break

                print(f"Received from server: {data}")

                if data.startswith("ID:"):
                    player_id = int(data.split(":")[1])
                    status_queue.put(f"You are Player {player_id + 1} ({'X' if player_id == 0 else 'O'})")
                    client_socket.send("READY".encode())

                elif data.startswith("STATE:"):
                    parts = data.split(":")
                    board_data = parts[1].split(",")
                    current_turn = int(parts[2])
                    move_queue.put({"type": "state", "board": board_data, "turn": current_turn})
                    game_started = True

                elif data.startswith("RESULT:"):
                    parts = data.split(":")
                    if parts[1] == "TIE":
                        status_queue.put("Game Over: It's a tie!")
                    elif parts[1] == "WIN":
                        winner = int(parts[2])
                        if winner == player_id:
                            status_queue.put("Game Over: You win!")
                        else:
                            status_queue.put("Game Over: You lose!")
                    move_queue.put({"type": "result"})

                elif data == "RESET":
                    move_queue.put({"type": "reset"})
                    status_queue.put("Game has been reset")

                elif data == "FULL":
                    status_queue.put("Server is full. Try again later.")
                    break

                elif data.startswith("DISCONNECT:"):
                    status_queue.put("The other player has disconnected")
                    break
        except Exception as e:
            print(f"Error receiving data: {e}")
            status_queue.put(f"Connection error: {e}")
            break
    print("Receive thread ended")
    connected = False

def send_move(position):
    if not connected or client_socket is None:
        return False
    try:
        client_socket.send(f"MOVE:{position}".encode())
        return True
    except Exception as e:
        print(f"Error sending move: {e}")
        status_queue.put(f"Failed to send move: {e}")
        return False

def request_reset():
    if connected and client_socket:
        try:
            client_socket.send("RESET".encode())
            return True
        except Exception as e:
            print(f"Error requesting reset: {e}")
            return False
    return False

# Game state variables
current_player = 0
game_over = False
board = [" " for _ in range(9)]
status_message = "Connecting to server..."

class Board(pygame.sprite.Sprite):
    def __init__(self, position):
        super().__init__()
        self.position = position
        self.row = position // 3
        self.col = position % 3
        self.width = SQUARE_SIZE
        self.height = SQUARE_SIZE
        self.x = self.col * self.width + MARGIN
        self.y = self.row * self.height + MARGIN
        self.content = ' '
        self.image = pygame.transform.scale(blank_image, (self.width, self.height))
        self.rect = self.image.get_rect()
        self.rect.topleft = (self.x, self.y)

    def update(self):
        if self.content == "X":
            self.image = pygame.transform.scale(x_image, (self.width, self.height))
        elif self.content == "O":
            self.image = pygame.transform.scale(o_image, (self.width, self.height))
        else:
            self.image = pygame.transform.scale(blank_image, (self.width, self.height))

def update_board_from_server(board_data):
    for i, value in enumerate(board_data):
        board[i] = value
        squares[i].content = value
        squares[i].update()

def update_display():
    win.blit(Background, (0, 0))
    square_group.draw(win)

    text = FONT.render(status_message, True, (255, 255, 255))
    text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT - 30))
    win.blit(text, text_rect)

    if game_over:
        pygame.draw.rect(win, reset_button_color, reset_button_rect, border_radius=10)
        win.blit(reset_button_text, reset_button_text_rect)

    pygame.display.update()

def process_network_messages():
    global current_player, game_over, status_message
    while not status_queue.empty():
        status_message = status_queue.get()
    while not move_queue.empty():
        data = move_queue.get()
        if data["type"] == "state":
            update_board_from_server(data["board"])
            current_player = data["turn"]
            if player_id is not None:
                if current_player == player_id:
                    status_message = "Your turn!"
                else:
                    status_message = "Opponent's turn..."
        elif data["type"] == "reset":
            game_over = False
            board[:] = [" " for _ in range(9)]
            for square in squares:
                square.content = " "
                square.update()
        elif data["type"] == "result":
            game_over = True

# Create board squares
square_group = pygame.sprite.Group()
squares = []
for i in range(9):
    sq = Board(i)
    square_group.add(sq)
    squares.append(sq)

# Connect to the server
connect_to_server()

# Add reset button
reset_button_rect = pygame.Rect(WIDTH - 120, HEIGHT - 60, 100, 40)
reset_button_color = (70, 70, 180)
reset_button_text = FONT.render("Reset", True, (255, 255, 255))
reset_button_text_rect = reset_button_text.get_rect(center=reset_button_rect.center)

# Game loop
run = True
while run:
    clock.tick(60)
    process_network_messages()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()

            if reset_button_rect.collidepoint(mouse_pos) and game_over:
                request_reset()

            if (player_id is not None and current_player == player_id and not game_over 
                    and game_started and connected):
                for square in squares:
                    if square.rect.collidepoint(mouse_pos) and square.content == ' ':
                        if send_move(square.position):
                            pass

    update_display()

pygame.quit()
if client_socket:
    client_socket.close()
sys.exit()
