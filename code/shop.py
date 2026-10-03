# Allows for players to buy back in and to get powerups
MAX_LOAN_AMOUNT = 1000

AVAILABLE_POWERUPS = {
    "Lucky Marble": {
        "price": 150,
        "type": "temp",
        "description": "Increases the chance of getting a winning bet in roulette.",
    },
    "Marked Deck": {
        "price": 250,
        "type": "temp",
        "description": "See what the next card is in blackjack.",
    },
    "Lucky Cards": {
        "price": 150,
        "type": "temp",
        "description": "Increase chance of good cards in poker.",
    },
    "Silver Reel": {
        "price": 500,
        "type": "temp",
        "description": "Increase odds of getting rarer symbols in slots.",
    },
    "Fishing Rod": {
        "price": 1000,
        "type": "temp",
        "description": "Guarantees at least a 3 symbols payout in slots.",
    },
    "Horseshoe": {
        "price": 500,
        "type": "perma",
        "max_owned": 1,
        "luck_percent": 3,
        "description": "Minor luck increase.",
    },
    "4-leaf Clover": {
        "price": 1000,
        "type": "perma",
        "max_owned": 1,
        "luck_percent": 5,
        "description": "Medium luck increase.",
    },
    "7's Talisman": {
        "price": 2000,
        "type": "perma",
        "max_owned": 1,
        "luck_percent": 7,
        "description": "Major luck increase.",
    },
    "Sunglasses": {
        "price": 1000,
        "type": "perma",
        "max_owned": 1,
        "description": "Look cooler.",
    },
    "Golden Chip": {
        "price": 100000,
        "type": "perma",
        "max_owned": 1,
        "description": "A shiny golden chip."
    }
}

# Loans
def total_loan_balance(player):
    return sum(loan["balance"] for loan in player["loans"])

def net_worth(player):
    temp_powerup_value = sum(
        AVAILABLE_POWERUPS[name]["price"]
        for name in player.get("temp_powerups", [])
    )
    perma_powerup_value = sum(
            AVAILABLE_POWERUPS[name]["price"]
            for name in player.get("perma_powerups", [])
        )
    return player["chips"] + temp_powerup_value + perma_powerup_value - total_loan_balance(player)

def take_loan(player, amount):
    try:
        ShopGame(player).take_loan(amount)
    except ValueError as error:
        print(error)


def repay_loans(player, amount):
    try:
        ShopGame(player).repay(amount)
    except ValueError as error:
        print(error)


def collect_winnings_interest(player, winnings):
    if winnings <= 0:
        return 0

    rate = sum(loan["interest_rate"] for loan in player["loans"])
    return min(winnings, winnings * rate // 100)

def get_luck_chance(player):
    perma_luck_percent = sum(
        AVAILABLE_POWERUPS[name].get("luck_percent", 0)
        for name in player.get("perma_powerups", [])
    )
    temp_luck_percent = sum(
        AVAILABLE_POWERUPS[name].get("luck_percent", 0)
        for name in player.get("temp_powerups", [])
    )
    luck_percent = perma_luck_percent + temp_luck_percent
    return min(luck_percent, 100) / 100


class ShopGame:
    def __init__(self, player):
        self.player = player
        self.player.setdefault("loans", [])
        self.player.setdefault("temp_powerups", [])
        self.player.setdefault("perma_powerups", [])

    def buy_powerup(self, name, quantity):
        if name not in AVAILABLE_POWERUPS:
            raise ValueError("That power-up is not available.")
        if not isinstance(quantity, int) or isinstance(quantity, bool):
            raise ValueError("Quantity must be a whole number.")
        if quantity < 1:
            raise ValueError("Quantity must be at least 1.")

        details = AVAILABLE_POWERUPS[name]
        if details["type"] == "perma":
            if quantity != 1:
                raise ValueError("Permanent items can only be bought one at a time.")
            if self.player["perma_powerups"].count(name) >= details.get("max_owned", 1):
                raise ValueError("You already own this permanent item.")

        total_cost = details["price"] * quantity
        if total_cost > self.player["chips"]:
            raise ValueError(f"You need {total_cost} chips for that quantity.")

        inventory_key = (
            "perma_powerups" if details["type"] == "perma"
            else "temp_powerups"
        )
        self.player[inventory_key].extend([name] * quantity)
        self.player["chips"] -= total_cost
        return total_cost

    def take_loan(self, amount):
        if not isinstance(amount, int) or isinstance(amount, bool):
            raise ValueError("Loan amount must be a whole number.")
        if not 1 <= amount <= MAX_LOAN_AMOUNT:
            raise ValueError(
                f"Borrow between 1 and {MAX_LOAN_AMOUNT} chips."
            )

        loan_number = max(
            (loan["number"] for loan in self.player["loans"]),
            default=0,
        ) + 1
        self.player["loans"].append({
            "number": loan_number,
            "balance": amount,
            "interest_rate": 5 * loan_number,
        })
        self.player["loans_taken"] = len(self.player["loans"])
        self.player["chips"] += amount
        return amount

    def repay(self, amount):
        if not isinstance(amount, int) or isinstance(amount, bool):
            raise ValueError("Repayment must be a whole number.")
        max_repayment = min(
            self.player["chips"],
            total_loan_balance(self.player),
        )
        if not 1 <= amount <= max_repayment:
            raise ValueError(
                f"Repay between 1 and {max_repayment} chips."
            )

        remaining_payment = amount
        while remaining_payment:
            oldest_loan = self.player["loans"][0]
            payment = min(remaining_payment, oldest_loan["balance"])
            oldest_loan["balance"] -= payment
            remaining_payment -= payment
            if oldest_loan["balance"] == 0:
                self.player["loans"].pop(0)

        self.player["chips"] -= amount
        self.player["loans_taken"] = len(self.player["loans"])
        return amount


# Main shop
def open_shop(player, players):
    print("Welcome to the shop")

    while True:
        print("\n1. Take a loan")
        print("2. Pay off all loans")
        print("3. Buy a power-up")
        print("4. Show player info")
        print("Q. Return to casino")

        choice = input("> ").strip().lower()

        if choice == "1":
            try:
                amount = int(input("How much? "))
                take_loan(player, amount)
            except ValueError:
                print("Enter a whole number")

        elif choice == "2":
            try:
                amount = int(input("How much? "))
                repay_loans(player, amount)
            except ValueError:
                print("Enter a whole number")

        elif choice == "3":
            print("Available power-ups:")
            for powerup_type, label in (
                ("temp", "Temporary power-ups:"),
                ("perma", "Permanent power-ups:"),
            ):
                print(f"\n{label}")
                for name, details in AVAILABLE_POWERUPS.items():
                    if details["type"] == powerup_type:
                        print(
                            f"- {name}: {details['price']} chips — "
                            f"{details['description']}"
                        )

            requested = input("Power-up name: ").strip().casefold()
            powerup = next(
                (
                    name for name in AVAILABLE_POWERUPS
                    if name.casefold() == requested
                ),
                None,
            )

            if powerup is None:
                print("That power-up is not available.")
                continue

            price = AVAILABLE_POWERUPS[powerup]["price"]
            if player["chips"] < price:
                print(f"You need {price} chips to buy {powerup}.")
                continue

            details = AVAILABLE_POWERUPS[powerup]
            if (
                details["type"] == "perma"
                and player["perma_powerups"].count(powerup) >= details["max_owned"]
            ):
                print(f"You can only own {details['max_owned']} {powerup}")
                continue

            player["chips"] -= price
            if AVAILABLE_POWERUPS[powerup]["type"] == "temp":
                player["temp_powerups"].append(powerup)
            elif AVAILABLE_POWERUPS[powerup]["type"] == "perma":
                player["perma_powerups"].append(powerup)
            print(f"Bought {powerup} for {price} chips.")

        elif choice == "4":
            loan_balance = total_loan_balance(player)
            rank = 1 + sum(
                net_worth(other_player) > net_worth(player)
                for other_player in players.values()
                if other_player is not player
            )
            print(f"Chips: {player['chips']}")
            print(f"Loans taken: {len(player['loans'])}")
            print(f"Loan balance: {loan_balance}")
            print(f"Place: {rank} of {len(players)}")
            temp_powerups = player.get("temp_powerups", [])
            perma_powerups = player.get("perma_powerups", [])

            print(f"Temporary power-ups: {', '.join(temp_powerups) or 'none'}")
            print(f"Permanent power-ups: {', '.join(perma_powerups) or 'none'}")

        elif choice in ("q", "quit"):
            return

        else:
            print("Choose 1, 2, 3, 4, or Q.")
