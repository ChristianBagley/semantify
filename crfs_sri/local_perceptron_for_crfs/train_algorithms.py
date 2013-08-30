
import numpy
import copy
import os

import time


class TrainAlgorithm(object):

    # __init__
    def __init__(self):

        return



class Perceptron(TrainAlgorithm):
    # averaged perceptron

    def __init__(self, 
                 inference_algorithm, 
                 single_pass, 
                 graph, 
                 decoder,
                 init_inference_algorithm = None):
        
        super(Perceptron, self).__init__()
                                                             
        self.inference_algorithm = inference_algorithm
        self.single_pass = single_pass
        self.graph = graph
        self.decoder = decoder
        self.init_inference_algorithm = init_inference_algorithm

        if single_pass:
            
            self.id = 'single pass averaged generalized perceptron'
            
        else:

            self.id = 'averaged generalized perceptron'

        return


    def train(self, parameters, 
              train_data, 
              devel_data, 
              prediction_file, 
              reference_file, 
              verbose):
        
#        from tempfile import TemporaryFile
#        tmp_file = TemporaryFile()

        cum_parameters = copy.deepcopy(parameters)
        hyperparameters = {'number of passes' : 1, 'number of updates' : 1}

        previous_performance = {'target measure' : None}
        time_consumption = {'train cpu time' : 0.0, 'devel cpu time' : 0.0}

        while(1):

            # make a pass over train data

            tic = time.clock()

            parameters, cum_parameters, hyperparameters, error_free = self.make_pass(train_data, parameters, cum_parameters, hyperparameters)
            
            time_consumption['train cpu time'] += time.clock() - tic

#            if self.init_inference_algorithm == None:

            parameters = self.compute_average_parameters(parameters, cum_parameters, hyperparameters)

            # decode devel data

            tic = time.clock()

            performance = self.decoder.decode(parameters, devel_data, prediction_file, reference_file)

            time_consumption['devel cpu time'] += time.clock() - tic

            if verbose:
                print "\tpass index %d, cpu time so far %.1f, %s (devel) %.2f" % (hyperparameters['number of passes'], time_consumption['train cpu time'], performance['target measure id'], performance['target measure'])

            # check for termination 

            if self.single_pass:

                break

            elif performance['target measure'] <= previous_performance['target measure']:

#                    tmp_file.seek(0)
#                    parameters = numpy.load(tmp_file)

                parameters = previous_parameters
                performance = previous_performance

                if self.init_inference_algorithm == None:

                    break

                else:

                    self.init_inference_algorithm = None
#                    cum_parameters = copy.deepcopy(parameters)
                    print "\tmove on to global training"
#                    hyperparameters['number of updates'] = 1

            else:

#                numpy.save(tmp_file, parameters)

                previous_parameters = copy.copy(parameters)
                previous_performance = copy.copy(performance)

#                if self.init_inference_algorithm == None:
                
                parameters = self.reverse_parameter_averaging(parameters, cum_parameters, hyperparameters)

                hyperparameters['number of passes'] += 1

        return parameters, hyperparameters, performance, time_consumption


    def make_pass(self, train_data, 
                  parameters, 
                  cum_parameters, 
                  hyperparameters):
        
        error_free = True

        for instance_index in range(train_data.size):

            # get instance

            observation, len_observation, feature_vector_set, true_state_index_set, true_state_set = train_data.get_instance(instance_index)

            # inference 

            if self.init_inference_algorithm != None:

                map_state_index_set, map_state_set = self.init_inference_algorithm.compute_map_state_index_set(parameters, feature_vector_set, len_observation, true_state_index_set)

            else:

                if self.inference_algorithm.id in ['pseudo inference', 'piecewise-pseudo (factor-as-piece) inference', 'piecewise-pseudo (chain-as-piece) inference']:
                    map_state_index_set, map_state_set = self.inference_algorithm.compute_map_state_index_set(parameters, feature_vector_set, len_observation, true_state_index_set)
                else:
                    map_state_index_set, map_state_set = self.inference_algorithm.compute_map_state_index_set(parameters, feature_vector_set, len_observation)

            # update parameters

            parameters, cum_parameters, hyperparameters, update_required = self.update_parameters(parameters, cum_parameters, hyperparameters, map_state_index_set, true_state_index_set, feature_vector_set, len_observation)

            hyperparameters['number of updates'] += 1

            if update_required:

                error_free = False

        return parameters, cum_parameters, hyperparameters, error_free


    def update_parameters(self, parameters, 
                          cum_parameters, 
                          hyperparameters,
                          map_state_index_set, 
                          true_state_index_set, 
                          feature_vector_set, 
                          len_observation):
        
        num_updates = hyperparameters['number of updates']

        if self.init_inference_algorithm != None:

            update_required = False

            for clique_set_index in self.graph.get_clique_set_index_set(size = 'double'): 
                
                clique_set_index_i, clique_set_index_j = self.graph.get_sub_clique_set_index_set(clique_set_index)

                for clique in self.graph.get_clique_set(len_observation, clique_set_index):

                    node_i, node_j = clique.position                    
                    
                    for free_node in clique.position:

                        map_state_index = map_state_index_set[(clique.position, free_node)]
                        true_state_index = true_state_index_set[clique.position]
                
                        if map_state_index != true_state_index:

                            (node_i, node_j) = clique.position
                            (l_i, t_i) = node_i
                            (l_j, t_j) = node_j
                            
                            feature_vector = feature_vector_set[t_j]
                            (feature_index_set, activation_set) = feature_vector

                            # update parameters
                            parameters[clique_set_index][true_state_index, feature_index_set] += activation_set
                            parameters[clique_set_index][map_state_index, feature_index_set] -= activation_set

                            if free_node == node_j:
                                
                                # update parameters
                                parameters[clique_set_index_j][true_state_index_set[node_j], feature_index_set] += activation_set
                                parameters[clique_set_index_j][map_state_index_set[(node_j, clique.position)], feature_index_set] -= activation_set
                                
                            update_required = True

        elif self.inference_algorithm.id in ['nonstructured inference']:

            update_required = False
            
            for clique_set_index in self.graph.get_clique_set_index_set(size = 'single'): 
                    
                for clique in self.graph.get_clique_set(len_observation, clique_set_index):

                    map_state_index = map_state_index_set[clique.position]
                    true_state_index = true_state_index_set[clique.position]
                
                    if map_state_index != true_state_index:

                        (l_j, t_j) = clique.position
                        
                        feature_vector = feature_vector_set[t_j]
                        (feature_index_set, activation_set) = feature_vector

                        # update parameters
                        parameters[clique_set_index][true_state_index, feature_index_set] += activation_set
                        parameters[clique_set_index][map_state_index, feature_index_set] -= activation_set

                        # update cumulative parameters                       
                        cum_parameters[clique_set_index][true_state_index, feature_index_set] += num_updates*activation_set
                        cum_parameters[clique_set_index][map_state_index, feature_index_set] -= num_updates*activation_set

                        update_required = True

        elif self.inference_algorithm.id in ['exact inference', 
                                             'loopy belief propagation inference']:
           
            update_required = False

            for clique_set_index in self.graph.get_clique_set_index_set(size = 'single'): 

                for clique in self.graph.get_clique_set(len_observation, clique_set_index):

                    map_state_index = map_state_index_set[clique.position]
                    true_state_index = true_state_index_set[clique.position]
                        
                    if map_state_index != true_state_index:

                        l, t = clique.position
                        
                        feature_vector = feature_vector_set[t]
                        (feature_index_set, activation_set) = feature_vector

                        # update parameters
                        parameters[clique_set_index][true_state_index, feature_index_set] += activation_set
                        parameters[clique_set_index][map_state_index, feature_index_set] -= activation_set
                            
                        # update cumulative parameters                       
                        cum_parameters[clique_set_index][true_state_index, feature_index_set] += num_updates*activation_set
                        cum_parameters[clique_set_index][map_state_index, feature_index_set] -= num_updates*activation_set

                        update_required = True

            for clique_set_index in self.graph.get_clique_set_index_set(size = 'double'): 

                clique_set_index_i, clique_set_index_j = self.graph.get_sub_clique_set_index_set(clique_set_index)
                
                for clique in self.graph.get_clique_set(len_observation, clique_set_index):

                    map_state_index = map_state_index_set[clique.position]
                    true_state_index = true_state_index_set[clique.position]
                        
                    if map_state_index != true_state_index:

                        node_i, node_j = clique.position
                        l_i, t_i = node_i
                        l_j, t_j = node_j
                        
                        feature_vector = feature_vector_set[t_j]
                        (feature_index_set, activation_set) = feature_vector

                        # update parameters
                        parameters[clique_set_index][true_state_index, feature_index_set] += activation_set
                        parameters[clique_set_index][map_state_index, feature_index_set] -= activation_set
                            
                        # update cumulative parameters                       
                        cum_parameters[clique_set_index][true_state_index, feature_index_set] += num_updates*activation_set
                        cum_parameters[clique_set_index][map_state_index, feature_index_set] -= num_updates*activation_set

        elif self.inference_algorithm.id in ['piecewise-pseudo (factor-as-piece) inference',
                                             'piecewise-pseudo (chain-as-piece) inference']:

                update_required = False

                for clique_set_index in self.graph.get_clique_set_index_set(size = 'double'): 
                
                    clique_set_index_i, clique_set_index_j = self.graph.get_sub_clique_set_index_set(clique_set_index)

                    for clique in self.graph.get_clique_set(len_observation, clique_set_index):

                        node_i, node_j = clique.position                    

                        for free_node in clique.position:

                            map_state_index = map_state_index_set[(clique.position, free_node)]
                            true_state_index = true_state_index_set[clique.position]
                
                            if map_state_index != true_state_index:

                                (node_i, node_j) = clique.position
                                (l_i, t_i) = node_i
                                (l_j, t_j) = node_j
                        
                                feature_vector = feature_vector_set[t_j]
                                (feature_index_set, activation_set) = feature_vector

                                # update parameters
                                parameters[clique_set_index][true_state_index, feature_index_set] += activation_set
                                parameters[clique_set_index][map_state_index, feature_index_set] -= activation_set

                                # update cumulative parameters                       
                                cum_parameters[clique_set_index][true_state_index, feature_index_set] += num_updates*activation_set
                                cum_parameters[clique_set_index][map_state_index, feature_index_set] -= num_updates*activation_set
                                
                                if free_node == node_j:
                                
                                    # update parameters
                                    parameters[clique_set_index_j][true_state_index_set[node_j], feature_index_set] += activation_set
                                    parameters[clique_set_index_j][map_state_index_set[(node_j, clique.position)], feature_index_set] -= activation_set
                                
                                    # update cumulative parameters                       
                                    cum_parameters[clique_set_index_j][true_state_index_set[node_j], feature_index_set] += num_updates*activation_set
                                    cum_parameters[clique_set_index_j][map_state_index_set[(node_j, clique.position)], feature_index_set] -= num_updates*activation_set                                
                                update_required = True

        elif self.inference_algorithm.id in ['pseudo inference']:

            update_required = False

            for clique_set_index in self.graph.get_clique_set_index_set(size = 'single'): 
                
                for clique in self.graph.get_clique_set(len_observation, clique_set_index):

                    map_state_index = map_state_index_set[clique.position]
                    true_state_index = true_state_index_set[clique.position]
                
                    if map_state_index != true_state_index:

                        l, t = clique.position
                        
                        feature_vector = feature_vector_set[t]
                        (feature_index_set, activation_set) = feature_vector

                        # update parameters
                        parameters[clique_set_index][true_state_index, feature_index_set] += activation_set
                        parameters[clique_set_index][map_state_index, feature_index_set] -= activation_set

                        # update cumulative parameters                       
                        cum_parameters[clique_set_index][true_state_index, feature_index_set] += num_updates*activation_set
                        cum_parameters[clique_set_index][map_state_index, feature_index_set] -= num_updates*activation_set
                                
                        update_required = True

                        for dependent_clique in self.graph.get_dependent_clique_set(len_observation, clique.position):
                
                            clique_set_index_i, clique_set_index_j = self.graph.get_sub_clique_set_index_set(dependent_clique.clique_set_index)

                            map_state_index = map_state_index_set[(dependent_clique.position, clique.position)]
                            true_state_index = true_state_index_set[dependent_clique.position]
                            
                            (node_i, node_j) = dependent_clique.position
                            (l_i, t_i) = node_i
                            (l_j, t_j) = node_j
                        
                            feature_vector = feature_vector_set[t_j]
                            (feature_index_set, activation_set) = feature_vector

                            # update parameters
                            parameters[dependent_clique.clique_set_index][true_state_index, feature_index_set] += activation_set
                            parameters[dependent_clique.clique_set_index][map_state_index, feature_index_set] -= activation_set

                            # update cumulative parameters                       
                            cum_parameters[dependent_clique.clique_set_index][true_state_index, feature_index_set] += num_updates*activation_set
                            cum_parameters[dependent_clique.clique_set_index][map_state_index, feature_index_set] -= num_updates*activation_set

        elif self.inference_algorithm.id in ['piecewise (factor-as-piece) inference',
                                             'piecewise (chain-as-piece) inference']:
           
            update_required = False

            for clique_set_index in self.graph.get_clique_set_index_set(size = 'double'): 

                clique_set_index_i, clique_set_index_j = self.graph.get_sub_clique_set_index_set(clique_set_index)
                
                for clique in self.graph.get_clique_set(len_observation, clique_set_index):

                    map_state_index = map_state_index_set[clique.position]
                    true_state_index = true_state_index_set[clique.position]
                        
                    if map_state_index != true_state_index:

                        node_i, node_j = clique.position
                        l_i, t_i = node_i
                        l_j, t_j = node_j
                        
                        feature_vector = feature_vector_set[t_j]
                        (feature_index_set, activation_set) = feature_vector

                        # update parameters
                        parameters[clique_set_index][true_state_index, feature_index_set] += activation_set
                        parameters[clique_set_index][map_state_index, feature_index_set] -= activation_set
                            
                        # update cumulative parameters                       
                        cum_parameters[clique_set_index][true_state_index, feature_index_set] += num_updates*activation_set
                        cum_parameters[clique_set_index][map_state_index, feature_index_set] -= num_updates*activation_set

                        map_state_index_j = map_state_index_set[(node_j, clique.position)]
                        true_state_index_j = true_state_index_set[node_j]
                            
                        if map_state_index_j != true_state_index_j:

                            # update parameters
                            parameters[clique_set_index_j][true_state_index_j, feature_index_set] += activation_set
                            parameters[clique_set_index_j][map_state_index_j, feature_index_set] -= activation_set
                                
                            # update cumulative parameters                       
                            cum_parameters[clique_set_index_j][true_state_index_j, feature_index_set] += num_updates*activation_set
                            cum_parameters[clique_set_index_j][map_state_index_j, feature_index_set] -= num_updates*activation_set

                        update_required = True

        elif self.inference_algorithm.id in ['piecewise (chain-as-piece) inference']:
           
            update_required = False

            for clique_set_index in self.graph.get_clique_set_index_set(size = 'double'): 

                clique_set_index_i, clique_set_index_j = self.graph.get_sub_clique_set_index_set(clique_set_index)
                
                for clique in self.graph.get_clique_set(len_observation, clique_set_index):

                    map_state_index = map_state_index_set[clique.position]
                    true_state_index = true_state_index_set[clique.position]
                        
                    if map_state_index != true_state_index:

                        node_i, node_j = clique.position
                        l_i, t_i = node_i
                        l_j, t_j = node_j
                        
                        feature_vector = feature_vector_set[t_j]
                        (feature_index_set, activation_set) = feature_vector

                        # update parameters
                        parameters[clique_set_index][true_state_index, feature_index_set] += activation_set
                        parameters[clique_set_index][map_state_index, feature_index_set] -= activation_set
                            
                        # update cumulative parameters                       
                        cum_parameters[clique_set_index][true_state_index, feature_index_set] += num_updates*activation_set
                        cum_parameters[clique_set_index][map_state_index, feature_index_set] -= num_updates*activation_set

                        map_state_index_j = map_state_index_set[(node_j, clique.position)]
                        true_state_index_j = true_state_index_set[node_j]
                            
                        if map_state_index_j != true_state_index_j:

                            # update parameters
                            parameters[clique_set_index_j][true_state_index_j, feature_index_set] += activation_set
                            parameters[clique_set_index_j][map_state_index_j, feature_index_set] -= activation_set
                                
                            # update cumulative parameters                       
                            cum_parameters[clique_set_index_j][true_state_index_j, feature_index_set] += num_updates*activation_set
                            cum_parameters[clique_set_index_j][map_state_index_j, feature_index_set] -= num_updates*activation_set

                        update_required = True

        return parameters, cum_parameters, hyperparameters, update_required


    def compute_average_parameters(self, parameters, cum_parameters, hyperparameters):

        num_updates = float(hyperparameters['number of updates'])

        if self.inference_algorithm.id in ['nonstructured inference']:

            for clique_set_index in self.graph.get_clique_set_index_set(size = 'single'):
                parameters[clique_set_index] -= cum_parameters[clique_set_index]/num_updates

        else:

            for clique_set_index in self.graph.get_clique_set_index_set(size = 'all'):
                parameters[clique_set_index] -= cum_parameters[clique_set_index]/num_updates

        return parameters


    def reverse_parameter_averaging(self, parameters, cum_parameters, hyperparameters): 

        num_updates = float(hyperparameters['number of updates'])

        if self.inference_algorithm.id in ['nonstructured inference']:

            for clique_set_index in self.graph.get_clique_set_index_set(size = 'single'):
                parameters[clique_set_index] += cum_parameters[clique_set_index]/num_updates

        else:

            for clique_set_index in self.graph.get_clique_set_index_set(size = 'all'):
                parameters[clique_set_index] += cum_parameters[clique_set_index]/num_updates

        return parameters




