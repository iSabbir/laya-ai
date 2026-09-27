import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from laya import Router

HOST = '127.0.0.1'
PORT = 8000
ROOT = Path(__file__).resolve().parent
router = Router()


def build_description(car_lane, obstacles):
    obstacle_text = []
    if not obstacles:
        obstacle_text.append('No obstacles in view.')
    else:
        for ob in sorted(obstacles, key=lambda o: (o['y'], o['lane'])):
            obstacle_text.append(f"lane {ob['lane'] + 1} at row {int(ob['y']) + 1}")

    return (
        f"A 3-lane road. The car is in lane {car_lane + 1}. "
        f"Obstacles are at: {', '.join(obstacle_text)}. "
        f"Choose the safer move. The car may move only one lane left or right each turn."
    )


def build_snake_description(snake, food, direction, grid_size=20):
    if not snake:
        snake = [{'x': 10, 'y': 10}]

    head = snake[0]
    body = ', '.join(f"({segment['x']},{segment['y']})" for segment in snake[1:5]) or 'none'
    direction_text = (
        'up' if direction.get('y') == -1 else
        'down' if direction.get('y') == 1 else
        'left' if direction.get('x') == -1 else
        'right'
    )

    valid_moves = []
    for name, delta in {'up': (0, -1), 'down': (0, 1), 'left': (-1, 0), 'right': (1, 0)}.items():
        x = head['x'] + delta[0]
        y = head['y'] + delta[1]
        blocked = x < 0 or x >= grid_size or y < 0 or y >= grid_size or any(segment['x'] == x and segment['y'] == y for segment in snake)
        if not blocked:
            valid_moves.append(name)

    invalid_moves = [name for name in ['up', 'down', 'left', 'right'] if name not in valid_moves]

    return (
        f"A snake game on a {grid_size} by {grid_size} grid. "
        f"The snake head is at ({head['x']}, {head['y']}). "
        f"The current body segments are: {body}. "
        f"The food is at ({food['x']}, {food['y']}). "
        f"The snake is moving {direction_text}. "
        f"Valid next moves are: {', '.join(valid_moves) if valid_moves else 'none'}. "
        f"Blocked moves are: {', '.join(invalid_moves) if invalid_moves else 'none'}. "
        f"Choose the safest move from the valid moves only. Prefer a move that gets closer to the food without hitting the wall or the body."
    )


def choose_target_move(snake, food, direction, grid_size=20):
    head = snake[0] if snake else {'x': 10, 'y': 10}
    moves = {'up': (0, -1), 'down': (0, 1), 'left': (-1, 0), 'right': (1, 0)}
    candidates = []

    def inside(point):
        return 0 <= point[0] < grid_size and 0 <= point[1] < grid_size

    def flood_space(start, occupied):
        queue = [start]
        visited = {start}
        while queue:
            point = queue.pop(0)
            for delta in moves.values():
                next_point = (point[0] + delta[0], point[1] + delta[1])
                if inside(next_point) and next_point not in occupied and next_point not in visited:
                    visited.add(next_point)
                    queue.append(next_point)
        return len(visited)

    for name, delta in moves.items():
        if len(snake) > 1 and delta[0] == -direction.get('x', 0) and delta[1] == -direction.get('y', 0):
            continue

        next_head = (head['x'] + delta[0], head['y'] + delta[1])
        if not inside(next_head):
            continue

        eating = next_head == (food['x'], food['y'])
        occupied = {(segment['x'], segment['y']) for segment in snake[:-1] if not eating}
        if next_head in occupied:
            continue

        simulated_body = [next_head] + list(occupied)
        occupied_after = set(simulated_body)
        space = flood_space(next_head, occupied_after - {next_head})

        queue = [(next_head, 0)]
        visited = {next_head}
        food_distance = None
        while queue:
            point, distance = queue.pop(0)
            if point == (food['x'], food['y']):
                food_distance = distance
                break
            for move_delta in moves.values():
                next_point = (point[0] + move_delta[0], point[1] + move_delta[1])
                if inside(next_point) and next_point not in occupied_after and next_point not in visited:
                    visited.add(next_point)
                    queue.append((next_point, distance + 1))

        candidates.append((food_distance is None, food_distance or grid_size * grid_size, -space, name))

    spacious_candidates = [candidate for candidate in candidates if -candidate[2] >= len(snake) + 2]
    if spacious_candidates:
        candidates = spacious_candidates

    if not candidates:
        return None

    candidates.sort()
    return candidates[0][3]


class Handler(BaseHTTPRequestHandler):
    def write_response(self, body):
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError):
            pass

    def do_GET(self):
        if self.path in ('/', '/index.html'):
            file_path = ROOT / 'index.html'
        elif self.path in ('/snake', '/snake.html'):
            file_path = ROOT / 'snake.html'
        else:
            self.send_response(404)
            self.end_headers()
            return

        content = file_path.read_bytes()
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_POST(self):
        try:
            if self.path == '/move':
                length = int(self.headers.get('Content-Length', '0'))
                raw = self.rfile.read(length)
                payload = json.loads(raw.decode('utf-8'))

                car_lane = int(payload.get('carLane', 1))
                obstacles = payload.get('obstacles', [])
                state = build_description(car_lane, obstacles)
                questions = {
                    'move': {
                        'type': 'choice',
                        'instructions': 'Choose the safest direction for the next move.',
                        'criteria': {
                            'left': 'move one lane left to avoid an obstacle',
                            'right': 'move one lane right to avoid an obstacle',
                        },
                    }
                }

                try:
                    result = router.predict(state, questions)
                    decision = result['answers']['move']['choice']
                except Exception:
                    decision = 'right' if car_lane < 2 else 'left'

                if decision == 'left' and car_lane == 0:
                    decision = 'right'
                if decision == 'right' and car_lane == 2:
                    decision = 'left'

                body = json.dumps({'decision': decision}).encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.write_response(body)
                return

            if self.path == '/snake-move':
                length = int(self.headers.get('Content-Length', '0'))
                raw = self.rfile.read(length)
                payload = json.loads(raw.decode('utf-8'))

                snake = payload.get('snake', [])
                food = payload.get('food', {'x': 0, 'y': 0})
                direction = payload.get('direction', {'x': 1, 'y': 0})
                head = snake[0] if snake else {'x': 10, 'y': 10}
                state = build_snake_description(snake, food, direction)
                questions = {
                    'move': {
                        'type': 'choice',
                        'instructions': 'Choose the safest next move for the snake from the valid moves only.',
                        'criteria': {
                            'up': 'move up only if it is not blocked and helps avoid danger while approaching food',
                            'down': 'move down only if it is not blocked and helps avoid danger while approaching food',
                            'left': 'move left only if it is not blocked and helps avoid danger while approaching food',
                            'right': 'move right only if it is not blocked and helps avoid danger while approaching food',
                        },
                    }
                }

                try:
                    result = router.predict(state, questions)
                    model_decision = result['answers']['move']['choice']
                except Exception:
                    model_decision = 'right'

                decision = model_decision

                valid_moves = []
                for name, delta in {'up': (0, -1), 'down': (0, 1), 'left': (-1, 0), 'right': (1, 0)}.items():
                    x = head['x'] + delta[0]
                    y = head['y'] + delta[1]
                    blocked = x < 0 or x >= 20 or y < 0 or y >= 20 or any(segment['x'] == x and segment['y'] == y for segment in snake)
                    if not blocked:
                        valid_moves.append(name)

                if decision not in valid_moves or not valid_moves:
                    decision = valid_moves[0] if valid_moves else 'right'

                target_move = choose_target_move(snake, food, direction)
                if target_move and target_move in valid_moves:
                    decision = target_move

                distance = abs(head['x'] - food['x']) + abs(head['y'] - food['y'])
                body = json.dumps({
                    'decision': decision,
                    'prediction': model_decision,
                    'target': target_move or decision,
                    'distance': distance,
                    'adjusted': decision != model_decision,
                }).encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.write_response(body)
                return

            self.send_response(404)
            self.end_headers()
        except Exception:
            fallback = {'decision': 'right', 'prediction': 'fallback', 'target': 'right', 'distance': 0, 'adjusted': True}
            body = json.dumps(fallback).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.write_response(body)

        self.send_response(404)
        self.end_headers()

    def log_message(self, format, *args):
        return


if __name__ == '__main__':
    print(f'Running Laya game server at http://{HOST}:{PORT}')
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
