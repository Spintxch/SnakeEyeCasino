# America Roulette
import random
from shop import collect_winnings_interest, get_luck_chance

# Constants
ROULETTE_NUMBERS = ['1', '2', '3', '4', '5', '6',
                    '7', '8', '9', '10', '11', '12',
                    '13', '14', '15', '16', '17', '18',
                    '19', '20', '21', '22', '23', '24',
                    '25', '26', '27', '28', '29', '30',
                    '31', '32', '33', '34', '35', '36',
                    '0', '00']

RED_NUMBERS = [
    '1', '3', '5', '7', '9', '12',
    '14', '16', '18', '19', '21', '23',
    '25', '27', '30', '32', '34', '36'
]

BLACK_NUMBERS = [
    '2', '4', '6', '8', '10', '11',
    '13', '15', '17', '20', '22', '24',
    '26', '28', '29', '31', '33', '35'
]

BET_SHAPES = {
    "Street": [(0, 0), (0, 1), (0, 2)],
    "Corner": [(0, 0), (0, 1), (1, 0), (1, 1)],
    "Line": [
        (0, 0), (0, 1), (0, 2),
        (1, 0), (1, 1), (1, 2)
        ]
}

SPLIT_SHAPES = {
    "Horizontal": [(0, 0), (0, 1)],
    "Vertical": [(0, 0), (1, 0)]
}


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


def payout(bet, bet_type):
    if bet_type == "Straight Up":
        return bet * 35
    elif bet_type == "Split":
        return bet * 17
    elif bet_type == "Street":
        return bet * 11
    elif bet_type == "Corner":
        return bet * 8
    elif bet_type == "Line":
        return bet * 5
    elif bet_type in ("Red", "Black", "Odd", "Even", "High", "Low"):
        return bet
    elif bet_type in ("Dozen", "Column"):
        return bet * 2

# Bet shapes
def get_groups(offsets):
    groups = []

    for row in range(12):
        for column in range(3):
            if all(
                row + row_offset < 12
                and column + column_offset < 3
                for row_offset, column_offset in offsets
            ):
                groups.append(tuple(
                    (row + row_offset) * 3 + column + column_offset + 1
                    for row_offset, column_offset in offsets
                ))

    return groups


def group_shape(bet_type):
    if bet_type == "Split":
        while True:
            direction = input("Horizontal or vertical?\n> ").strip().lower()

            if direction in ("horizontal", "h"):
                offsets = SPLIT_SHAPES["Horizontal"]
                break
            elif direction in ("vertical", "v"):
                offsets = SPLIT_SHAPES["Vertical"]
                break

            print("Enter horizontal or vertical.")
    else:
        offsets = BET_SHAPES[bet_type]

    groups_top_left = {
        group[0]: group for group in get_groups(offsets)
    }
    while True:
        try:
            top_left = int(input("Choose the upper-left number\n> "))
        except ValueError:
            print("Enter a whole number.")
            continue

        if top_left in groups_top_left:
            return bet_type, groups_top_left[top_left]
        
        print(f"That number can't start a {bet_type.lower()}.")

# Bet types
def inside_bets():
    options = ["Straight Up", "Split", "Street", "Corner", "Line"]

    for index, opt in enumerate(options, start=1):
        print(f"{index}. {opt}", end="    ")
    print()

    while True:
        try:
            choice = int(input("> ").strip())
        except ValueError:
            print(f"Enter a number from 1 to {len(options)}.")
            continue

        if 1 <= choice <= len(options):
            bet_type = options[choice - 1]
            break

        print(f"Enter a number from 1 to {len(options)}.")

    if bet_type == "Straight Up":
        while True:
            location = input("What number do you want to bet on?\n> ").strip()
            if location in ROULETTE_NUMBERS:
                return bet_type, location
            print("Enter a valid roulette number.")


    elif bet_type in options:
        bet_type, location = group_shape(bet_type)
        return bet_type, location

    return bet_type, None


def outside_bets():
    options = ["Red", "Black", "Odd", "Even", "High", "Low", "Dozen", "Column"]

    for index, opt, in enumerate(options, start=1):
        print(f"{index}. {opt}", end="    ")
    print()

    while True:
        try:
            choice = int(input("> ").strip())
        except ValueError:
            print(f"Enter a number from 1 to {len(options)}.")
            continue

        if 1 <= choice <= len(options):
            bet_type = options[choice - 1]
            break

        print(f"Enter a number from 1 to {len(options)}.")

    if bet_type == "Dozen":
        dozen_ranges = {
            1: (1, 12),
            2: (13, 24),
            3: (25, 36)
        }

        while True:
            try:
                dozen = int(input("Choose a dozen (1, 2, or 3):\n> "))
            except ValueError:
                print("Enter 1, 2, or 3.")
                continue

            if dozen in dozen_ranges:
                return bet_type, dozen_ranges[dozen]

            print("Enter 1, 2, or 3.")

    elif bet_type == "Column":
        columns = {
            1: tuple(range(1, 37, 3)),
            2: tuple(range(2, 37, 3)),
            3: tuple(range(3, 37, 3))
        }

        while True:
            try:
                column = int(input("Choose a column (1, 2, or 3):\n> "))
            except ValueError:
                print("Enter 1, 2, or 3.")
                continue

            if column in columns:
                return bet_type, columns[column]

            print("Enter 1, 2, or 3.")

    return bet_type, None

def is_winning_spin(bet_type, location, spin):
    if bet_type == "Straight Up":
        return spin == location
    elif bet_type in ("Split", "Street", "Corner", "Line"):
        return spin.isdigit() and int(spin) in location
    elif bet_type == "Red":
        return spin in RED_NUMBERS
    elif bet_type == "Black":
        return spin in BLACK_NUMBERS
    elif bet_type == "Odd":
        return spin.isdigit() and int(spin) != 0 and int(spin) % 2 == 1
    elif bet_type == "Even":
        return spin.isdigit() and int(spin) != 0 and int(spin) % 2 == 0
    elif bet_type == "Low":
        return spin.isdigit() and 1 <= int(spin) <= 18
    elif bet_type == "High":
        return spin.isdigit() and 19 <= int(spin) <= 36
    elif bet_type in ("Dozen", "Column"):
        return spin.isdigit() and int(spin) in location
    return False


class RouletteGame:
    def __init__(self, player):
        self.player = player
        self.player.setdefault("temp_powerups", [])
        self.last_spin = None
        self.pending_spin = None
        self.message = "Choose a bet type and amount."

    @property
    def chips(self):
        return self.player["chips"]

    def spin(
        self,
        bet,
        bet_type,
        location,
        use_lucky_marble=True,
    ):
        self.start_spin(
            bet,
            bet_type,
            location,
            use_lucky_marble=use_lucky_marble,
        )
        return self.finish_spin()

    def start_spin(
        self,
        bet,
        bet_type,
        location,
        use_lucky_marble=True,
    ):
        if self.pending_spin is not None:
            raise RuntimeError("The roulette wheel is already spinning.")
        if not isinstance(bet, int) or isinstance(bet, bool):
            raise ValueError("Bet must be a whole number.")
        if not 1 <= bet <= self.chips:
            raise ValueError(f"Enter a bet between 1 and {self.chips}.")
        self._validate_bet_location(bet_type, location)

        winning_spins = [
            number for number in ROULETTE_NUMBERS
            if is_winning_spin(bet_type, location, number)
        ]
        if not winning_spins:
            raise ValueError("That bet has no valid winning numbers.")

        if random.random() < get_luck_chance(self.player):
            result = random.choice(winning_spins)
        else:
            result = random.choice(ROULETTE_NUMBERS)

        won = is_winning_spin(bet_type, location, result)
        if (
            use_lucky_marble
            and not won
            and "Lucky Marble" in self.player["temp_powerups"]
        ):
            self.player["temp_powerups"].remove("Lucky Marble")
            result = random.choice(ROULETTE_NUMBERS)
            won = is_winning_spin(bet_type, location, result)

        self.pending_spin = {
            "bet": bet,
            "bet_type": bet_type,
            "location": location,
            "result": result,
            "won": won,
        }
        self.message = "The wheel is spinning..."
        return result

    def finish_spin(self):
        if self.pending_spin is None:
            raise RuntimeError("There is no roulette spin to finish.")

        pending = self.pending_spin
        bet = pending["bet"]
        result = pending["result"]
        won = pending["won"]
        self.player["chips"] -= bet
        if won:
            winnings = payout(bet, pending["bet_type"])
            interest = collect_winnings_interest(self.player, winnings)
            net_winnings = winnings - interest
            self.player["chips"] += bet + net_winnings
            self.message = (
                f"It landed on {result}. You won {net_winnings} chips!"
            )
            if interest:
                self.message += f" ({interest} went to loan interest.)"
        else:
            self.message = f"It landed on {result}. You lost {bet} chips."

        self.last_spin = result
        self.pending_spin = None
        return result

    @staticmethod
    def select_number(bet_type, selected_numbers, number):
        if bet_type == "Straight Up":
            if number not in ROULETTE_NUMBERS:
                return selected_numbers, None, "Select a valid roulette number."
            return [], number, f"Straight Up on {number} selected."

        if bet_type not in ("Split", "Street", "Corner", "Line"):
            return selected_numbers, None, "Choose an inside bet type to select numbers."
        if not number.isdigit() or not 1 <= int(number) <= 36:
            return selected_numbers, None, "Inside bets can only use numbers 1-36."

        selected = list(selected_numbers)
        value = int(number)
        if value not in selected:
            selected.append(value)

        if bet_type == "Split":
            shapes = (
                get_groups(SPLIT_SHAPES["Horizontal"])
                + get_groups(SPLIT_SHAPES["Vertical"])
            )
        else:
            shapes = get_groups(BET_SHAPES[bet_type])

        matching_group = next(
            (group for group in shapes if set(group) == set(selected)),
            None,
        )
        required_count = len(shapes[0]) if shapes else 0
        if matching_group is not None:
            return (
                selected,
                matching_group,
                f"{bet_type} on {', '.join(map(str, matching_group))} selected.",
            )
        if len(selected) >= required_count:
            return [], None, "Those numbers don't form a valid bet shape. Try again."

        remaining = required_count - len(selected)
        return selected, None, f"Select {remaining} more number(s)."

    @staticmethod
    def _validate_bet_location(bet_type, location):
        if bet_type == "Straight Up":
            if location not in ROULETTE_NUMBERS:
                raise ValueError("Select a valid roulette number.")
            return

        if bet_type == "Split":
            valid_groups = (
                get_groups(SPLIT_SHAPES["Horizontal"])
                + get_groups(SPLIT_SHAPES["Vertical"])
            )
            if not isinstance(location, (tuple, list)) or tuple(location) not in valid_groups:
                raise ValueError("Select a valid split.")
            return

        if bet_type in ("Street", "Corner", "Line"):
            valid_groups = get_groups(BET_SHAPES[bet_type])
            if not isinstance(location, (tuple, list)) or tuple(location) not in valid_groups:
                raise ValueError(f"Select a valid {bet_type.lower()}.")
            return

        if bet_type == "Dozen":
            if location not in (
                tuple(range(1, 13)),
                tuple(range(13, 25)),
                tuple(range(25, 37)),
            ):
                raise ValueError("Select a valid dozen.")
            return

        if bet_type == "Column":
            if location not in (
                tuple(range(1, 37, 3)),
                tuple(range(2, 37, 3)),
                tuple(range(3, 37, 3)),
            ):
                raise ValueError("Select a valid column.")
            return

        if bet_type not in (
            "Red", "Black", "Odd", "Even", "High", "Low",
        ) or location is not None:
            raise ValueError("Choose a valid roulette bet.")


# Main playing
def player_turn():
    while True:
        inside_out = input("Would you like to place an inside or outside bet?\n> ").lower()
        if inside_out in ("inside", "in", "i"):
            return inside_bets()
        elif inside_out in ("outside", "out", "o"):
            return outside_bets()
        else:
            print("Please enter 'inside' or 'outside'")


def play_round(bet, player=None):
    bet_type, location = player_turn()
    if player is not None and random.random() < get_luck_chance(player):
        winning_spins = [
            number for number in ROULETTE_NUMBERS
            if is_winning_spin(bet_type, location, number)
        ]
        spin = random.choice(winning_spins)
    else:
        spin = random.choice(ROULETTE_NUMBERS)
    won = is_winning_spin(bet_type, location, spin)

    if (
        not won
        and player is not None
        and "Lucky Marble" in player["temp_powerups"]
    ):
        player["temp_powerups"].remove("Lucky Marble")
        spin = random.choice(ROULETTE_NUMBERS)
        won = is_winning_spin(bet_type, location, spin)
        print(f"Lucky Marble reroll: the wheel landed on {spin}.")
    else:
        print(f"The wheel landed on {spin}.")

    if won:
        winnings = payout(bet, bet_type)
        print(f"You won {winnings} chips!")
        return winnings

    print(f"You lost {bet} chips.")
    return -bet


def play_roulette(chips, player=None):
    print("Welcome to Roulette")
    while chips > 0:
        print(f"\nYou have {chips} chips.")
        bet = get_bet(chips)
        round_winnings = play_round(bet, player)

        if player is not None and round_winnings > 0:
            intrest = collect_winnings_interest(player, round_winnings)
            round_winnings -= intrest
            if intrest:
                print(f"{intrest} chips were taken from winnings")
                
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
            print(f"You leave Roulette with {chips} chips.")
            break
    return chips


def main():
    play_roulette(100)


if __name__ == "__main__":
    main()