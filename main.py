import pygame
from pygame.locals import *
import sys

WHITE = True
BLACK = False
BISHOP = "B"
KNIGHT = "N"
KING = "K"
QUEEN = "Q"
ROOK = "R"
PAWN = "P"
LONG_CASTLE = 0
SHORT_CASTLE = 1
EN_PASSANT = 2
PROMOTION = 3
DARK_COLOR = (182,136,100)
LIGHT_COLOR = (239,216,182)
OFFSET = (100, 100)
SQUARE_SIZE = 100

def is_valid_position(pos):
        col, row = pos
        return col >= 0 and col <= 7 and row >= 0 and row <= 7

def get_square_under_cursor():
        cursor_vector = pygame.Vector2(pygame.mouse.get_pos()) - OFFSET
        square_col = int(cursor_vector[0] // SQUARE_SIZE)
        square_row = int(cursor_vector[1] // SQUARE_SIZE)
        pos = (square_col, square_row)
        if is_valid_position(pos): return pos
        return -1, -1

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
        self.has_moved = False
    
    def move(self, pos):
        self.has_moved = True
        self.change_pos(pos)
        self.rect.update(pos[0]*SQUARE_SIZE, pos[1]*SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
    
    def change_pos(self, pos):
        col, row = pos
        self.col = col
        self.row = row

    def draw(self, surface, pos = None):
        if pos:
            surface.blit(self.image, pos)
        else:
            surface.blit(self.image, self.rect)

class Board(pygame.surface.Surface):
    def __init__(self):
        super().__init__((SQUARE_SIZE*8, SQUARE_SIZE*8))
        self.board = []
        self.valid_moves = []
        for col in range(8):
            self.board.append([])
            self.valid_moves.append([])
            for row in range(8):
                self.board[col].append(None)
                self.valid_moves.append([])
        self.selected = None
        self.turn = WHITE
        self.last_move = None
        self.last_selected = None
        self.last_selected_moves = []
        self.transparent_surface = pygame.Surface((SQUARE_SIZE*8, SQUARE_SIZE*8), pygame.SRCALPHA)

    
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
                if (col, row) in self.last_selected_moves:
                    circle_color = (0, 0, 0, 100)
                    pygame.draw.circle(
                        self.transparent_surface, 
                        circle_color, 
                        (col*SQUARE_SIZE + SQUARE_SIZE // 2, row*SQUARE_SIZE + SQUARE_SIZE // 2,),
                        SQUARE_SIZE // 5
                        )
        if self.selected:
            cursor_vector = pygame.Vector2(pygame.mouse.get_pos()) - OFFSET - (SQUARE_SIZE // 2, SQUARE_SIZE // 2)
            self.selected.draw(self, cursor_vector)
        self.blit(self.transparent_surface, (0, 0))


    def draw(self, surface):
        surface.blit(self, OFFSET)

    def get_piece(self, pos, board = None):
        if board == None:
            board = self.board
        col, row = pos
        if is_valid_position(pos) and board[col][row]:
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
            self.last_move = (piece, lastpos, pos)
    
    def board_if_move(self, piece, pos):
        if piece:
            newboard = [col[:] for col in self.board]
            newboard[piece.col][piece.row] = None
            newboard[pos[0]][pos[1]] = piece
            return newboard
    
    def update_valid_moves(self, side):
        self.valid_moves = []
        for col in range(8):
            self.valid_moves.append([])
            for row in range(8):
                self.valid_moves.append([])
                piece = self.board[col][row]
                if piece and piece.side == side:
                    moves = self.get_valid_moves(piece)
                    if self.get_valid_moves(piece):
                        self.valid_moves[col][row] = moves

    def select_piece(self, piece):
        if piece:
            self.selected = piece
            self.transparent_surface.fill((0,0,0,0))
            self.last_selected = piece
            self.last_selected_moves = self.get_valid_moves(piece)

    def attempt_move(self, piece, pos):
        if piece:
            if is_valid_position(pos) and piece.side == self.turn:
                validity = self.is_valid_move(piece, pos)
                if validity:
                    if type(validity) is tuple:
                        match validity[0]:
                            case 0:
                                self.move_piece(piece, (2, piece.row))
                                self.move_piece(validity[1], (3, piece.row))
                            case 1:
                                self.move_piece(piece, (6, piece.row))
                                self.move_piece(validity[1], (5, piece.row))
                            case 2:
                                self.move_piece(piece, pos)
                                self.remove_piece(validity[1])
                    else: self.move_piece(piece, pos)
                    self.turn = not self.turn
                    self.last_selected = None
                    self.last_selected_moves = []
                    self.transparent_surface.fill((0,0,0,0))
                    if self.is_in_checkmate(not piece.side):
                        winner = "White" if piece.side == WHITE else "Black"
                        print(winner + " wins!")
                    return True
        return False

    def click(self, pos):
        if not is_valid_position(pos):
            return None
        piece = self.get_piece(pos)
        if piece and piece.side == self.turn:
            self.select_piece(piece)
        else:
            self.attempt_move(self.last_selected, pos)

    def unclick(self, pos):
        col, row = pos
        if self.selected:
            self.attempt_move(self.selected, pos)
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
                if piece and piece.side != side:
                    if self.is_possible_move(piece, (king.col, king.row), board):
                        return True
        return False
    
    def is_in_checkmate(self, side):
        for col in range(8):
            for row in range(8):
                piece = self.board[col][row]
                if piece and piece.side == side:
                    if self.get_valid_moves(piece):
                        return False
        return True
        
    
    def get_valid_diagonals(self, piece, board, m=8):
        directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
        oldpos = (piece.col, piece.row)
        possible_moves = []
        for direction in directions:
            limit = m
            pos = tuple(map(lambda x, y: x + y, oldpos, direction))
            while limit > 0 and is_valid_position(pos):
                piece_to_capture = self.get_piece(pos, board)
                if not piece_to_capture:
                    possible_moves.append(pos)
                else:
                    if piece_to_capture.side != piece.side:
                        possible_moves.append(pos)
                    break
                pos = tuple(map(lambda x, y: x + y, pos, direction))
                limit -= 1
        return possible_moves
    
    def get_valid_straights(self, piece, board, m=8):
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        oldpos = (piece.col, piece.row)
        possible_moves = []
        for direction in directions:
            limit = m
            pos = tuple(map(lambda x, y: x + y, oldpos, direction))
            while limit > 0 and is_valid_position(pos):
                piece_to_capture = self.get_piece(pos, board)
                if not piece_to_capture:
                    possible_moves.append(pos)
                else:
                    if piece_to_capture.side != piece.side:
                        possible_moves.append(pos)
                    break
                pos = tuple(map(lambda x, y: x + y, pos, direction))
                limit -= 1
        return possible_moves

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
    
    def is_special_move(self, piece, pos):
        oldcol, oldrow = piece.col, piece.row
        col, row = pos
        if piece.type == PAWN:
            if oldrow != row and oldcol != col and not self.get_piece(pos):
                return EN_PASSANT
            

    def get_possible_moves(self, piece, board = None):
        if board == None:
            board = self.board
        oldcol, oldrow = piece.col, piece.row
        possible_moves = []
        if piece:
            match piece.type:
                case "P":
                    pos_to_check = [(oldcol - 1, oldrow + (1 if piece.side == BLACK else -1)), (oldcol + 1, oldrow + (1 if piece.side == BLACK else -1))]
                    for pos in pos_to_check:
                        piece_to_capture = self.get_piece(pos, board)
                        if piece_to_capture and piece_to_capture.side != piece.side:
                            possible_moves.append(pos)
                        if self.last_move:
                            lastpiece, lastold, lastnew = self.last_move
                            if lastpiece.type == PAWN and lastpiece.side != piece.side and lastold[0] == pos[0] and abs(lastnew[1] - lastold[1]) == 2 and lastnew[1] == oldrow:
                                possible_moves.append(pos)
                    forward_pos = (oldcol, oldrow + (1 if piece.side == BLACK else -1))
                    if not self.get_piece(forward_pos, board):
                        possible_moves.append(forward_pos)
                        next_forward_pos = (oldcol, oldrow + (2 if piece.side == BLACK else -2))
                        if not self.get_piece(next_forward_pos, board) and oldrow == (1 if piece.side == BLACK else 6):
                            possible_moves.append(next_forward_pos)
                case "N":
                    pos_to_check = [(oldcol + 1, oldrow + 2), 
                                    (oldcol + 1, oldrow - 2), 
                                    (oldcol + 2, oldrow + 1), 
                                    (oldcol + 2, oldrow - 1), 
                                    (oldcol - 1, oldrow + 2), 
                                    (oldcol - 1, oldrow - 2), 
                                    (oldcol - 2, oldrow + 1), 
                                    (oldcol - 2, oldrow - 1)]
                    for pos in pos_to_check:
                        piece_to_capture = self.get_piece(pos, board)
                        if not piece_to_capture or piece_to_capture.side != piece.side:
                            possible_moves.append(pos)
                case "B":
                    possible_moves.extend(self.get_valid_diagonals(piece, board))
                case "R":
                    possible_moves.extend(self.get_valid_straights(piece, board))
                case "Q":
                    possible_moves.extend(self.get_valid_diagonals(piece, board))
                    possible_moves.extend(self.get_valid_straights(piece, board))
                case "K":
                    possible_moves.extend(self.get_valid_diagonals(piece, board, 1))
                    possible_moves.extend(self.get_valid_straights(piece, board, 1))
                    if not piece.has_moved and not self.is_in_check(piece.side):
                        if self.is_valid_straight((oldcol, oldrow), (0, oldrow), board):
                            rook_to_castle = self.get_piece((0, oldrow))
                            if rook_to_castle and rook_to_castle.type == ROOK and rook_to_castle.side == piece.side and not rook_to_castle.has_moved:
                                possible_moves.extend([(i, oldrow) for i in range(3)])
                        if self.is_valid_straight((oldcol, oldrow), (7, oldrow), board):
                            rook_to_castle = self.get_piece((7, oldrow))
                            if rook_to_castle and rook_to_castle.type == ROOK and rook_to_castle.side == piece.side and not rook_to_castle.has_moved:
                                possible_moves.extend([(6, oldrow), (7, oldrow)])
                case _:
                    return False
        return possible_moves
    
    def get_valid_moves(self, piece, board = None):
        if board == None:
            board = self.board
        possible_moves = self.get_possible_moves(piece, board)
        valid_moves = []
        for pos in possible_moves:
            if not is_valid_position(pos): continue
            oldpos = (piece.col, piece.row)
            newboard = self.board_if_move(piece, pos)
            piece.change_pos(pos)
            if not self.is_in_check(piece.side, newboard):
                valid_moves.append(pos)
            piece.change_pos(oldpos)
        return valid_moves
    
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
        if piece and is_valid_position(pos):
            match piece.type:
                case "P":
                    if oldcol == col + 1 or oldcol == col - 1:
                        if (piece.side == WHITE and oldrow == row + 1) or (piece.side == BLACK and oldrow == row - 1):
                            if piece_to_capture:
                                return True
                            if self.last_move:
                                lastpiece, lastold, lastnew = self.last_move
                                if lastpiece.type == PAWN and lastpiece.side != piece.side and lastold[0] == col and abs(lastnew[1] - lastold[1]) == 2 and lastnew[1] == oldrow:
                                    return (EN_PASSANT, lastpiece)
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
                    if not piece.has_moved and oldrow == row and not self.is_in_check(piece.side):
                        
                        direction = col - oldcol
                        if (direction == -2 or direction == -3 or direction == -4) and self.is_valid_straight((oldcol, oldrow), (0, oldrow), board):
                            rook_to_castle = self.get_piece((0, oldrow))
                            if rook_to_castle and rook_to_castle.type == ROOK and rook_to_castle.side == piece.side and not rook_to_castle.has_moved:
                                return (LONG_CASTLE, rook_to_castle)
                        if (direction == 2 or direction == 3) and self.is_valid_straight((oldcol, oldrow), (7, oldrow), board):
                            rook_to_castle = self.get_piece((7, oldrow))
                            if rook_to_castle and rook_to_castle.type == ROOK and rook_to_castle.side == piece.side and not rook_to_castle.has_moved:
                                return (SHORT_CASTLE, rook_to_castle)
                    return False
                case _:
                    return False
        return False
    
    def is_valid_move(self, piece, pos):
        possible = self.is_possible_move(piece, pos)
        if possible:
            oldpos = (piece.col, piece.row)
            newboard = self.board_if_move(piece, pos)
            piece.change_pos(pos)
            if self.is_in_check(piece.side, newboard):
                possible = False
            piece.change_pos(oldpos)
        return possible



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
                board_surface.click(square)
            if event.type == MOUSEBUTTONUP:
                square = get_square_under_cursor()
                board_surface.unclick(square)
                
        board_surface.update()
        board_surface.draw(surface)
        pygame.display.update()

if __name__ == '__main__':
    main()

"""
TODO: Castling, Animate Click-Click Moves, Add cache for valid movess
"""