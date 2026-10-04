# Casino blackjack
import random
from dataclasses import dataclass
from shop import collect_winnings_interest, get_luck_chance

CARD_VALUES = {
    "2": 2, "3": 3, "4": 4, "5": 5,
    "6": 6, "7": 7, "8": 8, "9": 9,
    "10": 10, "J": 10, "Q": 10, "K": 10, "A": 11
}
CARD_SUITS = ("♠", "♥", "♦", "♣")


def card_rank(card):
    return card[0] if isinstance(card, tuple) else card


def create_card_deck():
    deck = [
        (rank, suit)
        for rank in CARD_VALUES
        for suit in CARD_SUITS
    ]
    random.shuffle(deck)
    return deck

# Build base player hand
@dataclass
class PlayerHand:
    cards: list[str | tuple[str, str]]
    bet: int
    from_split: bool = False

# Deck and val
def create_deck():
    deck = list(CARD_VALUES.keys()) * 4
    random.shuffle(deck)
    return deck


def deal_card(deck):
    return deck.pop()


def calc_hand_value(hand):
    ranks = [card_rank(card) for card in hand]
    total = sum(CARD_VALUES[rank] for rank in ranks)
    aces = ranks.count("A")

    while total > 21 and aces:
        total -= 10
        aces -= 1

    return total


def has_blackjack(hand):
    return len(hand) == 2 and calc_hand_value(hand) == 21


class BlackjackGame:
    def __init__(self, player):
        self.player = player
        self.player.setdefault("temp_powerups", [])
        self.deck = []
        self.hands = []
        self.dealer_hand = []
        self.current_hand_index = 0
        self.round_active = False
        self.message = "Enter a bet, then deal."
        self.bet = 0
        self.marked_card = None

    def _deal_marked_card(self):
        card = deal_card(self.deck)
        if card == self.marked_card:
            self.marked_card = None
        return card

    @property
    def chips(self):
        return self.player["chips"]

    @property
    def current_hand(self):
        if 0 <= self.current_hand_index < len(self.hands):
            return self.hands[self.current_hand_index]
        return None

    @property
    def total_wager(self):
        return sum(hand.bet for hand in self.hands)

    @property
    def can_hit(self):
        hand = self.current_hand
        return (
            self.round_active
            and hand is not None
            and bool(self.deck)
            and calc_hand_value(hand.cards) < 21
        )

    @property
    def can_double(self):
        hand = self.current_hand
        return (
            self.round_active
            and hand is not None
            and len(hand.cards) == 2
            and not hand.from_split
            and bool(self.deck)
            and self.total_wager + hand.bet <= self.chips
        )

    @property
    def can_split(self):
        hand = self.current_hand
        return (
            self.round_active
            and hand is not None
            and len(self.hands) < 4
            and len(hand.cards) == 2
            and CARD_VALUES[card_rank(hand.cards[0])]
            == CARD_VALUES[card_rank(hand.cards[1])]
            and len(self.deck) >= 2
            and self.total_wager + hand.bet <= self.chips
        )

    def start_round(self, bet, use_marked_deck=True):
        if self.round_active:
            raise RuntimeError("A Blackjack round is already active.")
        if not isinstance(bet, int) or isinstance(bet, bool):
            raise ValueError("Bet must be a whole number.")
        if not 1 <= bet <= self.chips:
            raise ValueError(f"Enter a bet between 1 and {self.chips}.")

        self.bet = bet
        self.deck = create_card_deck()
        if random.random() < get_luck_chance(self.player):
            ace = next(card for card in self.deck if card_rank(card) == "A")
            self.deck.remove(ace)
            ten_value_card = next(
                card for card in self.deck
                if CARD_VALUES[card_rank(card)] == 10
            )
            self.deck.remove(ten_value_card)
            opening_hand = [ace, ten_value_card]
        else:
            opening_hand = [deal_card(self.deck), deal_card(self.deck)]

        self.hands = [PlayerHand(opening_hand, bet)]
        self.dealer_hand = [deal_card(self.deck), deal_card(self.deck)]
        self.current_hand_index = 0
        self.round_active = True
        self.message = "Hit, stand, double, or split."
        self.marked_card = None

        if (
            use_marked_deck
            and "Marked Deck" in self.player["temp_powerups"]
            and self.deck
        ):
            self.marked_card = self.deck[-1]
            self.player["temp_powerups"].remove("Marked Deck")
            self.message = "Marked Deck reveals the next card."

        if has_blackjack(self.hands[0].cards) or has_blackjack(self.dealer_hand):
            self._finish_round()

    def hit(self):
        if not self.can_hit:
            raise RuntimeError("Hit is not available for this hand.")

        self.current_hand.cards.append(self._deal_marked_card())
        if calc_hand_value(self.current_hand.cards) >= 21:
            self.advance_hand()
        else:
            self.message = "Hit or stand."

    def stand(self):
        if not self.round_active or self.current_hand is None:
            raise RuntimeError("Stand is not available.")
        self.advance_hand()

    def double_down(self):
        if not self.can_double:
            raise RuntimeError("Double down is not available for this hand.")

        self.current_hand.bet *= 2
        self.current_hand.cards.append(self._deal_marked_card())
        self.advance_hand()

    def split(self):
        if not self.can_split:
            raise RuntimeError("Split is not available for this hand.")

        hand = self.current_hand
        first_card, second_card = hand.cards
        self.hands[self.current_hand_index:self.current_hand_index + 1] = [
            PlayerHand([first_card, self._deal_marked_card()], hand.bet, True),
            PlayerHand([second_card, self._deal_marked_card()], hand.bet, True),
        ]

        if calc_hand_value(self.current_hand.cards) >= 21:
            self.advance_hand()
        else:
            self.message = f"Playing hand {self.current_hand_index + 1}."

    def advance_hand(self):
        self.current_hand_index += 1
        while self.current_hand_index < len(self.hands):
            if calc_hand_value(self.current_hand.cards) < 21:
                self.message = f"Playing hand {self.current_hand_index + 1}."
                return
            self.current_hand_index += 1

        self._finish_round()

    def leave(self):
        if not self.round_active:
            return
        forfeited = self.total_wager
        self.player["chips"] -= forfeited
        self.round_active = False
        self.message = f"Left Blackjack; forfeited {forfeited} chips."

    def _finish_round(self):
        self.round_active = False
        dealer_blackjack = has_blackjack(self.dealer_hand)
        can_draw_for_dealer = any(
            calc_hand_value(hand.cards) <= 21
            for hand in self.hands
        )

        if can_draw_for_dealer and not dealer_blackjack:
            while calc_hand_value(self.dealer_hand) < 17 and self.deck:
                self.dealer_hand.append(self._deal_marked_card())

        dealer_total = calc_hand_value(self.dealer_hand)
        net_change = 0
        for hand in self.hands:
            player_total = calc_hand_value(hand.cards)
            player_blackjack = has_blackjack(hand.cards) and not hand.from_split

            if player_total > 21:
                net_change -= hand.bet
            elif dealer_blackjack:
                if not player_blackjack:
                    net_change -= hand.bet
            elif player_blackjack:
                net_change += hand.bet * 3 // 2
            elif dealer_total > 21 or player_total > dealer_total:
                net_change += hand.bet
            elif player_total < dealer_total:
                net_change -= hand.bet

        if net_change > 0:
            interest = collect_winnings_interest(self.player, net_change)
            net_change -= interest
            if interest:
                self.message = f"{interest} chips went to loan interest."

        self.player["chips"] += net_change
        if net_change > 0:
            self.message = f"Round over: you won {net_change} chips."
        elif net_change < 0:
            self.message = f"Round over: you lost {-net_change} chips."
        else:
            self.message = "Round over: push. Your bet is returned."


def show_hand(name, hand):
    print(f"{name}: {', '.join(hand)} "
          f"(total: {calc_hand_value(hand)})")

# Betting
def get_bet(chips):
    while True:
        try:
            bet = int(input(f"Bet 1 to {chips} chips: "))
        except ValueError:
            print("Enter a whole number.")
            continue

        if 1 <= bet <= chips:
            return bet
        print(f"Your bet must be between 1 and {chips}.")

# Main
def player_turn(deck, hands, chips, player=None):
    index = 0
    while index < len(hands):
        hand = hands[index]

        while calc_hand_value(hand.cards) < 21:
            show_hand(f"Your hand {index + 1}", hand.cards)

            total_wager = sum(player_hand.bet for player_hand in hands)
            can_split = (
                len(hand.cards) == 2
                and CARD_VALUES[card_rank(hand.cards[0])]
                == CARD_VALUES[card_rank(hand.cards[1])]
                and len(deck) >= 2
                and total_wager + hand.bet <= chips
            )
            can_double = (
                len(hand.cards) == 2
                and not hand.from_split
                and len(deck) >= 1
                and total_wager + hand.bet <= chips
            )

            if (
                player is not None
                and "Marked Deck" in player.get("temp_powerups", [])
                and deck
            ):
                print(f"Marked Deck reveals the next card: {deck[-1]}")
                player["temp_powerups"].remove("Marked Deck")

            options = ["2. Stand"]
            if deck:
                options.insert(0, "1. Hit")
            if can_split:
                options.append("3. Split")
            if can_double:
                options.append("4. Double Down")
            action = input("    ".join(options) + "\n> ").strip()

            if action == "1":
                if deck:
                    hand.cards.append(deal_card(deck))
                else:
                    print("No cards remain to draw.")
            elif action == "2":
                break
            elif action == "3" and can_split:
                first_card, second_card = hand.cards
                hands[index:index + 1] = [
                    PlayerHand([first_card, deal_card(deck)], hand.bet, True),
                    PlayerHand([second_card, deal_card(deck)], hand.bet, True),
                ]
                hand = hands[index]
            elif action == "4" and can_double:
                hand.bet *= 2
                hand.cards.append(deal_card(deck))
                break
            elif action in ("3", "4"):
                print("That action is not available for this hand.")
            else:
                print("Enter a number from the available options.")

        index += 1

    return hands


def dealer_turn(deck, hand):
    while calc_hand_value(hand) < 17:
        hand.append(deal_card(deck))


def show_result(player_hand, dealer_hand, bet, hand_name="Your hand",
                show_dealer=True, from_split=False):
    player_total = calc_hand_value(player_hand)
    player_blackjack = has_blackjack(player_hand) and not from_split
    dealer_blackjack = has_blackjack(dealer_hand)
    show_hand(hand_name, player_hand)
    if player_total > 21:
        print(f"You lost {bet} chips; you busted.")
        return -bet
    
    dealer_total = calc_hand_value(dealer_hand)

    if show_dealer:
        show_hand("Dealer hand", dealer_hand)

    if player_blackjack and dealer_blackjack:
        print("Both hands have blackjack. Bet returned.")
        return 0
    if dealer_blackjack:
        print(f"Dealer has blackjack. You lost {bet} chips.")
        return -bet
    if player_blackjack:
        winnings = bet * 3 // 2
        print(f"Blackjack! You won {winnings} chips at 3:2.")
        return winnings

    if dealer_total > 21 or player_total > dealer_total:
        print(f"Player Win. You won {bet} chips.")
        return bet
    elif player_total < dealer_total:
        print(f"Dealer Win. You lost {bet} chips.")
        return -bet
    else:
        print("Tie. Bet returned")
        return 0


def play_round(bet, chips, player=None):
    deck = create_deck()

    if player is not None and random.random() < get_luck_chance(player):
        deck.remove("A")
        ten_value_card = next(
            card for card in deck if CARD_VALUES[card] == 10
        )
        deck.remove (ten_value_card)
        opening_hand = ["A", ten_value_card]
    else:
        opening_hand = [deal_card(deck) for _ in range(2)]

    hands = [PlayerHand(opening_hand, bet)]
    dealer_hand = [deal_card(deck) for _ in range(2)]
    print(f"Dealer showing: {dealer_hand[1]}")

    player_turn(deck, hands, chips, player)

    first_active_hand = next(
        (
            index for index, hand in enumerate(hands)
            if calc_hand_value(hand.cards) <= 21
        ),
        None,
    )
    if first_active_hand is not None:
        dealer_turn(deck, dealer_hand)

    result = 0
    for index, hand in enumerate(hands):
        result += show_result(
            hand.cards,
            dealer_hand,
            hand.bet,
            hand_name=f"Your hand {index + 1}",
            show_dealer=index == first_active_hand,
            from_split=hand.from_split,
        )
    return result


def play_blackjack(chips, player=None):
    print("Welcome to Blackjack")
    while chips > 0:
        print(f"\nYou have {chips} chips.")
        bet = get_bet(chips)
        round_winnings = play_round(bet, chips, player)
        if player is not None and round_winnings > 0:
            intrest = collect_winnings_interest(player, round_winnings)
            round_winnings -= intrest
            if intrest:
                print(f"{intrest} chips were taken from winnings.")

        chips += round_winnings
        print(f"You now have {chips} chips.")

        if chips == 0:
            print("You're out of chips.")
            break

        while True:
            keep_playing = input("Keep playing? (y/n)\n> ").strip().lower()
            if keep_playing in ("y", "n"):
                break
            print("Please enter 'y' or 'n'.")

        if keep_playing == "n":
            print(f"You leave Blackjack with {chips} chips.")
            break
    return chips


def main():
    play_blackjack(100)


if __name__ == "__main__":
    main()