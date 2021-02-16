# over_changes.R
#
# Convert ball-by-ball data to over-by-over data, for modelling
# the decision making process behind bowler changes. Creating this
# data with the hope of a clear pattern emerging.
#

# Load libraries
pacman::p_load(tidyverse, textclean)

#process_match <- function(bbb, gameid)


# Load ball-by-ball data
bbb <- readRDS('bbb_cleaned.rds') %>% as_tibble() %>% #na.omit(game_id) %>%
  select(-c(spell_balls, spell_runs, spell_wkts, bat_team_total_runs, bat_team_total_wkts,
            bowl_team_total_runs, bowl_team_total_wkts, host_country, venue, toss_win,
            toss_elect, winner, margin, is_wkt, bat_win_toss, bat_home_away, dism_mode,
            pitch_factor, runs, extras)) %>%   # Remove unused columns 
  filter(!is.na(game_id)) # Remove rows without a game_id

# Output tibble
overs <- tibble()


# Process each match
for (id in unique(bbb$game_id)) {
  # Get all corresponding ball-by-ball entries
  bbb_filt <- bbb %>% filter(game_id == id)
  
  team1 <- as.character(bbb_filt$bat_team[1])
  team2 <- as.character(bbb_filt$bowl_team[1])
  
  # Format match date
  date <- format.Date(bbb_filt$start_date[1], format = "%e%b%Y")
  # Remove leading space if present
  if (substring(date, 1, 1) == " ") {
    date <- substring(date, 2)
  }
  
  
  # Load player stats
  filename <- paste("../data/players/players_",team1,team2,"_",date,".csv", sep= "")
  if (!file.exists(filename)) {
    # Swap teams around in filename
    filename <- gsub(team1, "!", filename)
    filename <- gsub(team2, team1, filename)
    filename <- gsub("!", team2, filename)
  }
  stats <- read_csv(filename)
  
  
  
}

