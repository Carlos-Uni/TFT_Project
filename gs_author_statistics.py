import re
import urllib.request
import pandas as pd
from datetime import date

if __name__ == '__main__':

   today = date.today()
   #URL with university code in GS
   urlbase = "https://scholar.google.fr/citations?view_op=view_org&hl=en&org=15669781497478426561"
   url = urlbase

   page = 10
   finish = False #boolean that indicates when data extraction is finished
   flag_change = False #boolean that indicates when another search is performed
   df_columns = ['Nombre', 'GS-Code', 'Citas', 'Citas(5)', 'h-index', 'h-index(5)', 'i10-index', 'i10-index(5)']
   author_data_list = []

   while not finish:
      f = urllib.request.urlopen(url)
      #the content of the web source code is decoded in Latin1(ISO 8859-1)
      text = f.read().decode('ISO-8859-1')
      
      #get author codes and names
      authors = re.findall("<a href=\"/citations?\S*user=([\w-]*)\">",text)
      authors_names = re.findall("<img alt=\"(.*?)\"",text)
      #list that will contain the bibliographic data
      data = [] 

      #search authors statistics in their profile
      for author in authors:
         a = urllib.request.urlopen("https://scholar.google.fr/citations?hl=en&user="+author)
         autor_text = a.read().decode('ISO-8859-1')
         
         cites = re.search("Citations</a></td><td class=\"gsc_rsb_std\">(\d*)</td><td class=\"gsc_rsb_std\">(\d*)</td>", autor_text)
         h = re.search("h-index</a></td><td class=\"gsc_rsb_std\">(\d*)</td><td class=\"gsc_rsb_std\">(\d*)</td></tr>", autor_text)
         i10 = re.search("i10-index</a></td><td class=\"gsc_rsb_std\">(\d*)</td><td class=\"gsc_rsb_std\">(\d*)</td></tr>", autor_text)
         
         if cites is not None:
            data.append([author, cites.group(1), cites.group(2), 
                         h.group(1), h.group(2), i10.group(1), i10.group(2)])
         else:
            data.append([author, '0', '0', '0', '0', '0', '0'])
      
      for name,cite in zip(authors_names,data):

         author_data_list.append(list([name.strip()]) + list(cite))
         print(name + ", " + ', '.join(cite))

      #stop when there are no authors left
      after_author = re.search("after_author....([\w-]*)", text)
      if after_author is None:
         if flag_change is False:
            #Dataframe with autors that belong to the university
            df_author = pd.DataFrame(author_data_list, columns=df_columns)
            #URL with the search of academic profiles connected with the university in GS
            urlbase = "https://scholar.google.fr/citations?hl=en&view_op=search_authors&mauthors=ULPGC"
            url = urlbase
            flag_change = True
            page = 10
            author_data_list = []
         else:
            finish = True
            #Dataframe with authors that are connected to the university
            df_other_author = pd.DataFrame(author_data_list, columns=df_columns)
      else:
         url = urlbase + "&after_author="+after_author.group(1)+"&astart="+str(page)
         page += 10

   #merging the dataframes
   auth_result = pd.merge(df_author, df_other_author, on=df_columns, how='outer')
   #the different IDs are taken(*OPTIONAL*)
   """
   auth_result['ORCID'] = auth_result['Nombre'].str.extract(r'([0-9]{4}-[0-9]{4}-[0-9]{4}-[0-9]{4})')
   auth_result['ResearcherID'] = auth_result['Nombre'].str.extract(r'([A-Z]{1}-[0-9]{4}-[0-9]{4})')
   """
   #all the content of the parentheses are removed
   auth_result["Nombre"] = auth_result['Nombre'].str.replace(r"\(.*\)","").str.strip()
   auth_result.to_csv("C:\\Users\\charl\\Desktop\\Cosas TFG\\ProtoProyecto\\Datos\\Autores\\" + today.strftime("%Y-%m") + '-authors-GS.csv', index = False)
