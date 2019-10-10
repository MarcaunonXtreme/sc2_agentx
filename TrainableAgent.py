


from AgentBrain import AgentBrain

from sc2.position import Point2

class TrainableAgent:

    def __init__(self):
        self.training_data = None
        self.setup_stage = 0

    #Set a new brain to use
    def use_brain(self, brain : AgentBrain):
        raise NotImplementedError

    #Get the current brain
    def get_brain(self) -> AgentBrain:
        raise NotImplementedError


