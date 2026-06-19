import random
from collections import Counter
import itertools

SUITS = ['♠', '♥', '♦', '♣']
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
RANK_VALUES = {r: i for i, r in enumerate(RANKS, 2)}

def create_deck():
    """Returns a shuffled standard 52-card deck."""
    deck = [{'rank': r, 'suit': s, 'value': RANK_VALUES[r]} for s in SUITS for r in RANKS]
    random.shuffle(deck)
    return deck

def deal_cards(deck, num=1):
    """Pops a specified number of cards off the deck."""
    return [deck.pop() for _ in range(num)]


def deal_biased_cards(deck, num=1, luck=0, favor_high=True, preferred_ranks=None):
    """Deal cards using luck-based candidate selection.

    This gives the caller a way to slightly improve or reduce expected hand
    strength by selecting from multiple random candidates per draw.
    """
    dealt = []
    luck = max(0, int(luck))
    preferred = set(preferred_ranks or [])

    for _ in range(num):
        if not deck:
            break
        if luck == 0 or len(deck) == 1:
            dealt.append(deck.pop())
            continue

        # 0-100 luck scale: reaches max candidate pool near 100 luck.
        candidate_count = min(len(deck), 1 + min(4, luck // 25))
        candidate_indexes = random.sample(range(len(deck)), k=candidate_count)
        def _score(card):
            return card["value"] + (3 if card["rank"] in preferred else 0)

        if favor_high:
            chosen_index = max(candidate_indexes, key=lambda i: _score(deck[i]))
        else:
            chosen_index = min(candidate_indexes, key=lambda i: _score(deck[i]))
        dealt.append(deck.pop(chosen_index))

    return dealt

def evaluate_5_card_hand(hand):
    """
    Scores a 5-card hand. 
    Returns a tuple: (Rank Score, Tie-Breaker List, String Name)
    Using a tuple allows Python to automatically compare and resolve ties.
    """
    values = sorted([c['value'] for c in hand], reverse=True)
    suits = [c['suit'] for c in hand]
    is_flush = len(set(suits)) == 1

    # Check for straights
    is_straight = False
    straight_high = 0
    if len(set(values)) == 5 and values[0] - values[-1] == 4:
        is_straight = True
        straight_high = values[0]
    # Special case: The "Wheel" straight (A, 2, 3, 4, 5)
    elif values == [14, 5, 4, 3, 2]:
        is_straight = True
        straight_high = 5

    # Count frequencies for pairs, trips, quads
    counts = Counter(values)
    # Sort by frequency first, then by the card value
    freqs = sorted([(count, val) for val, count in counts.items()], reverse=True)
    freq_counts = [f[0] for f in freqs]
    freq_vals = [f[1] for f in freqs]

    # Return structured scorings (0 to 8)
    if is_flush and is_straight: return (8, [straight_high], "Straight Flush")
    if freq_counts == [4, 1]: return (7, freq_vals, "Four of a Kind")
    if freq_counts == [3, 2]: return (6, freq_vals, "Full House")
    if is_flush: return (5, values, "Flush")
    if is_straight: return (4, [straight_high], "Straight")
    if freq_counts == [3, 1, 1]: return (3, freq_vals, "Three of a Kind")
    if freq_counts == [2, 2, 1]: return (2, freq_vals, "Two Pair")
    if freq_counts == [2, 1, 1, 1]: return (1, freq_vals, "Pair")
    return (0, values, "High Card")

def get_best_hand(hole_cards, community_cards):
    """Generates all 21 combinations of 5 cards from the 7 available to find the highest score."""
    best_score = (-1, [], "")
    best_hand = []
    
    # Iterate through every possible 5-card combination
    for combo in itertools.combinations(hole_cards + community_cards, 5):
        score = evaluate_5_card_hand(list(combo))
        if score > best_score:
            best_score = score
            best_hand = list(combo)
            
    return best_score, best_hand

def determine_winner(player_score, dealer_score):
    if player_score > dealer_score:
        return "player"
    elif dealer_score > player_score:
        return "dealer"
    return "tie"

def format_card(card):
    return f"{card['rank']}{card['suit']}"

def format_hand(hand):
    if not hand:
        return "No cards"
    return " | ".join([format_card(c) for c in hand])