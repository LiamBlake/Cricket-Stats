# bbb_to_batterbowler.R
#
#

pacman::p_load(tidyverse, foreach, doParallel)

#setup parallel backend to use many processors
cores=detectCores()
cl <- makeCluster(cores[1]-1) #not to overload your computer
registerDoParallel(cl)


# Load cleaned data, select relevant columns
bbb <- readRDS("bbb_cleaned.RDS") %>% select(-c(bowl_team, spell_balls, 
                                                spell_runs, spell_wkts,
                                                bat_team_total_runs, 
                                                bat_team_total_wkts, 
                                                bowl_team_total_runs, 
                                                bowl_team_total_wkts,
                                                start_date, venue,
                                                toss_win, toss_elect,
                                                winner, margin,
                                                bat_home_away, pitch_factor,
                                                dism_mode, runs, extras, is_wkt))


# For each match, each innings
# In parallel
invisible(foreach(id = unique(bbb$game_id), .packages=c("tidyverse")) %dopar% {
  for (inns in 1:4) {
    bbb_filt <- bbb %>% filter(game_id == id & innings == inns)
    
    # EMpty case
    if (nrow(bbb_filt) == 0) next
    
    # Get all unique bowler-batter pairs
    pairs <- bbb_filt %>% select(batter, bowler) %>% distinct()
    for (pair_id in 1:nrow(pairs)) {
      pbat <- pairs[pair_id, "batter"] %>% pull(batter)
      pbowl <- pairs[pair_id, "bowler"] %>% pull(bowler)
      # Create a sequence object for each pair
      bbb_pair_only <- bbb_filt %>% filter(batter == pbat & bowler == pbowl) %>%
        select(-c(game_id))
      
      # Output to .csv file
      bbb_pair_only %>% write_csv(paste("../data/batter_bowler_sequences/", paste(as.character(id), as.character(inns), pbat, pbowl, sep = "-"), ".csv", sep = ""))
      
    }
    
  }
  
})


stopCluster(cl)