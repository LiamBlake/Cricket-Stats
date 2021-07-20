pacman::p_load(tidyverse, tidymodels, janitor)

source("src/R/pitch_qi.R")

# Load raw data
bbb <- rbind(
  read_csv("data/raw/bbb_full1.csv", na = c("", "-")) %>% as_tibble(), 
  read_csv("data/raw/bbb_full2.csv", na = c("", "-")) %>% as_tibble()
)
bbb <- bbb %>% clean_names()

# Factors
bbb <- bbb %>%
  mutate_at(c("innings", "bat_position", "team_wkts", "bowl_wkts"), as.factor) %>%
  mutate_if(is.character, as.factor)

# Convert career overs to balls
bbb <- bbb %>%
  mutate(career_overs = 5 * floor(career_overs) + career_overs) %>%
  rename(career_bat_balls = career_balls, career_bowl_balls = career_overs)

# Create simpler factor columns
bbb <- bbb %>%
  mutate(is_wkt = as.factor(ifelse(grepl("^W_", outcome), "W", "no"))) %>%
  mutate(bowl_class = as.factor(ifelse(bowl_type %in% c("lc", "lo", "rls", "rob"), "spin", "seam"))) %>%
  mutate(bat_win_toss = as.factor(ifelse(bat_team == toss_win, "yes", "no"))) %>%
  mutate(bat_home_away = as.factor(ifelse(bat_team == host_country, "home", "away")))

# Remove unwanted factors
bbb <- bbb %>%
  mutate(outcome = as.factor(case_when(
    str_detect(outcome, "W_") ~ "W",
    TRUE ~ as.character(outcome)
  )))

# Merge med bowling types
bbb <- bbb %>% mutate(
  bowl_type = fct_recode(bowl_type, m = "rm", m = "lm")
)

# Collapse opening position into 1
bbb <- bbb %>% mutate(bat_position = fct_collapse(bat_position, open = c("1", "2")))

# Remove outcomes which occur too infrequently
bbb$outcome <- fct_lump_min(bbb$outcome, 15)
bbb <- bbb[bbb$outcome != "Other", ]
bbb$outcome <- droplevels(bbb$outcome)

# Add extras column
bbb <- bbb %>%
  mutate(runs = as.factor(case_when(
    str_detect(outcome, "W") ~ 0,
    TRUE ~ as.double(substring(outcome, 1, 1))
  ))) %>%
  mutate(extras = as.factor(case_when(
    nchar(as.character(outcome)) > 1 ~ substring(outcome, 2),
    TRUE ~ "off_bat"
  )))


# Pitch factors
bbb <- pqi_on_all(bbb %>% na.omit()) %>% rename(game_id = game_id.y)

# Export as RDS object
saveRDS(bbb, "bbb_cleaned.RDS")
