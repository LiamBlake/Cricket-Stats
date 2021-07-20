# Convert ball-by-ball data to over-by-over data, for modelling
# the decision making process behind bowler changes. Creating this
# data with the hope of a clear pattern emerging.
#

# Load packages
pacman::p_load(tidyverse)

# Load raw bbb data and remove unused columns
bbb <- readRDS("../../data/processed/bbb_cleaned.RDS") %>%
  select(-c(bat_team, bowl_team, batter, bat_position, career_bat_balls,
            spell_balls, spell_runs, spell_wkts, career_bowl_balls, outcome, 
            bat_avg, bat_balls, bat_sr, bat_team_total_runs, bat_team_total_wkts,
            bowl_team_total_runs, bowl_team_total_wkts, start_date, host_country,
            venue, toss_win, toss_elect, winner, margin, is_wkt, bowl_class, 
            bat_win_toss, bat_home_away, dism_mode, pitch_factor, runs, extras)) %>%
  mutate(s = seam_factor + spin_factor) %>% mutate(seam_factor = seam_factor/s,
                                                   spin_factor = spin_factor/s) %>%
  select(-s)


colnames <- colnames(bbb)
output <- c(colnames, paste("old_", colnames, sep = "")) %>% purrr::map_dfc(setNames, object = list(numeric())) %>%
  select(-c(old_innings, old_match_balls, old_inn_balls, old_team_wkts,
            old_team_score, old_team_lead, old_bat_score, old_bat_arm, 
            old_game_id, old_seam_factor, old_spin_factor)) %>%
  mutate_at(c("innings", "team_wkts", "bowler", "old_bowler", "bat_arm", 
              "bowl_wkts", "old_bowl_wkts", "bowl_type", "old_bowl_type"), as.factor)

# Iterate through each match and get bowler changes
for (id in unique(bbb$game_id)) {
  bbb_filt <- bbb %>% filter(game_id == id) %>% arrange(match_balls)
  # Arrange ensures tibble is sorted by match_balls
  
  # Filter by each innings (except for last)
  for (inns in 1:3) {
    
    bbb_inns <- bbb_filt %>% filter(innings == as.character(inns)) 
    if (dim(bbb_inns)[1] == 0) {
      next
    }
    
    last_bowl <- bbb_inns[1, "bowler"]
    lasti <- 1
    # Iterate through each delivery and extract bowler changes
    for (i in 7:(nrow(bbb_inns)-1)) {
      curr_bowl <- bbb_inns[i, "bowler"]
      new_bowl <- bbb_inns[i+1, "bowler"]
      

      if (new_bowl != curr_bowl) {    
        # New bowler into attack
        if (new_bowl != last_bowl) {
          output <- output %>% add_row(bbb_inns[i+1,], old_bowler = last_bowl %>% pull("bowler"), 
                                       old_bowl_balls = bbb_inns[lasti, "bowl_balls"] %>% pull("bowl_balls"),
                                       old_bowl_runs = bbb_inns[lasti, "bowl_runs"] %>% pull("bowl_runs"),
                                       old_bowl_wkts = bbb_inns[lasti, "bowl_wkts"] %>% pull("bowl_wkts"),
                                       old_bowl_avg = bbb_inns[lasti, "bowl_avg"] %>% pull("bowl_avg"),
                                       old_bowl_sr = bbb_inns[lasti, "bowl_sr"] %>% pull("bowl_sr"),
                                       old_bowl_type = bbb_inns[lasti, "bowl_type"] %>% pull("bowl_type"),
                                       )
        }
        last_bowl <- curr_bowl
        lasti <- i
      }
      
    }
    
    
  }

}


# Save data
saveRDS(output,"../../data/processed/bowler_changes.rds")
