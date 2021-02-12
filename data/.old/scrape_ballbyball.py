# -*- coding: utf-8 -*-
"""
Created on Sat Jan 25 11:28:06 2020



Assumptions
    - At least three innings in match    
    - No more than 10 extras on any one legal delivery
    - No stumpings off wides
    - No runouts


Each of these need to be addressed


"""


import pandas as pd
from bs4 import BeautifulSoup
from os import path
from requests import get
from selenium import webdriver
from time import sleep
from numpy import floor
from level_keys import NAMES, NUM_MONTHS, BOWL_KEYS

# Global variables
DIR = path.dirname(path.realpath(__file__))

DATA_COLS = ['outcome', 'innings', 'team_wkts', 'team_score', 
                                   'team_lead', 'bat_score', 'bat_balls', 'bat_avg', 'bat_arm',
                                   'bowl_balls', 'bowl_runs', 'bowl_wkts', 'bowl_avg', 'bowl_type']


def get_players(inns):
    batters = inns.find_all('div', class_ = 'cell batsmen')
    ids = []
    urls = []
    names = []
    
    for b in batters:
        for r in b.find_all(href=True):
            url = r['href']
            urls.append(url)
            
            # Get ID from url
            ids.append(url.split('/')[-1][:-5])

    
    # Also include DNB
    dnb = inns.find_all('div', class_ = 'wrap dnb')[0]
    for r in dnb.find_all('a', href=True):
        url = r['href']
        urls.append(url)
        
        # Get ID from url
        ids.append(url.split('/')[-1][:-5])
        
    
    return(ids, urls)
    

# Extracts bowler name and batter name from delivery description. Pass delivery
# as string 
def desc_to_name(desc_txt):
    split = desc_txt.split(' ')
    
    bowl = split[0]
    bat = split[2][:-1]
    
    # Ensure no '\n' at end of bowler
    if bowl[-1:] == "\n":
        bowl = bowl[:-1]
    
    return bowl, bat


def data_row(comm_item, pregame_data, innings):
    # Globals
    global bats
    global bowls
    global team_wkts
    global team_score
    global team_lead
    
    # Entry for data
    n_row = pd.DataFrame(index = [0], columns = DATA_COLS)
    

    outcome = comm_item.find('span', class_ = "over-score").text
    desc = comm_item.find('div', class_ = "description").text


    # get bowler and batter
    bowl, bat = desc_to_name(desc)
    
    # Find in dictionary
    if not bowl in bowls.keys():
        # Initialise bowler in dict
        bowls.update({bowl: [0,0,0]})
     
    if not bat in bats.keys():
        # Initialise batter in dict
        bats.update({bat: [0,0]})
        
        
    # Save data
    n_row['outcome'] = outcome
    
    n_row['innings'] = innings
    n_row['team_wkts'] = team_wkts
    n_row['team_score'] = team_score
    n_row['team_lead'] = team_lead
    
    n_row['bat_score'] = bats[bat][0]
    n_row['bat_balls'] = bats[bat][1]
    n_row['bat_avg'] = pregame_data[bat][0]
    n_row['bat_arm'] = pregame_data[bat][2]
    
    n_row['bowl_balls'] = bowls[bowl][0]
    n_row['bowl_runs'] = bowls[bowl][1]
    n_row['bowl_wkts'] = bowls[bowl][2]     
    n_row['bowl_avg'] = pregame_data[bowl][1]
    n_row['bowl_type'] = pregame_data[bowl][3]
    
    
    # Update game situation and player states
    bowls[bowl][0] += 1

    if outcome[-1] == 'W':

    	# # Check if run out
     #    dism = comm_item.find('p', class_ = 'dismissal').text
     #    if dism.split(' ')[2:4] == "run out":
    	# 	# Compare out score, 
     #        diff = bats[dism.split(' ')[1]][0] - int(dism.split(' ')[-7])
     #        team_score += diff
     #        team_lead += diff

        team_wkts += 1
        bowls[bowl][2] += 1
        bats[bat][1] += 1
        
    else:
        score = int(outcome[0])
        
        team_score += score
        team_lead += score

        # If not byes, update bowler figures                

        if outcome[-2:] == 'nb' or outcome[-1] != 'b':
            bowls[bowl][1] += score
        
        # Check if delivery is legal
        if outcome[-1] == 'w' or outcome[-2:] == 'nb':

            # Check if extra runs scored off no ball
            if outcome[-2:] == 'nb' and int(score) > 1:
                bats[bat][0] += int(score) - 1
                
        else:
            if not outcome[-1] == 'b':
                bats[bat][0] += int(score)
                
            bats[bat][1] += 1



    return n_row


def scroll_down(driver):
    """A method for scrolling to bottom of a dynamically loading page.

    From https://stackoverflow.com/questions/48850974/selenium-scroll-to-end-of-page-in-dynamically-loading-webpage/48851166#48851166 
    """

    # Get scroll height.
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:

        # Scroll down to the bottom.
        driver.execute_script("window.scrollTo(0, 0);")
        sleep(0.25)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        sleep(1)

        # Calculate new scroll height and compare with last scroll height.
        new_height = driver.execute_script("return document.body.scrollHeight")

        if new_height == last_height:
              break


        last_height = new_height




def scrape_game(series_id, game_id):
    # Globals
    global bats
    global bowls
    global team_wkts
    global team_score
    global team_lead
    
    # Scorecard
    url = "https://www.espncricinfo.com/series/" + str(series_id) + "/scorecard/" + str(game_id)
    page = get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    
    # Determine date of start of match
    header = soup.find_all('div', class_ = 'sub-module gameHeader')[0]
    date = header.find_all('div', class_ = 'cscore_info-overview')[0].text.split(' ')
    month = date[-3]
    day = date[-2].split('-')[0]
    year = date[-1]
    date = day + "+" + month + "+" + year
    
    # Determine teams and order of innings
    all_scorecards = soup.find_all('article', class_ = 'sub-module scorecard')

    team1 = all_scorecards[0].find_all('a', class_ = '', role = "button")[0].text
    team2 = all_scorecards[1].find_all('a', class_ = '', role = "button")[0].text
    teams = [team1[:-12], team2[:-12]]
    inn_order = [0,1,None,None]
    
    # determine if follow on is enforced
    follow_on = (all_scorecards[2].find_all('a', class_ = '', role = "button")[0].text == team2 + " 2nd Innings (following on)")
    if follow_on:
        inn_order[2] = 1
    else:
        inn_order[2] = 0
        
    # check if third innings is played
    if len(all_scorecards) > 3:
        if follow_on:
            inn_order[3] = 0
        else:
            inn_order[3] = 1
       
    if inn_order[3] == None:
        inn_len = 3
    else:
        inn_len = 4
        
    del team1, team2, follow_on
    
    pregame_data = {}
    
    


    players1, play_urls1 = get_players(all_scorecards[0])
    players2, play_urls2 = get_players(all_scorecards[1])
    
    for (id, p_url) in zip(players1 + players2, play_urls1 + play_urls2):
        # Access URL
        sg_url = "http://stats.espncricinfo.com/ci/engine/player/" + str(id) + ".html?class=1;spanmax1=" + date + ";spanval1=span;template=results;type=allround"
        page = get(sg_url)
        soup = BeautifulSoup(page.content, 'html.parser')
        
        # Get player name
        name = soup.find_all('div', class_ = 'icc-home')[0].text.split(' / ')[2]

        name = name.split(' ')[1]

        
        # Get correct table
        stats_table = soup.find_all('tr', class_ = 'data1')[1].find_all('td')
        
        if stats_table[1].get('class') == ['left']:
            bat = stats_table[5].text
            bowl = stats_table[9].text
        else:
            bat = stats_table[4].text
            bowl = stats_table[8].text
        
        
        try:
            bat = float(bat)
        except ValueError:
            pass
        
        try:
            bowl = float(bowl)
        except ValueError:
            pass


        # Get player batting hand and bowl type
        page = get(p_url)
        soup = BeautifulSoup(page.content, 'html.parser')

        bat_arm = None
        bowl_arm_txt = None
        for c in soup.find_all('p', class_ = 'ciPlayerinformationtxt'):
            if c.text[:13] == "Batting style":
                bat_arm = c.text[14:]
            elif c.text[:13] == "Bowling style":
                bowl_arm_txt = c.text[14:]
                break

        try:
            bowl_arm = BOWL_KEYS[bowl_arm_txt]
        except KeyError:
            bowl_arm = "-"
        
        pregame_data.update({name: [bat, bowl, int(bat_arm == "Left-hand bat"), bowl_arm]})


    for inns in range(inn_len):
        bats = {}
        bowls = {}
        team_wkts = 0
        
        # Determine team lead
        if inns == 0:
            team_lead = 0
        elif inn_order[inns - 1] != inn_order[inns]:
            team_lead *= -1
            
        team_score = 0
        
    
        ballbyball ="https://www.espncricinfo.com/series/" + str(series_id) + "/commentary/" + str(game_id) + "?innings=" + str(inns + 1)
           # Open webdriver and load ball by ball
        driver = webdriver.Firefox(executable_path = 'geckodriver.exe')
        driver.get(ballbyball)
        
        # scroll to bottom of page
        sleep(3)
        scroll_down(driver)
        sleep(2)
        
        # Ball by ball
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        driver.close()
        
        data = pd.DataFrame(columns = DATA_COLS)
        
        # get main window
        main_element = soup.find(id = 'main-container')
        comm_elems = main_element.find_all('div', class_='content match-commentary__content')[0]
        
        
        # organise all relevant commentary objects into one dataframe
        ind = -1
        ball = 0
        pd_overs = pd.DataFrame(columns = [1, 2, 3, 4, 5, 6])
        pd_temp = None
        
        for comm in comm_elems.find_all('div', class_ = 'item-wrapper'):
            
            # check for end of over
            if ball <= 1:
                # append over to full dataframe
                if ind > -1:
                    pd_overs = pd_overs.append(pd_temp)
                
                # reset
                ind += 1
                ball = 6
                extras = 0
                pd_temp = pd.DataFrame(index = [ind], columns = [1, 2, 3, 4, 5, 6])
            
            txt = comm.find('span', class_ = "over-score").text
            time = float(comm.find('div', class_ = "time-stamp").text)
            ball = round(time - floor(time), 1)*10

            if txt[-1] == 'w' or txt[-2:] == 'nb':
                # add extra delivery
                pd_temp[10*(ball) + extras] = [comm]
                
                # add the column to pd_overs
                if not 10*ball + extras in pd_overs.columns:
                    pd_overs[10*(ball) + extras] = [None] * len(pd_overs.index)
                
                extras += 1
 
            else:
                pd_temp.at[ind, ball] = comm
                extras = 0

        pd_overs = pd_overs.append(pd_temp)


        # Run through each delivery and reconstruct innings
        for k in reversed(pd_overs.index):  
            
            # get over
            over = pd_overs.loc[k]
            
            # For each ball
            for b in range(1,7):
 
                if type(over[b]) == float:
                    continue
                
                # Check for corresponding extra deliveries
                searching = True
                ind = 0
                while searching:
                    key = 10*b + ind 
                    if key in pd_overs.columns:
                        try:
                            # Parse illegal delivery
                            data = data.append(data_row(over[b], pregame_data, inns + 1), ignore_index = True)
        
                            ind += 1
                            
                        except AttributeError:
                            searching = False
                            
                    else:
                        searching = False
                
                
                # Parse legal delivery
                data = data.append(data_row(over[b], pregame_data, inns + 1), ignore_index = True)
        
        
        driver.quit()

        # Export to CSV file
        if int(day) < 10:
            p_day = "0" + day
        
        # construct file name
        fname = p_day + NUM_MONTHS[month] + year + "-" + NAMES[teams[0]] + NAMES[teams[1]] + "-" + str(inns + 1) + NAMES[teams[inn_order[inns]]] + ".csv"
        
        print("Saving CSV to", fname)
        
        save_path = path.join(DIR, fname)
        data.to_csv(save_path, index = False)


scrape_game('19297', '1187672/new-zealand-vs-england-2nd-test-england-in-new-zealand-2019-20')