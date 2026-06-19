import random

# Define how common each symbol is (higher number = more common)
SYMBOL_WEIGHTS = {
    "cherry": 35,       # Very common
    "lemon": 25,
    "watermelon": 20,
    "bell": 15,
    "heart": 10,
    "horseShoe": 8,
    "bar": 5,
    "diamond": 3,
    "seven": 1,         # Jackpot! Very rare
}

# Define the multiplier payout for each symbol line
SYMBOL_MULTIPLIERS = {
    "cherry": 1.5,
    "lemon": 2.0,
    "watermelon": 3.0,
    "bell": 4.0,
    "heart": 5.0,
    "horseShoe": 10.0,
    "bar": 20.0,
    "diamond": 50.0,
    "seven": 100.0,     # Jackpot payout!
}

PITY_WEIGHTS = {
    "cherry": 15,       # Drastically reduced
    "lemon": 15,        # Reduced
    "watermelon": 15,
    "bell": 15,
    "heart": 15,        # Increased
    "horseShoe": 10,    # Increased
    "bar": 8,           # Increased
    "diamond": 5,       # Increased
    "seven": 2,         # Doubled chance!
}

slotMachineVariables = list(SYMBOL_WEIGHTS.keys())
slotWeights = list(SYMBOL_WEIGHTS.values())
pityWeights = list(PITY_WEIGHTS.values())

def spin_slots(consecutive_losses=0):
    """Return the three slot wheels. Increases win chance based on consecutive losses."""
    # Each consecutive loss adds a 10% invisible chance to force a win
    pity_chance = consecutive_losses * 0.10 
    
    # If the hidden pity roll succeeds, use the LUCKY WEIGHTS to generate the win!
    if random.random() < pity_chance:
        while True:
            wheel_one = random.choices(slotMachineVariables, weights=pityWeights, k=3)
            wheel_two = random.choices(slotMachineVariables, weights=pityWeights, k=3)
            wheel_three = random.choices(slotMachineVariables, weights=pityWeights, k=3)
            wheels = [wheel_one, wheel_two, wheel_three]
            
            if len(check_win(wheels)) > 0:
                return wheels

    # Otherwise, perform a completely normal, standard spin
    wheel_one = random.choices(slotMachineVariables, weights=slotWeights, k=3)
    wheel_two = random.choices(slotMachineVariables, weights=slotWeights, k=3)
    wheel_three = random.choices(slotMachineVariables, weights=slotWeights, k=3)
    return [wheel_one, wheel_two, wheel_three]

def is_three_of_a_kind(a, b, c):
    return a == b == c

def check_win(wheels):
    """Return a list of tuples containing (winning_line_name, winning_symbol)."""
    wins = []

    # Horizontal rows
    row_names = ["Top row", "Middle row", "Bottom row"]
    for row in range(3):
        if is_three_of_a_kind(wheels[0][row], wheels[1][row], wheels[2][row]):
            wins.append((row_names[row], wheels[0][row]))

    # Vertical columns
    col_names = ["Left wheel", "Center wheel", "Right wheel"]
    for col in range(3):
        if is_three_of_a_kind(wheels[col][0], wheels[col][1], wheels[col][2]):
            wins.append((col_names[col], wheels[col][0]))

    # Diagonals
    if is_three_of_a_kind(wheels[0][0], wheels[1][1], wheels[2][2]):
        wins.append(("Diagonal top-left to bottom-right", wheels[0][0]))
    if is_three_of_a_kind(wheels[0][2], wheels[1][1], wheels[2][0]):
        wins.append(("Diagonal bottom-left to top-right", wheels[0][2]))

    return wins

def calculate_slot_multiplier(winning_lines):
    """Return a total payout multiplier based on which symbols won."""
    total_multiplier = 0.0
    for line_name, symbol in winning_lines:
        total_multiplier += SYMBOL_MULTIPLIERS.get(symbol, 0.0)
    return total_multiplier

def print_spin(wheels):
    print("Top      Middle    Bottom")
    print(f"{wheels[0][0]:<9}{wheels[1][0]:<10}{wheels[2][0]}")
    print(f"{wheels[0][1]:<9}{wheels[1][1]:<10}{wheels[2][1]}")
    print(f"{wheels[0][2]:<9}{wheels[1][2]:<10}{wheels[2][2]}")
