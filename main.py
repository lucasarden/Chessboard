import pygame
from pygame.locals import *
import sys

WHITE = 0
BLACK = 1
BISHOP = "B"
KNIGHT = "N"
KING = "K"
QUEEN = "Q"
ROOK = "R"
PAWN = "P"
DARK_COLOR = (182,136,100)
LIGHT_COLOR = (239,216,182)
OFFSET = (100, 100)
SQUARE_SIZE = 100



class Piece(pygame.sprite.Sprite):
    def __init__(self, type, side, pos):
        super().__init__()
        col, row = pos
        image_name = "piece_images/" + ("w" if side == WHITE else "b") + type.lower() + ".png"
        self.image = pygame.image.load(image_name)
        self.image = pygame.transform.scale(self.image, (SQUARE_SIZE, SQUARE_SIZE))
        self.rect = pygame.Rect(col*SQUARE_SIZE, row*SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
        self.side = side
        self.col = col
        self.row = row
        self.type = type
    
    def move(self, pos):
        col, row = pos
        self.col = col
        self.row = row
        self.rect.update(col*SQUARE_SIZE, row*SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)

    def draw(self, surface, pos = None):
        if pos:
            surface.blit(self.image, pos)
        else:
            surface.blit(self.image, self.rect)

class Board(pygame.surface.Surface):
    def __init__(self):
        super().__init__((SQUARE_SIZE*8, SQUARE_SIZE*8))
        self.board = []
        for col in range(8):
            self.board.append([])
            for row in range(8):
                self.board[col].append(None)
        self.selected = None
        self.turn = WHITE
        self.lastmove = None

    
    def clear_board(self):
        for col in self.board:
            for piece in col:
                piece = None
    
    def starting_position(self):
        self.clear_board()
        for i in range(8):
            self.put(Piece(PAWN, WHITE, (i, 6)))
            self.put(Piece(PAWN, BLACK, (i, 1)))
        self.put(Piece(ROOK, BLACK, (0, 0)))
        self.put(Piece(ROOK, BLACK, (7, 0)))
        self.put(Piece(KNIGHT, BLACK, (1, 0)))
        self.put(Piece(KNIGHT, BLACK, (6, 0)))
        self.put(Piece(BISHOP, BLACK, (2, 0)))
        self.put(Piece(BISHOP, BLACK, (5, 0)))
        self.put(Piece(QUEEN, BLACK, (3, 0)))
        self.put(Piece(KING, BLACK, (4, 0)))

        self.put(Piece(ROOK, WHITE, (0, 7)))
        self.put(Piece(ROOK, WHITE, (7, 7)))
        self.put(Piece(KNIGHT, WHITE, (1, 7)))
        self.put(Piece(KNIGHT, WHITE, (6, 7)))
        self.put(Piece(BISHOP, WHITE, (2, 7)))
        self.put(Piece(BISHOP, WHITE, (5, 7)))
        self.put(Piece(QUEEN, WHITE, (3, 7)))
        self.put(Piece(KING, WHITE, (4, 7)))
    
    def put(self, piece):
        self.board[piece.col][piece.row] = piece
    
    def update(self):
        for col in range(8):
            for row in range(8):
                color = LIGHT_COLOR if (col + row) % 2 == 0 else DARK_COLOR
                pygame.draw.rect(self, color , pygame.Rect(
                    col*SQUARE_SIZE, 
                    row*SQUARE_SIZE, 
                    SQUARE_SIZE,
                    SQUARE_SIZE))
                if self.board[col][row] and self.board[col][row] != self.selected:
                    self.board[col][row].draw(self)
        if self.selected:
            cursor_vector = pygame.Vector2(pygame.mouse.get_pos()) - OFFSET - (SQUARE_SIZE // 2, SQUARE_SIZE // 2)
            self.selected.draw(self, cursor_vector)


    def draw(self, surface):
        surface.blit(self, OFFSET)
    
    

    def get_piece(self, pos, board = None):
        if board == None:
            board = self.board
        col, row = pos
        if col >= 0 and row >= 0 and board[col][row]:
            return board[col][row]
        else:
            return None
    
    def remove_piece(self, piece):
        self.board[piece.col][piece.row] = None
        
    def move_piece(self, piece, pos):
        if piece:
            lastpos = (piece.col, piece.row)
            self.remove_piece(piece)
            self.board[pos[0]][pos[1]] = piece
            piece.move(pos)
            if self.turn == WHITE:
                self.turn = BLACK
            else: 
                self.turn = WHITE
            self.lastmove = (piece, lastpos, pos)
    
    def board_if_move(self, piece, pos):
        if piece:
            newboard = [col[:] for col in self.board]
            newboard[piece.col][piece.row] = None
            newboard[pos[0]][pos[1]] = piece
            return newboard

    def select_piece(self, piece):
        if piece:
            self.selected = piece  

    def drop_selected(self, pos):
        col, row = pos
        piece = self.selected
        if piece:
            if col >= 0 and piece.side == self.turn:
                validity = self.is_valid_move(piece, pos)
                if validity:
                    self.move_piece(piece, pos)
                    if type(validity) is tuple:
                        piece_to_capture = self.get_piece(validity)
                        self.remove_piece(piece_to_capture)
            self.selected = None
    
    def is_in_check(self, side, board = None):
        if board == None:
            board = self.board

        for col in range(8):
            for row in range(8):
                piece = board[col][row]
                if piece and piece.type == KING and piece.side == side:
                    king = board[col][row]
                    
        for col in range(8):
            for row in range(8):
                piece = board[col][row]
                if piece and piece.side == (BLACK if side == WHITE else WHITE):
                    if self.is_possible_move(piece, (king.col, king.row), board):
                        return True
        return False

    def is_valid_diagonal(self, oldpos, pos, board):
        
        col, row = pos
        oldcol, oldrow = oldpos
        coldif = col - oldcol
        rowdif = row - oldrow
        coli = 1 if coldif > 0 else -1
        rowi = 1 if rowdif > 0 else -1
        if abs(coldif) == abs(rowdif):
            for i in range(1, abs(coldif)):
                if self.get_piece((oldcol + i * coli, oldrow + i * rowi), board):
                    return False
            return True
            
        return False
    
    def is_valid_straight(self, oldpos, pos, board):
        col, row = pos
        oldcol, oldrow = oldpos
        coldif = col - oldcol
        rowdif = row - oldrow
        coli = 1 if coldif > 0 else -1
        rowi = 1 if rowdif > 0 else -1
        if coldif == 0 or rowdif == 0:
            for i in range(1, abs(coldif) if rowdif == 0 else abs(rowdif)):
                if coldif == 0 and self.get_piece((oldcol, oldrow + i * rowi), board):
                    return False
                if rowdif == 0 and self.get_piece((oldcol + i * coli, oldrow), board):
                    return False
            return True
        return False
    
    def is_possible_move(self, piece, pos, board = None):
        if board == None:
            board = self.board
        col, row = pos
        oldcol, oldrow = piece.col, piece.row
        if oldcol == col and oldrow == row:
            return False
        piece_to_capture = self.get_piece(pos, board)
        if piece_to_capture and piece_to_capture.side == piece.side:
            return False
        if piece and col >= 0 and row >= 0:
            match piece.type:
                case "P":
                    if oldcol == col + 1 or oldcol == col - 1:
                        if (piece.side == WHITE and oldrow == row + 1) or (piece.side == BLACK and oldrow == row - 1):
                            if piece_to_capture:
                                return True
                            if self.lastmove:
                                lastpiece, lastold, lastnew = self.lastmove
                                if lastpiece.type == PAWN and lastpiece.side != piece.side and lastold[0] == col and abs(lastnew[1] - lastold[1]) == 2 and lastnew[1] == oldrow:
                                    return (lastpiece.col, lastpiece.row)
                        return False
                    elif oldcol == col:
                        if piece.side == WHITE:
                            if oldrow == row + 1 and not piece_to_capture:
                                return True
                            if oldrow == row + 2 and oldrow == 6 and not piece_to_capture and not self.get_piece((col, row + 1), board):
                                return True
                        if piece.side == BLACK:
                            if oldrow == row - 1 and not piece_to_capture:
                                return True
                            if oldrow == row - 2 and oldrow == 1 and not piece_to_capture and not self.get_piece((col, row - 1), board):
                                return True
                        return False
                    return False
                case "N":
                    if (oldcol == col + 1 or oldcol == col - 1) and (oldrow == row + 2 or oldrow == row - 2):
                        return True
                    if (oldcol == col + 2 or oldcol == col - 2) and (oldrow == row + 1 or oldrow == row - 1):
                        return True
                    return False
                case "B":
                    return self.is_valid_diagonal((oldcol, oldrow), pos, board)
                case "R":
                    return self.is_valid_straight((oldcol, oldrow), pos, board)
                case "Q":
                    return self.is_valid_diagonal((oldcol, oldrow), pos, board) or self.is_valid_straight((oldcol, oldrow), pos, board)
                case "K":
                    if (abs(col - oldcol) <= 1) and (abs(row - oldrow) <= 1):
                        return True
                    return False
                case _:
                    return False
        return False
    
    def is_valid_move(self, piece, pos):
        possible = self.is_possible_move(piece, pos)
        if possible:
            oldpos = (piece.col, piece.row)
            newboard = self.board_if_move(piece, pos)
            piece.move(pos)
            if self.is_in_check(piece.side, newboard):
                possible = False
            piece.move(oldpos)
        return possible

        
            
def get_square_under_cursor():
        cursor_vector = pygame.Vector2(pygame.mouse.get_pos()) - OFFSET
        square_row = int(cursor_vector[1] // SQUARE_SIZE)
        square_col = int(cursor_vector[0] // SQUARE_SIZE)
        if square_col >= 0 and square_row >= 0 and square_col <= 7 and square_row <= 7: return (square_col, square_row)
        return -1, -1

def main():
    pygame.init()

    FPS = pygame.time.Clock()
    FPS.tick(144)

    surface = pygame.display.set_mode((1000,1000))
    board_surface = Board()

    surface.fill(pygame.Color('lightblue'))

    board_surface.starting_position()


    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == MOUSEBUTTONDOWN:
                square = get_square_under_cursor()
                piece = board_surface.get_piece(square)
                if piece:
                    board_surface.select_piece(piece)
            if event.type == MOUSEBUTTONUP:
                square = get_square_under_cursor()
                board_surface.drop_selected(square)
                
        board_surface.update()
        board_surface.draw(surface)
        pygame.display.update()

if __name__ == '__main__':
    main()

"""
TODO: Castling, Detect Checkmate
"""