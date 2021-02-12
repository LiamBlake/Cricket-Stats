from pandas import DataFrame, Series, read_csv, isna
from yaml import safe_load
from os import path, fsencode, fsdecode, listdir

# Each value to be extracted for each delivery
DATA_COLS = ['Outcome', 'Dismissal', 'Innings', 'HostCountry', 'Venue', \
             'MatchBalls', 'InnBalls', 'BatTeam', 'TeamWkts', 'TeamScore', 'TeamLead', \
             'Batter', 'BatPosition', 'BatScore', 'BatBalls', 'BatAvg', 'CareerBalls', 'BatSR', 'BatArm', \
             'BowlTeam', \
             'Bowler', 'BowlBalls', 'BowlRuns', 'BowlWkts', 'CareerOvers' 'BowlAvg', 'BowlSR', 'BowlType', \
             'SpellBalls', 'SpellRuns', 'SpellWkts', \
             'TossWin', 'TossElect', 'BatTeamTotalRuns', 'BatTeamTotalWkts', 'BowlTeamTotalRuns', 'BowlTeamTotalWkts', \
             'Commentary']

COUNTRY_CODES = {'Afghanistan': 'AFG', \
                 'Australia': 'AUS', \
                 'Bangladesh': 'BAN', \
                 'England': 'ENG', \
                 'India': 'IND', \
                 'Ireland': 'IRE', \
                 'New Zealand': 'NZL', \
                 'Pakistan': 'PAK', \
                 'South Africa': 'RSA', \
                 'Sri Lanka': 'SRL', \
                 'West Indies': 'WIN', \
                 'Zimbabwe': 'ZIM', \
                 'United Arab Emirates': 'UAE', \
                 'ICC World XI': 'ICC'}

NUM_MONTHS = {'01': 'Jan', \
              '02': 'Feb', \
              '03': 'Mar', \
              '04': 'Apr', \
              '05': 'May', \
              '06': 'Jun', \
              '07': 'Jul', \
              '08': 'Aug', \
              '09': 'Sep', \
              '10': 'Oct', \
              '11': 'Nov', \
              '12': 'Dec'}    

DIR = path.dirname(path.realpath(__file__))

# Load match list
MATCHES = read_csv(DIR + "/match_list.csv")



def concat_bbb_stats(yaml_dir):

    # Parses a team score
    def team_score_to_nums(string):

        if string == '-':
            (runs, wkts, fo) = (0,0,0)

        else:
            fo = False
            if ('(f/o)' in string):
                # Follow-on innings
                fo = True
                string = string.split(" ")[0]

            split_str = string.split("/")
            if len(split_str) > 1:
                wkts = int(split_str[1][0])
            else:
                wkts = 10

            runs = int(split_str[0])



        return (runs, wkts, fo)


    # Load YAML file
    with open(yaml_dir, "r") as stream:
        data = safe_load(stream)

    # Match info
    info = data['info']
    #print(info)

    teams = info['teams']

    start_date = (info['dates'])[0]
    start_date = start_date.isoformat()
    start_date_list = start_date.split("-")
    date_format = start_date_list[2] + " " + NUM_MONTHS[start_date_list[1]] + " " + start_date_list[0]

    # Remove 0 from start of day if present
    if (date_format[0] == '0'):
        date_format = date_format[1:]


    home_team = COUNTRY_CODES[teams[0]]
    away_team = COUNTRY_CODES[teams[1]]

    # Search for corresponding team in match list
    possible_matches = MATCHES.loc[(MATCHES['Team1'].isin([home_team, away_team])) & (MATCHES['Team2'].isin([home_team, away_team])) & (MATCHES['StartDate'] == date_format)]
    
    # If no or multiple matches, raise exception
    if len(possible_matches.index) != 1:
        raise AttributeError("Unable to find unique match to %s in match_list.csv. Found %i corresponding matches." % (yaml_dir, len(possible_matches.index) ))

    match_detail = possible_matches.iloc[0,]
    
    # Find player statistics
    players_dir = DIR + "/players/players_" + match_detail['Team1'] + match_detail['Team2'] + "_" + date_format.replace(" ", "") + ".csv"
    try:
        players_pregame = read_csv(players_dir)
    except FileNotFoundError:
        raise AttributeError("Unable to find match to %s in players directory. Searched for %s." % (yaml_dir, players_dir))


    # Total no runs, wickets
    (team1_total_runs, team1_total_wkts, fo) = team_score_to_nums(match_detail['Score1'])
    (team2_total_runs, team2_total_wkts, fo) = team_score_to_nums(match_detail['Score2'])

    (temp3_runs, temp3_wkts, fo) = team_score_to_nums(match_detail['Score3'])
    (temp4_runs, temp4_wkts, fo) = team_score_to_nums(match_detail['Score4'])
    if fo:
        team2_total_runs += temp3_runs
        team2_total_wkts += temp3_wkts

        team1_total_runs += temp4_runs
        team1_total_wkts += temp4_wkts
    else:
        team1_total_runs += temp3_runs
        team1_total_wkts += temp3_wkts

        team2_total_runs += temp4_runs
        team2_total_wkts += temp4_wkts


    # List of delivery detail
    output = []

    match_balls = 0
    lead = 0
    last_team = ""

    batters = {}
    bowlers = {}

    BROKEN_NAMES = ["Sarfraz Ahmed", "Imran Khan (2)", "Mehedi Hasan Miraz", "Nazmul Hossain Shanto", "Tanvir Ahmed (1)", "Suhrawadi Shuvo"]
    CORRECT_NAMES = [("Sarfaraz", "Ahmed"), ("Imran", "Khan"), ("Mehidy", "Hasan Miraz"), ("Najmul", "Hossain Shanto"), ("Tanvir", "Ahmed"), ("Sohrawordi", "Shuvo")]


    # Each innings
    for (num, inns) in enumerate(data['innings']):
        inns_dict = inns[list(inns.keys())[0]]

        bat_team = COUNTRY_CODES[inns_dict['team']]
        if (bat_team != last_team):
            lead = -lead

        last_team = bat_team

        bowl_team = COUNTRY_CODES[teams[1] if (bat_team == teams[0]) else teams[0]]
        

        # Reset score trackers
        score = 0
        wkts = 0
        balls = 0
        
        # Reset stats trackers
#        for key in batters.keys():
#            batters[key][1:2] = [0]*2

#        for key in bowlers.keys():
#            bowlers[key][1:3] = [0]*3
#            bowlers[key][8:] = [0]*3

        batters = {}
        bowlers = {}

        pos = 1

        for deliv_dict in inns_dict['deliveries']:
            row = {'Innings': num + 1, 'MatchBalls': match_balls, "InnBalls": balls, 'BatTeam': bat_team, 'TeamWkts': wkts, 'TeamScore': score, 'TeamLead': lead, 'BowlTeam':
bowl_team}
            deliv = list(deliv_dict.keys())[0]
            deliv_info = deliv_dict[deliv]

            batter = deliv_info['batsman']
            bowler = deliv_info['bowler']

            if batter not in batters.keys():
                # New batter to crease

                # Find in pregame stats
      

                try:
                    batter_pregame = players_pregame.loc[(players_pregame['Initials'] == batter.split(" ")[0]) & (players_pregame['Surname'] == " ".join(batter.split(" ")[1:]))].iloc[0,]
                except IndexError:

                    try:
                        # Known issues with names
                        if batter in BROKEN_NAMES:
                            ind = BROKEN_NAMES.index(batter)
                            batter_pregame = players_pregame.loc[(players_pregame['Initials'] == CORRECT_NAMES[ind][0]) & (players_pregame['Surname'] == CORRECT_NAMES[ind][1])].iloc[0,]

                        else:
                            # Deal with players such as Misbah-ul-Haq lacking a surname in the .csv
                            batter_pregame = players_pregame.loc[(players_pregame['Initials'] == batter.split(" ")[0]) & (isna(players_pregame['Surname']))].iloc[0,]

                    except IndexError:
                        print(players_pregame)
                        print(batter) 
                        raise IndexError()


                batters.update({batter: [pos, 0, 0, batter_pregame['BatAvg'], batter_pregame['BallsFaced'], batter_pregame['BatSR'], batter_pregame['BatArm']]})
                pos = pos + 1


            if bowler not in bowlers.keys():
                 # New bowler
                # Find in pregame stats
                try:
                    bowler_pregame = players_pregame.loc[(players_pregame['Initials'] == bowler.split(" ")[0]) & (players_pregame['Surname'] == " ".join(bowler.split(" ")[1:]))].iloc[0,]
                except IndexError:

                    try:
                        # Known issues with names
                        if bowler in BROKEN_NAMES:
                            ind = BROKEN_NAMES.index(batter)
                            bowler_pregame = players_pregame.loc[(players_pregame['Initials'] == CORRECT_NAMES[ind][0]) & (players_pregame['Surname'] == CORRECT_NAMES[ind][1])].iloc[0,]

                        else:
                            # Deal with players such as Misbah-ul-Haq lacking a surname in the .csv
                            bowler_pregame = players_pregame.loc[(players_pregame['Initials'] == bowler.split(" ")[0]) & (isna(bowler_pregame['Surname']))].iloc[0,]
                    except IndexError:
                        print(players_pregame)
                        print(bowler) 
                        raise IndexError("")

                bowlers.update({bowler: [0, 0, 0, bowler_pregame['OversBowled'], bowler_pregame['BowlAvg'], bowler_pregame['BowlSR'], bowler_pregame['BowlType'], 0, 0, 0]})

            # Batter, bowler prior to delivery
            row['Batter'] = batter
            row['Bowler'] = bowler
            for (i,x) in enumerate(['BatPosition', 'BatScore', 'BatBalls', 'BatAvg', 'CareerBalls', 'BatSR', 'BatArm']):
                row[x] = batters[batter][i]

            for (i,x) in enumerate(['BowlBalls', 'BowlRuns', 'BowlWkts', 'CareerOvers', 'BowlAvg', 'BowlSR', 'BowlType', 'SpellBalls', 'SpellRuns', 'SpellWkts']):
                row[x] = bowlers[bowler][i]

            # Parse delivery
            outcome = ""
            runs_dict = deliv_info['runs']
            #print(runs_dict)

            score += runs_dict['total']
            lead += runs_dict['total']

            batters[batter][1] += runs_dict['batsman']
            batters[batter][2] += 1

            # Check for wicket
            if 'wicket' in deliv_info.keys():
                wktdetail = deliv_info['wicket']

                howout = wktdetail['kind']
                wkts += 1

                outcome = 'W' + '_' + howout

                if howout != "runout":
                    bowlers[bowler][2] += 1
                    bowlers[bowler][9] += 1

            # Check for extras
            elif 'extras' in deliv_info.keys():
                extras_dict = deliv_info['extras']
                
                # No ball
                if 'noballs' in extras_dict.keys():
                    bowlers[bowler][1] += extras_dict['noballs']
                    bowlers[bowler][8] += extras_dict['noballs']
                    outcome = str(extras_dict['noballs']) + 'nb'

                # Wides
                if 'wides' in extras_dict.keys():
                    bowlers[bowler][1] += extras_dict['wides']
                    bowlers[bowler][8] += extras_dict['wides']
                    outcome = str(extras_dict['wides']) + 'wd'

                    batters[batter][2] -= 1

                # Byes
                if 'byes' in extras_dict.keys(): 
                    outcome = str(extras_dict['byes']) + 'b'

                # Legbyes
                if 'legbyes' in extras_dict.keys(): 
                    outcome = str(extras_dict['legbyes']) + 'lb'

            else:
                bowlers[bowler][1] += runs_dict['total']
                bowlers[bowler][8] += runs_dict['total']
                outcome = runs_dict['total']

            row['Outcome'] = outcome

            # Team totals
            row['BatTeamTotalRuns'], row['BatTeamTotalWkts'], row['BowlTeamTotalRuns'], row['BowlTeamTotalWkts'] = (team1_total_runs, team1_total_wkts, team2_total_runs, team2_total_wkts) if (bat_team == match_detail['Team1']) else (team2_total_runs, team2_total_wkts, team1_total_runs, team1_total_wkts)

            bowlers[bowler][0] += 1
            bowlers[bowler][7] += 1

            balls += 1
            match_balls += 1

            output.append(row)

            


    # Convert list of dictionaries to dataframe
    ret_df = DataFrame(data = output)            


    # Fill in match information
    ret_df['StartDate'] = start_date
    ret_df['HostCountry'] = home_team 
    ret_df['Venue'] = match_detail['Venue']
    ret_df['TossWin'] = COUNTRY_CODES[info['toss']['winner']]
    ret_df['TossElect'] = info['toss']['decision']
    
    ret_df['Winner'] = match_detail['Winner']
    ret_df['Margin'] = match_detail['Margin']

    return ret_df










# Create output .csv file
output_dir = DIR + '/bbb_full.csv'

# Loop through each file in ballbyball directory
bbb_dir = fsencode(DIR + "/ballbyball")
first_entry = True

for (id, file) in enumerate(listdir(bbb_dir)):
    name = fsdecode(file)
    print('Parsing ' + name + '...')

    try:
        dat = concat_bbb_stats(DIR + "/ballbyball/" + name)
        print('Appending to ' + output_dir + '...')
        # Add unique match id
        dat['GameID'] = id + 1
        dat.to_csv(output_dir, mode='a', header=first_entry, index = False)
        first_entry = False

        print('Success!')

    except Exception as e:
        #print(e)
        continue

print('Completed parsing of ball-by-ball data.')
