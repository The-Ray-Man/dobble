import socket
from threading import Thread
from queue import Queue
import random
import time
import os


size = 7
def test(card_list):
    for card in card_list:
        for check_card in card_list:
            if card != check_card:
                counter = 0
                for elm in card:
                    if elm in check_card:
                        counter += 1
                if counter != 1:
                    return False
    return True


def generateVectors(size):
    vectors = []
    for i in range(1, size):
        vectors.append((i,1))
    
    return vectors


def fanoplane(size):

    List = [[i+size*j for i in range(size)] for j in range(size)]
    List2 = [size*size+i for i in range(size+1)]

    vectors = generateVectors(size)
    card_list = []
    for l in List:
        newList = l[:]
        newList.append(List2[0])
        card_list.append(newList)


    for i in range(size):
        newList = []
        for j in range(size):
            newList.append(List[j][i])
        newList.append(List2[-1])
        card_list.append(newList)


    for i in range(len(vectors)):
        x,y = vectors[i]
        x_pos = 0
        y_pos = 0
        for offset in range(size):
            x_pos = offset
            new_List = []
            for step in range(size):
                new_List.append(List[(x_pos+step*x)%size][(y_pos+step*y)%size])
            new_List.append(List2[i+1])
            card_list.append(new_List)

    card_list.append(List2)

    return card_list
cards = fanoplane(size)


##---------------------------------------SERVERCONFIG----------------------------------------------------------------------------


##Protocol:

"""
|catagory|Info|

"$" between objects

=> Start                START|.
=> Setup                USERID|userid
=> Card Stack           CARDSTACK|cardstack
=> new active Card      ACTIVCARD|picturelist|list_of_playerscore
=> end                  END|winner
=> countdown            COUNTDOWN|second
=> ready                READY|userid
"""

num_players = 1
ip = "localhost"
port = 5772
input_queue = Queue(maxsize=0)
output_queu = Queue(maxsize=0)

newplayer_queue = Queue(maxsize=0)

serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

serverSocket.bind((ip,port))

def listen(socket,queue):
    
    while True:

        socket.listen(5)
        connection, address = serverSocket.accept()
        queue.put(connection)

def recv_from(socket,queue):
    
    while True:
        msg = socket.recv(1024)
        queue.put(msg)

for i in range(1):
    loading = True
    players = []
    user_ready = []
    Thread(target=listen, args=[serverSocket,newplayer_queue]).start()
    while loading:
        if not newplayer_queue.empty():
            connection = newplayer_queue.get()
            connection.send(("$USERID|"+str(len(players))).encode("utf-8"))
            players.append(connection)
            Thread(target=recv_from,args=[connection,input_queue]).start()

        if not input_queue.empty():
            
            msg = input_queue.get().decode("utf-8")
            msg_split = msg.split("|")
            print(msg)
            if msg_split[0] == "READY":
                user_ready.append(int(msg_split[1]))
            if len(user_ready) == len(players):

                for card in cards:
                    random.shuffle(card)
                    
                random.shuffle(cards)

                active_card = cards.pop()
                player_cardlist = [[] for player in players]
                for i in range(len(cards)):
                    player_cardlist[i%len(players)].append(cards[i])

                for p in range(len(players)):
                    player_cardlist_join = []
                    for card in player_cardlist[p]:
                        card_join = ":".join([str(imageId) for imageId in card])
                        player_cardlist_join.append(card_join)
                    encoded_message = "#".join(player_cardlist_join)
                    send_message = "$CARDSTACK|"+encoded_message
                    players[p].send(send_message.encode("utf-8"))
                    
                msg_activ_card = "$ACTIVECARD|"+":".join([str(imageId) for imageId in active_card])
                msg_score = "|"+":".join(["0"] * len(players))
                for player in players:
                    player.send((msg_activ_card+msg_score).encode("utf-8"))
                for i in range(5, 0, -1):
                    msg_countdown = "$COUNTDOWN|"+str(i)
                    for player in players:
                        player.send(msg_countdown.encode("utf-8"))
                    time.sleep(1)
                for player in players:
                    player.send("$START|.".encode("utf-8"))
                loading = False

 # Add demons = True

    score = [0] * len(players)

    while True:
        if not input_queue.empty():
            msg = input_queue.get().decode("utf-8")
            msg_split = msg.split("|")
            if msg_split[0] == "CARDPLAYED":
                actor = int(msg_split[1])
                score[actor] += 1
                active_card = player_cardlist[actor].pop()
                msg_activ_card = "$ACTIVECARD|"+":".join([str(imageId) for imageId in active_card])
                msg_score = "|"+":".join([str(points) for points in score])
                for player in players:
                    player.send((msg_activ_card+msg_score).encode("utf-8"))
                print(score)
                
                if len(player_cardlist[actor]) == 1:
                    print("player won!")
                    msg_won = "$END|"+str(actor)
                    for player in players:
                        player.send(msg_won.encode("utf-8"))



    print("restart")