#' Calculate the pitch quality index from adequete ball-by-ball data.
#'
#' @param bbb Ball-by-ball information for the match in question, as a dplyr tibble.
#'
#' @return The pitch quality index, as a single value.
#'
#' @examples
pitch_qi <- function(bbb, key) {
  # Get RpW and compare to average
  totals <- bbb %>% summarise(runs = sum(as.numeric(levels(runs)[runs])), wkts = sum(is_wkt == "W"))
  r_RpW <- (totals$runs / totals$wkts) / 30.0 # 30 is the rounded RpW for all test matches

  # Identify each batter, no. times batted and expected score
  exp_runs <- bbb %>%
    group_by(batter, innings) %>%
    summarise(bat_avg = dplyr::first(bat_avg)) %>%
    mutate(bat_avg = ifelse(is.na(bat_avg), 30, bat_avg)) %>%
    select(bat_avg)
  exp_runs <- colSums(exp_runs[, 2])
  # TODO: Properly handle not outs

  r_runs <- totals$runs / exp_runs
  if (r_runs > 3) {
    r_runs <- 3 # Forced maximum of 3
  }

  # Calculate expected wickets for balls bowled
  exp_wkts <- bbb %>%
    group_by(bowler) %>%
    summarize(n = n(), sr = dplyr::first(bowl_sr)) %>%
    mutate(exp_wkts <- ifelse(is.na(sr), 1e4, n / sr))
  # TODO: Implement better handling of missing data (i.e. NA sr because no career wickets)
  exp_wkts <- colSums(exp_wkts[, 4])

  r_wkts <- totals$wkts / exp_wkts
  if (r_wkts > 3) {
    r_wkts <- 3 # Forced maximum of 3
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


  return(pqi)
}


"%!in%" <- function(x, y) !("%in%"(x, y))

pqi_on_all <- function(bbb) {
  gb <- bbb %>% group_by(game_id)

  pqis <- suppressMessages(gb %>% group_map(pitch_qi))

  pqis <- tibble(game_id = 1:length(pqis), pqi = pqis) %>% unnest(pqi)

  # Join to original df and return
  unique_gameids <- unique(bbb$game_id)
  return(bbb %>% left_join(pqis, by = "game_id"))
}
