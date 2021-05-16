#' Calculate the pitch quality index from adequete ball-by-ball data.
#'
#' @param bbb Ball-by-ball information for the match in question, as a dplyr tibble.
#'
#' @return The pitch quality index, as a single value.
#'
#' @examples
pitch_qi <- function(bbb, key) {
  # Get RpW and compare to average
  total_runs <- bbb[1,"bat_team_total_runs"] + bbb[1,"bowl_team_total_runs"]
  total_wkts <- bbb[1,"bat_team_total_wkts"] + bbb[1,"bowl_team_total_wkts"]
  r_RpW <- (total_runs / total_wkts) / 30.0  # 30 is the rounded RpW for all test matches
  r_RpW <- r_RpW$bat_team_total_runs
    
  # Identify each batter, no. times batted and expected score
  exp_runs <- bbb %>% group_by(batter, innings) %>% 
    summarise(bat_avg = dplyr::first(bat_avg)) %>%
    select(bat_avg)
  exp_runs <- colSums(exp_runs[,2])
  # TODO: Properly handle not outs
  out <- tryCatch({
    r_runs <- total_runs / exp_runs
    r_runs <- r_runs$bat_team_total_runs
    if (r_runs > 3) {
      r_runs <- 3   # Forced maximum of 3
    }
    
    # Calculate expected wickets for balls bowled
    exp_wkts <- bbb %>% group_by(bowler) %>% 
      summarize(n = n(), sr = dplyr::first(bowl_sr)) %>%
      mutate(exp_wkts <- ifelse(is.na(sr), 0, n / sr))
    # TODO: Implement better handling of missing data (i.e. na sr because no career wickets)
    exp_wkts <- colSums(exp_wkts[,4])
    
    r_wkts <- exp_wkts / total_wkts
    r_wkts <- r_wkts$bat_team_total_wkts
    if (r_wkts > 3) {
      r_wkts <- 3   # Forced maximum of 3
    }
    
    # Calculate and map to 0-100 linear map
    pqi <- r_RpW + r_runs + r_wkts
    if (pqi <= 3.0) {
      # Map to range 0-50
      pqi <- 50 * pqi / 3.0
    } else {
      # Map to range 50-100
      pqi <- 50 * (pqi - 3) / 6.0 + 50
    }
    
  
  pqi
}, error=function(cond){NA})
  
  return(out)
  
  
}