import re
import urllib.request
import pandas as pd
import html
from datetime import date

today = date.today()
#university codes used for training
train_uni_codes = ['11708991605694184852', '15421803288417240838', '14108176128635076915']
#university codes used for testing
test_uni_codes = ['8867661471528740601', '4836318610601440500']
url_list = [train_uni_codes, test_uni_codes]
#number of authors from which articles will be extracted. It must be a multiple of 10
number_authors = 10
file_name = "train"
df_columns = ['GS-Code', 'Art-Code', 'Article', 'Authors', 'Journal', 'Cites', 'Year']

for all_uni_codes in url_list:
   final_authors = []
   articles_list = []
   
   for uni_code in all_uni_codes:

      url = "https://scholar.google.fr/citations?view_op=view_org&hl=en&org=" + uni_code
      urlbase = url
      number_page = 10
      finish = False

      while not finish:

         f = urllib.request.urlopen(url)
         text = f.read().decode('ISO-8859-1')
         #get author codes
         authors = re.findall("<a href=\"/citations?\S*user=([\w-]*)\">",text)
         #add all authors codes in a list
         for x in authors:
            final_authors.append(x)

         #stop when there are no authors left and the number of selected authors is less than the number of pages
         after_author = re.search("after_author....([\w-]*)", text)
         if after_author and number_page < number_authors:
            url = urlbase + "&after_author="+after_author.group(1)+"&astart="+str(number_page)
            number_page += 10
         else:
            finish = True

   for code in final_authors:
      print("Processing...", code)
      
      show_more = True
      p = 0
      author_code = [code]

      while show_more:
         #access author profile
         a = urllib.request.urlopen("https://scholar.google.fr/citations?hl=en&cstart="+ str(p*100) +"&pagesize=100&user="+ code)
         print("  page=", p)
         #the content of the web source code is decoded in Latin1(ISO 8859-1).Unicode characters and HTML tags are also removed
         page = a.read().decode('ISO-8859-1').replace('\xa0', ' ').replace('\xad', '').replace('<i>', '').replace('< i>', '').replace('</i>', '').replace('<sup>', '').replace('</sup>', '').replace('<sub>', '').replace('< sub>', '').replace('</sub>', '').replace('<b>', '').replace('</b>', '')

         #get article code
         if p == 0:
            artCode = re.findall("a href=\"/citations\?view_op=view_citation&amp;hl=en&amp;oe=ASCII&amp;user=" + code + "&amp;pagesize=100&amp;citation_for_view=(.*?)\"", page)
         else:
            artCode = re.findall("a href=\"/citations\?view_op=view_citation&amp;hl=en&amp;oe=ASCII&amp;user=" + code + "&amp;cstart="+ str(p*100) + "&amp;pagesize=100&amp;citation_for_view=(.*?)\"", page)

         #get article title
         titles = re.findall("class=\"gsc_a_at\">(.*?)</a>", page)

         #delete all vectorial image from titles and remove whitespace
         filtered_titles = [re.sub(r'<svg class=\"gs_fsvg\"(.*?)</g></svg>', '', title) for title in titles]
         final_titles = [" ".join(title.split()) for title in filtered_titles]

         #get article citations
         cites = re.findall(r"class=\"gsc_a_ac gs_ibl\">(\d*)</a>|data-eud=\"\S*:\S*\">(\d*)</a>", page)
         final_cites = []
         #collect only the number of cites
         for number in cites:
            result = re.search("(\d+)", str(number))
            if result is None:
               final_cites.append('')
            else:
               final_cites.append(result.group(1))
         
         #get list of author, journal and year
         contributors = re.findall("</a><div class=\"gs_gray\">(.*?)</div>", page)
         journals = re.findall("</div><div class=\"gs_gray\">(.*?)</div>", page)
         years = re.findall("class=\"gsc_a_h gsc_a_hc gs_ibl\">(\d*)</span>", page)

         #stop when there are no articles left
         if len(titles)!= 100:
            show_more=False
         p=p+1

         #adds article data to a list only if there are articles to include
         if titles:
            [articles_list.append(data) for data in zip(author_code*len(titles), artCode, final_titles, contributors, journals,
            final_cites, years)]
            
   df_articles = pd.DataFrame(articles_list, columns = df_columns)
   
   #clean the article data of html entities and html code
   def clean_articles(x):
      x['Article'] = html.unescape(x['Article']).replace('<span class="gs_fscp">', '')
      x['Authors'] = html.unescape(x['Authors'])
      x['Journal'] = html.unescape(x['Journal']).replace('<span class="gs_oph">,',',').replace('</span>','')
      return x

   df_articles = df_articles.apply(lambda x: clean_articles(x), axis=1)
   df_articles.to_csv(today.strftime("%Y-%m") + "_" + file_name + "_other_uni_paper_cites.csv", index = False)
   file_name = "test"