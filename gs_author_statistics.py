import re
import urllib.request
import pandas as pd
from datetime import date

if __name__ == '__main__':

   today = date.today()
   """
   List with the terms or groups you want to search.For example we want to take all researchers related to 
   the University of Las Palmas de Gran Canaria, for this we take all researchers who are in the 'group' and 
   researchers who appear with the term ULPGC. The 'group' is the code assigned to the university by Google Scholar. 
   https://scholar.google.fr/citations?view_op=view_org&hl=en&org=15669781497478426561
   """
   search_list = ['15669781497478426561', 'ULPGC']
   author_data_list = []
   
   for search_element in search_list:
      if re.search('(^[0-9]{20}$)',search_element):
         #URL with university code in GS
         urlbase = "https://scholar.google.fr/citations?hl=en&view_op=view_org&org=" + search_element
         url = urlbase
      else:
         #URL with the terms in GS
         urlbase = "https://scholar.google.fr/citations?hl=en&view_op=search_authors&mauthors=" + search_element.replace(' ','+')
         url = urlbase
   
      page = 10
      finish = False #boolean that indicates when data extraction is finished
      df_columns = ['Nombre', 'GS-Code', 'Citas', 'Citas(5)', 'h-index', 'h-index(5)', 'i10-index', 'i10-index(5)']

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
            a = urllib.request.urlopen("https://scholar.google.fr/citations?hl=en&user=" + author)
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
            finish = True
         else:
            url = urlbase + "&after_author="+after_author.group(1)+"&astart="+str(page)
            page += 10

   #dataframe with all the authors and remove duplicates
   auth_result = pd.DataFrame(author_data_list, columns=df_columns)
   auth_result = auth_result.drop_duplicates(subset='GS-Code', keep="first")
   #the different IDs are taken(*OPTIONAL*)
   #auth_result['ORCID'] = auth_result['Nombre'].str.extract(r'([0-9]{4}-[0-9]{4}-[0-9]{4}-[0-9]{4})')
   #auth_result['ResearcherID'] = auth_result['Nombre'].str.extract(r'([A-Z]{1}-[0-9]{4}-[0-9]{4})')
   
   #all the content of the parentheses are removed
   auth_result["Nombre"] = auth_result['Nombre'].str.replace(r"\(.*\)","").str.strip()
   auth_result.to_csv("C:\\Users\\charl\\Desktop\\Cosas TFG\\ProtoProyecto\\Datos\\Autores\\" + today.strftime("%Y-%m") + '-authors-GS.csv', index = False)