import random

# Standard deck values
SUITS = ['♠', '♥', '♦', '♣']
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
VALUES = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10, 'J': 10, 'Q': 10, 'K': 10, 'A': 11}

def create_deck():
    """Returns a shuffled list of card dictionaries."""
    # Using 4 decks to simulate a real casino shoe and reduce card counting predictability
    deck = [{'rank': r, 'suit': s, 'value': VALUES[r]} for s in SUITS for r in RANKS] * 4
    random.shuffle(deck)
    return deck

def deal_card(deck):
    """Pops a card off the top of the deck."""
    return deck.pop()

def calculate_hand_value(hand):
    """Calculates the optimal score of a hand, handling Aces appropriately."""
    value = sum(card['value'] for card in hand)
    aces = sum(1 for card in hand if card['rank'] == 'A')
    
    # If we are over 21 and have an Ace, drop the Ace's value from 11 to 1
    while value > 21 and aces > 0:
        value -= 10
        aces -= 1
        
    return value

def is_blackjack(hand):
    """Checks if a 2-card hand is exactly 21."""
    return len(hand) == 2 and calculate_hand_value(hand) == 21

def can_split(hand):
    """Checks if a hand can be split (exactly 2 cards of the same rank)."""
    return len(hand) == 2 and hand[0]['rank'] == hand[1]['rank']

def format_card(card):
    """Returns a nice string representation of a card (e.g., 'A♠')."""
    return f"{card['rank']}{card['suit']}"

def format_hand(hand):
    """Returns a string of the full hand."""
    return " | ".join([format_card(c) for c in hand])