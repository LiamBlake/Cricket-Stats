
# Libraries
pacman::p_load(tidymodels, visNetwork, sparkline, vip)

# Load data
dec <- readRDS("../data/rds/declarations.rds") %>% mutate(is_dec = as.factor(is_dec), innings = as.factor(innings))

# Ignore impossible declarations
dec <- dec %>% filter(!(lead <= -200 & innings == 2) & !(lead < 0 & innings == 3))

# Convert outcome to wicket or runs
dec <- dec %>% mutate(outcome = as.character(outcome)) %>%
  mutate(outcome = substr(outcome, 1,1)) %>% 
  mutate(outcome = as.factor(outcome))
dec$outcome <- droplevels(dec$outcome)
dec <- dec %>% add_column(is_wkt = as.factor(ifelse(grepl('^W', dec$outcome), "W", "no")))
dec <- dec %>% mutate(bat_score =  ifelse(outcome == "W", bat_score, bat_score + as.numeric(as.character(outcome))))


# Split into training, testing
split <- initial_split(dec, strata = is_dec)
train <- training(split)
test <- testing(split)

# Create a balanced dataset
train_bal <- bind_rows(train %>% filter(is_dec == "yes"), sample_n(train %>% filter(is_dec == "no"), size = 5*nrow(train %>% filter(is_dec == "yes"))))



balanced <- function(df, cond, factor = 1) {
  return()
}


# Decision tree
wf_tree <- workflow() %>% 
  add_recipe(
    recipe(is_dec ~ innings + match_balls + lead + bat_score + is_wkt, data = train_bal)
    ) %>%
  add_model(
    decision_tree(mode = "classification", tree_depth = tune(), min_n = 5) %>% 
      set_engine("rpart"))

tune_grid <- grid_regular(tree_depth(), levels = 30)
dec_folds <- vfold_cv(train_bal)

# Tune tree depth
tree_res <- wf_tree %>% 
  tune_grid(
    resamples = dec_folds,
    grid = tune_grid
  )

tree_res %>% collect_metrics()


final_tree <- wf_tree %>% finalize_workflow(tree_res %>% select_best("accuracy")) %>% fit(data = train_bal)
tree_fit <- final_tree %>% pull_workflow_fit()

visTree(tree_fit$fit)

vip(tree_fit)

# Evaluate on test set
tree_test <- test %>% add_column(tree_fit %>% predict(new_data = test, type = "prob")) %>% add_column(tree_fit %>% predict(new_data = test))
tree_test %>% roc_curve(truth = is_dec, estimate = .pred_yes, event_level = "second") %>% autoplot()
tree_test %>% roc_auc(truth = is_dec, estimate = .pred_yes, event_level = "second") 
tree_test %>% accuracy(truth = is_dec, estimate = .pred_class, event_level = "second")

# Logistic regression
log_wf <- workflow() %>%
  add_recipe(recipe(is_dec ~ ., data = train_bal) %>%
                    step_rm(outcome) %>%
                    step_naomit(all_predictors()) %>%
                    step_BoxCox(all_numeric(), -lead) %>%
                    #step_cut(bat_score, breaks = c(39,50,89,100,139,150,189,200,239,250)) %>%
                    step_dummy(is_wkt, wkts, innings) %>%
                    #step_log(bat_score, offset = 1) %>%     
                    step_normalize(all_numeric())) %>%
               #step_interact(terms = ~ starts_with("bat_score_"):bat_score_int) %>%
               #step_corr(all_numeric())) %>%
                add_model(logistic_reg() %>% set_engine("glm"))
log_fit <- log_wf %>% fit(data = train_bal)
log_coeff <- tidy(log_fit)

# Evaluate on test set
log_test <- test %>% add_column(log_fit %>% predict(new_data = test %>% mutate(bat_score_int = bat_score), type = "prob"))
log_test %>% roc_curve(truth = is_dec, estimte = .pred_yes, event_level = "second") %>% autoplot()
log_test %>% roc_auc(truth = is_dec, estimte = .pred_yes, event_level = "second") 


dec_log <- train_bal %>%
  add_column(log_fit %>% predict(new_data = train_bal %>% mutate(bat_score_int = bat_score), type = "prob")) %>%
  mutate(logit = log(.pred_yes/(1-.pred_yes)))


# Linearity
ggplot(aes(match_balls, logit), data = dec_log) + geom_point()  +
  geom_smooth(method = "loess")

ggplot(aes(lead, logit), data = dec_log) + geom_point()  +
  geom_smooth(method = "loess")

ggplot(aes(bat_score, logit), data = dec_log) + geom_point()  +
  geom_smooth(method = "loess")




prepped <- log_fit %>% pull_workflow_prepped_recipe() %>% bake(train_bal)


# Normality
ggplot(aes(sample = match_balls), data = prepped) + geom_qq() 

ggplot(aes(sample = lead), data = prepped) + geom_qq() 

ggplot(aes(sample = bat_score), data = prepped) + geom_qq()



# So these models are problematic because the data is highly correlated
train_bal %>% ggplot(aes(x = match_balls, y = lead, colour = is_dec)) + geom_point()
train_bal %>% ggplot(aes(x = bat_score, y = lead, colour = is_dec)) + geom_point()


# Remove innings which were not declared
nodec <- dec %>% group_by(game_id) %>% 

dec %>% group_by(game_id) %>% summarise(n = n()) %>%
  ggplot(aes(x = n)) + geom_histogram()
