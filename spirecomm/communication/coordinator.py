import sys
import queue
import threading
import json
import collections

from spirecomm.spire.game import Game
from spirecomm.spire.screen import ScreenType
import spirecomm.communication.action


def read_stdin(input_queue):
    """Read lines from stdin and write them to a queue

    :param input_queue: A queue, to which lines from stdin will be written
    :type input_queue: queue.Queue
    :return: None
    """
    while True:
        stdin_input = ""
        while True:
            input_char = sys.stdin.read(1)
            if input_char == '\n':
                break
            else:
                stdin_input += input_char
        input_queue.put(stdin_input)


def write_stdout(output_queue):
    """Read lines from a queue and write them to stdout

    :param output_queue: A queue, from which this function will receive lines of text
    :type output_queue: queue.Queue
    :return: None
    """
    while True:
        output = output_queue.get()
        print(output, end='\n', flush=True)


class Coordinator:

    def __init__(self):
        self.input_queue = queue.Queue()
        self.output_queue = queue.Queue()
        self.input_thread = threading.Thread(target=read_stdin, args=(self.input_queue,))
        self.output_thread = threading.Thread(target=write_stdout, args=(self.output_queue,))
        self.input_thread.daemon = True
        self.input_thread.start()
        self.output_thread.daemon = True
        self.output_thread.start()
        self.action_queue = collections.deque()
        self.state_change_callback = None
        self.out_of_game_callback = None
        self.error_callback = None
        self.game_is_ready = False
        self.stop_after_run = False
        self.in_game = False
        self.last_game_state = None
        self.last_available_commands = []
        self.last_error = None

    def signal_ready(self):
        self.send_message("ready")

    def send_message(self, message):
        self.output_queue.put(message)
        self.game_is_ready = False

    def add_action_to_queue(self, action):
        self.action_queue.append(action)

    def clear_actions(self):
        self.action_queue.clear()

    def execute_next_action(self):
        action = self.action_queue.popleft()
        action.execute(self)

    def execute_next_action_if_ready(self):
        if len(self.action_queue) > 0 and self.action_queue[0].can_be_executed(self):
            self.execute_next_action()

    def register_state_change_callback(self, new_callback):
        self.state_change_callback = new_callback

    def register_command_error_callback(self, new_callback):
        self.error_callback = new_callback

    def register_out_of_game_callback(self, new_callback):
        self.out_of_game_callback = new_callback

    def perform_callbacks(self):
        if self.in_game:
            self.state_change_callback(self.last_game_state, self.last_available_commands)
        else:
            self.out_of_game_callback()

    def get_next_raw_message(self, block=False):
        if block or not self.input_queue.empty():
            return self.input_queue.get()

    def receive_game_state_update(self, block=False):
        message = self.get_next_raw_message(block)
        if message is not None:
            communication_state = json.loads(message)
            self.last_error = communication_state.get("error", None)
            self.game_is_ready = communication_state.get("ready_for_command")
            if self.last_error is None:
                self.in_game = communication_state.get("in_game")
                if self.in_game:
                    self.last_game_state = Game.from_json(communication_state.get("game_state"))
                    self.last_available_commands = communication_state.get("available_commands")
            return True
        return False

    def handle_game_state_update(self, block=False, perform_callbacks=True):
        state_changed = self.receive_game_state_update(block)
        if state_changed:
            if self.last_error is not None:
                self.action_queue.clear()
                new_action = self.error_callback(self.last_error)
                self.add_action_to_queue(new_action)
            elif self.in_game:
                if len(self.action_queue) == 0 and perform_callbacks:
                    new_action = self.state_change_callback(self.last_game_state, self.last_available_commands)
                    self.add_action_to_queue(new_action)
            elif self.stop_after_run:
                self.clear_actions()
            elif perform_callbacks:
                new_action = self.out_of_game_callback()
                self.add_action_to_queue(new_action)
        return state_changed

    def run(self):
        while True:
            self.execute_next_action_if_ready()
            self.handle_game_state_update()

    def play_one_game(self, player_class, ascension_level=0, seed=None):
        self.clear_actions()
        while not self.game_is_ready:
            self.receive_game_state_update(True)
        if not self.in_game:
            spirecomm.communication.action.StartGameAction(player_class, ascension_level, seed).execute(self)
            self.handle_game_state_update(block=True)
        while self.in_game:
            self.execute_next_action_if_ready()
            self.handle_game_state_update()
        if self.last_game_state.screen_type == ScreenType.GAME_OVER:
            return self.last_game_state.screen.victory
        else:
            return False

