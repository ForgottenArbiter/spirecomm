import spirecomm.spire.card


class Power:

    def __init__(self, power_id, name, amount, damage=0, misc=0, just_applied=False, card=None):
        self.power_id = power_id
        self.power_name = name
        self.amount = amount
        self.damage = damage
        self.misc = misc
        self.just_applied = just_applied
        self.card = card

    @classmethod
    def from_json(cls, json_object):
        power_id = json_object["id"]
        name = json_object["name"]
        amount = json_object["amount"]
        damage = json_object.get("damage", 0)
        misc = json_object.get("misc", 0)
        just_applied = json_object.get("just_applied", False)
        card = json_object.get("card", None)
        if card is not None:
            card = spirecomm.spire.card.Card.from_json(card)
        return cls(power_id, name, amount, damage, misc, just_applied, card)

    def __eq__(self, other):
        return self.power_id == other.power_id and self.amount == other.amount
