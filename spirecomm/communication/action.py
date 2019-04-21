from spirecomm.spire.screen import ScreenType, RewardType


class Action:

    def __init__(self, command="state", requires_game_ready=True):
        self.command = command
        self.requires_game_ready = requires_game_ready

    def can_be_executed(self, coordinator):
        if self.requires_game_ready:
            return coordinator.game_is_ready
        else:
            return True

    def execute(self, coordinator):
        coordinator.send_message(self.command)


class PlayCardAction(Action):

    def __init__(self, card=None, card_index=-1, target_monster=None, target_index=None):
        super().__init__("play")
        self.card = card
        self.card_index = card_index
        self.target_index = target_index
        self.target_monster = target_monster

    def execute(self, coordinator):
        if self.card is not None:
            self.card_index = coordinator.last_game_state.hand.index(self.card)
        if self.card_index == -1:
            raise Exception("Specified card for CardAction is not in hand")
        hand_card_index = self.card_index + 1
        if self.target_monster is not None:
            self.target_index = self.target_monster.monster_index
        if self.target_index is None:
            coordinator.send_message("{} {}".format(self.command, hand_card_index))
        else:
            coordinator.send_message("{} {} {}".format(self.command, hand_card_index, self.target_index))


class PotionAction(Action):

    def __init__(self, use, potion=None, potion_index=-1, target_monster=None, target_index=None):
        super().__init__("potion")
        self.use = use
        self.potion = potion
        self.potion_index = potion_index
        self.target_monster = target_monster
        self.target_index = target_index

    def execute(self, coordinator):
        if self.potion is not None:
            self.potion_index = coordinator.last_game_state.potions.index(self.potion)
        if self.potion_index == -1:
            raise Exception("Specified potion for PotionAction is not available")
        arguments = [self.command]
        if self.use:
            arguments.append("use")
        else:
            arguments.append("discard")
        arguments.append(str(self.potion_index))
        if self.target_monster is not None:
            self.target_index = self.target_monster.monster_index
        if self.target_index is not None:
            arguments.append(str(self.target_index))
        coordinator.send_message(" ".join(arguments))


class EndTurnAction(Action):

    def __init__(self):
        super().__init__("end")


class ProceedAction(Action):

    def __init__(self):
        super().__init__("proceed")


class CancelAction(Action):

    def __init__(self):
        super().__init__("cancel")


class ChooseAction(Action):

    def __init__(self, choice_index=0, name=None):
        super().__init__("choose")
        self.choice_index = choice_index
        self.name = name

    def execute(self, coordinator):
        if self.name is not None:
            coordinator.send_message("{} {}".format(self.command, self.name))
        else:
            coordinator.send_message("{} {}".format(self.command, self.choice_index))


class ChooseShopkeeperAction(ChooseAction):

    def __init__(self):
        super().__init__(name="shop")


class OpenChestAction(ChooseAction):

    def __init__(self):
        super().__init__(name="open")


class BuyCardAction(ChooseAction):

    def __init__(self, card):
        super().__init__(name=card.name)


class BuyPotionAction(ChooseAction):

    def __init__(self, potion):
        super().__init__(name=potion.name)

    def execute(self, coordinator):
        if coordinator.game.are_potions_full():
            raise Exception("Cannot buy potion because potion slots are full.")
        super().execute(coordinator)


class BuyRelicAction(ChooseAction):

    def __init__(self, relic):
        super().__init__(name=relic.name)


class BuyPurgeAction(Action):

    def __init__(self, card_to_purge=None):
        super().__init__()
        self.card_to_purge = card_to_purge

    def execute(self, coordinator):
        if coordinator.last_game_state.screen_type != ScreenType.SHOP_SCREEN:
            raise Exception("BuyPurgeAction is only available on a Shop Screen")
        coordinator.add_action_to_queue(ChooseAction(name="purge"))
        if self.card_to_purge is not None:
            coordinator.add_action_to_queue(GridSelectAction([self.card_to_purge]))


class EventOptionAction(ChooseAction):

    def __init__(self, option):
        super().__init__(choice_index=option.choice_index)


class RestAction(ChooseAction):

    def __init__(self, rest_option):
        super().__init__(name=rest_option.name)


class CardRewardAction(ChooseAction):

    def __init__(self, card=None, bowl=False):
        if bowl:
            name = "bowl"
        elif card is not None:
            name = card.name
        else:
            raise Exception("Must provide a card for CardRewardAction if not choosing the Singing Bowl")
        super().__init__(name=name)


class CombatRewardAction(ChooseAction):

    def __init__(self, combat_reward):
        self.combat_reward = combat_reward
        super().__init__()

    def execute(self, coordinator):
        if coordinator.last_game_state.screen_type != ScreenType.COMBAT_REWARD:
            raise Exception("CombatRewardAction is only available on a Combat Reward Screen.")
        reward_list = coordinator.last_game_state.screen.rewards
        if self.combat_reward not in reward_list:
            raise Exception("Reward is not available: {}".format(self.combat_reward.reward_type))
        if self.combat_reward.reward_type == RewardType.POTION and coordinator.last_game_state.are_potions_full():
            raise Exception("Cannot choose potion reward with full potion slots.")
        self.choice_index = reward_list.index(self.combat_reward)
        super().execute(coordinator)


class BossRewardAction(ChooseAction):

    def __init__(self, relic):
        super().__init__(name=relic.name)


class OptionalGridConfirmAction(Action):

    def __init__(self):
        super().__init__()

    def execute(self, coordinator):
        if coordinator.last_game_state.screen_type == ScreenType.GRID and coordinator.last_game_state.screen.confirm_up:
            coordinator.add_action_to_queue(ProceedAction())
        else:
            coordinator.add_action_to_queue(StateAction())


class GridSelectAction(Action):

    def __init__(self, cards):
        self.cards = cards
        super().__init__()

    def execute(self, coordinator):
        if coordinator.last_game_state.screen_type != ScreenType.GRID:
            raise Exception("GridSelectAction is only available on a Grid Select Screen.")
        num_selected_cards = len(coordinator.last_game_state.screen.selected_cards)
        num_remaining_cards = coordinator.last_game_state.screen.num_cards - num_selected_cards
        available_cards = coordinator.last_game_state.screen.cards
        if len(self.cards) != num_remaining_cards:
            raise Exception("Wrong number of cards selected for GridSelectAction (provided {}, need {})".format(len(self.cards), num_remaining_cards))
        chosen_indices = []
        for card in self.cards:
            if card not in available_cards:
                raise Exception("Card {} is not available in the Grid Select Screen".format(card.name))
            else:
                chosen_indices.append(available_cards.index(card))
        chosen_indices.sort(reverse=True)
        for index in chosen_indices:
            coordinator.add_action_to_queue(ChooseAction(choice_index=index))
        coordinator.add_action_to_queue(OptionalGridConfirmAction())


class ChooseMapNodeAction(ChooseAction):

    def __init__(self, node):
        self.node = node
        super().__init__()

    def execute(self, coordinator):
        if coordinator.last_game_state.screen_type != ScreenType.MAP:
            raise Exception("MapChoiceAction is only available on a Map Screen")
        next_nodes = coordinator.last_game_state.screen.next_nodes
        if self.node not in next_nodes:
            raise Exception("Node {} is not available to choose.".format(self.node))
        self.choice_index = next_nodes.index(self.node)
        super().execute(coordinator)


class ChooseMapBossAction(ChooseAction):

    def __init__(self):
        super().__init__()

    def execute(self, coordinator):
        if coordinator.last_game_state.screen_type != ScreenType.MAP:
            raise Exception("ChooseMapBossAction is only available on a Map Screen")
        if not coordinator.last_game_state.screen.boss_available:
            raise Exception("The boss is not available to choose.")
        self.name = "boss"
        super().execute(coordinator)


class StartGameAction(Action):

    def __init__(self, player_class, ascension_level=0, seed=None):
        super().__init__("start")
        self.player_class = player_class
        self.ascension_level = ascension_level
        self.seed = seed

    def execute(self, coordinator):
        arguments = [self.command, self.player_class.name, str(self.ascension_level)]
        if self.seed is not None:
            arguments.append(str(self.seed))
        coordinator.send_message(" ".join(arguments))


class StateAction(Action):

    def __init__(self, requires_game_ready=False):
        super().__init__(command="state", requires_game_ready=False)

