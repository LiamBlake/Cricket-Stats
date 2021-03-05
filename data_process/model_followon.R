#
# model_followon.R
#


# Load packages and data
pacman::p_load(tidyverse, tidymodels, vip, tidyroc)
fo <- readRDS("follow_ons.rds") %>% mutate_at(c("follow_on"), as.factor) %>% filter(lead <= -200)


models <- data.frame()

# First model - decision tree
# Set up workflow
wf_tree <- workflow() %>%
                      add_recipe(
                        recipe(follow_on ~ lead + match_balls + last_score, data = fo)
                      ) %>%
                      add_model(
                        decision_tree(mode = 'classification', tree_depth = tune()) %>%
                          set_engine('rpart'))


# Tune tree depth
set.seed(24022021)
tune_tree <- tune_grid(
  wf_tree,
  resamples = vfold_cv(fo),
  grid = grid_regular(tree_depth(), levels = 15)
)

tune_tree %>% collect_metrics()
show_best(tune_tree, metric = "accuracy", n = 10)
(M1 <- select_best(tune_tree, metric = 'accuracy'))

final_tree <- wf_tree %>% finalize_workflow(M1) %>% fit(data = fo)
final_fit <- final_tree %>% pull_workflow_fit()



# Second model - logistic regression
logis_fit <- logistic_reg() %>% set_engine("glm") %>% fit(follow_on ~ ., data = fo) 

tmp <- fo %>% add_column(logis_fit %>% predict(new_data = fo)) 
tmp %>% make_roc(predictor = tmp$.pred_class, known_class = follow_on)


models <- rbind(models, data.frame())
