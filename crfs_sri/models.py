
from data import *
from decoders import *
from feature_managers import *
from graphs import *
from inference_algorithms import *
from parsers import *
from performance_measures import *
from state_managers import *
from train_algorithms import *

import cPickle
import os
import copy
import gzip


class Model(object):

    # __init__
    def __init__(self):

        return


    def init(self): 

        return


    def save(self, model_file):

        d = {'decoder' : self.decoder, 
             'feature manager' : self.feature_manager, 
             'graph' : self.graph, 
             'parameters' : self.parameters,  
             'state manager' : self.state_manager, 
             }
        
	FILE = gzip.GzipFile(model_file, 'wb')
	FILE.write(cPickle.dumps(d, 1))
	FILE.close()

        return


    def load(self, model_file):

	FILE = gzip.GzipFile(model_file, 'rb')

        d = cPickle.load(FILE)

        self.decoder = d['decoder']
        self.feature_manager = d['feature manager']
        self.graph = d['graph']
        self.parameters = d['parameters']
        self.state_manager = d['state manager']

        FILE.close()

        return


    def initialize_parameters(self):

        num_features = self.feature_manager.num_features

        if self.graph.id in ['non-structured-chain']:

            parameters = []
            num_parameters = 0

            for clique_set_index in self.graph.get_clique_set_index_set(size = 'single'):
                parameters.append(numpy.zeros((self.state_manager.num_states[clique_set_index], num_features), dtype=numpy.float32)) 
                num_parameters += self.state_manager.num_states[clique_set_index] * num_features

        else:
                
            parameters = []
            num_parameters = 0
                
            for clique_set_index in self.graph.get_clique_set_index_set(size = 'single'):
                parameters.append(numpy.zeros((self.state_manager.num_states[clique_set_index], self.feature_manager.num_features), dtype=numpy.float32)) 
                num_parameters += self.state_manager.num_states[clique_set_index] * num_features

            for clique_set_index in self.graph.get_clique_set_index_set(size = 'double'):
                parameters.append(numpy.zeros((self.state_manager.num_states[clique_set_index], self.feature_manager.num_features), dtype=numpy.float32)) 
                num_parameters += self.state_manager.num_states[clique_set_index] * num_features

        return parameters, num_parameters
    
    
        
    def train(self, # corpus_id,               
#              train_algorithm_id, 
              graph_id, 
              performance_measure_id,
#              inference_id, 
              single_pass, 
              train_file, 
              devel_file, 
              prediction_file,               
              verbose):

        print "\tpreprocess"

#         self.corpus_id = corpus_id

        # initialize graph

        if graph_id == 'non-structured-chain':
            self.graph = NonStructuredChain()
        elif graph_id == 'first-order-chain':
            self.graph = FirstOrderChain()

        # initialize state manager
                
        if graph_id == 'non-structured-chain':
            self.state_manager = NonStructuredStateManager(train_file, self.graph)
        else:
            self.state_manager = StructuredStateManager(train_file, self.graph)

        # initialize feature manager
    
        self.feature_manager = FeatureManager(train_file, self.graph)

        # initialize devel and train data sets

        train_data = TrainData(train_file, self.feature_manager, self.state_manager, self.graph)
        devel_data = DevelData(devel_file, self.feature_manager, self.state_manager, self.graph)

        print '\ttrain data size:', train_data.size
        print '\tdevel data size:', devel_data.size
        print "\tnumber of features:", self.feature_manager.num_features
        print "\tnumber of states per clique set:", self.state_manager.num_states
        for clique_set_index in self.graph.get_clique_set_index_set(size = 'single'):
            print "\tstates:", self.state_manager.state_sets[clique_set_index]

        # initialize decoder
            
        if graph_id == 'non-structured-chain':
            inference_algorithm = NonStructuredInference(self.graph, self.state_manager)
        else:
            inference_algorithm = ExactInference(self.graph, self.state_manager)

        self.decoder = Decoder(inference_algorithm, self.graph, performance_measure_id)

        # initialize training algorithm
            
        if graph_id == 'non-structured-chain':
            inference_algorithm = NonStructuredInference(self.graph, self.state_manager)
        else:
            inference_algorithm = ExactInference(self.graph, self.state_manager)

        train_algorithm = Perceptron(inference_algorithm, single_pass, self.graph, self.decoder)

        # train

        initial_parameters, num_parameters = self.initialize_parameters() 

        if verbose:
            print "\tnumber of parameters:", num_parameters
            print

        print "\ttrain"
        print
        print "\tgraph structure:", self.graph.id
        print "\ttrain algorithm:", train_algorithm.id
        print
        
        self.parameters, hyperparameters, performance, time_consumption = train_algorithm.train(initial_parameters, train_data, devel_data, prediction_file, devel_file, verbose)

        # print

        print

        for key, value in hyperparameters.items():

            print "\t%s: %.1f" % (key, value)

        print 

#        print "\t%s: %.1f" % (performance['target measure id'], performance['target measure'])
#        print '\ttarget performance measure id: %s' % performance['target measure id']

        for key, value in performance['all'].items():
            
            accuracy=value
            print '\t%s (devel): %.2f' % (key, value)

        print

        for key, value in time_consumption.items():

            print "\t%s: %.1f" % (key, value)

        print                
              
        return accuracy 
    


    def apply(self, test_file, prediction_file, reference_file, verbose):

        # initialize data

        test_data = TestData(test_file, self.feature_manager, self.state_manager, self.graph)

        print
        print "\ttest set size:", test_data.size
        print

        # decode

        performance = self.decoder.decode(self.parameters, test_data, prediction_file, reference_file, num_subsets = 10)

        measures = {}

        if performance != None:

            for sub_performance in performance:

                for measure_id, value in sub_performance['all'].items():
                    
                    if measure_id not in measures:
                        
                        measures[measure_id] = [value]

                    else:

                        measures[measure_id].append(value)

            #for measure_id, values in measures.items():

                #print '\t%s (test): %.2f$\pm$%.2f ' % (measure_id, numpy.mean(values), numpy.std(values))

        print
            
        return


            







