"""
Scrapes from ESPNCricinfo Statsguru data, teams, venue, country and id for
every test match since Januray 1, 2001. The data is saved as csv files:
- match_list.csv: data for each test match, and
- venues.csv: a list of venues and their corresponding countries.

NOTE: Assumes that each team has played less than 200 games since 2001.

Main script does not handle certain test matches with unusual circumstances,
e.g. the forfeited match between ENG and PAK in 2006. Given these are unusual
matches usually with external factors involved, we'll just ignore them in our
data analysis.

"""

from os import path
from requests import get
from bs4 import BeautifulSoup
from pandas import DataFrame

from level_keys import COUNTRY_CODES

# Directory for saving data
DIR = path.dirname(path.realpath(__file__))

# This list *MUST* be the same order as the country date of first match
COUNTRIES = {1: 'England', 2: 'Australia', 3: 'South Africa', \
             4: 'West Indies', 5: 'New Zealand', 6: 'India', \
             7: 'Pakistan', 8: 'Sri Lanka', 9: 'Zimbabwe', \
             25: 'Bangladesh', 27: 'United Arab Emirates', 29: 'Ireland'}

# URL components
URL_START = 'https://stats.espncricinfo.com/ci/engine/stats/index.html?class=1;filter=advanced;host='
URL_END = ';orderby=start;size=200;spanmin1=01+Jan+2001;spanval1=span;template=results;type=aggregate;view=results'

# Data to extract from each match
COLUMNS = ['urlEnd', 'Team1', 'Team2', 'Venue', 'Country', 'StartDate', \
           'TossWin', 'TossElect', 'Score1', 'Score2', 'Score3', 'Score4', \
           'Winner', 'Margin']


""" Helper function - remove " (xx ov)" from string, where xx is any substring
"""
def remove_ov(string):
    # From start, find (
    start = string.find('(')
    if start == -1: 
        raise ValueError

    # From end, find ov)
    end = string.rfind('ov)')
    if end == -1: 
        raise ValueError

    return string[:start-1] + string[end+3:]


# Storage of data, to output to csv
data = DataFrame(columns=COLUMNS)
venues = {}

for i, c in COUNTRIES.items():
    print("Scraping matches in", c)

    # Construct URL
    url = URL_START + str(i) + URL_END

    # Get HTML and parse to BeautifulSoup
    page = get(url)
    soup = BeautifulSoup(page.content, 'html.parser')

    # Each entry is a "Data1" class
    for j, tr in enumerate(soup.find_all('tr', class_='data1')):

        try:
            # New dataframe to append to full dataset
            n_row = DataFrame(index=[0], columns=COLUMNS)
            n_row['Country'] = COUNTRY_CODES[c]

            # Get ground and add to dictionary if not already there
            ground = tr.find_all('td', class_='left')[4].text
            if ground not in venues.keys():
                venues.update({ground : COUNTRY_CODES[c]})

            n_row['Venue'] = ground


            # Get start date
            start_date = tr.find_all('td')[6]
            n_row['StartDate'] = start_date.text


            # Get corresponding popup for link
            popup = soup.find('div', class_='engine-dd', id='engine-dd' + str(j + 1))

            # Get href
            href = popup.find_all('a')[1]
            url_s = href['href']
            url_s = 'https://www.espncricinfo.com' + url_s

            n_row['urlEnd'] = url_s.split('/')[-1][:-5]

            # Parse scorecard to get toss information and team scores
            scorecard = get(url_s)
            url_soup = BeautifulSoup(scorecard.content, 'html.parser')

            # Get toss details
            toss_full = url_soup.find_all('div', class_='match-detail--right')[1].text.split(' , ')
            n_row['TossWin'] = COUNTRY_CODES[toss_full[0]]
            toss_elect = toss_full[1]

            if toss_elect == 'elected to bat first':
                n_row['TossElect'] = 'bat'
            elif toss_elect == 'elected to field first':
                n_row['TossElect'] = 'bowl'
            else:
                raise ValueError('Invalid toss result')

            # Get teams
            header = url_soup.find('div', class_='gp__cricket__gameHeader')
            team1_det = header.find('li', class_='cscore_item cscore_item--home')
            team2_det = header.find('li', class_='cscore_item cscore_item--away')

            # NOTE: Cricinfo labels the teams as home and away in the HTML, 
            # but this has nothing to do with which team actually is the home 
            # team.
            # Team1 is always the team that batted first
            n_row['Team1'] = COUNTRY_CODES[team1_det.find('span', class_='cscore_name cscore_name--long').text]
            n_row['Team2'] = COUNTRY_CODES[team2_det.find('span', class_='cscore_name cscore_name--long').text]

            # Get scores
            team1_scores = team1_det.find('div', class_='cscore_score').text.split(' & ')
            team2_scores = team2_det.find('div', class_='cscore_score').text.split(' & ')

            # TODO: Refactor this into less shoddy code
            no_inns = len(team1_scores) + len(team2_scores)
            try:
                # Team 1 always bats first
                n_row['Score1'] = team1_scores[0]

                # Team 2 bats second
                n_row['Score2'] = team2_scores[0]

                # Team 2 bats again
                if len(team2_scores) > 1:
                    # Check for follow-on
                    if team2_scores[1][-5:] == "(f/o)":
                        n_row['Score3'] = team2_scores[1]
                        n_row['Score4'] = team1_scores[1]
                    else:
                        n_row['Score3'] = team1_scores[1]
                        n_row['Score4'] = team2_scores[1]

                # Team 2 wins by an innings
                else:
                    n_row['Score3'] = team1_scores[1]

            except IndexError:
                # Leave as is, treat NaN as innings not played
                pass

            # Remove over count from final inning score
            n_row.at[0, 'Score' + str(no_inns)] = remove_ov(n_row.at[0, 'Score' + str(no_inns)])


            # Get match result
            result = header.find('span', class_='cscore_notes_game').text
            if result == 'Match drawn':
                n_row['Winner'] = 'draw'
                n_row['Margin'] = '-'
            else:
                result_split = result.split(' won by ')
                n_row['Winner'] = COUNTRY_CODES[result_split[0]]
                n_row['Margin'] = result_split[1]

            data = data.append(n_row, ignore_index=True)

        except (ValueError, AttributeError, IndexError, KeyError) as e:
            # If an error is caused, skip this match and continue
            print(e)
            continue


# Replace NaN with "-" in data
data = data.fillna("-")

# Output data to csv
print('Saving data to match_list.csv')
save_path = path.join(DIR, 'match_list.csv')
data.to_csv(save_path, index=False)

# Output venues to csv
print('Saving venues list to venues.csv')
save_path = path.join(DIR, 'venues.csv')
with open(save_path, 'w') as f:
    for key, val in venues.items():
        f.write("%s,%s\n" % (key, val))
