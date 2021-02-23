# followon_declaration.R
#
# Convert ball-by-ball data to follow-on and declaration data
#

# Load libraries
pacman::p_load(tidyverse, textclean)

# Load ball-by-ball data
bbb <- readRDS('bbb_cleaned.rds') %>% as_tibble() %>% #na.omit(game_id) %>%
  select(-c(spell_balls, spell_runs, spell_wkts, bat_team_total_runs, bat_team_total_wkts,
            bowl_team_total_runs, bowl_team_total_wkts, host_country, venue, toss_win,
            toss_elect, margin, is_wkt, bat_win_toss, bat_home_away, dism_mode,
            pitch_factor, runs, extras)) %>%   # Remove unused columns 
  filter(!is.na(game_id)) # Remove rows without a game_id

# Storage of data
declarations <- tibble(innings = integer(), match_balls = numeric(), lead = numeric(), wkts = factor())
followons <- tibble()

# Process each match
for (id in unique(bbb$game_id)) {
  bbb_filt <- bbb %>% filter(game_id == id) %>% arrange(match_balls)
  # Arrange ensures tibble is sorted by match_balls
  
  # Filter by each innings (except for last)
  for (inns in 1:3) {
  
    bbb_inns <- bbb_filt %>% filter(innings == as.character(inns)) 
    if (dim(bbb_inns)[1] == 0) {
      next
    }
    
    
    # Ignore if final innings of match and result was draw
    if ((inns == max(as.numeric(bbb_filt$innings))) & (bbb_inns$winner[1] == "draw")) {
      next
    }
    
    # Check for declarations
    last_ball <- bbb_inns %>% slice_tail(n = 1)
    if (last_ball$team_wkts != 9 | last_ball$outcome != "W") {
      # Declaration has occured - record the circumstances
      declarations <- declarations %>% 
        add_row(innings = inns, match_balls = last_ball$match_balls, lead = last_ball$team_lead, wkts = last_ball$team_wkts)
    }

  }  
}

