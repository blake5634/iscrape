import re
import nltk as nl
from nltk.corpus import stopwords
import sys
import datetime
import random

import bs4
import time
import requests
 
base_url = 'https://www.indeed.com'

githuburl = 'https://github.com/blake5634/iscrape'   # replace w/ github

################   CUSTOMIZATION  #########################################
#  Set up custom parameters in your searchwords.txt file and at top of jobwords.py
#

#
#  TODO: github.iscrape master branch
#
#    4) permute search URL to prevent count limit
#

# thanks / credits / influence:   
#     https://beckernick.github.io/job-discovery/
#     https://towardsdatascience.com/scraping-job-posting-data-from-indeed-using-selenium-and-beautifulsoup-dfc86230baac

import jobwords as jw

##  obtain the search scorer instance and list of cities
cities, evaluator = jw.readwords(jw.searchwordfile)

 
HTML = True



if jw.TESTING:         ###  set this test flag in jobwords
    MAX_PAGES = 4
    delayscale = 1.0
    citiestmp =  cities
    random.shuffle(citiestmp)
    cities = citiestmp[0:2]  # a short randomly selected city list for testing
    print '\n\n                  TESTING MODE\n\n'
else:
    MAX_PAGES = 60
    delayscale = 4.0    # slow down for big production searches
    print '\n\n                  PRODUCTION MODE  (', len(cities), 'cities)\n                 (this might take an hour or more) \n'

#
#nl.download('stopwords')  # you need to uncomment this ONCE - then the words stay downloaded
#

stop_words = set(stopwords.words("english")) # Filter out any stop words
 
def get_job_descrip(job):
    #  retrieve the detailed job description from its url
    #  process job description for easy searching
    #  add it to the job.
    url = job['url']
    # clean the title
    job['title'] = job['title'].lower()
    #print 'looking at url for job:', url
    jpage = requests.get(url)
    jsoup = bs4.BeautifulSoup(jpage.content, 'lxml')
    descript = jsoup.find('div', {'id':'jobDescriptionText'})
    if descript is not None:
        text = descript.text
    else:
        text = 'Job description not given.'
    #
    # clean up the text for good searching
    text = text
    text = re.sub("[^a-zA-Z+3]"," ", text)
    text = re.sub('()','',text)
    text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text) # Fix spacing issue from merged words
    text = text.lower() # Go to lower case
    text = text.split()  # break into a list of words
    text = [str(w) for w in text if not w in stop_words]
    #print 'Im storing description: ', text[0:10]
    # text is a list of words
    job['description'] = text  # a list of lowercase words
    return job

def extract_job_data_from_page_soup(soup):
    #response = requests.get(query_url)
    #soup = bs4.BeautifulSoup(response.content, 'lxml')
    
    tags = soup.find_all('div', {'data-tn-component' : "organicJob"})
    #print 'Found ', len(tags), 'jobs'
    
    attrs_list = []
    for i,x in enumerate(tags):
        attrs_list.append({})
        attrs_list[i]['title'] = 'placeholder'
        attrs_list[i]['location'] = 'placeholder'
        attrs_list[i]['company'] = 'placeholder'
        attrs_list[i]['date posted'] = 'placeholder'
        attrs_list[i]['summary'] = 'placeholder'
        attrs_list[i]['url'] = 'placeholder'
        attrs_list[i]['title'] = x.find_all('a', {'class':'jobtitle turnstileLink '})[0]['title']
        link = x.find_all('a', {'class':'jobtitle turnstileLink '})[0]['href']
        attrs_list[i]['url'] = base_url+link
        attrs_list[i]['location'] = x.find_all('div', {'class':'recJobLoc'})[0]['data-rc-loc']
        attrs_list[i]['company'] = x.span.text.strip()
        attrs_list[i]['date posted'] = x.find_all('span', {'class':'date'} )[0].text.strip()
        attrs_list[i]['summary'] = x.find_all('div', {'class':'summary'} )[0].text.strip()
        #print '-----------------__Tag: (',len(attrs_list[i]), 'attribs)' 
        #print attrs_list[i]
        #if i in [3,5]:
            #print x
            ##print x.div.attrs
        #print '  '
    #print '\n\n\n'
    #print 'number of jobs / attribute dicts:', len(attrs_list) 
        
    return attrs_list

def outputcsv(of,job):
    csvline = job['date posted']+','
    csvline += job['title'].replace(',','-')+','
    csvline += job['company'].replace(',','-')+','
    #csvline += job['company']+','
    csvline += job['location'].replace(',','-')+','
    for s in job['scorelist']:
        csvline += str(s)+','
    csvline += job['url']
    #csvline += str(kw).replace(',','|')
    print >> of, csvline.encode('utf-8')

###   keep permuting these to block URL count blocking
#searchminus = '+-technician+-nurse+-camp+-teacher+-instructor+-accounting+-driver'
#searchminus = '+-camp+-driver+-nurse'
#searchminus = '+-driver+-nurse+-camp'

#searchplus = 'embedded'   # for testing variety

# output file
ofname = 'jobs.csv'
of = open(ofname, 'w')


today_st = '{:%B %d, %Y}'.format(datetime.datetime.now())
 
if HTML:
    hname = 'jobs.html'
    oh = open(hname,'w')
    # insert details into HTML before the output table
    oh.write(jw.html_prefix.replace('XXXdateXXX', today_st+ '  for ' + evaluator.jobtarget))  # start of the html page
    
tpages = 0

tdupe = 0
tstale = 0

alljoblist = []

ncities = len(cities)
citcount = 0

for city in cities:
    citcount += 1
    print '\n\n'
    print '   Searching: ',city, '    (city ', citcount, '/', ncities,')'
    print '\n\n'
    
    # search indeed using terms from scorer instance.
    current_url = 'https://www.indeed.com/jobs?q='+evaluator.indeedsearch+evaluator.indeedavoid+'++%2490+-+%24125%2C000&l='+city+'&ts=1561653578141&rq=1&fromage=last'
    print current_url[0:100]
    
    
    pagecollection = []

    #print 'extracting first page of job searching results...'  ,
    #print 'current search: ', current_url
    page = requests.get(current_url)
    tpages += 1
    psoup = bs4.BeautifulSoup(page.content, "lxml")   # a page of listings
    x = psoup.find(id = 'searchCount')
    if x is None:
        print 'No jobs found for ', city
        time.sleep(0.5)
        continue
    num_found = x.string.split() #this returns the total number of results
    num_jobs = int(num_found[3].replace(',', ''))
    num_pages = num_jobs/10 #calculates how many pages needed to do the scraping
    print 'Found a total of ', num_jobs, 'jobs in ', city, ', in ', num_pages, ' pages'

    pagecollection.append(psoup)  # add in the first page

    #    Rest of the pages

    # page limit from a single city
    num_pages = min(num_pages, MAX_PAGES)   

    
    # We slow it down for production to avoid server overloads
    delays = [d*delayscale for i,d in enumerate(jw.delays)] 
        
    nd = len(delays)

    for j in range(num_pages-1):
        k=j+1  # we already have first page (page 0)
        #if k%5==0:
            #driver.quit()
            #driver=webdriver.Firefox()
            #driver.set_page_load_timeout(15)
        print 'Sleeping for ', delays[tpages%nd],'seconds'
        time.sleep(delays[k%nd])  # wait a random time
        
        if k > 1:
            current_url = current_url + "&start=" + str(k*10)
        else:
            current_url = current_url
        #print 'extracting page %d of job searching results...' % (k+1) ,
        #print 'current URL: ', current_url
        page = requests.get(current_url)
        tpages += 1
        psoup = bs4.BeautifulSoup(page.content, "lxml")   # a page of listings
        pagecollection.append(psoup)


    cityjoblist = []
    for ps in pagecollection:
        l = extract_job_data_from_page_soup(ps)
        cityjoblist = cityjoblist + l
        
    #print ' received ', len(cityjoblist), ' jobs'
    stale = 0
    dupes = 0
    
    b=[]
    # get rid of postings more than 30 days old
    for i in range(len(cityjoblist)):
        daysago = cityjoblist[i]['date posted']
        fresh = True
        if 'days' in daysago and daysago[0:3] == '30+':
            fresh = False
            stale += 1
        if fresh:
            b.append(cityjoblist[i])
    cityjoblist = b
    
    # get rid of duplicates in cityjoblist
    origlen = len(cityjoblist)
    dupelist = [] # testing only
    ulist = []
    for i,j in enumerate(cityjoblist):  # if urls same dedup. 
        ulist.append(j['url'])
    b = []
    for i,j in enumerate(cityjoblist):
        if j['url'] not in ulist[i+1:]: # this uses the last occurance of a dup
            b.append(cityjoblist[i])
        else:
            dupes += 1
            dupelist.append(j)  # keep track
    cityjoblist = b
    
    newlen = len(cityjoblist)
    print 'Joblist deduped/freshened from ', origlen, 'to', newlen
    print 'Stale jobs: ', stale, '   dupe jobs: ', dupes, '\n\n'
    tdupe += dupes
    tstale += stale
    
    ij = 0 # job number
    # generate output and list the jobs
    for job in cityjoblist:
        ij += 1
        M = False
        job = get_job_descrip(job)
        
        #job['scorelist'] = jw.scoretxt(job)
        scores_txt = evaluator.evaluate(job['description'])
        scores_title = evaluator.evaluate(job['title'].lower())
        s = []
        # combine scores to weight the title words 
        for i,st in enumerate(scores_txt):
            s.append(st+jw.titleweight*scores_title[i])
        job['scorelist'] = s
        
        alljoblist.append(job)   # store them up for a big sort
         
        if jw.TESTING:
            print '--------------------- ',ij
            print job['title']
            print job['company'], job['location']
            print '     ', job['summary'][0:100]
            #print job['url'][0:100]
            print 'Score: ', job['scorelist']
            print '========== end of job ==========='
        #print 'Keywords:', kw
        #print '\n'
        
        outputcsv(of, job)

 #sorted(student_objects, key=lambda student: student.age) 
alljoblist = sorted(alljoblist, key=lambda j: j['scorelist'][1], reverse=True)  # sort by MSTI score (scorelist[1])

if HTML:
    for i,job in enumerate(alljoblist):
        html = '<tr><td>'+str(i)+'</td><td>'+job['title']+'</td>\n'
        html += '<td>' + str(job['scorelist']) +'</td>'
        html += '<td>  ' + job['company'] + ' </td><td> ' + job['location'] + '</td><td> <a href='+job['url']+'> [Link] </a></td></tr>\n\n' 
        oh.write(html.encode('utf-8'))


report = '\n\n--------------------  Job Search Report ----------------------------------- ('+jw.searchwordfile+')\n'
report += str(len(cities)) +  ' Cities: ' + str(cities)+'\n'
report +=  str(len(alljoblist)) + ' Jobs,   after, ' + str(tstale) + ' stale and '+str(tdupe)+'duplicates\n'
report += '  output is in ' + ofname + '/ '+ hname + '\n'
report += '\n\n'
report += 'Search:\n' + str(evaluator)
report += 'Cities:\n' + str(cities) + '\n'
report += '--------------------  end: Job Search Report --------------------------------------------\n'
report += '(for project code: <a href=' + githuburl + '> iscrape project code </a>)\n'

print report

if HTML:
    oh.write('</table><hr><div><pre>'+report+'</pre></div>\n'.encode('utf-8'))
    oh.write(jw.html_postfix.encode('utf-8')) # close out the html file
    oh.close()
    of.close()


if False:
    # for testing de-duplicate function
    f2 = open('dupes.csv', 'w')
    for j in dupelist:
        j=get_job_descrip(j)
        #job['scorelist'] = jw.scoretxt(job)
        scores_txt = evaluator.evaluate(j['description'])
        scores_title = evaluator.evaluate(j['title'])
        s = []
        # combine scores to weight the title words 
        for i,st in enumerate(scores_txt):
            s.append(st+jw.titleweight*scores_title[i])
        j['scorelist'] = s    
        outputcsv(f2,j)
    f2.close()
