from pandas import DataFrame, read_csv
from os import path
from scrape_match import scrape_cricbuzz

DIR = path.dirname(path.realpath(__file__))

print("Loading match_list.csv")
matches = read_csv(DIR + '/match_list.csv')
print("Succesfully loaded .csv file")

row = matches.iloc[129]
filename = DIR + '/players/players_' + row['Team1'] + row['Team2'] + '_' + row['StartDate'].replace(' ', '') + '.csv'
players = read_csv(filename)
scrape_cricbuzz('https://www.cricbuzz.com/cricket-scores/20718/eng-vs-aus-4th-test-the-ashes-2019', row, players)