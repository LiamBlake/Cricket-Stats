pacman::p_load(tidyverse, tidymodels, vip, survival, ggfortify, poissonreg)
source("../pitch_qi.R")

bbb <- readRDS("../../data/processed/bbb_cleaned.RDS") %>%
  mutate_if(is.character, as.factor) %>%
  mutate_at(c("innings", "bat_position"), as.factor)

# Use better pitch factors:
bbb <- pqi_on_all(bbb) %>% 
  select(-c(bat_team_total_runs, 
            bat_team_total_wkts, bowl_team_total_runs, bowl_team_total_wkts,
            host_country, venue, winner, margin, outcome, toss_win, toss_elect,
            batter, bowler, dism_mode, bat_win_toss, 
            bat_home_away, bat_team, bowl_team, runs, extras, spell_balls,
            spell_runs, spell_wkts, pitch_factor, start_date, game_id, bowl_class, spin_factor, seam_factor)) %>%
  na.omit()

# Save
bbb %>% write_csv("../../data/processed/bbb_cleaned.csv")
