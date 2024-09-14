import discord
from discord.ext import commands
import random

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)


games = {}

CONNECT4_ROWS = 6
CONNECT4_COLS = 6

def display_board(board):

    board_str = '\n'.join([' | '.join(row) for row in board])
    return f"```\n{board_str}\n```"

def check_winner(board):

    lines = [
        board[0], board[1], board[2],  # Rows
        [board[0][0], board[1][0], board[2][0]],  # Columns
        [board[0][1], board[1][1], board[2][1]],
        [board[0][2], board[1][2], board[2][2]],
        [board[0][0], board[1][1], board[2][2]],  # Diagonals
        [board[0][2], board[1][1], board[2][0]],
    ]
    for line in lines:
        if line == ['X', 'X', 'X']:
            return 'X'
        elif line == ['O', 'O', 'O']:
            return 'O'
    return None

def bot_move_tictactoe(board):

    empty_spots = [(r, c) for r in range(3) for c in range(3) if board[r][c] == ' ']
    if empty_spots:
        return random.choice(empty_spots)
    return None

def bot_move_connect4(board):

    valid_columns = [c for c in range(CONNECT4_COLS) if board[0][c] == ' ']
    if valid_columns:
        return random.choice(valid_columns)
    return None

@bot.command()
async def start(ctx, player2: discord.Member = None):

    board = [[' ' for _ in range(3)] for _ in range(3)]
    opponent = bot.user if player2 is None else player2
    games[ctx.channel.id] = {
        'board': board,
        'turn': ctx.author,
        'players': [ctx.author, opponent],
        'type': 'tictactoe'
    }
    await ctx.send(f'Tic-Tac-Toe game started between {ctx.author.mention} and {opponent.mention if opponent != bot.user else "the bot"}!\n{display_board(board)}')
    if opponent == bot.user and games[ctx.channel.id]['turn'] == bot.user:
        await tictactoe_bot_move(ctx)

@bot.command()
async def connect4(ctx, player2: discord.Member = None):

    board = [[' ' for _ in range(CONNECT4_COLS)] for _ in range(CONNECT4_ROWS)]
    opponent = bot.user if player2 is None else player2
    games[ctx.channel.id] = {
        'board': board,
        'turn': ctx.author,
        'players': [ctx.author, opponent],
        'type': 'connect4'
    }
    await ctx.send(f'Connect 4 game started between {ctx.author.mention} and {opponent.mention if opponent != bot.user else "the bot"}!\n{display_board(board)}')
    if opponent == bot.user and games[ctx.channel.id]['turn'] == bot.user:
        await connect4_bot_move(ctx)

@bot.command()
async def move(ctx, *args):

    game = games.get(ctx.channel.id)
    if not game:
        await ctx.send('No game is active. Use !start or !connect4 to begin.')
        return
    if game['turn'] != ctx.author:
        await ctx.send(f"It's not your turn, {ctx.author.mention}!")
        return

    if game['type'] == 'tictactoe':
        if len(args) != 2:
            await ctx.send('Please provide row and column for Tic-Tac-Toe (e.g., `!move 1 1`).')
            return
        try:
            row = int(args[0])
            col = int(args[1])
        except ValueError:
            await ctx.send('Row and column must be integers.')
            return
        await tictactoe_move(ctx, row, col)
    elif game['type'] == 'connect4':
        if len(args) != 1:
            await ctx.send('Please provide a column for Connect 4 (e.g., `!move 2`).')
            return
        try:
            col = int(args[0])
        except ValueError:
            await ctx.send('Column must be an integer.')
            return
        await connect4_move(ctx, col)

async def tictactoe_move(ctx, row: int, col: int):

    game = games.get(ctx.channel.id)
    if not (0 <= row < 3 and 0 <= col < 3):
        await ctx.send('Row and column must be between 0 and 2.')
        return
    if game['board'][row][col] != ' ':
        await ctx.send('That spot is already taken.')
        return
    marker = 'X' if game['turn'] == game['players'][0] else 'O'
    game['board'][row][col] = marker
    await process_turn(ctx)

async def connect4_move(ctx, col: int):

    game = games.get(ctx.channel.id)
    if not (0 <= col < CONNECT4_COLS):
        await ctx.send('Column must be between 0 and 5.')
        return
    if game['board'][0][col] != ' ':
        await ctx.send('This column is full.')
        return

    for row in range(CONNECT4_ROWS - 1, -1, -1):
        if game['board'][row][col] == ' ':
            marker = 'X' if game['turn'] == game['players'][0] else 'O'
            game['board'][row][col] = marker
            break
    await process_turn(ctx)

async def process_turn(ctx):

    game = games.get(ctx.channel.id)
    board_display = display_board(game['board'])

    if game['type'] == 'tictactoe':
        winner = check_winner(game['board'])
    elif game['type'] == 'connect4':
        winner = check_connect4_winner(game['board'])

    if winner:
        await ctx.send(f'{board_display}\n{game["turn"].mention} wins!')
        del games[ctx.channel.id]
        return

    if all(space != ' ' for row in game['board'] for space in row):
        await ctx.send(f'{board_display}\nIt\'s a draw!')
        del games[ctx.channel.id]
        return


    game['turn'] = game['players'][1] if game['turn'] == game['players'][0] else game['players'][0]

    await ctx.send(f'{board_display}\nNow {game["turn"].mention}\'s turn!')


    if game['turn'] == bot.user:
        if game['type'] == 'tictactoe':
            await tictactoe_bot_move(ctx)
        elif game['type'] == 'connect4':
            await connect4_bot_move(ctx)

async def tictactoe_bot_move(ctx):

    game = games.get(ctx.channel.id)
    move = bot_move_tictactoe(game['board'])
    if move:
        row, col = move
        game['board'][row][col] = 'O'
        await process_turn(ctx)
    else:
        await ctx.send('Bot cannot make a move. The game is a draw!')
        del games[ctx.channel.id]

async def connect4_bot_move(ctx):

    game = games.get(ctx.channel.id)
    col = bot_move_connect4(game['board'])
    if col is not None:
        # Drop the checker into the column
        for row in range(CONNECT4_ROWS - 1, -1, -1):
            if game['board'][row][col] == ' ':
                game['board'][row][col] = 'O'
                break
        await process_turn(ctx)
    else:
        await ctx.send('Bot cannot make a move. The game is a draw!')
        del games[ctx.channel.id]

def check_connect4_winner(board):


    for r in range(CONNECT4_ROWS):
        for c in range(CONNECT4_COLS - 3):
            if board[r][c] != ' ' and board[r][c] == board[r][c+1] == board[r][c+2] == board[r][c+3]:
                return board[r][c]

    for r in range(CONNECT4_ROWS - 3):
        for c in range(CONNECT4_COLS):
            if board[r][c] != ' ' and board[r][c] == board[r+1][c] == board[r+2][c] == board[r+3][c]:
                return board[r][c]
 
    for r in range(3, CONNECT4_ROWS):
        for c in range(CONNECT4_COLS - 3):
            if board[r][c] != ' ' and board[r][c] == board[r-1][c+1] == board[r-2][c+2] == board[r-3][c+3]:
                return board[r][c]
    
    for r in range(CONNECT4_ROWS - 3):
        for c in range(CONNECT4_COLS - 3):
            if board[r][c] != ' ' and board[r][c] == board[r+1][c+1] == board[r+2][c+2] == board[r+3][c+3]:
                return board[r][c]
    return None

@bot.command()
async def stop(ctx):
    """Stop the current game."""
    if ctx.channel.id in games:
        del games[ctx.channel.id]
        await ctx.send('Game stopped.')
    else:
        await ctx.send('No game is currently active in this channel.')
        
        
#bot.run(insert your bot token here.)
