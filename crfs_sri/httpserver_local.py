import SimpleHTTPServer
import SocketServer
#import devutil
import json
import os
import string
import semantify_local
import sqlite3, shlex, subprocess,  sys,  re,  time
from bs4 import BeautifulSoup as Soup
from bs4 import NavigableString
from datetime import datetime
import unicodedata

PORT = 50010

conn = sqlite3.connect('sentence.db')
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS sentences (id INTEGER PRIMARY KEY AUTOINCREMENT, entity text, tag text, added datetime)''')

#   Opening error log 
errorlog=open(os.getcwd()+'/temp/errorlog.txt',  'w')
successlog=open(os.getcwd()+'/temp/successlog.txt',  'w')

filename=   'snippetfile'
experiment='experiment80'
confusion='confusion80'
factor=0.8
tagset=['home','away','score','date']
tagdict=['WebAnnotator_home', 'WebAnnotator_away', 'WebAnnotator_score','WebAnnotator_date']

testfile                        =os.getcwd()+'/temp/'+filename+'.test'
testreferencefile         =os.getcwd()+'/temp/'+filename+'.test.reference'

trainfile                       =os.getcwd()+'/temp/'+filename+'.train'    
traindevelfile              =os.getcwd()+'/temp/'+filename+'.train.devel' 
develpredictionfile      =os.getcwd()+'/temp/'+filename+'.devel.prediction' 
testpredictionfile         =os.getcwd()+'/temp/'+filename+'.test.prediction'
clientmodel                 =os.getcwd()+'/temp/'+filename+'.model'

experimenttrainfile                          =os.getcwd()+'/temp/'+filename+'.'+experiment+'.train'
experimenttraindevelfile                =os.getcwd()+'/temp/'+filename+'.'+experiment+'.train.devel'
experimentdevelpredictionfile      =os.getcwd()+'/temp/'+filename+'.'+experiment+'.devel.prediction' 
experimenttestpredictionfile         =os.getcwd()+'/temp/'+filename+'.'+experiment+'.test.prediction'
experimentclientmodel                   =os.getcwd()+'/temp/'+filename+'.'+experiment+'.model'

standardmodel=os.getcwd()+'/temp/snippetfiletest.model'


            
            

class TestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    """The test example handler."""

    def do_POST(self):
        """Handle a post request by returning the square of the number."""
        length = int(self.headers.getheader('content-length'))        
        data_string = self.rfile.read(length)

        self.send_response(200)
        self.send_header('Content-type', 'application/json')        
        self.end_headers()
        t=time.time()
        counter=0
        o = json.loads(data_string) 
      
        # Writing to a file for processing
        f=open(os.getcwd()+"/temp/snippetfile.html", 'w')    
        content=o['content']
        f.write('<html><<body>')
        for i in range(len(content)):            
            f.write(content[i].encode('utf8'))
        f.write('</body></html>')
        f.close()
    
        
        
        
        if o["command"] == "PUT":            
            # Do what should be done during PUT           
               
           
            value=0
            value=semantify_local.preprocess(filename, experiment, tagset, tagdict,  factor)
            if value==1:    
                 #print 'Devel files extracted' 
                 command='python train.py --graph first-order-chain --performance_measure accuracy --train_file %s --devel_file %s --devel_prediction_file %s --model_file %s' % (trainfile,traindevelfile, develpredictionfile, clientmodel)              
                 args = shlex.split(command)
                 process=subprocess.Popen(args)
                 process.wait() 
                 #print 'Model trained'
                 command='python apply.py --model_file %s --test_file %s --test_prediction_file %s' % (clientmodel,testfile, testpredictionfile)               
                 args = shlex.split(command)
                 process=subprocess.Popen(args)
                 process.wait()  
                 semantify_local.confusionmatrix(filename,  experiment, confusion,  tagset)
                 
                 ################## Experiment10
                 
                 command='python train.py --graph first-order-chain --performance_measure accuracy --train_file %s --devel_file %s --devel_prediction_file %s --model_file %s' % (experimenttrainfile,experimenttraindevelfile, experimentdevelpredictionfile, experimentclientmodel)              
                 args = shlex.split(command)
                 process=subprocess.Popen(args)
                 process.wait() 
                 #print 'Model trained'
                 command='python apply.py --model_file %s --test_file %s --test_prediction_file %s' % (experimentclientmodel,testfile, experimenttestpredictionfile)               
                 args = shlex.split(command)
                 process=subprocess.Popen(args)
                 process.wait()  
                 semantify_local.confusionmatrix(filename,  experiment, confusion,  tagset)
                 
                 #####################
                 
                 semantify_local.accuracy(filename, experiment)
                 #print 'Model Applied'
                 content=semantify_local.keywordtag(filename, tagset, tagdict)                       
                 successlog.write(filename)
                 successlog.write('\t')
                 successlog.write( str(datetime.now()))
                 successlog.write('\n') 
                 elapsed=time.time()-t
                 print 'File', filename, 'served in:',  elapsed
                 pass
            
        elif o["command"] == "TAG":
            # Replace this line with real action
          
            value=0
            value=semantify_localmodified.preprocess(filename, experiment, tagset, tagdict)
            if value==1:    
                 print 'Devel files extracted' 
                 command='python train.py --graph first-order-chain --performance_measure accuracy --train_file %s --devel_file %s --devel_prediction_file %s --model_file %s' % (trainfile,traindevelfile, develpredictionfile, clientmodel)
                 args = shlex.split(command)
                 process=subprocess.Popen(args)
                 process.wait() 
                 print 'Model trained'
                 command='python apply.py --model_file %s --test_file %s --test_prediction_file %s' % (clientmodel,testfile, testpredictionfile)
                 args = shlex.split(command)
                 process=subprocess.Popen(args)
                 process.wait()  
                 semantify_local.confusionmatrix(filename,  experiment, confusion,  tagset)
                 
                 ################## Experiment10
                 
                 command='python train.py --graph first-order-chain --performance_measure accuracy --train_file %s --devel_file %s --devel_prediction_file %s --model_file %s' % (experimenttrainfile,experimenttraindevelfile, experimentdevelpredictionfile, experimentclientmodel)              
                 args = shlex.split(command)
                 process=subprocess.Popen(args)
                 process.wait() 
                 #print 'Model trained'
                 command='python apply.py --model_file %s --test_file %s --test_prediction_file %s' % (experimentclientmodel,testfile, experimenttestpredictionfile)               
                 args = shlex.split(command)
                 process=subprocess.Popen(args)
                 process.wait()  
                 semantify_local.confusionmatrix(filename,  experiment, confusion,  tagset)
                 #####################
                 
                 semantify_local.accuracy(filename, experiment)
                 #print 'Model Applied'
                 content=semantify_localmodified.keywordtag(filename, tagset, tagdict)                        
                 successlog.write(filename)
                 successlog.write('\t')
                 successlog.write( str(datetime.now()))
                 successlog.write('\n')             
                 
                 o['content']=''.join(content)                     
                 
                 self.wfile.write(json.dumps(o))
                 elapsed=time.time()-t
                 print 'File', filename, 'served in:',  elapsed
               

httpd = SocketServer.TCPServer(("", PORT), TestHandler)

if __name__ == "__main__":
    print "serving at port", PORT
    httpd.serve_forever()
