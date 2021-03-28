"""

"""
from os import path
from time import sleep, time

from pandas import DataFrame, Series
from requests import get
from bs4 import BeautifulSoup, SoupStrainer
#from selenium import webdriver

from level_keys import BOWL_KEYS


PLAYER_COLS = ['Initials', 'Surname', 'Matches', 'BatAvg', 'BallsFaced', 'BatSR', 'BatArm', 'OversBowled', 'BowlAvg', 'BowlSR', 'BowlEcon', 'BowlType', 'Team']  
# Note: player stats are from BEFORE the start of the match


# Each value to be extracted for each delivery
DATA_COLS = ['Outcome', 'Dismissal', 'Innings', 'HostCountry', \
             'InnBalls', 'BatTeam', 'TeamWkts', 'TeamScore', 'TeamLead', \
             'Batter', 'BatPosition', 'BatScore', 'BatBalls', 'BatAvg', 'BatSR', 'BatArm', \
             'BowlTeam', \
             'Bowler', 'BowlBalls', 'BowlRuns', 'BowlWkts', 'BowlAvg', 'BowlSR', 'BowlType', \
             'SpellBalls', 'SpellRuns', 'SpellWkts', \
             'TossWin', 'TossElect', 'BatTeamTotalRuns', 'BatTeamTotalWkts', 'BowlTeamTotalRuns', 'BowlTeamTotalWkts', \
             'Commentary']

DIR = path.dirname(path.realpath(__file__))


def scrape_players(pd_row):

    def get_players(innings1, innings2):
        batters = innings1.find_all('div', class_ = 'cell batsmen') \
                      + innings2.find_all('div', class_ = 'cell batsmen') 

        # Also include DNB
        dnb = innings1.find_all('div', class_ = 'wrap dnb') + innings2.find_all('div', class_ = 'wrap dnb')

        ids = []
        urls = []
        names = []

        scraped = 0
        
        for b in batters:
            for r in b.find_all(href=True):
                url = r['href']
                urls.append(url)
                
                # Get ID from url
                ids.append(url.split('/')[-1][:-5])

        for d in dnb:
            for r in d.find_all('a', href=True):
                url = r['href']
                urls.append(url)
            
                # Get ID from url
                ids.append(url.split('/')[-1][:-5])
            
        
        return(ids, urls)


    def get_player_stats(p_url, p_id):

        # Access batting stats URL
        sg_url = "http://stats.espncricinfo.com/ci/engine/player/" + str(p_id) + ".html?class=1;spanmax1=" + date + ";spanval1=span;template=results;type=batting"
        page = get(sg_url)
        soup = BeautifulSoup(page.content, 'html.parser')
        # Pandas series to return
        row = Series(index = PLAYER_COLS)

        # Get player name
        name = soup.find('div', class_ = 'icc-home').text.split(' / ')[2]
        name = name.split(' ')
        row['Initials'] = name[0]
        row['Surname'] = " ".join(name[1:])   # Need to combine list into one

        
        # Get correct table
        stats_table = soup.find_all('tr', class_ = 'data1')[1].find_all('td')
        
        if stats_table[1].get('class') == ['left']:
            row['Matches'] = stats_table[2].text
            row['BatAvg']  = stats_table[7].text

            if len(stats_table) > 12:
                row['BallsFaced'] =stats_table[8].text
                row['BatSR'] = stats_table[9].text
        
        else:
            row['Matches'] = stats_table[1].text
            row['BatAvg'] = stats_table[6].text
        
            if len(stats_table) > 11:
                row['BallsFaced'] =stats_table[7].text
                row['BatSR'] = stats_table[8].text   


        # Access bowling stats URL
        sg_url = "http://stats.espncricinfo.com/ci/engine/player/" + str(p_id) + ".html?class=1;spanmax1=" + date + ";spanval1=span;template=results;type=bowling"
        page = get(sg_url)
        strainer = SoupStrainer('tr', class_ = 'data1')
        soup = BeautifulSoup(page.content, 'html.parser', parse_only = strainer)        
 
        # Get correct table
        stats_table = soup.find_all('tr', class_ = 'data1')[1].find_all('td')

        if stats_table[1].get('class') == ['left']:
            row['OversBowled'] = stats_table[4].text
            row['BowlAvg'] = stats_table[10].text
            row['BowlEcon'] = stats_table[11].text
            row['BowlSR'] = stats_table[12].text
        else:
            row['OversBowled'] = stats_table[3].text
            row['BowlAvg'] = stats_table[9].text
            row['BowlEcon'] = stats_table[10].text
            row['BowlSR'] = stats_table[11].text  



        # Get player batting hand and bowl type
        page = get(p_url)
        strainer = SoupStrainer('p', class_ = 'ciPlayerinformationtxt')
        soup = BeautifulSoup(page.content, 'html.parser', parse_only = strainer)

        bowl_arm_txt = None
        for c in soup:
            if c.text[:13] == "Batting style":
                row['BatArm'] = c.text[14:]
            elif c.text[:13] == "Bowling style":
                bowl_arm_txt = c.text[14:]
                break

        try:
            row['BowlType'] = BOWL_KEYS[bowl_arm_txt]
        except KeyError:
            row['BowlType'] = "-"


        return row

    date = pd_row['StartDate'].replace(' ', '+')
    player_detail = DataFrame(columns = PLAYER_COLS)

    # Access scorecard page
    s_url = "https://www.espncricinfo.com/ci/engine/match/" + str(pd_row['urlEnd']) + ".html"
    page = get(s_url)
    strainer = SoupStrainer('article', class_ = 'sub-module scorecard')
    soup = BeautifulSoup(page.content, 'html.parser', parse_only = strainer)

    # Get players
    first_innings = soup.find_all('article', class_ = 'sub-module scorecard')[:2]
    play_ids, play_urls = get_players(first_innings[0], first_innings[1])
    for p_id, p_url in zip(play_ids, play_urls):
        n_play = get_player_stats(p_url, p_id)
        player_detail = player_detail.append(n_play, ignore_index = True)



    # Format save string
    save_str = pd_row['Team1'] + pd_row['Team2'] + '_' + date.replace("+","")

    # Output data to CSV file
    player_detail.to_csv('players/players_' + save_str+ '.csv', index = False)



def scrape_ballbyball(pd_row, players):

    def driver_scroll_ballbyball(driver):
        """ Scrolls through ball-by-ball to fully load page.
            
            Modified version of accepted answer on
            https://stackoverflow.com/questions/48850974/selenium-scroll-to-end-of-page-in-dynamically-loading-webpage/48851166#48851166 

        """

        # Get scroll height.
        last_height = driver.execute_script("return document.body.scrollHeight")

        changed = 0
        SCROLL_NUM_LIM = 3      # Number of scrolls required without a change in page height before returning
        while True:
            
            # Scroll down to the bottom.
            driver.execute_script("window.scrollTo(0, 0);")
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            sleep(1.5)

            # Calculate new scroll height and compare with last scroll height.
            new_height = driver.execute_script("return document.body.scrollHeight")

            if changed == SCROLL_NUM_LIM:
                break

            if new_height != last_height:
                changed = 0
            else:
                changed += 1

            last_height = new_height

    # Helper function - convert innings score to runs and wickets
    def add_score(string, total):
        # Remove '(f/o)' and 'd' from score
        string = string.replace('d', '')
        string = string.replace('(f/o)', '')

        score = string.split('/')
        runs = int(score[0])

        try:
            wkts = int(score[1])
        except IndexError:
            wkts = 10

        return [sum(i) for i in zip(total, [runs, wkts])]

    
    # Relabel row information
    match_id = pd_row['urlEnd']
    teams = pd_row[['Team1', 'Team2']]
    date = pd_row['StartDate'].replace(' ', '+')

    # Total runs scored and wickets lost for each team in entire game
    # Provides some measure of the pitch quality
    total1 = [0, 0]
    total2 = [0, 0]


    # Team1 always bats first
    team_bat = 0

        # Determine order of innings from prelimiary data
    inns_order = [0]
    total1 = add_score(pd_row['Score1'], total1)
    follow_on = False

    if pd_row['Score2'] != '-':
        inns_order.append(1)
        total2 = add_score(pd_row['Score2'], total2)

        if pd_row['Score3'] != '-':
            if pd_row['Score3'][-5:] == '(f/o)':
                # Follow-on enforced
                follow_on = True
                inns_order.append(1)
                total2 = add_score(pd_row['Score3'], total2)

            else:
                inns_order.append(0)
                total1 = add_score(pd_row['Score3'], total1)

            if pd_row['Score4'] != '-':
                if follow_on:
                    inns_order.append(0)
                    total1 = add_score(pd_row['Score4'], total1)

                else:
                    inns_order.append(1)
                    total2 = add_score(pd_row['Score4'], total2)

    # Nested if statements prevent unnessecary checking if game lasted less than 4 innings

    # Extract commentary URL
    s_url = "https://www.espncricinfo.com/ci/engine/match/" + str(pd_row['urlEnd']) + ".html"
    page = get(s_url)
    strainer = SoupStrainer('a', class_ = 'widget-tab-link ')
    soup = BeautifulSoup(page.content, 'html.parser', parse_only = strainer)

    c_id = soup.find_all('a')[1]['href']
    c_url = 'https://www.espncricinfo.com' + c_id

    # 
    lead = 0

    # Each innings
    for inns in range(1, len(inns_order) + 1):
        print('Scraping innings ' + str(inns))

        # Load ball commentary and scroll
        url = c_url + "?innings=" + str(inns)
        driver = webdriver.Firefox(executable_path = DIR + '/geckodriver.exe')
        driver.get(url)
        
        # scroll to bottom of page
        sleep(0.5)
        driver_scroll_ballbyball(driver)

        # Parse with BeautifulSoup
        strainer = SoupStrainer('div', class_ = 'item-wrapper')
        soup = BeautifulSoup(driver.page_source, 'html.parser', parse_only = strainer)
        driver.close()

        times = list(reversed(soup.find_all('div', class_ = 'time-stamp')))
        outcomes = list(reversed(soup.find_all('span', class_ = 'over-score')))
        descs = list(reversed(soup.find_all('div', class_ = 'description')))

        # All dismissal descriptions in innings
        disms = list(reversed(soup.find_all('p', class_ = 'dismissal')))

        # Prepare player dictionaries
        bat_stats = {}
        bowl_stats = {}

        # Bowler spells
        curr_bowl = []
        last_bowl = []

        # Team score
        t_score = 0
        t_wkts = 0


        data = DataFrame(columns = DATA_COLS)
        data['InnBalls'] = range(len(times))

        # Fill in match information
        data['HostCountry'] = pd_row['Country']
        data['TossWin'] = pd_row['TossWin']
        data['TossElect'] = pd_row['TossElect']

        # Fill in innings information
        data['Innings'] = inns
        data['BatTeam'] = pd_row['Team' + str(inns_order[inns - 1] + 1)]
        data['BowlTeam'] = pd_row['Team' + str((not inns_order[inns - 1]) + 1)]

        if inns_order[inns - 1]:
            data['BatTeamTotalRuns'] = total2[0]
            data['BatTeamTotalWkts'] = total2[1]
            data['BowlTeamTotalRuns'] = total1[0]
            data['BowlTeamTotalWkts'] = total1[1]

        else:
            data['BatTeamTotalRuns'] = total1[0]
            data['BatTeamTotalWkts'] = total1[1]
            data['BowlTeamTotalRuns'] = total2[0]
            data['BowlTeamTotalWkts'] = total2[1]



        # Iterate through each ball
        for ball, over, outcome, desc in zip(range(len(times)), times, outcomes, descs):
            if ball == 0 and over.text != '0.1':
                raise AttributeError('Missing deliveries, cannot scrape')

            data.at[ball,'Outcome'] = outcome.text
            data.at[ball,'Commentary'] = desc.text


            # Get bowler and batter
            [bowler, batter] = desc.text.split(', ')[0].split(' to ')
            bowler_full = bowler
            batter_full = batter

            if False and batter not in bat_stats.keys():
                # Find in pregame player stats
                possible = players[players['Surname'].str == batter].values
                if len(possible) == 0:
                    # We have a problem - ditch this match and move on
                    raise AttributeError('Cannot resolve player name conflict: multiple players with name %s' % (batter))

                if len(possible) == 1:
                    bat_stats.update(possible.to_dict('records'))


            # Team score detail
            data.at[ball, 'TeamScore'] = t_score
            data.at[ball, 'TeamWkts'] = t_wkts
            data.at[ball, 'TeamLead'] = lead

            if outcome.text == 'W':
                # Handle wicket

                # Determine mode of dimissal
                dimis_str = disms[t_wkts].text
                dimis_str = dimis_str.replace(batter_full, "")
                data.at[ball, 'Dismissal'] = dismis_str.split(" ")[1]

                # Handle runout

                t_wkts += 1

                continue

            else:
                data.at[ball, 'Dismissal'] = 'no'

            # Update team score, batter and bowler figures
            if outcome.text[-2:] == 'nb':
                # Assume extra runs on no ball were scored by batter
                t_score += int(outcome.text[:-2])
                lead += int(outcome.text[:-2])
            
            elif outcome.text[-1:] == 'w':
                t_score += int(outcome.text[:-1])
                lead += int(outcome.text[:-1])

            elif outcome.text[-2:] == 'lb':
                t_score += int(outcome.text[:-2])
                lead += int(outcome.text[:-2])

            elif outcome.text[-1:] == 'b':
                t_score += int(outcome.text[:-1])
                lead += int(outcome.text[:-1])

            else:
                t_score += int(outcome.text)
                lead += int(outcome.text)




            # DATA_COLS = ['Outcome', 'Dismissal', 'Innings', 'HostCountry', \
            #  'InnBalls', 'BatTeam', 'TeamWkts', 'TeamScore', 'TeamLead', \
            #  'Batter', 'BatScore', 'BatBalls', 'BatAvg', 'BatSR', 'BatArm', \
            #  'BowlTeam', \
            #  'Bowler', 'BowlBalls', 'BowlRuns', 'BowlWkts', 'BowlAvg', 'BowlSR', 'BowlType', \
            #  'SpellBalls', 'SpellRuns', 'SpellWkts', \
            #  'TossWin', 'TossElect', 'BatTeamTotalRuns', 'BatTeamTotalWkts', 'BowlTeamTotalRuns', 'BowlTeamTotalWkts', \
            #  'Commentary']


        # Save as .csv
        save_str = pd_row['Team1'] + pd_row['Team2'] + '_' + pd_row['StartDate'].replace(' ', '') + '_inn' + str(inns)

        # Output data to CSV file
        data.to_csv(DIR + '/ballbyball/' + save_str + '.csv', index = False)

        # Prepare for next innings
        if inns != len(inns_order):
            # If follow on, maintain lead
            if inns != 2 or not follow_on:
                # Change lead
                lead = -lead

            team_bat = inns_order[inns - 1]


def scrape_cricbuzz(url, pd_row, players):

    
    # Helper function - convert innings score to runs and wickets
    def add_score(string, total):
        # Remove '(f/o)' and 'd' from score
        string = string.replace('d', '')
        string = string.replace('(f/o)', '')

        score = string.split('/')
        runs = int(score[0])

        try:
            wkts = int(score[1])
        except IndexError:
            wkts = 10

        return [sum(i) for i in zip(total, [runs, wkts])]


    # Helper function - 
    def find_player(players_df, name):
        return None

    # Log time
    start_time = time()

    teams = pd_row[['Team1', 'Team2']]
    date = pd_row['StartDate'].replace(' ', '+')

    # Total runs scored and wickets lost for each team in entire game
    # Provides some measure of the pitch quality
    total1 = [0, 0]
    total2 = [0, 0]


    # Team1 always bats first
    team_bat = 0

        # Determine order of innings from prelimiary data
    inns_order = [0]
    total1 = add_score(pd_row['Score1'], total1)
    follow_on = False

    if pd_row['Score2'] != '-':
        inns_order.append(1)
        total2 = add_score(pd_row['Score2'], total2)

        if pd_row['Score3'] != '-':
            if pd_row['Score3'][-5:] == '(f/o)':
                # Follow-on enforced
                follow_on = True
                inns_order.append(1)
                total2 = add_score(pd_row['Score3'], total2)

            else:
                inns_order.append(0)
                total1 = add_score(pd_row['Score3'], total1)

            if pd_row['Score4'] != '-':
                if follow_on:
                    inns_order.append(0)
                    total1 = add_score(pd_row['Score4'], total1)

                else:
                    inns_order.append(1)
                    total2 = add_score(pd_row['Score4'], total2)

    # Nested if statements prevent unnessecary checking if game lasted less than 4 innings

    page = get(url)
    strainer = SoupStrainer(class_ = ['cb-col cb-col-90 cb-com-ln', 'cb-col cb-col-8 text-bold'])
    soup = BeautifulSoup(page.content, 'html.parser', parse_only = strainer)


    comms = soup.find_all(class_ = 'cb-col cb-col-90 cb-com-ln')
    overcount = soup.find_all(class_ = 'cb-col cb-col-8 text-bold')

    
    inns = 0
    lead = 0

    data = DataFrame(index = range(0,len(overcount)), columns = DATA_COLS)

    # Iterate through each ball-by-ball item in reverse
    for i,(over_tag, bbb_tag) in enumerate(zip(reversed(overcount), reversed(comms))):
        over = over_tag.text
        commentary = bbb_tag.text

        if (over == "0.1"):
            # Start of new innings
            balls = 0  
            inns = inns + 1

            # Prepare player dictionaries
            bat_stats = {}
            bowl_stats = {}

            # Team score
            t_score = 0
            t_wkts = 0

            # Change lead - check for follow on
            if not (follow_on and inns == 3):
                lead = -lead


        data.at[i,'InnBalls'] = balls
        balls = balls + 1

        # Fill in innings information
        data.at[i,'Innings'] = inns
        data.at[i,'BatTeam'] = pd_row['Team' + str(inns_order[inns - 1] + 1)]
        data.at[i,'BowlTeam'] = pd_row['Team' + str((not inns_order[inns - 1]) + 1)]

        # Get batter and bowler
        comma_split = commentary.split(', ')
        [bowler,batter] = comma_split[0].split(" to ")

        # Find identifying key in players dataframe
        bowl_key = find_player(players, bowler)
        bat_key = find_player(players, batter)

        # Get outcome
        outcome = comma_split[1]

        if outcome[:3] == "out":
            # Dismissal
            dism_det = (commentary.split(". "))[-1][:-7]
            outcome = outcome.split(" ")[0]
            print(dism_det)

            # Handle dismissal
            t_wkts += 1

            continue

        else:
            data.at[i, 'Dismissal'] = 'no'

    
                # Update team score, batter and bowler figures
        if outcome[-2:] == 'nb':
            # Assume extra runs on no ball were scored by batter
            t_score += int(outcome[:-2])
            lead += int(outcome[:-2])
        
        elif outcome[-1:] == 'w':
            t_score += int(outcome[:-1])
            lead += int(outcome[:-1])

        elif outcome[-2:] == 'lb':
            t_score += int(outcome[:-2])
            lead += int(outcome[:-2])

        elif outcome[-1:] == 'b':
            t_score += int(outcome[:-1])
            lead += int(outcome[:-1])

        else:
            if outcome != "no run":
                t_score += int(outcome[0])
                lead += int(outcome[0])


        data.at[i, 'Outcome'] = outcome


        


        





    # Fill in remaining (universal) match information
    data['HostCountry'] = pd_row['Country']
    data['TossWin'] = pd_row['TossWin']
    data['TossElect'] = pd_row['TossElect']


    # Match totals
    if inns_order[inns - 1]:
        data['BatTeamTotalRuns'] = total2[0]
        data['BatTeamTotalWkts'] = total2[1]
        data['BowlTeamTotalRuns'] = total1[0]
        data['BowlTeamTotalWkts'] = total1[1]
    else:
        data['BatTeamTotalRuns'] = total1[0]
        data['BatTeamTotalWkts'] = total1[1]
        data['BowlTeamTotalRuns'] = total2[0]
        data['BowlTeamTotalWkts'] = total2[1]

    print(data)
    print("--- %s seconds ---" % (time() - start_time))