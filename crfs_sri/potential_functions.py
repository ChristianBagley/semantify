
import numpy




class NonStructuredPotentialFunction(object):


    def __init__(self, graph, state_manager):

        self.graph = graph        
        self.state_manager = state_manager

        return


    def compute_potential_vector_set(self, parameters, feature_vector_set, len_observation, observation = None):

        # return this
        potential_vector_set = {}

        for clique_set_index in self.graph.get_clique_set_index_set(size = 'single'):
                       
            for clique in self.graph.get_clique_set(len_observation, clique_set_index):

                l_j, t_j = clique.position

                feature_vector = feature_vector_set[t_j]

                potential_vector_set[clique.position] = self.compute_potential_vector(parameters, clique_set_index, feature_vector)
                
        return potential_vector_set


    def compute_potential_vector(self, parameters, clique_set_index, feature_vector):

        feature_index_set, activation_set = feature_vector

        potential_vector = numpy.sum(parameters[clique_set_index][:, feature_index_set]*activation_set, 1)

        return potential_vector



class StructuredPotentialFunction(object):


    def __init__(self, graph, state_manager):

        self.graph = graph        
        self.state_manager = state_manager

        return


    def compute_potential_vector_set(self, parameters, feature_vector_set, len_observation, observation = None):

        # return this
        potential_vector_set = {}

        for clique_set_index in self.graph.get_clique_set_index_set(size = 'single'):
                       
            for clique in self.graph.get_clique_set(len_observation, clique_set_index):

                l_j, t_j = clique.position

                feature_vector = feature_vector_set[t_j]

                potential_vector_set[clique.position] = self.compute_potential_vector(parameters, clique_set_index, feature_vector)

        for clique_set_index in self.graph.get_clique_set_index_set(size = 'double'):
                       
            clique_set_index_i, clique_set_index_j = self.graph.get_sub_clique_set_index_set(clique_set_index)

            for clique in self.graph.get_clique_set(len_observation, clique_set_index):
                
                node_i, node_j = clique.position
                l_i, t_i = node_i
                l_j, t_j = node_j
                
                if observation != None:

                    state_index_set = self.state_manager.tag_dictionary.get(observation[t_j], -1)

                    if state_index_set == -1:

                        potential_vector = self.compute_potential_vector(parameters, clique_set_index, feature_vector_set[t_j])
                        potential_vector = potential_vector.reshape((self.state_manager.num_states[clique_set_index_i], self.state_manager.num_states[clique_set_index_j]))
                    
                        potential_vector_j = potential_vector_set[node_j] # self.compute_potential_vector(parameters, clique_set_index_j, feature_vector_set[t_j])

                        potential_vector_set[clique.position] = potential_vector+potential_vector_j                        

                    else:
                    
                        p = self.compute_potential_vector(parameters, clique_set_index, feature_vector_set[t_j])
                        p = p.reshape((self.state_manager.num_states[clique_set_index_i], self.state_manager.num_states[clique_set_index_j]))
                        potential_vector = numpy.zeros_like(p)
                        potential_vector[:, state_index_set] = p[:, state_index_set]

                        p = potential_vector_set[node_j] # self.compute_potential_vector(parameters, clique_set_index_j, feature_vector_set[t_j])
                        potential_vector_j = numpy.zeros_like(p)
                        potential_vector_j[state_index_set] = p[state_index_set]

                        potential_vector_set[clique.position] = potential_vector+potential_vector_j

                else:

                    potential_vector = self.compute_potential_vector(parameters, clique_set_index, feature_vector_set[t_j])
                    potential_vector = potential_vector.reshape((self.state_manager.num_states[clique_set_index_i], self.state_manager.num_states[clique_set_index_j]))
                    
                    potential_vector_j = potential_vector_set[node_j] # self.compute_potential_vector(parameters, clique_set_index_j, feature_vector_set[t_j])

                    potential_vector_set[clique.position] = potential_vector+potential_vector_j

        return potential_vector_set


    def compute_potential_vector(self, parameters, clique_set_index, feature_vector):

        (feature_index_set, activation_set) = feature_vector

        potential_vector = numpy.sum(parameters[clique_set_index][:, feature_index_set]*activation_set, 1)

        return potential_vector

