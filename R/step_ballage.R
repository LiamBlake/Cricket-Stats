step_ballage_new <- 
  function(terms, role, trained, ref_dist, options, skip, id) {
    step(
      subclass = "ballage", 
      terms = terms,
      role = role,
      trained = trained,
      ref_dist = ref_dist,
      options = options,
      skip = skip,
      id = id
    )
  }


step_ballage <- function(
  recipe, 
  ..., 
  role = NA, 
  trained = FALSE, 
  ref_dist = NULL,
  options = list(newball_ovs = 80, names = TRUE),
  skip = FALSE,
  id = rand_id("ball_age")
) {
  
 
  terms <- ellipse_check(...) 
  
  add_step(
    recipe, 
    step_percentile_new(
      terms = terms, 
      trained = trained,
      role = role, 
      ref_dist = ref_dist,
      options = options,
      skip = skip,
      id = id
    )
  )
}

prep.step_percentile <- function(x, training, info = NULL, ...) {
  col_names <- terms_select(terms = x$terms, info = info) 
  # TODO finish the rest of the function
}