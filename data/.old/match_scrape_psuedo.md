The following psuedocode describes the process for scraping ball-by-ball data from a single match. Data is read from ```match_list.csv``` and passed line by line to the ```scrape_ballbyball``` function.

```
def scrape(prelim):
	# Assume that prelim consists of 
	# - URL to scorecard
	# - Teams
	# - Venue
	# - Host country
	# - Start date
	# - Toss winner
	# - Toss decision
	# - Scores
	# - Winner
	# - Margin


	# Helper functions
	def check_for_close():

	# Converts a score string (as saved in match_list) to a number of runs and wickets, as integers
	def convert_score(string):
		score = string.split('/')
		runs = score[0] as int

		if score[1] exists:
			wkts = score[1] as int
		else:
			wkts = 10

		return runs, wkts

```