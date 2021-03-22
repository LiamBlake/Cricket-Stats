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
                        recipe(follow_on ~ lead + match_balls, data = fo)
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
tree_fit <- final_tree %>% pull_workflow_fit()



# Second model - logistic regression
wf_logis <- workflow() %>% 
  add_recipe(
    recipe(follow_on ~ lead + match_balls + last_score, data = fo)
  ) %>%
  add_model(
    logistic_reg() %>%
      set_engine('glm'))


logis_fit <- wf_logis %>% fit(data = fo)



logis_roc <- fo %>% add_column(logis_fit %>% predict(new_data = fo, type = "prob")) %>%
  roc_curve(truth = follow_on, estimte = .pred_yes, event_level = "second")
logis_roc %>% autoplot()

tree_roc <- fo %>% add_column(final_fit %>% predict(new_data = fo, type = "prob")) %>%
  roc_curve(truth = follow_on, estimte = .pred_yes, event_level = "second")
tree_roc %>% autoplot()



# Cross-validation to evaluate
data_cv <- vfold_cv(fo, v = 5, strata = follow_on)
tree_cvs <- fit_resamples(final_tree, resamples = data_cv, control = control_resamples(save_pred = TRUE))
logis_cvs <- fit_resamples(logis_fit, resamples = data_cv, control = control_resamples(save_pred = TRUE))


tree_cvs %>% collect_metrics()
logis_cvs %>% collect_metrics()


# Logistic Regression assumption checking
fo_logis <- fo %>%
  add_column(logis_fit %>% predict(new_data = fo, type = "prob")) %>%
  mutate(logit = log(.pred_yes/(1-.pred_yes)))


# Linearity
ggplot(aes(match_balls, logit), data = fo_logis) + geom_point()  +
  geom_smooth(method = "loess")

ggplot(aes(lead, logit), data = fo_logis) + geom_point()  +
  geom_smooth(method = "loess")

ggplot(aes(last_score, logit), data = fo_logis) + geom_point()  +
  geom_smooth(method = "loess")


# Normality
ggplot(aes(sample = match_balls), data = fo_logis) + geom_qq() 

ggplot(aes(sample = lead), data = fo_logis) + geom_qq() 

ggplot(aes(sample = last_score), data = fo_logis) + geom_qq()


# Improved model
nl_fo <- fo %>% mutate(lead = -lead)
wf_final <- workflow() %>% 
  add_recipe(
    recipe(follow_on ~ lead, data = nl_fo) %>%
      step_BoxCox(all_predictors()) #%>% 
      #step_normalize(all_predictors())
  ) %>%
  add_model(
    logistic_reg() %>%
      set_engine('glm'))
final_fit <- wf_final %>% fit(data = nl_fo)

# ROC Curve
logis_roc <- fo %>% add_column(final_fit %>% predict(new_data = nl_fo, type = "prob")) %>%
  roc_curve(truth = follow_on, estimte = .pred_yes, event_level = "second")
logis_roc %>% autoplot()

# Cross-validation
logis_cvs <- fit_resamples(final_fit, resamples = data_cv, control = control_resamples(save_pred = TRUE))
logis_cvs %>% collect_metrics()


final_recp <- final_fit %>% pull_workflow_prepped_recipe()

fo_logis <- final_recp %>% bake(new_data = nl_fo) %>%
  add_column(final_fit %>% predict(new_data = nl_fo, type = "prob")) %>%
  mutate(logit = log(.pred_yes/(1-.pred_yes)))

# Linearity
ggplot(aes(match_balls, logit), data = fo_logis) + geom_point()  +
  geom_smooth(method = "loess")

ggplot(aes(lead, logit), data = fo_logis) + geom_point()  +
  geom_smooth(method = "loess")

ggplot(aes(last_score, logit), data = fo_logis) + geom_point()  +
  geom_smooth(method = "loess")


# Normality
ggplot(aes(sample = match_balls), data = fo_logis) + geom_qq() 

ggplot(aes(sample = lead), data = fo_logis) + geom_qq() 

ggplot(aes(sample = last_score), data = fo_logis) + geom_qq() 


# Residuals
ggplot(aes(x = logit, y = final_fit$fit$fit$fit$residuals), data = fo_logis) + geom_point()
ggplot(aes(sample = final_fit$fit$fit$fit$residuals), data = fo_logis) + geom_qq()


# So we will use the logistic regression fit. Assumptions are a bit dodgy, but 75% accuracy is pretty decent for now
tidy(final_fit)
# transformations
tidy(final_recp, n = 1)
