


from AgentBrain import AgentBrain

from sc2.position import Point2

class TrainableAgent:

    def __init__(self):
        self.enemy_location_0 : Point2 = Point2((32,32))
        self.training_data = None

    #Set a new brain to use
    def use_brain(self, brain : AgentBrain):
        raise NotImplementedError

    #Get the current brain
    def get_brain(self) -> AgentBrain:
        raise NotImplementedError


