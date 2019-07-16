## iscrape: a scraper for Indeed

This is a user-configurable tool to scrape Indeed.com for job data. 

> This tool is intended for job seekers.  Please observe terms of service of any sites accessed.

### how to use:

You can use this to  search Indeed.com for a list of cities you are interested in.  
You specify a search query using a text file, 
and then one or more "categories" by which you can rank the results.   Indeed has a permissive search 
strategy so it helps to experiment with search setup.

#### Search setup

1. edit the file `searchwords.txt` to customize it as follows:
    * Tags start with '*' in the first position of a line.
    * Major tags begin with '**'.  They include
        1. `**SearchName`:   a name you make up for this search
        2. `**IndeedSearch`:  search terms in the indeed "what" box. (must be in single quotes (') so you can have
            multi-word searches such as 'project manager' or 'data science'.
        3. `**IndeedAvoid`:   search terms you DON'T want (online you add this to the "what" box with a "-" minus sign).
        4. Then you set up one or more search categories:
            1.  name the category via the `**Category` tag
            2. `**Seek`'   followed by comma-separated words  and pairs of words. (lower case)
            3. `**Avoid`'  followed by comma-separated words to avoid (lower case)        
        5. `**Cities`:  follow this with a comma-separated list of cities  (capitalized)
        (in testing mode, a short list of cities is substituted)

2. run the script:
   `> python iscrape.py`

    Delays are inserted to keep server loads down.   A big search can take on the order of 
1hr. 

3. your output will be:
    * `jobs.csv`  a file that can be opened with Excel or LibreOffice.   The scores in columns E...
    refer to your categories (in txt file order).
    * `jobs.html` a web page that can be opened by your browser (`<ctl>O`)

4. use the testing option for quicker preliminary search results:
    * `> python iscrape.py  TESTING`

    
### Installation

You need the following python packages: 

* nltk  (`sudo pip install nltk`)
* nltk stopwords  (you have to download the actual words just one time after installation, 
search for 'stopwords' in `iscrape.py` for a line to uncomment for this).
* BeautifulSoup (`sudo pip install bs4` on linux)
* requests  (`sudo pip install requests`)

### Unit tests:
*   `> python jobwords.py` will run some.   Tests rely on `testsearch.txt` so do not
modify that file. 

This package was developed at [GIX](https://gixnetwork.org) to predict job opportunties for the New Master of Science in Technology Innovation, [MSTI(Robotics) program](https://gixnetwork.org/program/msti/) graduates. 


