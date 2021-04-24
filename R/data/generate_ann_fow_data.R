

pacman::p_load(tidyverse, tidymodels)

bbb <- readRDS("../../data/processed/bbb_cleaned.RDS") %>% 
  select(-c(bat_team_total_runs, 
            bat_team_total_wkts, bowl_team_total_runs, bowl_team_total_wkts,
            host_country, venue, winner, margin, outcome, toss_win, toss_elect,
            batter, bowler, dism_mode, bat_win_toss, 
            bat_home_away, bat_team, bowl_team, runs, extras, spell_balls,
            spell_runs, spell_wkts, pitch_factor, start_date)) %>%
  mutate_if(is.character, as.factor) %>%
  mutate_at(c("innings", "bat_position"), as.factor)

# Normalise pitch factors
bbb <- bbb %>% mutate(rsum = seam_factor + spin_factor) %>% mutate(seam_factor = seam_factor/rsum) %>%
  mutate(spin_factor = spin_factor/rsum) %>% select(-rsum)

# Create artificial split at each new ball
bbb <- bbb %>% mutate(ball_age <- inn_balls %% 480)

# Create recipe specification (I love this package)
prepped <- recipe(is_wkt ~ ., data = bbb) %>%
  step_naomit(everything()) %>%
  step_rm(team_score, game_id, bowl_class, seam_factor) %>%
  step_range(all_numeric()) %>%
  step_dummy(all_nominal()) %>%
  prep(data = bbb) %>%
  juice()

# Save as .csv
prepped %>% select(-starts_with("is_wkt")) %>% write_csv("../../ann/data/fow_ann_X.csv")
prepped %>% select(is_wkt_W) %>% write_csv("../../ann/data/fow_ann_Y.csv")

