# Slots
import random
from shop import collect_winnings_interest, get_luck_chance

SYMBOLS = ("CHERRY", "LEMON", "ORANGE",
           "PLUM", "BELL", "BAR",
            "HORSESHOE", "DIAMOND",  "7",
            )

SYMBOL_MULTIPLIERS = {
    "CHERRY": 1,
    "LEMON": 2,
    "ORANGE": 2,
    "PLUM": 3,
    "BELL": 4,
    "BAR": 5,
    "HORSESHOE": 6,
    "DIAMOND": 8,
    "7": 10,
}

BASE_WEIGHTS = {
    "CHERRY": 30,
    "LEMON": 25,
    "ORANGE": 18,
    "PLUM": 12,
    "BELL": 7,
    "BAR": 4,
    "HORSESHOE": 2,
    "DIAMOND": 1,
    "7": 1,
}

RARE_SYMBOLS = {"BAR", "HORSESHOE", "DIAMOND", "7"}

LINE_MULTIPLIERS = {
    "row": 3,
    "column": 2,
    "diagonal": 1,
}

BLACKOUT_MULTIPLIER = 50

PAYLINES = (
    ("row", ((0, 0), (0, 1), (0, 2))),
    ("row", ((1, 0), (1, 1), (1, 2))),
    ("row", ((2, 0), (2, 1), (2, 2))),
    ("column", ((0, 0), (1, 0), (2, 0))),
    ("column", ((0, 1), (1, 1), (2, 1))),
    ("column", ((0, 2), (1, 2), (2, 2))),
    ("diagonal", ((0, 0), (1, 1), (2, 2))),
    ("diagonal", ((0, 2), (1, 1), (2, 0))),
)

def symbol_weights(player=None, silver_reel=False):
    luck = get_luck_chance(player) if player is not None else 0
    rare_multiplier = 1 + 4 * luck

    if silver_reel:
        rare_multiplier *= 3

    return [
        BASE_WEIGHTS[symbol]
        * (rare_multiplier if symbol in RARE_SYMBOLS else 1)
        for symbol in SYMBOLS
    ]


def spin_reels(player=None, silver_reel=False):
    weights = symbol_weights(player, silver_reel)
    return [
        [random.choices(SYMBOLS, weights=weights, k=1)[0] for _ in range(3)]
        for _ in range(3)
    ]

def apply_fishing_rod(grid, player):
    if player is None or "Fishing Rod" not in player.get("temp_powerups", []):
        return False

    positions = PAYLINES[-2][1]
    symbol = random.choices(
        SYMBOLS,
        weights=symbol_weights(player),
        k=1,
    )[0]

    for row, column in positions:
        grid[row][column] = symbol

    player["temp_powerups"].remove("Fishing Rod")
    return True


def get_payout(grid, bet, fishing_rod=False):
    total_payout = 0
    wins = []

    if fishing_rod:
        symbol = grid[1][1]
        payout = bet * SYMBOL_MULTIPLIERS[symbol]
        return payout, [("fishing_rod", symbol, payout)]

    if all(symbol == grid[0][0] for row in grid for symbol in row):
        symbol = grid[0][0]
        payout = (
            bet
            * SYMBOL_MULTIPLIERS[symbol]
            * BLACKOUT_MULTIPLIER
        )
        return payout, [("blackout", symbol, payout)]

    for line_type, positions in PAYLINES:
        symbols = [grid[row][column] for row, column in positions]

        if symbols[0] == symbols[1] == symbols[2]:
            symbol = symbols[0]
            payout = (
                bet
                * SYMBOL_MULTIPLIERS[symbol]
                * LINE_MULTIPLIERS[line_type]
            )
            total_payout += payout
            wins.append((line_type, symbol, payout))

    return total_payout, wins


class SlotsGame:
    def __init__(self, player):
        self.player = player
        self.player.setdefault("temp_powerups", [])
        self.reels = [["?", "?", "?"] for _ in range(3)]
        self.wins = []
        self.last_payout = 0
        self.message = "Choose a bet, then spin."
        self.pending_bet = None

    @property
    def chips(self):
        return self.player["chips"]

    def start_spin(
        self,
        bet,
        use_silver_reel=True,
        use_fishing_rod=True,
    ):
        if self.pending_bet is not None:
            raise RuntimeError("The reels are already spinning.")
        if not isinstance(bet, int) or isinstance(bet, bool):
            raise ValueError("Bet must be a whole number.")
        if not 1 <= bet <= self.chips:
            raise ValueError(f"Bet must be between 1 and {self.chips} chips.")

        temp_powerups = self.player["temp_powerups"]
        silver_reel = (
            use_silver_reel and "Silver Reel" in temp_powerups
        )
        self.reels = spin_reels(self.player, silver_reel)

        if silver_reel:
            temp_powerups.remove("Silver Reel")

        fishing_rod = (
            apply_fishing_rod(self.reels, self.player)
            if use_fishing_rod
            else False
        )

        self.last_payout, self.wins = get_payout(
            self.reels,
            bet,
            fishing_rod=fishing_rod,
        )
        self.pending_bet = bet
        self.message = "Spinning..."
        return self.reels, self.last_payout, self.wins

    def finish_spin(self):
        if self.pending_bet is None:
            return False

        bet = self.pending_bet
        self.pending_bet = None
        self.player["chips"] -= bet

        if self.last_payout:
            self.player["chips"] += self.last_payout
            interest = collect_winnings_interest(self.player, self.last_payout)
            self.player["chips"] -= interest
            self.message = f"Winning spin! Payout: {self.last_payout} chips."
            if interest:
                self.message += f" {interest} chips went to loan interest."
        else:
            self.message = f"No win. You lost {bet} chips."

        return True

    def spin(
        self,
        bet,
        use_silver_reel=True,
        use_fishing_rod=True,
    ):
        result = self.start_spin(
            bet,
            use_silver_reel=use_silver_reel,
            use_fishing_rod=use_fishing_rod,
        )
        self.finish_spin()
        return result


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


def play_slots(chips, player=None):
    print("Welcome to Slots.")

    while chips > 0:
        print(f"\nYou have {chips} chips.")
        bet = get_bet(chips)
        temp_powerups = player.get("temp_powerups", []) if player else []
        silver_reel = "Silver Reel" in temp_powerups

        reels = spin_reels(player, silver_reel)

        if silver_reel:
            player["temp_powerups"].remove("Silver Reel")

        fishing_rod = apply_fishing_rod(reels, player)

        for row in reels:
            print(" | ".join(f"{symbol:10}" for symbol in row))

        payout, wins = get_payout(reels, bet, fishing_rod=fishing_rod)
        chips -= bet

        if payout:
            chips += payout
            for line_type, symbol, line_payout in wins:
                if line_type == "blackout":
                    print(f"Blackout! All nine symbols are {symbol}: {line_payout} chips.")
                elif line_type == "fishing_rod":
                    print(
                        f"Fishing Rod diagonal: three {symbol}s, "
                        f"{line_payout} chips."
                    )
                    continue
                print(
                    f"Three {symbol}s on a {line_type} line: "
                    f"{line_payout} chips."
                )

            if player is not None and payout > 0:
                interest = collect_winnings_interest(player, payout)
                chips -= interest
                if interest:
                    print(f"{interest} chips were taken from winnings.")

            print(f"You won {payout} chips.")
        else:
            print(f"You lost {bet} chips.")

        print(f"You now have {chips} chips.")
        if chips <= 0:
            print("You're out of chips.")
            break

        while True:
            again = input("Spin again? (y/n)\n> ").strip().lower()
            if again in ("y", "n"):
                break
            print("Please enter 'y' or 'n'.")

        if again == "n":
            break

    return chips