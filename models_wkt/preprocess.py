from numpy import std, array, divide, divmod, zeros, insert


def standardise(x, means = None, sds = None):
    try:
        if means == None:
            means = x.mean(axis = 0)
        if sds == None:
            sds = std(x, axis = 0)
    except ValueError:
        pass
        
    x = x - array([means]*x.shape[0])
    x = divide(x, [sds]*x.shape[0])
    
    return x, means, sds
    

# def preprocess(x, params = [None]*len(PREDS_NUM)):
#     opt_params = [None]*len(PREDS_NUM)
#     trans = [""]*len(PREDS_NUM)
    
#     N_FEATS = [6,8,12,14,15]
    
#     # Box-cox transform of bat_avg, bat_sr, bowl_avg
#     for i in N_FEATS:
#         trans[i] = "Box-Cox"
#         x[:,i], opt_params[i] = boxcox(x[:,i] + 1) if params[i] == None else (boxcox(x[:,i] + 1, params[i]), None)
#         # Adding shift parameter 1 ensures all data is positive
    
#     # Standardize all "normal" features
#     #x[:,N_FEATS] = (x[:,N_FEATS] - np.mean(x[:,N_FEATS], axis=0)) / np.std(x[:,N_FEATS], axis=0)
    
#     # Normalise all numeric features
#     #x[:,:len(PREDS_NUM)] = normalize(x[:,:len(PREDS_NUM)], axis = 0)
    
    
#     return x, DataFrame(data = {'Predictor': PREDS_NUM, 'Transformation': trans, 'Parameters': opt_params})
  
    
def split_new_ball(x, col = 1):
    ball_num, ball_age = divmod(x[:,col], 480)
    
    #if np.any(ball_num3): raise ValueError()
    
    ball_num_ind = zeros((x.shape[0], 3))
    for i,num in enumerate(ball_num):
        # TODO: vectorise this
        ball_num_ind[i,int(num)-1] = 1
    for i in range(3):
        x = insert(x, col + i + 1, ball_num_ind[:,i], axis = 1)
        
    x[:,col] = ball_age
    
    return x