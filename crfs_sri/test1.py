
import string
import re

line='.2-0'

char=re.escape(string.punctuation)
#line=re.sub(r'['+char+']', '',line)
line=re.sub('[^a-zA-Z0-9\.\-]', ' ', line)  


print line
