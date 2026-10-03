import random
from itertools import combinations
from shop import collect_winnings_interest, get_luck_chance

MAX_SEATS = 6
SMALL_BLIND = 5
BIG_BLIND = 10

RANKS = ("2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A")
SUITS = ("♠", "♥", "♦", "♣")
RANK_VALUES = {rank: value for value, rank in enumerate(RANKS, start=2)}

def make_deck():
    deck = [(rank, suit) for rank in RANKS for suit in SUITS]
    random.shuffle(deck)
    return deck

def format_cards(cards):
    return " ".join(f"{rank}{suit}" for rank, suit in cards)

def create_table(player_name, players, starting_chips):
    seats = [{
        "name": player_name,
        "is_bot": False,
        "stack": starting_chips,
    }]
    used_names = {player_name}

    for name in sorted(players):
        if name in used_names:
            continue
        if len(seats) == MAX_SEATS:
            break

        seats.append({
            "name": name,
            "is_bot": True,
            "stack": starting_chips,
        })
        used_names.add(name)

    bot_number = 1
    while len(seats) < MAX_SEATS:
        name = f"bot_{bot_number:03d}"
        bot_number += 1

        if name in used_names:
            continue

        seats.append({
            "name": name,
            "is_bot": True,
            "stack": starting_chips,
        })
        used_names.add(name)

    return seats

def straight_high(values):
    unique = set(values)
    if 14 in unique:
        unique.add(1)

    ordered = sorted(unique, reverse=True)
    for start in range(len(ordered) - 4):
        group = ordered[start:start + 5]
        if group[0] - group[4] == 4:
            return group[0]
    return 0

def rank_five_cards(cards):
    values = sorted(
        (RANK_VALUES[rank] for rank, _ in cards),
        reverse=True
    )
    counts = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1

    groups = sorted(
        ((count, value) for value, count in counts.items()),
        reverse=True,
    )

    flush = len({suit for _, suit in cards}) == 1
    straight = straight_high(values)

    if flush and straight:
        return (8, straight)
    if groups[0][0] == 4:
        four = groups[0][1]
        kicker = max(value for value in values if value != four)
        return (7, four, kicker)
    if groups[0][0] == 3 and groups[1][0] == 2:
        return (6, groups[0][1], groups[1][1])
    if flush:
        return (5, *values)
    if straight:
        return (4, straight)
    if groups[0][0] == 3:
        trip = groups[0][1]
        kickers = sorted(
            (value for value in values if value != trip),
            reverse=True,
        )
        return (3, trip, *kickers)
    if groups[0][0] == 2 and groups[1][0] == 2:
        high_pair, low_pair = sorted(
            (groups[0][1], groups[1][1]),
            reverse=True,
        )
        kicker = max(
            value for value in values
            if value != high_pair and value != low_pair
        )
        return (2, high_pair, low_pair, kicker)
    if groups[0][0] == 2:
        pair = groups[0][1]
        kickers = sorted(
            (value for value in values if value != pair),
            reverse=True,
        )
        return (1, pair, *kickers)
    return (0, *values)

def best_hand(cards):
    return max(
        rank_five_cards(hand)
        for hand in combinations(cards, 5)
    )

def next_seat(seats, start, predicate):
    for offset in range(1, len(seats) + 1):
        index = (start + offset) % len(seats)
        if predicate(seats[index]):
            return index
    return None

def post_chips(seat, amount):
    posted = min(seat["stack"], amount)
    seat["stack"] -= posted
    seat["street_bet"] += posted
    seat["contribution"] += posted
    return posted

def get_hand_strength(seat, board):
    if len(board) >= 3:
        return best_hand(seat["hole_cards"] + board)[0]

    values = sorted(
        (RANK_VALUES[rank] for rank, _ in seat["hole_cards"]),
        reverse=True,
    )
    if values[0] == values[1]:
        return 2
    if values[0] >= 13 and values[1] >=12:
        return 1
    return 0

def choose_bot_action(seat, board, amount_to_call):
    strength = get_hand_strength(seat, board)

    if amount_to_call == 0:
        if strength >= 2 and seat["stack"] > BIG_BLIND:
            if random.random() < 0.1:
                return "raise"
        return "check"

    if amount_to_call >= seat["stack"]:
        return "call" if strength >= 2 else "fold"

    if strength == 0 and amount_to_call >= BIG_BLIND:
        return "fold" if random.random() < 0.6 else "call"

    if strength >= 2 and seat["stack"] > amount_to_call + BIG_BLIND:
        if random.random() < 0.1:
            return "raise"

    return "call"

def ask_user_action(seat, board, pot, amount_to_call):
    print(f"\nYour cards: {format_cards(seat['hole_cards'])}")
    print(f"Board: {format_cards(board) or '(no community cards yet)'}")
    print(
        f"Pot: {pot} | Your chips: {seat['stack']} "
        f"| To call: {amount_to_call}"
    )

    choices = ["fold", "check" if amount_to_call == 0 else "call"]
    if seat["stack"] > amount_to_call + BIG_BLIND:
        choices.append("raise")

    while True:
        action = input(
            f"Choose {'/'.join(choices)}: "
        ).strip().lower()
        if action in choices:
            return action
        print(f"Choose one of: {', '.join(choices)}.")

def betting_round(seats, board, first_actor):
    current_bet = max(seat["street_bet"] for seat in seats)
    pending = [
        (first_actor + offset) % len(seats)
        for offset in range(len(seats))
        if not seats[(first_actor + offset) % len(seats)]["folded"]
        and not seats[(first_actor + offset) % len(seats)]["all_in"]
    ]

    while pending:
        if sum(not seat["folded"] for seat in seats) <= 1:
            return

        index = pending.pop(0)
        seat = seats[index]
        if seat["folded"] or seat["all_in"]:
            continue

        amount_to_call = current_bet - seat["street_bet"]
        if seat["is_bot"]:
            action = choose_bot_action(seat, board, amount_to_call)
            print(f"{seat['name']} {action}s.")
        else:
            pot = sum(other["contribution"] for other in seats)
            action = ask_user_action(
                seat, board, pot, amount_to_call
            )

        if action == "fold":
            seat["folded"] = True
            continue

        if action in ("check", "call"):
            post_chips(seat, amount_to_call)
            if seat["stack"] == 0:
                seat["all_in"] = True
            continue

        raise_amount = amount_to_call + BIG_BLIND
        post_chips(seat, raise_amount)
        current_bet = seat["street_bet"]
        print(f"{seat['name']} raises.")

        pending = [
            (index + offset) % len(seats)
            for offset in range(1, len(seats))
            if not seats[(index + offset) % len(seats)]["folded"]
            and not seats[(index + offset) % len(seats)]["all_in"]
        ]


def award_pot(seats, board, button, announce=True):
    remaining = [
        index for index, seat in enumerate(seats)
        if not seat["folded"]
    ]

    if len(remaining) == 1:
        winner = seats[remaining[0]]
        pot = sum(seat["contribution"] for seat in seats)
        winner["stack"] += pot
        if announce:
            print(f"{winner['name']} wins {pot} chips.")
        return

    levels = sorted({
        seat["contribution"] for seat in seats
        if seat["contribution"] > 0
    })
    previous = 0
    odd_chip_order = [
        (button + offset) % len(seats)
        for offset in range(1, len(seats) + 1)
    ]

    for level in levels:
        contributors = [
            index for index, seat in enumerate(seats)
            if seat["contribution"] >= level
        ]
        pot = (level - previous) * len(contributors)

        if len(contributors) == 1:
            seats[contributors[0]]["stack"] += pot
            previous = level
            continue

        eligible = [
            index for index in contributors
            if not seats[index]["folded"]
        ]
        if not eligible:
            previous = level
            continue

        ranks = {
            index: best_hand(seats[index]["hole_cards"] + board)
            for index in eligible
        }
        best_rank = max(ranks.values())
        winners = [
            index for index in eligible
            if ranks[index] == best_rank
        ]
        winners.sort(key=odd_chip_order.index)

        share, remainder = divmod(pot, len(winners))
        for index in winners:
            seats[index]["stack"] += share
        for index in winners[:remainder]:
            seats[index]["stack"] += 1

        if announce:
            print(
                f"{', '.join(seats[index]['name'] for index in winners)} "
                f"win(s) {pot} chips."
            )
        previous = level

class PokerRound:
    def __init__(self, seats, previous_button, player=None):
        self.seats = seats
        self.player = player
        self.button = previous_button
        self.deck = []
        self.board = []
        self.street = 0
        self.current_bet = 0
        self.pending = []
        self.finished = False
        self.message = ""

        active = [
            index for index, seat in enumerate(seats)
            if seat["stack"] > 0
        ]
        if len(active) < 2:
            self.finished = True
            self.message = "Not enough players to start a hand."
            return

        for seat in seats:
            seat.update({
                "hole_cards": [],
                "folded": seat["stack"] == 0,
                "all_in": False,
                "street_bet": 0,
                "contribution": 0,
            })

        self.button = next_seat(
            seats,
            previous_button,
            lambda seat: seat["stack"] > 0,
        )

        if len(active) == 2:
            small_blind_index = self.button
        else:
            small_blind_index = next_seat(
                seats,
                self.button,
                lambda seat: seat["stack"] > 0,
            )

        big_blind_index = next_seat(
            seats,
            small_blind_index,
            lambda seat: seat["stack"] > 0,
        )

        self.deck = make_deck()
        user_index = next(
            (index for index, seat in enumerate(seats) if not seat["is_bot"]),
            None,
        )
        has_lucky_cards = (
            player is not None
            and "Lucky Cards" in player.get("temp_powerups", [])
        )
        lucky_cards = None
        if user_index is not None and (
            has_lucky_cards
            or (player is not None and random.random() < get_luck_chance(player))
        ):
            rank = random.choice(RANKS)
            lucky_cards = random.sample(
                [(rank, suit) for suit in SUITS],
                2,
            )
            for card in lucky_cards:
                self.deck.remove(card)
            if has_lucky_cards:
                player["temp_powerups"].remove("Lucky Cards")

        for _ in range(2):
            for index in active:
                if index == user_index and lucky_cards:
                    seats[index]["hole_cards"].append(lucky_cards.pop())
                else:
                    seats[index]["hole_cards"].append(self.deck.pop())

        post_chips(seats[small_blind_index], SMALL_BLIND)
        post_chips(seats[big_blind_index], BIG_BLIND)
        seats[small_blind_index]["all_in"] = (
            seats[small_blind_index]["stack"] == 0
        )
        seats[big_blind_index]["all_in"] = (
            seats[big_blind_index]["stack"] == 0
        )

        self.current_bet = max(seat["street_bet"] for seat in seats)
        first_actor = next_seat(
            seats,
            big_blind_index,
            lambda seat: not seat["folded"] and not seat["all_in"],
        )
        self.pending = self._eligible_order(first_actor)
        self.message = "Pre-flop."
        self.advance()

    @property
    def actor_index(self):
        return self.pending[0] if self.pending else None

    @property
    def amount_to_call(self):
        if self.actor_index is None:
            return 0
        seat = self.seats[self.actor_index]
        return max(0, self.current_bet - seat["street_bet"])

    @property
    def pot(self):
        return sum(seat["contribution"] for seat in self.seats)

    @property
    def can_raise(self):
        if self.actor_index is None:
            return False
        seat = self.seats[self.actor_index]
        return seat["stack"] > self.amount_to_call + BIG_BLIND

    def _eligible_order(self, start):
        if start is None:
            return []

        return [
            (start + offset) % len(self.seats)
            for offset in range(len(self.seats))
            if not self.seats[(start + offset) % len(self.seats)]["folded"]
            and not self.seats[(start + offset) % len(self.seats)]["all_in"]
        ]

    def _players_left(self):
        return sum(not seat["folded"] for seat in self.seats)

    def act(self, action):
        if self.finished or self.actor_index is None:
            raise RuntimeError("There is no player action to apply.")

        index = self.actor_index
        seat = self.seats[index]
        if seat["is_bot"]:
            raise RuntimeError("It is not the human player's turn.")

        amount_to_call = self.amount_to_call

        if action == "fold":
            seat["folded"] = True
            self.message = "You folded."

        elif action == "check":
            if amount_to_call:
                raise ValueError("You cannot check while facing a bet.")
            self.message = "You checked."

        elif action == "call":
            post_chips(seat, amount_to_call)
            seat["all_in"] = seat["stack"] == 0
            self.message = "You called."

        elif action == "raise":
            if not self.can_raise:
                raise ValueError("A raise is not available.")
            post_chips(seat, amount_to_call + BIG_BLIND)
            seat["all_in"] = seat["stack"] == 0
            self.current_bet = seat["street_bet"]
            self.pending = [
                (index + offset) % len(self.seats)
                for offset in range(1, len(self.seats))
                if not self.seats[(index + offset) % len(self.seats)]["folded"]
                and not self.seats[(index + offset) % len(self.seats)]["all_in"]
            ]
            self.message = "You raised."

        else:
            raise ValueError(f"Unknown poker action: {action}")

        if action != "raise":
            self.pending.pop(0)

        self.advance()

    def advance(self):
        while not self.finished:
            if self._players_left() <= 1:
                award_pot(self.seats, self.board, self.button, announce=False)
                self.finished = True
                self.message = "Hand over. The remaining player wins."
                return

            if not self.pending:
                self._advance_street()
                continue

            index = self.actor_index
            seat = self.seats[index]

            if not seat["is_bot"]:
                return

            action = choose_bot_action(
                seat,
                self.board,
                self.amount_to_call,
            )
            self._act_for_bot(index, action)

    def _act_for_bot(self, index, action):
        seat = self.seats[index]
        amount_to_call = self.current_bet - seat["street_bet"]

        if action == "fold":
            seat["folded"] = True
            self.message = f"{seat['name']} folded."
        elif action in ("check", "call"):
            post_chips(seat, amount_to_call)
            seat["all_in"] = seat["stack"] == 0
            self.message = f"{seat['name']} {action}ed."
        elif action == "raise":
            post_chips(seat, amount_to_call + BIG_BLIND)
            seat["all_in"] = seat["stack"] == 0
            self.current_bet = seat["street_bet"]
            self.pending = [
                (index + offset) % len(self.seats)
                for offset in range(1, len(self.seats))
                if not self.seats[(index + offset) % len(self.seats)]["folded"]
                and not self.seats[(index + offset) % len(self.seats)]["all_in"]
            ]
            self.message = f"{seat['name']} raised."
            return

        self.pending.pop(0)

    def _advance_street(self):
        if self.street == 3:
            self._showdown()
            return

        cards_to_deal = (3, 1, 1)[self.street]
        for seat in self.seats:
            seat["street_bet"] = 0

        self.deck.pop()
        self.board.extend(self.deck.pop() for _ in range(cards_to_deal))
        self.street += 1
        self.current_bet = 0

        first_actor = next_seat(
            self.seats,
            self.button,
            lambda seat: not seat["folded"] and not seat["all_in"],
        )
        self.pending = self._eligible_order(first_actor)
        self.message = ("Flop", "Turn", "River")[self.street - 1]

    def _showdown(self):
        while len(self.board) < 5 and self._players_left() > 1:
            self.deck.pop()
            self.board.append(self.deck.pop())

        award_pot(self.seats, self.board, self.button, announce=False)
        self.finished = True
        self.message = "Showdown complete."


class PokerGame:
    def __init__(self, player):
        self.player = player
        self.player.setdefault("temp_powerups", [])
        self.seats = create_table("You", {}, player["chips"])
        for seat in self.seats:
            seat.update({
                "hole_cards": [],
                "folded": False,
                "all_in": False,
                "street_bet": 0,
                "contribution": 0,
            })
        self.previous_button = len(self.seats) - 1
        self.round = None
        self._hand_start_chips = player["chips"]
        self._settled_round = None

    @property
    def can_raise(self):
        return self.is_player_turn and self.round.can_raise

    @property
    def is_player_turn(self):
        if self.round is None or self.round.finished:
            return False
        actor_index = self.round.actor_index
        return (
            actor_index is not None
            and not self.round.seats[actor_index]["is_bot"]
        )

    def start_hand(self):
        if self.round is not None and not self.round.finished:
            return
        if self.player["chips"] <= 0:
            raise RuntimeError("You need chips to play poker.")

        self.seats[0]["stack"] = self.player["chips"]
        self._hand_start_chips = self.player["chips"]
        self.round = PokerRound(
            self.seats,
            self.previous_button,
            self.player,
        )
        if self.round.button is not None:
            self.previous_button = self.round.button
        self._settled_round = None
        self.sync_player_chips()

    def act(self, action):
        if not self.is_player_turn:
            raise RuntimeError("It is not your turn.")
        self.round.act(action)
        self.sync_player_chips()

    def sync_player_chips(self):
        player_seat = self.seats[0]
        if self.round is not None and not self.round.finished:
            self.player["chips"] = (
                player_seat["stack"] + player_seat["contribution"]
            )
            return

        self.player["chips"] = player_seat["stack"]
        if (
            self.round is not None
            and self.round.finished
            and self._settled_round is not self.round
        ):
            winnings = self.player["chips"] - self._hand_start_chips
            if winnings > 0:
                interest = collect_winnings_interest(self.player, winnings)
                self.player["chips"] -= interest
                if interest:
                    self.round.message += (
                        f" {interest} chips went to loan interest."
                    )
            self._settled_round = self.round

    def leave(self):
        if self.is_player_turn:
            self.act("fold")
        self.sync_player_chips()


def play_round(seats, previous_button, player=None):
    active = [
        index for index, seat in enumerate(seats)
        if seat["stack"] > 0
    ]
    if len(active) < 2:
        return previous_button

    for seat in seats:
        seat.update({
            "hole_cards": [],
            "folded": seat["stack"] == 0,
            "all_in": False,
            "street_bet": 0,
            "contribution": 0,
        })

    button = next_seat(
        seats,
        previous_button,
        lambda seat: seat["stack"] > 0,
    )
    if button is None:
        return previous_button

    if len(active) == 2:
        small_blind_index = button
        big_blind_index = next_seat(
            seats, button, lambda seat: seat["stack"] > 0
        )
    else:
        small_blind_index = next_seat(
            seats, button, lambda seat: seat["stack"] > 0
        )
        big_blind_index = next_seat(
            seats, small_blind_index, lambda seat: seat["stack"] > 0
        )

    deck = make_deck()
    user_index = next(
        (index for index, seat in enumerate(seats) if not seat["is_bot"]),
        None,
    )

    lucky_cards = None
    has_lucky_cards = (
        player is not None
        and "Lucky Cards" in player.get("temp_powerups", [])
    )

    luck_triggered = (
        user_index is not None
        and (
            has_lucky_cards
            or (
                player is not None
                and random.random() < get_luck_chance(player)
            )
        )
    )

    if luck_triggered:
        lucky_rank = random.choice(RANKS)
        lucky_cards = random.sample(
            [(lucky_rank, suit) for suit in SUITS],
            2,
        )
        for card in lucky_cards:
            deck.remove(card)

        if has_lucky_cards:
            player["temp_powerups"].remove("Lucky Cards")
            print("Lucky Cards gave you a pocket pair for this hand.")
        else:
            print("Your permanent luck gave you a pocket pair.")

    for _ in range(2):
        for index in active:
            if index == user_index and lucky_cards:
                seats[index]["hole_cards"].append(lucky_cards.pop())
            else:
                seats[index]["hole_cards"].append(deck.pop())

    small_blind = post_chips(
        seats[small_blind_index], SMALL_BLIND
    )
    big_blind = post_chips(
        seats[big_blind_index], BIG_BLIND
    )
    seats[small_blind_index]["all_in"] = (
        seats[small_blind_index]["stack"] == 0
    )
    seats[big_blind_index]["all_in"] = (
        seats[big_blind_index]["stack"] == 0
    )

    print(
        f"{seats[small_blind_index]['name']} posts {small_blind}; "
        f"{seats[big_blind_index]['name']} posts {big_blind}."
    )

    board = []
    first_actor = next_seat(
        seats, big_blind_index,
        lambda seat: not seat["folded"] and not seat["all_in"],
    )
    if first_actor is not None:
        betting_round(seats, board, first_actor)

    for cards_to_deal in (3, 1, 1):
        if sum(not seat["folded"] for seat in seats) <= 1:
            break

        for seat in seats:
            seat["street_bet"] = 0

        deck.pop()
        for _ in range(cards_to_deal):
            board.append(deck.pop())

        if cards_to_deal == 3:
            print(f"Flop: {format_cards(board)}")
        elif len(board) == 4:
            print(f"Turn: {format_cards(board)}")
        else:
            print(f"River: {format_cards(board)}")

        first_actor = next_seat(
            seats, button,
            lambda seat: not seat["folded"] and not seat["all_in"],
        )
        if first_actor is not None:
            betting_round(seats, board, first_actor)

    while len(board) < 5 and sum(not seat["folded"] for seat in seats) > 1:
        deck.pop()
        board.append(deck.pop())

    if sum(not seat["folded"] for seat in seats) > 1:
        print(f"Showdown board: {format_cards(board)}")
        for seat in seats:
            if not seat["folded"]:
                print(f"{seat['name']}: {format_cards(seat['hole_cards'])}")

    award_pot(seats, board, button)
    return button


def play_poker(chips, player, players, player_name):
    if chips <= 0:
        print("You need chips to play poker.")
        return chips
    
    seats = create_table(player_name, players, chips)
    print("Welcome to Texas Hold'em.")
    print("Table:")
    for seat in seats:
        label = "You" if not seat["is_bot"] else "Bot"
        print(f"- {seat['name']} ({label}): {seat['stack']} chips")

    button = len(seats) - 1
    while seats[0]["stack"] > 0:
        button = play_round(seats, button, player)

        if seats[0]["stack"] == 0:
            print("You're out of chips.")
            break
        if sum(seat["stack"] > 0 for seat in seats) <= 1:
            print("You are the last player with chips.")
            break

        while True:
            again = input("Play another hand? (y/n)\n> ").strip().lower()
            if again in ("y", "n"):
                break
            print("Please enter 'y' or 'n'.")

        if again == "n":
            break

    final_chips = seats[0]["stack"]
    if player is not None and final_chips > chips:
        winnings = final_chips - chips
        interest = collect_winnings_interest(player, winnings)
        final_chips -= interest
        if interest:
            print(f"{interest} chips were taken from your winnings.")

    print(f"You leave poker with {final_chips} chips.")
    return final_chips