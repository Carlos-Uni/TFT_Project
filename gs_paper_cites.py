import sys, re
import urllib.request
import html
import pandas as pd
from datetime import date
import argparse


if __name__ == '__main__':

   today = date.today()
   #check that the parameters are correct.
   def file_checker(file_name):
      if "authors-GS.csv" not in file_name:
         parser.error("The file " + file_name + " is incorrect. Use the -h command to see the format and run the script correctly.")
      return file_name

   parser = argparse.ArgumentParser(description="Script that extracts articles from Google Scholar authors")
   parser.add_argument("authors_file", metavar='authors-GS.csv', type=lambda s:file_checker(s),
                        help="File that contains the data of the authors obtained from Google Scholar")
   args = parser.parse_args()
   

   def collect_data(row):

      name = row['Nombre']
      code = row['GS-Code']
      print("Processing...", name, code)
      
      show_more = True
      p = 0
      author_code = [code]
      while show_more:
         #access author profile
         a = urllib.request.urlopen("https://scholar.google.fr/citations?hl=en&cstart="+ str(p*100) +"&pagesize=100&user="+ code)
         print("  page=", p)
         #the content of the web source code is decoded in Latin1(ISO 8859-1).Unicode characters are removed
         page = a.read().decode('ISO-8859-1').replace('\xa0', ' ').replace('\xad', '')

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

         #get the link to article page
         article_page = ["https://scholar.google.com/citations?view_op=view_citation&hl=en&user=" + code + "&citation_for_view=" + art_code for art_code in artCode]

         #stop when there are no articles left
         if len(titles)!= 100:
            show_more=False
         p=p+1

         #adds article data to a list only if there are articles to include
         if titles:
            [articles_list.append(data) for data in zip(author_code*len(titles), artCode, final_titles, contributors, journals,
            final_cites, years, article_page)]
   
   
   articles_list = []
   df = pd.read_csv(args.authors_file)

   df.apply(lambda row: collect_data(row), axis=1)

   df_articles = pd.DataFrame(articles_list, columns=['GS-Code', 'Art-Code', 'Article', 'Authors', 'Journal', 'Cites', 'Year', 'Link'])

   #clean the article data of html entities and html code
   def clean_articles(x):
      x['Article'] = re.sub(r'<([\s]*[\/]*span|[\s]*[\/]*i|[\s]*[\/]*sub|[\s]*[\/]*sup|[\s]*[\/]*b)>', '', html.unescape(x['Article'])).replace('<span class="gs_fscp">', '')
      x['Authors'] = html.unescape(x['Authors'])
      x['Journal'] = html.unescape(x['Journal']).replace('<span class="gs_oph">,',',').replace('</span>','')
      return x

   df_articles = df_articles.apply(lambda x: clean_articles(x), axis=1)
   print(df_articles)
   #df_articles.to_csv(today.strftime("%Y-%m") + '-paper-cites-GS.csv', index = False)