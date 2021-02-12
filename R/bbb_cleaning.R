pacman::p_load(tidyverse, tidymodels, janitor)


# Save as .csv
save_to_csv <- function(obj, filename) {
  # Save labels
  obj %>% select(starts_with("outcome")) %>% write.csv(paste(filename, '_labs.csv', sep = ""), row.names = FALSE)
  
  # Save predictors
  obj %>% select(!starts_with("outcome")) %>% write.csv(paste(filename, '_preds.csv', sep = ""), row.names = FALSE)
}


prep_data <- function(df, filename, no_outs, add_class = "") {
  # Split into training, testing
  df_split <- initial_split(df, strata = outcome)
  df_train <- training(df_split)
  df_test <- testing(df_split)
  
  # Encode categorical variables
  rc <- recipe(outcome ~ ., data = df_train) %>% 
    step_naomit(outcome) %>%
    step_dummy(all_nominal(), one_hot = TRUE) %>% 
    step_meanimpute(all_numeric()) %>%
    step_range(c(seam_factor,spin_factor))  # Normalise pitch factors to be between 0 and 1
  
  prc <- rc %>% prep(data = df_train) 
  df_train <- prc %>% juice()
  df_test <- prc %>% bake(df_test)
  
  # Account for reference category
  #if (no_outs > 2) {
  #  df_train <- df_train %>% add_column(nc = as.integer(!rowSums((df_train %>% select(starts_with("outcome")))[1:(no_outs - 1)])))
  #  ncn <- paste("outcome_X", add_class, sep = "") 
  #  df_train <- rename(df_train, !!ncn := nc)
    
  #  df_test <- df_test %>% add_column(nc = as.integer(!rowSums((df_test %>% select(starts_with("outcome")))[1:(no_outs - 1)])))
  #  ncn <- paste("outcome_X", add_class, sep = "") 
  #  df_test <- rename(df_test, !!ncn := nc)
  #}
  
  
  
  # Export to .csv
  save_to_csv(df_train, paste("data/", filename, "_train", sep = ""))
  save_to_csv(df_test, paste("data/", filename, "_test", sep = ""))
}

# Load raw data
bbb <- read_csv('../../../bbb_full.csv', na = c("", "-")) %>% as_tibble()
bbb <- bbb %>% clean_names()

# Factors
bbb <- bbb %>% mutate_at(c("innings", "bat_position", "team_wkts", "bowl_wkts"), as.factor) %>% mutate_if(is.character, as.factor)

# Convert career overs to balls
bbb <- bbb %>% mutate(career_overs = 5*floor(career_overs) + career_overs) %>%
  rename(career_bat_balls = career_balls, career_bowl_balls = career_overs)

# Create simpler factor columns
bbb <- bbb %>% mutate(is_wkt = as.factor(ifelse(grepl('^W_', outcome), "W", "no"))) %>% 
  mutate(bowl_class = as.factor(ifelse(bowl_type %in% c("lc", "lo", "rls", "rob"), "spin", "seam"))) %>% 
  mutate(bat_win_toss = as.factor(ifelse(bat_team == toss_win, "yes", "no"))) %>%
  mutate(bat_home_away = as.factor(ifelse(bat_team == host_country, "home", "away"))) %>%
  mutate(dism_mode = as.factor(ifelse(is_wkt == "W", substring(outcome, 3), NA)))

# Pitch factors
g_wkts_sum <- bbb %>% group_by(game_id) %>% 
  filter(is_wkt == "W") %>% 
  tally(bowl_class == "seam") %>%
  add_column(spin_wkts = (
    bbb %>% group_by(game_id) %>% filter(is_wkt == "W" ) %>% tally(bowl_class == "spin")
  )[,2]) %>%
  add_column(total_wkts = (
    bbb %>% group_by(game_id) %>% summarise(mean(bat_team_total_wkts + bowl_team_total_wkts))
  )[,2]) %>%
  rename(seam_wkts = n)

bbb <- bbb %>% group_by(game_id) %>% mutate(gws_ind = which(g_wkts_sum[,1] == game_id)) %>% ungroup() %>%
  mutate(pitch_factor = (bat_team_total_runs + bowl_team_total_runs)/(bat_team_total_wkts + bowl_team_total_wkts)) %>%
  mutate(seam_factor = unlist(pitch_factor*g_wkts_sum[gws_ind,2]/g_wkts_sum[gws_ind,4], use.name = FALSE)) %>%
  mutate(spin_factor = unlist(pitch_factor*g_wkts_sum[gws_ind,3]/g_wkts_sum[gws_ind,4], use.name = FALSE)) %>%
  select(-gws_ind)
  
# Remove unwanted factors
bbb <- bbb %>%
  mutate(outcome = as.factor(case_when(
    str_detect(outcome, "W_") ~ "W", 
    TRUE ~ as.character(outcome))))

# Remove outcomes which occur too infrequently
bbb$outcome <- fct_lump_min(bbb$outcome, 15)
bbb <- bbb[bbb$outcome != "Other",]
bbb$outcome <- droplevels(bbb$outcome)

# Add extras column
bbb <- bbb %>% mutate(runs = as.factor(case_when(
  str_detect(outcome, "W") ~ 0, 
  TRUE ~ as.double(substring(outcome, 1, 1))
))) %>% 
  mutate(extras = as.factor(case_when(
    nchar(as.character(outcome)) > 1 ~ substring(outcome, 2),
    TRUE ~ "off_bat"
  )))

# Output for EDA
saveRDS(bbb, "bbb_cleaned.RDS")

# Remove unusued columns
bbb <- bbb %>% select(-c(bat_team, bowl_team, batter, bowler, toss_win, venue, winner, margin, start_date, spell_balls, spell_runs, spell_wkts, toss_win, toss_elect, game_id, bowl_class, pitch_factor, bat_team_total_runs, bat_team_total_wkts, bowl_team_total_runs, bowl_team_total_wkts))

# Shuffle rows
set.seed(8112020)
bbb <- sample_frac(bbb, 1L)

# Save full data
#prep_data(bbb %>% select(-c(is_wkt, dism_mode, extras, run)), "bbb_full", 22, "0")

# Wicket data
set.seed(1153)
bbb %>% sample_frac(0.9) %>% select(-c(outcome, dism_mode, extras, runs)) %>%
  rename(outcome = is_wkt) %>%
  na.omit(outcome) %>%
  prep_data("is_wkt", 2)


# Dismissal data
bbb %>% filter(outcome == "W") %>%
  select(-c(outcome, is_wkt, extras, runs)) %>%
  rename(outcome = dism_mode) %>%
  na.omit(outcome) %>%
  prep_data("dism_mode", 8, "bowled")


# Ball outcome data
set.seed(1153)
bbb %>% sample_frac(0.9) %>% filter(outcome != "W") %>% 
  select(-c(outcome, is_wkt, dism_mode, runs)) %>%
  rename(outcome = extras) %>%
  na.omit(outcome) %>%
  prep_data("outcome", 5, "b")

# Runs scored for each ball outcome
set.seed(1153)
bbb %>% sample_frac(0.9) %>% filter(outcome != "W" & extras == "off_bat") %>% 
  select(-c(outcome, is_wkt, dism_mode, extras)) %>%
  rename(outcome = runs) %>%
  na.omit(outcome) %>%
  prep_data("runs", 1)

bbb %>% filter(extras == "b") %>% 
  select(-c(outcome, is_wkt, dism_mode, extras)) %>%
  rename(outcome = runs) %>%
  na.omit(outcome) %>%
  prep_data("byes", 1)

bbb %>% filter(extras == "lb") %>% 
  select(-c(outcome, is_wkt, dism_mode, extras)) %>%
  rename(outcome = runs) %>%
  na.omit(outcome) %>%
  prep_data("legbyes", 1)

bbb %>% filter(extras == "nb") %>% 
  select(-c(outcome, is_wkt, dism_mode, extras)) %>%
  rename(outcome = runs) %>%
  na.omit(outcome) %>%
  prep_data("noballs", 1)

bbb %>% filter(extras == "wd") %>% 
  select(-c(outcome, is_wkt, dism_mode, extras)) %>%
  rename(outcome = runs) %>%
  na.omit(outcome) %>%
  prep_data("wides", 1)