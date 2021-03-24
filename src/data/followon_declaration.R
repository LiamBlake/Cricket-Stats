# followon_declaration.R
#
# Convert ball-by-ball data to follow-on and declaration data
#

# Load libraries
pacman::p_load(tidyverse, textclean)

# Load ball-by-ball data
bbb <- readRDS('../rds/bbb_cleaned.rds') %>% as_tibble() %>% #na.omit(game_id) %>%
  select(-c(spell_balls, spell_runs, spell_wkts, bat_team_total_runs, bat_team_total_wkts,
            bowl_team_total_runs, bowl_team_total_wkts, host_country, venue, toss_win,
            toss_elect, margin, is_wkt, bat_win_toss, bat_home_away, dism_mode,
            pitch_factor, runs, extras)) %>%   # Remove unused columns 
  filter(!is.na(game_id)) # Remove rows without a game_id

# Storage of data
declarations <- tibble(innings = integer(), match_balls = numeric(), lead = numeric(), wkts = factor(), is_dec = factor(), bat_score = numeric(), outcome = factor(), game_id = numeric(), inns_balls = numeric())
followons <- tibble(match_balls = numeric(), last_score = numeric(), lead = numeric(), follow_on = factor())

dec_pred <- tibble(game_id = integer(), 
                   innings = integer(), 
                   start_lead = numeric(), 
                   dec_lead = numeric(), 
                   start_match_balls = numeric(),
                   dec_match_balls = numeric(),
                   spin_factor = numeric(),
                   seam_factor = numeric())
all_dec <- tibble(game_id = integer(),
                  innings = integer(),
                  lead = integer(),
                  match_balls = integer(),
                  inns_balls = integer(),
                  wkts = factor(),
                  outcome = factor(),
                  bat_score = integer(),
                  spin_factor = numeric(),
                  seam_factor = numeric(),
                  declared = integer())

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
    
    
    # Ignore if final innings of match 
    if ((inns == max(as.numeric(bbb_filt$innings)))) {
      next
    }
    
    # Check for declarations
    last_ball <- bbb_inns %>% slice_tail(n = 1)
    remain <- bbb_inns %>% slice_head(n = nrow(bbb_inns) - 1)
    declarations <- declarations %>% add_row(innings = inns, match_balls = remain$match_balls, lead = remain$team_lead, wkts = remain$team_wkts, bat_score = remain$bat_score, outcome = remain$outcome, game_id = remain$game_id, inns_balls = remain$inn_balls, is_dec = "no")
    
    if (last_ball$team_wkts != 9 | last_ball$outcome != "W") {
      # Declaration has occured - record the circumstances
      declarations <- declarations %>% head(-1) %>%  
        add_row(innings = inns, match_balls = last_ball$match_balls + 1, lead = last_ball$team_lead, wkts = last_ball$team_wkts, bat_score = last_ball$bat_score, outcome = last_ball$outcome, game_id = last_ball$game_id, inns_balls = last_ball$inn_balls, is_dec = "yes")
      
      
      # Predictive declaration
      first_ball <- remain %>% arrange(inn_balls) %>% head(1)
      dec_pred <- dec_pred %>% add_row(game_id = id, 
                                       innings = inns, 
                                       start_lead = first_ball$team_lead, 
                                       dec_lead = last_ball$team_lead, 
                                       start_match_balls = first_ball$match_balls,
                                       dec_match_balls = last_ball$match_balls,
                                       spin_factor = first_ball$spin_factor,
                                       seam_factor = first_ball$seam_factor)
      
      is_dec = 1
    } else {
      is_dec = 0
    }
    all_dec <- all_dec %>% add_row (game_id = id,
                      innings = inns,
                      lead = last_ball$team_lead,
                      match_balls = last_ball$match_balls,
                      inns_balls = last_ball$inn_balls,
                      wkts = last_ball$team_wkts,
                      outcome = last_ball$outcome,
                      bat_score = last_ball$bat_score,
                      spin_factor = last_ball$spin_factor,
                      seam_factor = last_ball$seam_factor,
                      declared = is_dec)
    
    # Follow-on
    if (inns == 2) {
      if (bbb_inns$bat_team[1] == (bbb_filt %>% filter(innings == "3"))$bat_team[1]) {
        fo <- "yes"
      }  else {
        fo <- "no"
      }
      
      followons <- followons %>% add_row(match_balls = last_ball$match_balls + 1, last_score = last_ball$team_score, lead = last_ball$team_lead, follow_on = fo)
      
      
    }

  }  
}

# Export
saveRDS(declarations, '../rds/declarations.rds')
saveRDS(followons, '../rds/follow_ons.rds')
saveRDS(dec_pred, '../rds/dec_pred.rds')
saveRDS(all_dec, '../rds/all_dec.rds')



