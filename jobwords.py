#!/usr/bin/env python
import sys

##############################################################
#
#    Customize your settings here for your application
#         (also customize your search in 'searchwords.txt')
#

#   Command line arguments will overwrite your settings
#
#    usage:    > iscrape [TESTING] [search definition file]
#
    
TESTING = False
 
searchwordfile = 'searchwords.txt'  # your search words and cities

titleweight = 2.0   # words in job title count *twice* as much

delays = [0, 4, 2, 3, 5, 9, 8, 6, 1, 8, 2]

#      (end of customizations)
#
#############################################################
#
#   Now the command line args (which overwrite settings)
args = sys.argv[1:]
for a in args:
    if a == 'TESTING':
        TESTING = True
    else:
        searchwordfile = a    
    
######################################################
#
#  We can't just search single word matches
#    bigrams are two-word pairs
#    they help us find things like "program manager" or "deep learning"
#

# make list of word pairs
def make_bigrams(list):
    # list: a list of words
    bl = []
    l = len(list)
    for i,w in enumerate(list):
        if '-' in w:
            bl.append(w.split('-'))  # de hyphenate
        elif i <= l-2:
            bl.append([w, list[i+1]])
    return bl  # a list of 2-word lists

def get_bigrams(list):
    # list: a list of words containing instances of 
    #   'word1 word2' or 'word1-word2' mixed in w/ single words
    bl = []
    for i,w in enumerate(list):
        if '-' in w:
            bl.append(w.split('-'))
        if ' ' in w:
            bl.append(w.split(' '))
                      
    return bl

def score_bigrams(goal, target):
    # args are lists of bigrams
    #
    #   besides word matching
    #
    sc = 0 # of bigram matches btwn score and target
    for g in goal:
        if g in target:
            sc += 1
            #print 'bi-gram match: ', bt
    return sc


class scorer:
    def __init__(self):
        self.categories = []
        self.jobtarget = 'unnamed'
        self.indeedsearch = ''
        self.indeedavoid = ''
        
    def __repr__(self):
        out = ''
        for c in self.categories:            
            out +=  c[0] + '\n'
            out +=  '      +:' + str(c[1]) + '\n'
            out +=  '      -:' + str(c[2]) + '\n'
        return out
    
    def add_searches(self, searches):
        # searches is list of 3-vectors:
        # [ name, seekwordslist, avoidwordslist ]
        self.categories = searches
    
    def add_category(self,name, gw, bw):
        # name = string name of category (e.g. 'data scientist')
        # gw = list of "good words" for matching data scientist jobs (e.g. 'python')
        # bw = list of words to kill the job (e.g. 'punchcards')
        self.categories.append([name, gw, bw])

    def evaluate(self,txt): # txt is a list of words
        assert len(self.categories) > 0, 'scorer: no categories have been set up '
        scores = []
        keywords = {}
        for cat in self.categories:
            stmp = 0
            bgtxt = make_bigrams(txt) # get bigrams in txt
            gbg = get_bigrams(cat[1])  #'good' bigrams
            bbg = get_bigrams(cat[2])  #'bad' bigrams
            # good words and bigrams for this cat
            tg = []
            tb = []
            for w in cat[1]: # the 'good' words
                for t in txt: # t is a word
                    if t.startswith(w):
                        stmp += 1
                        tg.append(w)
            stmp += score_bigrams(gbg, bgtxt)
            # bad words and bigrams for this cat
            for w in cat[2]: # the 'bad' words
                for t in txt:
                    if t.startswith(w):
                        stmp -= 1
                        tb.append(w)
            stmp -= score_bigrams(bbg, bgtxt)
            scores.append(int(stmp))
            #print 'categ:', cat[0]
            #print '       good:',tg, '    score: ', stmp
            #print '        bad:',tb
            keywords[cat[0]] = [tg,tb]  # 'good' and 'bad' keywords key is category name / cat[0]
        return scores, keywords
          
#
#  read in the searchwords file and return cities and scorer
def readwords(fname):
    sc = scorer()
    infile = open(fname, 'r')
    lines = [line.rstrip() for line in infile]
    mode = 0
    sc.categories = []
    cat = ''
    swords = awords = cities = []
    for l in lines:
        l = l.split('#')[0]  # only keep before comments
        if len(l.strip()) < 1:
            continue           # ignore comment only lines
        #print 'Line: ', l
        if l.startswith('**'):
            if cat != '':
                seekwords = [w.strip() for w in swords if (len(w) > 0)][1:]    #delete '*Seek'
                avoidwords =  [w.strip() for w in awords if (len(w) > 0)][1:]
                sc.categories.append([ cat, seekwords, avoidwords])

            if l.startswith('**Categ'):
                #start new category
                cat = l.split()[1]
                swords = []
                awords = []
                #print "I got category ", cat
                mode = 1
            elif l.startswith('**Citi'):
                mode = 4
            elif l.startswith('**SearchNa'):
                sc.jobtarget = l.split()[1]                
            elif l.startswith('**IndeedSea'):
                words = l.split()[1:]
                sc.indeedsearch = ' '.join([w.replace("'",'') for w in words if (len(w)>0)])
            elif l.startswith('**IndeedAvo'):
                indeedtmp = l.split()[1].split(',')             
                # make negative words into URL format
                indeedsearchbar = ''
                for w in indeedtmp:
                    w = w.strip()
                    if len(w) > 0:
                        sc.indeedavoid += '+-'+w
                #indeedsearchbar = '+-carpenter+-nurse+-surgery'        #

        if l.startswith('*See'):
            mode = 2
        if l.startswith('*Avo'):
            mode = 3 
        # process the content of fields
        if mode == 2: 
            swords += l.split(',')
        if mode == 3: 
            awords += l.split(',')
        if mode == 4: 
            cities += l.split(',')
    cities = [c.strip() for c in cities if (len(c) > 0)][1:]
    #print '---Cities---'
    #print cities
    #print '---Categories---'
    #for s in searches:
        #print s
    #print '------'
    infile.close()
    return cities, sc


html_prefix = '''<!doctype html>

<html lang="en">
<head>
  <meta charset="utf-8">

  <title>Indeed search results</title> 

<style>
table {
  width:80%;
}
table, th, td {
  border: 1px solid black;
  border-collapse: collapse;
}
th, td {
  padding: 15px;
  text-align: left;
}
table#t01 tr:nth-child(even) {
  background-color: #eee;
}
table#t01 tr:nth-child(odd) {
 background-color: #fff;
}
table#t01 th {
  background-color: black;
  color: white;
}
</style>
   
</head>
<body>
<h3> Indeed Job search results retrieved on XXXdateXXX </h3>
<div class="w3-white w3-padding notranslate w3-padding-16">
<table id="t01">
 <tr>
    <th>N</th>
    <th>Title</th>
    <th>Job Scores</th>
    <th>Company</th>
    <th>City</th>
    <th>keyword matches</th>
 </tr>

'''

html_postfix = '''
</div>
</body>
</html>
'''



###    Test code for these functions:  just run >python jobwords.py
if __name__=='__main__':
    # Tests
    
    words1 = ['startup','ux','manager','planner','robot','design','shakespeare','mustang','humanitarian','ROS']
    words2 = ['algorithm', 'search', 'vision','planner','robot','design', 'shakespeare','mustang', 'cook', 'humanitarian', 'ROS']
    
    #
    #   might want to revive this func later
    #print 'Keywords:'
    #fs = 'Keywords Fail: get_kw()'
    #k1=get_kw(words1)
    #k1a = (k1[0] == [])
    #k1b = (k1[1] == ['startup', 'humanitarian', 'design', 'ROS'])
    #k1c = (k1[2] == ['planner'])
    
    #k2=get_kw(words2)
    #k2a = (k2[0] == [])
    #k2b = (k2[1] == ['humanitarian', 'design', 'ROS'])
    #k2c = (k2[2] == ['algorithm', 'search', 'vision','planner'])
    #print k2
    
    #assert k1a and k1b and k1c, fs
    #assert k2a and k2b and k2c, fs
   
    print 'Testing make_bigrams'
    # make_bigrams
    bl = make_bigrams(words1)
    fs = 'make_bigrams FAIL'
    assert bl[0] == ['startup','ux'], fs
    assert bl[1] == ['ux', 'manager'], fs
    assert bl[-1] == ['humanitarian','ROS'], fs
    
    print 'Testing get_bigrams'
    # get_bigrams
    mstititles = ['intern', 'program manager', 'programs manager',  'product manager', 'ui-ux', 'designer', 'engineer']

    bl = get_bigrams(mstititles)
    fs = 'get_bigrams FAIL'
    assert len(bl) == 4, fs
    assert bl[0] == ['program','manager'], fs
    assert bl[1] == ['programs', 'manager'], fs
    assert bl[2] == ['product', 'manager'], fs
    assert bl[3] == ['ui','ux'], fs
    
    print 'Testing score_bigrams'
    # score_bigrams
    g = [['program','manager'],['ui','ux']]
    score = score_bigrams(g,bl)
    print 'bg Score: ',score
    fs = 'score bigrams FAIL'
    assert score == 2, fs
    
    # scorer class
    
    
    print 'Testing scorer'
    s = scorer()
    s.add_category('overall match', ['data scientist', 'data analyst', 'data', 'learning','prediction'], ['chemistry', 'pharma', 'biotech'] )
    s.add_category('ML', ['neural nets', 'deep learning'], ['reenforcement learning'])
    s.add_category('finance', ['investment'] , ['commodity', 'cook'])

    txt1 = 'data scientist work on deep learning for biotech in pharma industry investment'
    txt2 = 'data scientist work on neural nets for financial industry on wall street'
    txt3 = 'restaurant clerk chemistry and fast food cook'
    
    #print s
    fs = 'scorer class FAIL'
     
    s1, kw =  s.evaluate(txt1)
    print s1, txt1
    print 'scorer test 1 keywords:',kw
    assert s1 == [1,1,1], fs
    s2, kw =  s.evaluate(txt2)
    assert s2 == [2,1,0], fs
    s3, kw = s.evaluate(txt3)
    assert s3 == [-1,0,-1]
    
    
    # readwords
    print 'Testing readwords()'
    
    fs = 'read search words (readwords(fname)) --  FAIL'
    fname = 'testsearch.txt'
    cities, sc = readwords('testsearch.txt')
    s0 = sc.categories[1]
    s2 = sc.categories[2]
    assert s0[0] == 'DataScienceStartup',fs
    assert s0[1][3] == 'data scientist', fs
    assert s2[0] == 'Academic', fs
    assert s2[1][4] == 'tenure',fs
    
     
    print '\n\n passed all tests \n\n'
    
