import pygame
import sys
import random
import numpy as np
from gym import Env, spaces
from stable_baselines3 import PPO  
import os

# Initialize pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 500, 500
SQUARE_SIZE = 120
MARGIN = 20
FONT = pygame.font.Font(None, 40)

# Load images
blank_image = pygame.image.load('Blank.png')
x_image = pygame.image.load('x.png')
o_image = pygame.image.load('o.png')
Background = pygame.image.load('NewBackground.jpeg')
Background = pygame.transform.scale(Background, (WIDTH, HEIGHT))

# Create Pygame window
win = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Tic Tac Toe')
clock = pygame.time.Clock()

# Game variables
current_player = "X"
game_over = False
board = [[" " for _ in range(3)] for _ in range(3)]

class TicTacToeEnv(Env):
    def __init__(self):
        super(TicTacToeEnv, self).__init__()
        self.action_space = spaces.Discrete(9)
        self.observation_space = spaces.Box(low=0, high=2, shape=(9,), dtype=np.int32)
        self.reset()
        
    def reset(self):
        self.board = [" " for _ in range(9)]
        self.current_player = "X"
        self.done = False
        return self._get_obs()
    
    def _get_obs(self):
        obs = [0 if cell == " " else 1 if cell == "X" else 2 for cell in self.board]
        return np.array(obs, dtype=np.int32)
    
    def step(self, action):
        if self.done or self.board[action] != " ":
            return self._get_obs(), -10, True, {}

        self.board[action] = self.current_player
        winner = self._check_winner()
        if winner:
            self.done = True
            reward = 1 if winner == "O" else -1 if winner == "X" else 0
            return self._get_obs(), reward, True, {}

        self.current_player = "O" if self.current_player == "X" else "X"
        return self._get_obs(), 0, False, {}
    
    def _check_winner(self):
        b = self.board
        for i in range(0, 9, 3):
            if b[i] == b[i+1] == b[i+2] != " ": return b[i]
        for i in range(3):
            if b[i] == b[i+3] == b[i+6] != " ": return b[i]
        if b[0] == b[4] == b[8] != " ": return b[0]
        if b[2] == b[4] == b[6] != " ": return b[2]
        if " " not in b: return "Draw"
        return None

def train_model(total_timesteps=50000, save_path="tictactoe_model"):
    env = TicTacToeEnv()
    model = PPO("MlpPolicy", env, verbose=1)
    model.learn(total_timesteps=total_timesteps)
    model.save(save_path)
    print(f"Model trained and saved to {save_path}")

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
        if board[0][col] == board[1][col] == board[2][col] != " ":
            return board[0][col]
    if board[0][0] == board[1][1] == board[2][2] != " ":
        return board[0][0]
    if board[0][2] == board[1][1] == board[2][0] != " ":
        return board[0][2]
    if all(board[r][c] != " " for r in range(3) for c in range(3)):
        return "Draw"
    return None

# Load or train model
if os.path.exists("tictactoe_model.zip"):
    model = PPO.load("tictactoe_model")
else:
    train_model()
    model = PPO.load("tictactoe_model")

def ai_move():
    obs = [0 if cell == " " else 1 if cell == "X" else 2 for row in board for cell in row]
    obs = np.array(obs, dtype=np.int32)
    for _ in range(10):
        action, _ = model.predict(obs)
        r, c = action // 3, action % 3
        if board[r][c] == " ":
            board[r][c] = "O"
            squares[r * 3 + c].content = "O"
            squares[r * 3 + c].update()
            return True
    return False

def update_display():
    win.blit(Background, (0, 0))
    square_group.draw(win)
    for square in squares:
        if square.rect.collidepoint(pygame.mouse.get_pos()) and square.content == ' ' and current_player == "X" and not game_over:
            square.highlight()

    winner = check_winner()
    if winner:
        text = FONT.render(f'{winner} wins!' if winner != "Draw" else "It\'s a draw!", True, (255, 255, 255))
        win.blit(text, (WIDTH // 3, HEIGHT - 50))
        reset_text = FONT.render("Press R to restart", True, (255, 255, 255))
        win.blit(reset_text, (WIDTH // 3 - 40, HEIGHT - 20))
    else:
        turn_text = FONT.render(f"Turn: {current_player}", True, (255, 255, 255))
        win.blit(turn_text, (WIDTH // 3, HEIGHT - 50))

    pygame.display.update()

# Create board squares
square_group = pygame.sprite.Group()
squares = []
num = 1
for y in range(3):  
    for x in range(3):
        sq = Board(x, y, num)
        square_group.add(sq)
        squares.append(sq)
        num += 1 

# Game loop
run = True
game_over = False
while run:
    clock.tick(60)
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

        if event.type == pygame.MOUSEBUTTONDOWN and not game_over:
            mx, my = pygame.mouse.get_pos()
            for square in squares:
                if square.rect.collidepoint(mx, my) and square.content == ' ' and current_player == "X":
                    r, c = (square.number - 1) // 3, (square.number - 1) % 3
                    square.content = "X"
                    board[r][c] = "X"
                    square.update()
                    game_over = check_winner() is not None
                    current_player = "O" if not game_over else "X"
                    if not game_over:
                        ai_move()
                        game_over = check_winner() is not None
                        current_player = "X"

        if event.type == pygame.KEYDOWN and game_over:
            if event.key == pygame.K_r:
                board = [[" " for _ in range(3)] for _ in range(3)]
                for square in squares:
                    square.content = ' '
                    square.update()
                current_player = "X"
                game_over = False

    update_display()

pygame.quit()
sys.exit()
