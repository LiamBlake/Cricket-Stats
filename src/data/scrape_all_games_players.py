
from pandas import DataFrame, read_csv
from scrape_match import scrape_players

# Import
print("Loading match_list.csv")
matches = read_csv('match_list.csv')
print("Succesfully loaded .csv file")

START_IND = 788

no_succ = 0
for ind in (matches.index[START_IND:]):

	row = matches.loc[ind]
	print("Scraping players from match %i:\n%s v %s,\n%s" % (ind, row['Team1'], row['Team2'], row['StartDate']))
		
	try:
		scrape_players(row)
		no_succ += 1
	except (AttributeError, IndexError, ValueError) as e:
		print("Scrape failed")
		print(e)

	print('===============================')


print("====== Scraping Finished ======")
print("Successfully scraped players from %i matches " % no_succ)
print("out of %i possible" % len(matches.index[START_IND:]))
print("===============================")