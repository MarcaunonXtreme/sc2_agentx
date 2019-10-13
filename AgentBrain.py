import numpy as np

import pickle

from sc2 import Race
from copy import deepcopy

# An agent brain is a collection of networks that can be used to make decisions with


class Network:
    #TODO: switch over to floats everywhere!!! not doubles!
    #TODO: allow supporting different network configurations?
    def __init__(self, max_input, max_outputs = 1, hidden_count=16):
        self.inputs = max_input
        self.outputs = max_outputs
        self.w0 = np.random.randn(max_input,hidden_count)
        self.w0 /= 8.0
        self.b0 = np.random.randn(hidden_count)
        self.b0 /= 16.0
        self.w1 = np.random.randn(hidden_count, max_outputs)
        self.w1 /= 8.0
        self.b1 = np.random.randn(max_outputs)
        self.b1 /= 16.0
        self.generation = 0
        #self.scenario_count = 0
        self.score = 0
        self.stars = 0

    def process(self, inputs_values):
        assert inputs_values.ndim == 1
        assert len(inputs_values) == self.inputs
        tmp = inputs_values
        #first dense layer:
        tmp = np.matmul(tmp, self.w0)
        tmp = np.add(tmp, self.b0)
        #relu activator:
        tmp = np.maximum(tmp,0)
        #second dense layer:
        tmp = np.matmul(tmp, self.w1)
        tmp = np.add(tmp,self.b1)
        #Linear output
        assert tmp.ndim == 1
        assert len(tmp) == self.outputs
        return tmp


    def mutate(self, factor1 = 0.05, factor2 = 0.20):
        self._mutate_a(self.w0,factor1,factor2)
        self._mutate_a(self.b0, factor1, factor2)
        self._mutate_a(self.w1, factor1, factor2)
        self._mutate_a(self.b1, factor1, factor2)

    @staticmethod
    def _mutate_a(a , factor1, factor2):
        tmp = np.random.random(a.shape)
        tmp = tmp <= factor1
        delta = np.random.randn(*a.shape) * factor2
        delta = delta * tmp
        a += delta
        np.clip(a, -10.0, 10.0, out=a) # Prevent weights from going 2 crazy!



class AgentBrain:

    def __init__(self, filename = "brain.p"):
        self.default_filename = filename
        self.networks = {Race.Zerg : dict(), Race.Terran : dict(), Race.Protoss : dict()}
        self.used = False # Used to track if all brains have been used on a scenario

    def get_existing_network(self, race, name):
        nets = self.networks[race]
        return nets.get(name, None)

    def get_network(self, race, name, max_inputs, max_outputs, hidden_count=24) -> Network:
        nets = self.networks[race]
        assert isinstance(nets,dict)
        if name in nets:
            result = nets[name]
        else:
            result = Network(max_inputs, max_outputs=max_outputs, hidden_count=hidden_count)
            nets[name] = result

        #TODO: deal better with this
        assert result.inputs >= max_inputs
        assert result.outputs >= max_outputs
        #TODO: check or increase hidden also?
        return result

    def has_network(self, race, name):
        return name in self.networks[race]

    # this assigns score to all networks 
    def score_networks(self, race, network_names : list, score):
        nets = self.networks[race]
        for n in network_names:
            if n in nets:
                nets[n].score = score
            else:
                print(f"Warning: Giving score to non-existing network: {n}")

    def get_score(self, race, network_name):
        nets = self.networks[race]
        if network_name in nets:
            return nets[network_name].score
        else:
            return 0

    def give_stars(self, race, network_name, stars):
        nets = self.networks[race]
        if network_name in nets:
            nets[network_name].stars = min(nets[network_name].stars + stars, 4)
            return nets[network_name].stars
        else:
            print(f"Warning: Giving stars to non-existing network: {network_name}")
            return 0

    def get_stars(self, race, network_name):
        nets = self.networks[race]
        if network_name in nets:
            return nets[network_name].stars
        else:
            return -2

    def get_average_stars(self, race):
        nets = self.networks[race]
        s = [n.stars for n in nets]
        return np.average(s)

    def delete_network(self, race, name):
        print(f"Deleting network {race}:{name} from brain")
        nets = self.networks[race]
        if name in nets:
            del name[nets]

    def copy_and_mutate_from(self, race, name, source_brain, factor1=0.1,factor2=0.2):
        assert isinstance(source_brain, AgentBrain)
        net = deepcopy(source_brain.networks[race][name])
        assert isinstance(net, Network)
        net.mutate(factor1,factor2)
        net.generation += 1
        if name in self.networks[race]:
            del self.networks[race][name]
        self.networks[race][name] = net

    def save(self, filename):
        if not filename:
            filename = self.default_filename
        print(f"Saving Agent Brain to file : {filename}")
        f = open(filename, "wb")
        pickle.dump(self, f)
        f.close()

    @staticmethod
    def load(filename):
        print(f"Loading Agent Brain from file : {filename}")
        try:
            f = open(filename,"rb")
            result = pickle.load(f)
            f.close()
            assert isinstance(result, AgentBrain) #loading something else?
            return result
        except Exception as e:
            print(f"Exception: {e}")
            print("Failed to load, creating new Brain")
            return AgentBrain(filename)

    def reset_scores(self):
        self.used = False
        for nets in self.networks.values():
            for n in nets.values():
                n.score = 0


