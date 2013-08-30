import time
from optparse import OptionParser


from models import *



if __name__ == "__main__":

    tic = time.clock()

    # parse options
    parser = OptionParser("Usage: %prog [options]")
    parser.add_option("--corpus", dest = "corpus_id", default = None)
    parser.add_option("--task", dest = "task_id", default = None)
    parser.add_option("--train_algorithm", dest = "train_algorithm_id", default = None)
    parser.add_option("--inference", dest = "inference", default = None)
    parser.add_option("--single_pass", action = "store_true", dest = "single_pass", default = False)
    parser.add_option("--train_file", dest = "train_file", default = None)
    parser.add_option("--devel_file", dest = "devel_file", default = None)
    parser.add_option("--prediction_file", dest = "prediction_file", default = None)
    parser.add_option("--model_file", dest = "model_file", default = None)
    parser.add_option("--verbose", action = "store_true", dest = "verbose", default = False)

    (options, args) = parser.parse_args()

    # print options

    print "options"
    print "\tcorpus:", options.corpus_id
    print "\ttask:", options.task_id
    print "\ttrain algorithm:", options.train_algorithm_id
    print "\tinference:", options.inference_id
    print "\tsingle pass:", options.single_pass
    print "\ttrain file:", options.train_file
    print "\tdevel file:", options.devel_file
    print "\tprediction file (devel):", options.prediction_file
    print "\tverbose:", options.verbose
    print
    print "initialize model"
    m = Model()
    print "done"
    print
    print "train model"
    m.train(options.corpus_id, 
            options.task_id, 
            options.train_algorithm_id, 
            options.inference, 
            options.single_pass, 
            options.train_file, 
            options.devel_file, 
            options.prediction_file, 
            options.verbose)
    print "done"
    print
    print "save model"
    print "\tmodel file:", options.model_file
    m.save(options.model_file)
    print "done"
    print
    print "time consumed in total:", time.clock() - tic
    print
    print

    exit()





