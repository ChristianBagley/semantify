
from potential_functions import *

import numpy
import copy

# fixme
import numpy.random


class InferenceAlgorithm(object):

    def __init__(self, graph, state_manager):

        self.graph = graph
        self.state_manager = state_manager
        
        return





class NonStructuredInference(InferenceAlgorithm):


    def __init__(self, graph, state_manager):

        super(NonStructuredInference, self).__init__(graph, state_manager)

        self.id = 'nonstructured inference'

        self.potential_function = NonStructuredPotentialFunction(graph, state_manager)

        return


    def compute_map_state_index_set(self, parameters, feature_vector_set, len_observation, observation = None):

        potential_vector_set = self.potential_function.compute_potential_vector_set(parameters, feature_vector_set, len_observation, observation)
        
        map_state_index_set = {}

        for clique_set_index in self.graph.get_clique_set_index_set(size = 'single'): 

            for clique in self.graph.get_clique_set(len_observation, clique_set_index):

                map_state_index_set[clique.position] = numpy.argmax(potential_vector_set[clique.position])

        map_state_set = self.state_manager.convert_state_index_set_to_state_set(map_state_index_set, len_observation)

        return map_state_index_set, map_state_set




class ExactInference(InferenceAlgorithm):
    # exact inference for a first order chain

    def __init__(self, graph, state_manager):

        super(ExactInference, self).__init__(graph, state_manager)

        self.id = 'exact inference'

        self.potential_function = StructuredPotentialFunction(graph, state_manager)

        return


    def compute_map_state_index_set(self, parameters, feature_vector_set, len_observation, observation = None):
        
        potential_vector_set = self.potential_function.compute_potential_vector_set(parameters, feature_vector_set, len_observation, observation)

        map_state_index_set = {}

        backtrack_pointers = -1*numpy.ones((len_observation, self.state_manager.num_states[0]))
                                           
        a = None
        
        for t_j in range(1, len_observation):
                                               
            t_i = t_j - 1
            ab = potential_vector_set[((0, t_i), (0, t_j))]
            if a != None:
                a_ab = a.reshape(a.size, 1) + ab # broadcast
            else:
                a_ab = ab
            backtrack_pointers[t_j, :] = numpy.argmax(a_ab, 0)
            a = numpy.max(a_ab, 0)

        map_state_index_set[(0, t_j)] = int(numpy.argmax(a))

        # backward
                
        for t_j in range(len_observation-1, 0, -1):
                                          
            t_i = t_j - 1

            map_j = map_state_index_set[(0, t_j)] # t_j already has likeliest state
            map_i = int(backtrack_pointers[t_j, map_j])
            map_state_index_set[(0, t_i)] = map_i
            map_state_index_set[((0, t_i), (0, t_j))] = int(map_i*self.state_manager.num_states[0] + map_j)

        map_state_set = self.state_manager.convert_state_index_set_to_state_set(map_state_index_set, len_observation)

        return map_state_index_set, map_state_set




class LoopyBeliefPropagation(InferenceAlgorithm):
    # loopy belief propagation (Yedidia, 2003)

    def __init__(self, graph, state_manager):

        super(LoopyBeliefPropagation, self).__init__(graph, state_manager)

        self.id = 'loopy belief propagation inference'

        self.potential_function = StructuredPotentialFunction(graph, state_manager)

        return


    def compute_map_state_index_set(self, parameters, feature_vector_set, len_observation):

        self.map_inference = True

        potential_vector_set = self.potential_function.compute_potential_vector_set(parameters, feature_vector_set, len_observation)

        for key, value in potential_vector_set.items():

            potential_vector_set[key] = numpy.exp(value)

        initial_messages, message_keys = self.initialize_messages(len_observation)
        converged_messages = self.pass_messages(potential_vector_set, initial_messages, message_keys, len_observation)
        map_state_index_set = self.get_map_state_index_set(potential_vector_set, converged_messages, message_keys, len_observation)
        map_state_set = self.state_manager.convert_state_index_set_to_state_set(map_state_index_set, len_observation)

        return map_state_index_set, map_state_set


    def initialize_messages(self, len_observation):
        
        # return this
        messages = {}
        message_keys = {'forward' : [], 'backward': []} 

        # initialize from nodes

        for clique_set_index in self.graph.get_clique_set_index_set(size = 'single'):

            for clique in self.graph.get_clique_set(len_observation, clique_set_index):

                node_i = clique.position
                messages[node_i] = {}
                        
        for clique_set_index in self.graph.get_clique_set_index_set(size = 'double'):

            clique_set_index_i, clique_set_index_j = self.graph.get_sub_clique_set_index_set(clique_set_index)

            for clique in self.graph.get_clique_set(len_observation, clique_set_index):

                (node_i, node_j) = clique.position

                # forward

                message_keys['forward'].append((node_i, node_j))
                messages[node_i][node_j] = numpy.ones(self.state_manager.num_states[clique_set_index_j])/self.state_manager.num_states[clique_set_index_j]

                # backward

                message_keys['backward'].insert(0, (node_j, node_i))
                messages[node_j][node_i] = numpy.ones(self.state_manager.num_states[clique_set_index_i])/self.state_manager.num_states[clique_set_index_i]

#        for key, value in messages.items():
#            print key, value

        return messages, message_keys


    def pass_messages(self, potential_vector_set, messages, message_keys, len_observation):

        message_change_threshold = 10**-2
        max_num_iterations = 10**2
        iteration_index = 0 # number of times node has sent and received message to and from all neighbors
        
        while(1):

            converged = True
            
            for flow_direction in ['forward', 'backward']:
                
                for message_key in message_keys[flow_direction]:

                    (node_i, node_j) = message_key

                    old_message = messages[node_i][node_j]

                    updated_message = self.update_message(potential_vector_set, message_key, messages, flow_direction)
                    
                    messages[node_i][node_j] = updated_message

                    if converged and numpy.max(numpy.abs(1-(updated_message/old_message))) > message_change_threshold:
                        converged = False

            iteration_index += 1

            if converged or iteration_index == max_num_iterations:
#                print "convergence:", iteration_index
                break

        return messages


    def update_message(self, potential_vector_set, message_key, messages, flow_direction):
        # update message from node i to node j
        # note: (Yedidia, 2002) equation (14)

        (node_i, node_j) = message_key

        if flow_direction == 'forward':
            potential_vector_ij = potential_vector_set[(node_i, node_j)]
        else:
            potential_vector_ij = potential_vector_set[(node_j, node_i)].T

        if self.map_inference:
        
            incoming_message_product_i = self.combine_incoming_messages(node_i, node_j, messages)
            incoming_message_product_i = incoming_message_product_i.reshape(incoming_message_product_i.size, 1)
            updated_message = numpy.max(incoming_message_product_i * potential_vector_ij, 0) # broadcast
            updated_message /= numpy.sum(updated_message) # normalize

        else:

            incoming_message_product_i = self.combine_incoming_messages(node_i, node_j, messages)
            incoming_message_product_i = incoming_message_product_i.reshape(incoming_message_product_i.size, 1)
            updated_message = numpy.sum(incoming_message_product_i * potential_vector_ij, 0) # broadcast
            updated_message /= numpy.sum(updated_message) # normalize

        return updated_message


    def combine_incoming_messages(self, node_i, node_j, messages):
        # sum/multiply incoming messages to node i skipping node j

        incoming_message_product = None

        for neighbor in messages[node_i]:

            if neighbor != node_j: # skip node_j; see compute_updated_message()

                if incoming_message_product == None:

                    incoming_message_product = copy.copy(messages[neighbor][node_i])

                else:

                    incoming_message_product *= messages[neighbor][node_i]

        return incoming_message_product


    def get_map_state_index_set(self, potential_vector_set, converged_messages, message_keys, len_observation):

        map_state_index_set = {}

        for clique_set_index in self.graph.get_clique_set_index_set(size = 'single'):

            for clique in self.graph.get_clique_set(len_observation, clique_set_index):

                incoming_message_product = self.combine_incoming_messages(clique.position, None, converged_messages)

                map_state_index_set[clique.position] = numpy.argmax(incoming_message_product)

        for clique_set_index in self.graph.get_clique_set_index_set(size = 'double'):

            clique_set_index_i, clique_set_index_j = self.graph.get_sub_clique_set_index_set(clique_set_index)

            for clique in self.graph.get_clique_set(len_observation, clique_set_index):
                   
                (node_i, node_j) = clique.position
                
                potential_vector_ij = potential_vector_set[(node_i, node_j)]
            
                incoming_message_product_i = self.combine_incoming_messages(node_i, node_j, converged_messages)
                incoming_message_product_i = incoming_message_product_i.reshape(incoming_message_product_i.size, 1)
                incoming_message_product_j = self.combine_incoming_messages(node_j, node_i, converged_messages)
                incoming_message_product_j = incoming_message_product_j.reshape(1, incoming_message_product_j.size)

                map_state_index_set[clique.position] = numpy.argmax(incoming_message_product_i * potential_vector_ij * incoming_message_product_j)

#        for key, value in map_state_index_set.items():
#            print key, value
#        raw_input("")

        return map_state_index_set





class FactorAsPieceInference(InferenceAlgorithm):

    def __init__(self, graph, state_manager):

        super(FactorAsPieceInference, self).__init__(graph, state_manager)

        self.id = 'piecewise (factor-as-piece) inference'

        self.potential_function = StructuredPotentialFunction(graph, state_manager)

        return


    def compute_map_state_index_set(self, parameters, feature_vector_set, len_observation):

        potential_vector_set = self.potential_function.compute_potential_vector_set(parameters, feature_vector_set, len_observation)
        
        map_state_index_set = {}

        for clique_set_index in self.graph.get_clique_set_index_set(size = 'double'): 

            clique_set_index_i, clique_set_index_j = self.graph.get_sub_clique_set_index_set(clique_set_index)

            for clique in self.graph.get_clique_set(len_observation, clique_set_index):

                map_state_index = numpy.argmax(potential_vector_set[clique.position])

                map_state_index_set[clique.position] = map_state_index

                map_state_index_j = map_state_index % self.state_manager.num_states[clique_set_index_j]
                
                node_i, node_j = clique.position

                map_state_index_set[(node_j, clique.position)] = map_state_index_j 

        map_state_set = None # this inference is not used at decoding stage

        return map_state_index_set, map_state_set



class ChainAsPieceInference(InferenceAlgorithm):
    # this is a semi-hack of a chain-as-piece approximation for a two-level grid structure

    def __init__(self, graph, state_manager):

        super(ChainAsPieceInference, self).__init__(graph, state_manager)

        self.id = 'piecewise (chain-as-piece) inference'

        self.potential_function = StructuredPotentialFunction(graph, state_manager)

        return



    def compute_map_state_index_set(self, parameters, feature_vector_set, len_observation):

        potential_vector_set = self.potential_function.compute_potential_vector_set(parameters, feature_vector_set, len_observation)

        map_state_index_set = {}

        # chains up-down (are cliques)
        
        for clique_set_index in [2]:

            clique_set_index_i, clique_set_index_j = self.graph.get_sub_clique_set_index_set(clique_set_index)

            for clique in self.graph.get_clique_set(len_observation, clique_set_index):

                map_state_index = numpy.argmax(potential_vector_set[clique.position])

                map_state_index_set[clique.position] = map_state_index

                map_state_index_j = map_state_index % self.state_manager.num_states[clique_set_index_j]
                
                node_i, node_j = clique.position

                map_state_index_set[(node_j, clique.position)] = map_state_index_j

        # chains left-right

        for chain_index in range(2):

            backtrack_pointers = -1*numpy.ones((len_observation, self.state_manager.num_states[chain_index]))
                                           
            a = None
        
            for t_j in range(1, len_observation):
                                               
                t_i = t_j - 1
                ab = potential_vector_set[((chain_index, t_i), (chain_index, t_j))]
                if a != None:
                    a_ab = a.reshape(a.size, 1) + ab # broadcast
                else:
                    a_ab = ab
                backtrack_pointers[t_j, :] = numpy.argmax(a_ab, 0)
                a = numpy.max(a_ab, 0)

            map_state_index_set[(chain_index, t_j)] = int(numpy.argmax(a))

            # backward
                
            for t_j in range(len_observation-1, 0, -1):
                                          
                t_i = t_j - 1

                map_j = map_state_index_set[(chain_index, t_j)] # t_j already has likeliest state
                map_state_index_set[((chain_index, t_j), ((chain_index, t_i), (chain_index, t_j)))] = map_j
                map_i = int(backtrack_pointers[t_j, map_j])
                map_state_index_set[(chain_index, t_i)] = map_i
                map_state_index_set[((chain_index, t_i), (chain_index, t_j))] = int(map_i*self.state_manager.num_states[chain_index] + map_j)
                
        map_state_set = None # this inference is not used at decoding stage

        return map_state_index_set, map_state_set





class PseudoInference(InferenceAlgorithm):


    def __init__(self, graph, state_manager):

        super(PseudoInference, self).__init__(graph, state_manager)

        self.id = 'pseudo inference'

        self.pseudo_state_index_sets = self.prepare_pseudo_state_index_sets(state_manager)
        self.potential_function = PseudoPotentialFunction(graph, state_manager, self.pseudo_state_index_sets)

        return


    def prepare_pseudo_state_index_sets(self, state_manager):

        pseudo_state_index_sets = []

        for clique_set_index in self.graph.get_clique_set_index_set(size = 'single'):

            pseudo_state_index_sets.append(None)

        for clique_set_index in self.graph.get_clique_set_index_set(size = 'double'):
        
            state_set_cardinality = state_manager.num_states[clique_set_index]

            clique_set_index_i, clique_set_index_j = self.graph.get_sub_clique_set_index_set(clique_set_index)            
            state_set_cardinality_i = state_manager.num_states[clique_set_index_i]
            state_set_cardinality_j = state_manager.num_states[clique_set_index_j]
            
            pseudo_state_index_sets.append(numpy.array(range(state_set_cardinality)).reshape(state_set_cardinality_i, state_set_cardinality_j))

        return pseudo_state_index_sets


    def compute_map_state_index_set(self, parameters, feature_vector_set, len_observation, true_state_index_set):
        
        potential_vector_set = self.potential_function.compute_potential_vector_set(parameters, feature_vector_set, len_observation, true_state_index_set)

        map_state_index_set = {}

        for clique_set_index in self.graph.get_clique_set_index_set(size = 'single'):

            for clique in self.graph.get_clique_set(len_observation, clique_set_index):

                summed_potential_vector = None

                for dependent_clique in self.graph.get_dependent_clique_set(len_observation, clique.position):
                    
                    if summed_potential_vector == None: 

                        summed_potential_vector = potential_vector_set[(dependent_clique.position, clique.position)]

                    else:

                        summed_potential_vector += potential_vector_set[(dependent_clique.position, clique.position)]

                map_state_index = numpy.argmax(summed_potential_vector)

                map_state_index_set[clique.position] = map_state_index

                for dependent_clique in self.graph.get_dependent_clique_set(len_observation, clique.position):

                    map_state_index_set[(clique.position, dependent_clique.position)] = map_state_index

                    clique_set_index_i, clique_set_index_j = self.graph.get_sub_clique_set_index_set(dependent_clique.clique_set_index)
                    node_i, node_j = dependent_clique.position

                    if node_i == clique.position: # node i is free

                        state_index_i = map_state_index
                        state_index_j = true_state_index_set[node_j]

                    elif node_j == clique.position: # node j is free

                        state_index_i = true_state_index_set[node_i]
                        state_index_j = map_state_index                        

                    map_state_index_set[(dependent_clique.position, clique.position)] = state_index_i*self.state_manager.num_states[clique_set_index_j]+state_index_j

        map_state_set = None # this inference is not used at decoding stage

        return map_state_index_set, map_state_set





class FactorAsPiecePseudoInference(PseudoInference):


    def __init__(self, graph, state_manager):

        super(FactorAsPiecePseudoInference, self).__init__(graph, state_manager)

        self.id = 'piecewise-pseudo (factor-as-piece) inference'

        self.pseudo_state_index_sets = self.prepare_pseudo_state_index_sets(state_manager)
        self.potential_function = PseudoPotentialFunction(graph, state_manager, self.pseudo_state_index_sets)

        return


    def compute_map_state_index_set(self, parameters, feature_vector_set, len_observation, true_state_index_set):
        
        potential_vector_set = self.potential_function.compute_potential_vector_set(parameters, feature_vector_set, len_observation, true_state_index_set)

        map_state_index_set = {}

        for clique_set_index in self.graph.get_clique_set_index_set(size = 'double'):

            clique_set_index_i, clique_set_index_j = self.graph.get_sub_clique_set_index_set(clique_set_index)

            for clique in self.graph.get_clique_set(len_observation, clique_set_index):

                node_i, node_j = clique.position

                for free_node in clique.position:

                    map_state_index = numpy.argmax(potential_vector_set[(clique.position, free_node)])

                    map_state_index_set[(free_node, clique.position)] = map_state_index

                    if free_node == node_i: 

                        state_index_i = map_state_index
                        state_index_j = true_state_index_set[node_j]

                    elif free_node == node_j:

                        state_index_i = true_state_index_set[node_i]
                        state_index_j = map_state_index                        

                    map_state_index_set[(clique.position, free_node)] = state_index_i*self.state_manager.num_states[clique_set_index_j]+state_index_j

        map_state_set = None # this inference is not used at decoding stage

        return map_state_index_set, map_state_set





class ChainAsPiecePseudoInference(PseudoInference):
    # this is a semi-hack of a chain-as-piece approximation for a two-level grid structure

    def __init__(self, graph, state_manager):

        super(ChainAsPiecePseudoInference, self).__init__(graph, state_manager)

        self.id = 'piecewise-pseudo (chain-as-piece) inference'

        self.pseudo_state_index_sets = self.prepare_pseudo_state_index_sets(state_manager)
        self.potential_function = PseudoPotentialFunction(graph, state_manager, self.pseudo_state_index_sets)

        return



    def compute_map_state_index_set(self, parameters, feature_vector_set, len_observation, true_state_index_set):

        potential_vector_set = self.potential_function.compute_potential_vector_set(parameters, feature_vector_set, len_observation, true_state_index_set)

        map_state_index_set = {}

        # chains up-down (are cliques)

        for clique_set_index in [2]:

            for clique in self.graph.get_clique_set(len_observation, clique_set_index):

                node_i, node_j = clique.position
                clique_set_index_i, clique_set_index_j = self.graph.get_sub_clique_set_index_set(clique_set_index)

                for free_node in clique.position:

                    potential_vector = potential_vector_set[(clique.position, free_node)]
                    map_state_index = numpy.argmax(potential_vector)

                    map_state_index_set[(free_node, clique.position)] = map_state_index
                    
                    if free_node == node_i: 

                        state_index_i = map_state_index
                        state_index_j = true_state_index_set[node_j]

                    elif free_node == node_j:

                        state_index_i = true_state_index_set[node_i]
                        state_index_j = map_state_index                        

                    map_state_index_set[(clique.position, free_node)] = state_index_i*self.state_manager.num_states[clique_set_index_j]+state_index_j


        # chains left-right

        for clique_set_index in self.graph.get_clique_set_index_set(size = 'single'):

            for clique in self.graph.get_clique_set(len_observation, clique_set_index):

                (l, t) = clique.position
                summed_potential_vector = None

                for dependent_clique in self.graph.get_dependent_clique_set(len_observation, clique.position):

                    node_i, node_j = dependent_clique.position
                    (l_i, t_i) = node_i
                    (l_j, t_j) = node_j
                    
                    if l_i != l or l_j != l:
                        continue

                    if summed_potential_vector == None: 

                        summed_potential_vector = potential_vector_set[(dependent_clique.position, clique.position)]

                    else:

                        summed_potential_vector += potential_vector_set[(dependent_clique.position, clique.position)]

                map_state_index = numpy.argmax(summed_potential_vector)

                for dependent_clique in self.graph.get_dependent_clique_set(len_observation, clique.position):

                    node_i, node_j = dependent_clique.position
                    (l_i, t_i) = node_i
                    (l_j, t_j) = node_j
                    
                    if l_i != l or l_j != l:
                        continue

                    map_state_index_set[(clique.position, dependent_clique.position)] = map_state_index

                    clique_set_index_i, clique_set_index_j = self.graph.get_sub_clique_set_index_set(dependent_clique.clique_set_index)
                    node_i, node_j = dependent_clique.position

                    if node_i == clique.position: # node i is free

                        state_index_i = map_state_index
                        state_index_j = true_state_index_set[node_j]

                    elif node_j == clique.position: # node j is free

                        state_index_i = true_state_index_set[node_i]
                        state_index_j = map_state_index                        

                    map_state_index_set[(dependent_clique.position, clique.position)] = state_index_i*self.state_manager.num_states[clique_set_index_j]+state_index_j

        map_state_set = None # this inference is not used at decoding stage

        return  map_state_index_set, map_state_set





