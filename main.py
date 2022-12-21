import threading
from requests.models import Response
from telegram import Update, ParseMode, User
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, PollAnswerHandler
from telegram.ext.filters import Filters
import json
from datetime import datetime
from random import randint, shuffle

#Session Dictionaries:
players = {}
gameIsActive = {}
NumberOfActiveCards = {}
pollIds = {}
maxCount = {}

#Getters and setters for the sessions:
def getPlayers(chatId):
    global players
    return players.get(chatId) or []

def setPlayers(newPlayers, chatId):
    global players
    players[chatId] = newPlayers

def getMaxCount(chatId):
    global maxCount
    if maxCount.get(chatId) == None:
        setMaxCount(100, chatId)
    return maxCount.get(chatId)

def setMaxCount(newMaxCount, chatId):
    global maxCount
    maxCount[chatId] = newMaxCount

def getGameIsActive(chatId):
    global gameIsActive
    return gameIsActive.get(chatId)

def setGameIsActive(newGameIsActive, chatId):
    global gameIsActive
    gameIsActive[chatId] = newGameIsActive

def getNumberOfActiveCards(chatId):
    global NumberOfActiveCards
    if NumberOfActiveCards.get(chatId) == None:
        setNumberOfActiveCards(50, chatId)
    return NumberOfActiveCards.get(chatId)

def setNumberOfActiveCards(newNumberOfActiveCards, chatId):
    global NumberOfActiveCards
    NumberOfActiveCards[chatId] = newNumberOfActiveCards

def start_thread(id):
    print("")

def thread_exist(chatId):
    threadExist = False
    for thread in threading.enumerate(): 
        if thread.name == str(chatId):
            threadExist = True
            break
    return threadExist

def start_handler(update: Update, context: CallbackContext):
    global pollIds
    setPlayers([],update.effective_chat.id)
    message = update.message.reply_poll("Let's start a game! Who's in?\nType /startGame whenever you want to start", ["I'm in!", "Nope"], False)
    pollIds[message.poll.id] = update.effective_chat.id

def startGame_handler(update: Update, context: CallbackContext):

    if getGameIsActive(update.effective_chat.id):
        update.message.reply_text("The game has already started 😐")
        return

    NumberOfActiveCards = getNumberOfActiveCards(update.effective_chat.id)
    players = getPlayers(update.effective_chat.id)

    if players.__len__() < 2:
        update.message.reply_text("Not enough players have joined 😅")

    numbers = list(range(1,getMaxCount(update.effective_chat.id)))
    while numbers.__len__() > NumberOfActiveCards:
        numbers.pop(randint(0, numbers.__len__()-1))

    shuffle(numbers)

    for playerIndex in range(0, players.__len__()):
        players[playerIndex][1] = []
        for _ in range(0, NumberOfActiveCards // players.__len__()):
            players[playerIndex][1].append(numbers.pop(0))
        if numbers.__len__() == 1:
            players[playerIndex][1].append(numbers.pop(0))

    update.message.reply_text(f"The game has started\nThe rules are:\nWe count from 0 to {getMaxCount(update.effective_chat.id)}\nWe play with {getNumberOfActiveCards(update.effective_chat.id)} active cards\nHers's your cards\. *Only open your own name\!*", parse_mode='MarkdownV2')
    for player in players:
        player[1].sort()
        update.message.reply_text(player[0].full_name + " cards: ||" + str(player[1]) + "||", parse_mode='MarkdownV2')
    
    setPlayers(players, update.effective_chat.id)
    setGameIsActive(True, update.effective_chat.id)

def stop_handler(update: Update, context: CallbackContext):
    setPlayers([],update.effective_chat.id)
    setGameIsActive(False, update.effective_chat.id)
    update.message.reply_text("The game has stopped")

def message_handler(update: Update, context: CallbackContext):
    if getGameIsActive(update.effective_chat.id) == False:
        return

def active_cards_handler(update: Update, context: CallbackContext):
    if getGameIsActive(update.effective_chat.id) == True:
        update.message.reply_text("Too late to edit active cards now. The game has already begun 🙃")
    try:
        number = int(update.message.text.split(" ")[1])
        maxNumber = int(getMaxCount(update.effective_chat.id))
        if number < 2 or number >= maxNumber:
            update.message.reply_text(f"Invalid number. It shoukd be between 2 and {maxNumber-1}")
            return
        setNumberOfActiveCards(number, update.effective_chat.id)

        update.message.reply_text(f"New number of active cards in the game: {number}")
    except:
        update.message.reply_text("That didn't work. Format you sentence like so: /activeCards 50")

def show_cards(update: Update, context: CallbackContext):
    update.message.reply_text(f"Hers's your cards again. Only open your own name!")
    for player in players:
        player[1].sort()
        update.message.reply_text(player[0].full_name + " cards: ||" + str(player[1]) + "||", parse_mode='MarkdownV2')

def number_handler(update: Update, context: CallbackContext):
    if getGameIsActive(update.effective_chat.id) == False:
        return
    number = int(update.message.text)
    players : list = getPlayers(update.effective_chat.id)
    lowestNumber = 999
    personWithLowestNumber : User = players[0][0]
    for i in range(0,players.__len__() - 1):
        playerCards : list = players[i][1]
        if playerCards[0] != None and playerCards[0] < lowestNumber:
            lowestNumber = playerCards[0]
            personWithLowestNumber = players[i][0]
        if playerCards[0] == number:
            players[i][1].pop(0)

    if (number != lowestNumber or personWithLowestNumber.id != update.effective_user.id):
        setPlayers([],update.effective_chat.id)
        setGameIsActive(False, update.effective_chat.id)
        update.message.reply_text(f"You lost! The lowest number was: {str(lowestNumber)}, owned by {personWithLowestNumber.full_name}")
    else:
        setPlayers(players, update._effective_chat.id)
        #update.message.reply_text("✅")

def answerRegistered(update: Update, context: CallbackContext):
    global pollIds
    chatId = pollIds.get(update.poll_answer.poll_id)

    players = getPlayers(chatId)
    if update.poll_answer.option_ids.__len__() == 0:
        for i in range(players.__len__() - 1, -1, -1):
            if players[i][0].id == update.poll_answer.user.id:
                players.pop(i)
                setPlayers(players, chatId)
                print(f"Removed player {update.poll_answer.user.full_name} from the player list")

    elif update.poll_answer.option_ids[0] == 0:
        players.append([update.poll_answer.user,[]])
        setPlayers(players, chatId)
        print(f"Added {update.poll_answer.user.full_name} to the players list")

def get_bot_config(): 
    f = open('botConfig.json')
    botConfig = json.load(f)
    f.close()
    return botConfig

def help_handler(update: Update, context: CallbackContext):
    update.message.reply_text('Welcome!\n/setup -> Setup a new game\n/startGame -> start the game\n/stop -> Stop the game\n/showCards -> Show the cards every person have left\n/activeCards [number] -> Set the number of cards to be in the game')

updater = Updater(get_bot_config()["apiKey"])

updater.dispatcher.add_handler(CommandHandler('setup', start_handler))
updater.dispatcher.add_handler(CommandHandler('startGame', startGame_handler))
updater.dispatcher.add_handler(CommandHandler('stop', stop_handler))
updater.dispatcher.add_handler(CommandHandler('showCards', show_cards))
updater.dispatcher.add_handler(CommandHandler('activeCards', active_cards_handler))
updater.dispatcher.add_handler(CommandHandler('help', help_handler))
updater.dispatcher.add_handler(CommandHandler('start', help_handler))
updater.dispatcher.add_handler(PollAnswerHandler(answerRegistered))
updater.dispatcher.add_handler(MessageHandler(Filters.regex(r'([0-9])*'), number_handler))

print("Starting telegram polling...")
updater.start_polling()
updater.idle()