
import sys

for line in sys.stdin:

    line = line.strip()

    if not line:
        print 

    else:

#        line = line.split('\t')
#        line.pop(-1)
#        word, tag = line[0], line[1]
#        print "((word(t)=%s), (1))\t((suffix(word(t))=%s), (1))\t((suffix(word(t))=%s), (1))\t%s" % (word, word[-2:], word[-4:], tag)

        word = line
        print "((word(t)=%s), (1))\t((suffix(word(t))=%s), (1))\t((suffix(word(t))=%s), (1))" % (word, word[-2:], word[-4:])    

