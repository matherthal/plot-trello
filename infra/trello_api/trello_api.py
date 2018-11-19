#!/usr/bin/env python
import requests

from resources.config import Config

def get_cards(sprint_start, trello_board):
    """
    Request cards informations from the API
    """

    url_cards = 'https://api.trello.com/1/boards/{}/cards/?key={}&token={}'
    url_cards = url_cards.format(trello_board, Config.TRELLO_KEY, 
        Config.TRELLO_TOKEN)

    cards = None
    r = requests.get(url_cards)
    if r.status_code == 200:
        cards = r.json()
    else:
        raise Exception("Error in trello get cards. StatusCode: {}.\
            Message: {}".format(r.status_code, r.content))

    
    # For each card we request from the API the last action of type 'updateCard' 
    # which contains information regarding the change of board. 
    # If it's unknown we set the sprint_start for this column
    
    url_card_list = 'https://api.trello.com/1/cards/{}/actions?'\
        'filter=updateCard:idList&limit=1&key={}&token={}'

    for card in cards:
        url_card_info = url_card_list.format(card['id'], 
            Config.TRELLO_KEY, Config.TRELLO_TOKEN)

        r = requests.get(url_card_info)
        if r.status_code == 200:
            card_info = r.json()
            if card_info is None or len(card_info) < 1:
                card['last_move_date'] = sprint_start
            else:
                card['last_move_date'] = card_info[0]['date']
        else:
            raise Exception("Error in trello get cards. StatusCode: {}.\
                Message: {}".format(r.status_code, r.content))
    
    # Also for each card we request the action 'createCard' which contains the 
    # card creation date. If it is unknown or the date is before the 
    # sprint_start then we use the sprint_start.
    url_card_createdat = 'https://api.trello.com/1/cards/{}/actions?\
        filter=createCard&key={}&token={}'

    for c in cards:
        url_card_info = url_card_createdat.format(c['id'], 
            Config.TRELLO_KEY, Config.TRELLO_TOKEN)

        r = requests.get(url_card_info)
        if r.status_code == 200:
            card_info = r.json()
            if card_info is None or len(card_info) < 1:
                c['create_date'] = sprint_start
            else:
                dt = card_info[0]['date']
                c['create_date'] = sprint_start if dt < sprint_start else dt

    return cards

def get_lists(board):
    """
    Get the board's lists
    """
    url_lists = 'https://api.trello.com/1/boards/{}/lists/?key={}&token={}'
    url_lists = url_lists.format(board, Config.TRELLO_KEY, Config.TRELLO_TOKEN)
    r = requests.get(url_lists)
    if r.status_code == 200:
        board_lists = r.json()
    else:
        raise Exception("Error in trello get cards. StatusCode: {}.\
            Message: {}".format(r.status_code, r.content))
    
    return board_lists
