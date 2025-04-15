import pygame
import sys
import socket
import threading

# Initialisation de Pygame
pygame.init()

# Constantes
WIDTH, HEIGHT = 500, 500
SQUARE_SIZE = 120
MARGIN = 20
FONT = pygame.font.Font(None, 40)

# Images
blank_image = pygame.image.load('Blank.png')
x_image = pygame.image.load('x.png')
o_image = pygame.image.load('o.png')
Background = pygame.image.load('NewBackground.jpeg')
Background = pygame.transform.scale(Background, (WIDTH, HEIGHT))

# Fenêtre Pygame
win = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Tic Tac Toe')
clock = pygame.time.Clock()

# Connexion au serveur
HOST = "0.0.0.0"
PORT = 5555
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.settimeout(5)

try:
    client_socket.connect((HOST, PORT))
    player_id = int(client_socket.recv(1024).decode())
except Exception as e:
    print(f"Connexion échouée : {e}")
    pygame.quit()
    sys.exit()

current_player = "X" if player_id == 0 else "O"
opponent = "O" if current_player == "X" else "X"
game_over = False
connection_lost = False

board = [[" " for _ in range(3)] for _ in range(3)]

class Board(pygame.sprite.Sprite):
    def __init__(self, x_id, y_id, number):
        super().__init__()
        self.width = SQUARE_SIZE
        self.height = SQUARE_SIZE
        self.x = x_id * self.width + MARGIN
        self.y = y_id * self.height + MARGIN
        self.content = ' '
        self.number = number
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

    def highlight(self):
        pygame.draw.rect(win, (0, 255, 0), self.rect, 3)

def check_winner():
    for row in board:
        if row[0] == row[1] == row[2] and row[0] != " ":
            return row[0]
    for col in range(3):
        if board[0][col] == board[1][col] == board[2][col] and board[0][col] != " ":
            return board[0][col]
    if board[0][0] == board[1][1] == board[2][2] and board[0][0] != " ":
        return board[0][0]
    if board[0][2] == board[1][1] == board[2][0] and board[0][2] != " ":
        return board[0][2]
    if all(board[r][c] != " " for r in range(3) for c in range(3)):
        return "Draw"
    return None

def update_display():
    win.blit(Background, (0, 0))
    square_group.draw(win)

    # Surligner les cases disponibles si c'est notre tour
    if not game_over and current_player == ("X" if player_id == 0 else "O"):
        for square in squares:
            if square.content == ' ' and square.rect.collidepoint(pygame.mouse.get_pos()):
                square.highlight()

    if connection_lost:
        text = FONT.render("Connexion perdue.", True, (255, 0, 0))
    else:
        winner = check_winner()
        if winner:
            msg = "Match nul !" if winner == "Draw" else f"{winner} a gagné !"
            text = FONT.render(msg, True, (255, 255, 255))
            restart = FONT.render("Appuyez sur R pour recommencer", True, (255, 255, 255))
            win.blit(restart, (WIDTH // 2 - 140, HEIGHT - 25))
        else:
            text = FONT.render(f"Tour de : {current_player}", True, (255, 255, 255))

    win.blit(text, (WIDTH // 3 - 20, HEIGHT - 50))
    pygame.display.update()

# Plateau
square_group = pygame.sprite.Group()
squares = []
num = 1
for y in range(3):
    for x in range(3):
        sq = Board(x, y, num)
        square_group.add(sq)
        squares.append(sq)
        num += 1

def send_move(row, col):
    try:
        client_socket.send(f"{row},{col}".encode())
    except:
        global connection_lost
        connection_lost = True

def receive_move():
    global game_over, current_player, connection_lost
    try:
        while True:
            data = client_socket.recv(1024)
            if not data:
                connection_lost = True
                break
            row, col = map(int, data.decode().split(','))
            board[row][col] = opponent
            squares[row * 3 + col].content = opponent
            squares[row * 3 + col].update()
            game_over = check_winner() is not None
            if not game_over:
                current_player = opponent
    except:
        connection_lost = True

threading.Thread(target=receive_move, daemon=True).start()

def reset_game():
    global board, game_over, current_player
    board = [[" " for _ in range(3)] for _ in range(3)]
    for square in squares:
        square.content = ' '
        square.update()
    game_over = False
    current_player = "X" if player_id == 0 else "O"

# Boucle principale
run = True
while run:
    clock.tick(60)

    if connection_lost:
        run = False
        break

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

        if event.type == pygame.KEYDOWN and game_over:
            if event.key == pygame.K_r:
                reset_game()

        if event.type == pygame.MOUSEBUTTONDOWN and not game_over and current_player == ("X" if player_id == 0 else "O"):
            mx, my = pygame.mouse.get_pos()
            for square in squares:
                if square.rect.collidepoint(mx, my) and square.content == ' ':
                    r, c = (square.number - 1) // 3, (square.number - 1) % 3
                    board[r][c] = current_player
                    square.content = current_player
                    square.update()
                    send_move(r, c)
                    game_over = check_winner() is not None
                    if not game_over:
                        current_player = opponent

    update_display()

pygame.quit()
sys.exit()
