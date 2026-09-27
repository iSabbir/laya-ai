import random
import time

from laya import Router

LANES = 3
ROWS = 12
CAR_ROW = ROWS - 1


def build_description(car_lane, obstacles, decision_hint=None):
    obstacle_text = []
    if not obstacles:
        obstacle_text.append("No obstacles currently in view.")
    else:
        for row, lane in sorted(obstacles):
            obstacle_text.append(f"lane {lane + 1} at row {row + 1}")

    text = (
        f"A 3-lane road. The car is in lane {car_lane + 1} (left=1, middle=2, right=3). "
        f"The bottom row is the current car position. Obstacles are at: {', '.join(obstacle_text)}. "
        f"Only one lane move left or right is allowed each turn. "
        f"Choose the safer direction to avoid collisions."
    )
    if decision_hint:
        text += f" Prefer {decision_hint}."
    return text


def render(car_lane, obstacles):
    board = []
    for row in range(ROWS):
        cells = []
        for lane in range(LANES):
            cell = " "
            if (row, lane) in obstacles:
                cell = "X"
            if row == CAR_ROW and lane == car_lane:
                cell = "A"
            cells.append(cell)
        board.append(" | ".join(cells))
    print("\n".join(board))
    print("Lanes: 1  2  3")
    print("-" * 20)


def choose_move(router, car_lane, obstacles):
    state = build_description(car_lane, obstacles)
    questions = {
        "move": {
            "type": "choice",
            "instructions": (
                "You are driving a car in a 3-lane road. Choose the safest direction for the next move. "
                "The car can only move one lane left or right each turn."
            ),
            "criteria": {
                "left": "move one lane left to avoid an obstacle",
                "right": "move one lane right to avoid an obstacle",
            },
        }
    }
    result = router.predict(state, questions)
    decision = result["answers"]["move"]["choice"]

    # Make sure the move is valid at the edges.
    if decision == "left" and car_lane == 0:
        return "right"
    if decision == "right" and car_lane == LANES - 1:
        return "left"
    return decision


def game():
    router = Router()
    car_lane = 1
    obstacles = set()
    score = 0
    dead = False

    for step in range(1, 200):
        print(f"\n=== STEP {step} | SCORE {score} ===")

        if random.random() < 0.8:
            obstacle_lane = random.randint(0, LANES - 1)
            obstacle_row = 0
            obstacles.add((obstacle_row, obstacle_lane))

        move = choose_move(router, car_lane, obstacles)
        print(f"Laya decision: {move.upper()}")

        if move == "left":
            if car_lane > 0:
                car_lane -= 1
        elif move == "right":
            if car_lane < LANES - 1:
                car_lane += 1

        next_obstacles = set()
        for row, lane in obstacles:
            next_row = row + 1
            if next_row <= CAR_ROW:
                next_obstacles.add((next_row, lane))
        obstacles = next_obstacles

        if (CAR_ROW, car_lane) in obstacles:
            dead = True
            print("CRASH! The car hit an obstacle.")
            render(car_lane, obstacles)
            break

        score += 1
        render(car_lane, obstacles)
        time.sleep(0.6)

    if not dead:
        print("\nYou survived the full run! Great driving.")
    print(f"Final score: {score}")


if __name__ == "__main__":
    print("Laya car game: left/right decisions only")
    print("The model chooses a move each turn based on obstacle positions.")
    game()
