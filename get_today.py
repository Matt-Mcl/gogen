from helper import *

# get_tables()
urls = read_tables()

puzzle_board = get_board(urls[0][0])
solution_board = get_board(urls[0][1])
words = get_words(urls[0][0])

print((urls[0], words, puzzle_board, solution_board))

