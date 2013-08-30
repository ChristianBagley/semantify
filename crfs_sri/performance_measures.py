
from parsers import *
from graphs import *



class PerformanceMeasure(object):

    def __init__(self):

        return

    def evaluate(self, prediction_file, reference_file): 

        prediction_file_parser = PredictionFileParser(prediction_file)
        reference_file_parser = ReferenceFileParser(reference_file)

        prediction_file_parser.open()
        reference_file_parser.open()

        statistics = self.initialize_statistics()
        
        if prediction_file_parser.size != reference_file_parser.size:
            print 'fatal warning: prediction and reference sizes do not match: %d vs %d!' % (prediction_file_parser.size, reference_file_parser.size)

        for instance_index in range(prediction_file_parser.size):

            observation, len_observation, predicted_state_set = prediction_file_parser.parse(instance_index)
            observation, len_observation, true_state_set = reference_file_parser.parse(instance_index)

            statistics = self.update_statistics(statistics, predicted_state_set, true_state_set, observation, len_observation)
            
        performance = self.compute_performance(statistics)

        prediction_file_parser.close()
        reference_file_parser.close()
        
        return performance


    def evaluate(self, prediction_file, reference_file, num_subsets):

        if num_subsets == None:

            prediction_file_parser = PredictionFileParser(prediction_file)
            reference_file_parser = ReferenceFileParser(reference_file)

            prediction_file_parser.open()
            reference_file_parser.open()

            statistics = self.initialize_statistics()
        
            if prediction_file_parser.size != reference_file_parser.size:
                print 'fatal warning: prediction and reference sizes do not match: %d vs %d!' % (prediction_file_parser.size, reference_file_parser.size)

            for instance_index in range(prediction_file_parser.size):

                observation, len_observation, predicted_state_set = prediction_file_parser.parse(instance_index)
                observation, len_observation, true_state_set = reference_file_parser.parse(instance_index)

                statistics = self.update_statistics(statistics, predicted_state_set, true_state_set, observation, len_observation)
            
            performance = self.compute_performance(statistics)

            prediction_file_parser.close()
            reference_file_parser.close()

        else:

            performance = []

            prediction_file_parser = PredictionFileParser(prediction_file)
            reference_file_parser = ReferenceFileParser(reference_file)

            prediction_file_parser.open()
            reference_file_parser.open()

            if prediction_file_parser.size != reference_file_parser.size:
                print 'fatal warning: prediction and reference sizes do not match: %d vs %d!' % (prediction_file_parser.size, reference_file_parser.size)

            test_instance_index_subsets = self.make_instance_index_subsets(prediction_file_parser.size, num_subsets)

            for test_instance_index_subset in test_instance_index_subsets:

                statistics = self.initialize_statistics()
                
                for instance_index in test_instance_index_subset:

                    observation, len_observation, predicted_state_set = prediction_file_parser.parse(instance_index)
                    observation, len_observation, true_state_set = reference_file_parser.parse(instance_index)

                    statistics = self.update_statistics(statistics, predicted_state_set, true_state_set, observation, len_observation)
            
                performance.append(self.compute_performance(statistics))

            prediction_file_parser.close()
            reference_file_parser.close()

        return performance


    def initialize_statistics(self):

        pass


    def update_statistics(self, statistics, true_state_set, predicted_state_set, observation):

        pass


    def compute_performance(self, statistics):

        pass


    def make_instance_index_subsets(self, num_instances, num_subsets):

        instance_index_subsets = [[] for i in range(num_subsets)]

        for subset_index in range(num_subsets):

            instance_index = subset_index

            while instance_index < num_instances:

                instance_index_subsets[subset_index].append(instance_index)

                instance_index += num_subsets
        
        return instance_index_subsets


class FMeasureBIO(PerformanceMeasure):

    # __init__
    def __init__(self):

        super(FMeasureBIO, self).__init__()
    
        self.graph = NonStructuredChain()

        return


    def initialize_statistics(self):

        statistics = {}
        statistics['precision numerator'] = 0
        statistics['precision denominator'] = 0
        statistics['recall numerator'] = 0
        statistics['recall denominator'] = 0
        
        return statistics


    def update_statistics(self, statistics, predicted_state_set, true_state_set, observation, len_observation):

        predicted_chunk_set = []       
        current_chunk = ''

        for clique_set_index in self.graph.get_clique_set_index_set(size = 'single'):

            for clique in self.graph.get_clique_set(len_observation, clique_set_index):

                node = clique.position
                (l, t) = node
                
                if t == 0:
                    continue
                elif t == len_observation-1:
                    continue 

                predicted_state = predicted_state_set[node]

#                 print clique, predicted_state, true_state # fixme

                if predicted_state[0] == 'B':

                    if current_chunk != '': # add current chunk to chunk set if current chunk not empty
                        predicted_chunk_set.append(current_chunk)

                    current_chunk = predicted_state + ' (t = %d)' % t # begin new chunk

                elif predicted_state[0] == 'I':

                    current_chunk += ' ' + predicted_state + ' (t = %d)' % t # add to current chunk

                elif predicted_state in ['O', 'STOP']:                    

                    if current_chunk != '': # add chunk to chunk set if chunk not empty
                        predicted_chunk_set.append(current_chunk)
                        current_chunk = '' # empty chunk

        true_chunk_set = []        
        current_chunk = ''

        for clique_set_index in self.graph.get_clique_set_index_set(size = 'single'):

            for clique in self.graph.get_clique_set(len_observation, clique_set_index):

#                print node # fixme

                node = clique.position
                (l, t) = node
                
                if t == 0:
                    continue
                elif t == len_observation-1:
                    continue 

                true_state = true_state_set[node]

#               print clique, true_state, true_state # fixme

                if true_state[0] == 'B' or true_state[0] == 'S':

                    if current_chunk != '': # add current chunk to chunk set if current chunk not empty
                        true_chunk_set.append(current_chunk)

                    current_chunk = true_state + ' (t = %d)' % t # begin new chunk

                elif true_state[0] == 'I' or true_state[0] == 'M' or true_state[0] == 'E':                    

                    current_chunk += ' ' + true_state + ' (t = %d)' % t # add to current chunk

                elif true_state in ['O', 'STOP']:                    

                    if current_chunk != '': # add chunk to chunk set if chunk not empty
                        true_chunk_set.append(current_chunk)
                        current_chunk = '' # empty chunk

        for chunk in predicted_chunk_set:
            statistics['precision denominator'] += 1
            if chunk in true_chunk_set: 
                statistics['precision numerator'] += 1

        for chunk in true_chunk_set:
            statistics['recall denominator'] += 1 
            if chunk in predicted_chunk_set:
                statistics['recall numerator'] += 1

#        print statistics # fixme

        return statistics


    def compute_performance(self, statistics):

        pre = float(statistics['precision numerator']) / statistics['precision denominator'] * 100
        rec = float(statistics['recall numerator']) / statistics['recall denominator'] * 100
        
        f =  2*pre*rec/(pre + rec)

        performance = {'target measure id' : None, 'target measure' : None, 'all' : {}}

        performance['target measure id'] = 'f'
        performance['target measure'] = f

        performance['all']['pre'] = pre
        performance['all']['rec'] = rec
        performance['all']['f'] = f

        return performance
            
            

class FMeasureIO(PerformanceMeasure):

    # __init__
    def __init__(self):

        super(FMeasureIO, self).__init__()

        self.graph = NonStructuredChain()    

        return


    def initialize_statistics(self):

        statistics = {}
        statistics['precision numerator'] = 0
        statistics['precision denominator'] = 0
        statistics['recall numerator'] = 0
        statistics['recall denominator'] = 0
        
        return statistics


    def update_statistics(self, statistics, predicted_state_set, true_state_set, observation, len_observation):

        predicted_chunk_set = []       
        current_chunk = ''
        current_chunk_type = None

        for clique_set_index in self.graph.get_clique_set_index_set(size = 'single'):

            for clique in self.graph.get_clique_set(len_observation, clique_set_index):

                node = clique.position
                (l, t) = node
                
                if t == 0:
                    continue
                elif t == len_observation-1:
                    continue 

                predicted_state = predicted_state_set[node]

                if predicted_state in ['O', 'STOP']:                    

                    if current_chunk != '': # add chunk to chunk set if chunk not empty
                        predicted_chunk_set.append(current_chunk)

                    current_chunk = '' 
                    current_chunk_type = None

                elif predicted_state != current_chunk_type:

                    if current_chunk != '': # add current chunk to chunk set if current chunk not empty
                        predicted_chunk_set.append(current_chunk)

                    current_chunk = predicted_state + ' (t = %d)' % t # begin new chunk
                    current_chunk_type = predicted_state

                else:

                    current_chunk += ' ' + predicted_state + ' (t = %d)' % t # add to current chunk

        true_chunk_set = []        
        current_chunk = ''
        current_chunk_type = None

        for clique_set_index in self.graph.get_clique_set_index_set(size = 'single'):

            for clique in self.graph.get_clique_set(len_observation, clique_set_index):

#                print node # fixme

                node = clique.position
                (l, t) = node
                
                if t == 0:
                    continue
                elif t == len_observation-1:
                    continue 

                true_state = true_state_set[node]

#               print clique, true_state, true_state # fixme

                if true_state in ['O', 'STOP']:                    

                    if current_chunk != '': # add chunk to chunk set if chunk not empty
                        true_chunk_set.append(current_chunk)

                    current_chunk = '' 
                    current_chunk_type = None

                elif true_state != current_chunk_type:

                    if current_chunk != '': # add current chunk to chunk set if current chunk not empty
                        true_chunk_set.append(current_chunk)

                    current_chunk = true_state + ' (t = %d)' % t # begin new chunk
                    current_chunk_type = true_state

                else:

                    current_chunk += ' ' + true_state + ' (t = %d)' % t # add to current chunk

        for chunk in predicted_chunk_set:
            statistics['precision denominator'] += 1
            if chunk in true_chunk_set: 
                statistics['precision numerator'] += 1

        for chunk in true_chunk_set:
            statistics['recall denominator'] += 1 
            if chunk in predicted_chunk_set:
                statistics['recall numerator'] += 1

#        print statistics # fixme

        return statistics


    def compute_performance(self, statistics):

        pre = float(statistics['precision numerator']) / statistics['precision denominator'] * 100
        rec = float(statistics['recall numerator']) / statistics['recall denominator'] * 100
        
        f =  2*pre*rec/(pre + rec)

        performance = {'target measure id' : None, 'target measure' : None, 'all' : {}}

        performance['target measure id'] = 'f'
        performance['target measure'] = f

        performance['all']['pre'] = pre
        performance['all']['rec'] = rec
        performance['all']['f'] = f

        return performance



class Accuracy(PerformanceMeasure):

    # __init__
    def __init__(self):

        super(Accuracy, self).__init__()

        self.graph = NonStructuredChain()
    
        return


    def initialize_statistics(self):

        statistics = {}
        statistics['num correct predictions'] = 0
        statistics['num predictions'] = 0
        
        return statistics


    def update_statistics(self, statistics, predicted_state_set, true_state_set, observation, len_observation):

        for clique_set_index in self.graph.get_clique_set_index_set(size = 'single'):

            for clique in self.graph.get_clique_set(len_observation, clique_set_index):

                node = clique.position
                (l, t) = node
                
                if t == 0:
                    continue
                elif t == len_observation-1:
                    continue 

                predicted_state = predicted_state_set[node]
                true_state = true_state_set[node]
                
#                print predicted_state, true_state

                if predicted_state == true_state:

                    statistics['num correct predictions'] += 1

                statistics['num predictions'] += 1                

#        raw_input("")
        return statistics


    def compute_performance(self, statistics):

        acc = float(statistics['num correct predictions'])/statistics['num predictions']*100
        
        performance = {'target measure id' : None, 'target measure' : None, 'all' : {}}

        performance['target measure id'] = 'acc'
        performance['target measure'] = acc

        performance['all']['acc'] = acc

        return performance

