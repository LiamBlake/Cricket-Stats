
from scrape_players import scrape_statsguru
#'mtest', 
for c in ['mtest', 'wtest', 'modi', 'wodi', 'mt20', 'wt20']:
    print('============= Scraping ' + c + ' =============')
    scrape_statsguru(c)

print("Done :)")