import os
import pandas as pd
import numpy as np
from src.situation_testing.situation_testing import SituationTesting

# working directory
wd = os.path.dirname(os.path.dirname(__file__))
# relevant folders
data_path = os.path.abspath(os.path.join(wd, 'data'))
resu_path = os.path.abspath(os.path.join(wd, 'results'))

# load and modify factual data accordingly (same for all SCFs versions)
org_df = pd.read_csv(data_path + '\\clean_LawSchool.csv', sep='|').reset_index(drop=True)
# we focus on sex and race_nonwhite
df = org_df[['sex', 'race_nonwhite', 'LSAT', 'UGPA']].copy()
df.rename(columns={'sex': 'Gender', 'race_nonwhite': 'Race'}, inplace=True)

# Our decision maker:
b1 = 0.6
b2 = 0.4
min_score = round(b1*3.93 + b2*46.1, 2)  # 20.8
max_score = round(b1*4.00 + b2*48.00)    # 22
# add the decision maker to factual dataset
df['Score'] = b1*df['UGPA'] + b2*df['LSAT']
df['Y'] = np.where(df['Score'] >= min_score, 1, 0)

# ST-specific params
# k-neighbors
k_list = [15, 30, 50, 100]
# significance level
alpha = 0.05
# tau deviation
tau = 0.0

########################################################################################################################
# Single discrimination: do(Gender:= Male)
########################################################################################################################

do = 'Male'
org_cf_df = \
    pd.read_csv(data_path + '\\counterfactuals\\' + f'cf_LawSchool_lev3_do{do}.csv', sep='|').reset_index(drop=True)
cf_df = org_cf_df[['Sex', 'Race', 'scf_LSAT', 'scf_UGPA']].copy()
cf_df = cf_df.rename(columns={'Sex': 'Gender', 'scf_LSAT': 'LSAT', 'scf_UGPA': 'UGPA'})

# add the decision maker
cf_df['Score'] = b1*cf_df['UGPA'] + b2*cf_df['LSAT']
cf_df['Y'] = np.where(cf_df['Score'] >= min_score, 1, 0)

# store do:=Male results
m_res_df = df[['Gender', 'Race', 'Y']].copy()
m_res_df['cf_Y'] = cf_df[['Y']].copy()
# store for all k
k_m_res = []

# --- attribute-specific params
feat_trgt = 'Y'
feat_trgt_vals = {'positive': 1, 'negative': 0}
# list of relevant features
feat_rlvt = ['LSAT', 'UGPA']
# protected feature
feat_prot = 'Gender'
# values for the protected feature: use 'non_protected' and 'protected' accordingly
feat_prot_vals = {'non_protected': 'Male', 'protected': 'Female'}

# for percentages of complainants:
n_pro = df[df['Gender'] == 'Female'].shape[0]

# standard discrimination
res_k = pd.DataFrame(index=['stST', 'cfST', 'cfST_w', 'CF'])
dic_res_k = {}
res_p = pd.DataFrame(index=['stST', 'cfST', 'cfST_w', 'CF'])
dic_res_p = {}

# positive discrimination
res_k_pos = pd.DataFrame(index=['stST', 'cfST', 'cfST_w', 'CF'])
dic_res_k_pos = {}
res_p_pos = pd.DataFrame(index=['stST', 'cfST', 'cfST_w', 'CF'])
dic_res_p_pos = {}

# run experiments
for k in k_list:

    temp_k = []
    temp_p = []
    temp_k_pos = []
    temp_p_pos = []

    # Standard Situation Testing
    test_df = df.copy()
    st = SituationTesting()

    st.setup_baseline(test_df, nominal_atts=['Gender'], continuous_atts=['LSAT', 'UGPA'])
    m_res_df['ST'] = st.run(target_att=feat_trgt, target_val=feat_trgt_vals,
                            sensitive_att=feat_prot, sensitive_val=feat_prot_vals,
                            k=k, alpha=alpha, tau=tau)

    temp_k.append(m_res_df[m_res_df['ST'] > tau].shape[0])
    temp_p.append(round(m_res_df[m_res_df['ST'] > tau].shape[0] / n_pro * 100, 2))
    temp_k_pos.append(m_res_df[m_res_df['ST'] < tau].shape[0])
    temp_p_pos.append(round(m_res_df[m_res_df['ST'] < tau].shape[0] / n_pro * 100, 2))

    # Counterfactual Situation Testing
    test_df = df.copy()
    test_cfdf = cf_df.copy()
    cf_st = SituationTesting()

    cf_st.setup_baseline(test_df, test_cfdf, nominal_atts=['Gender'], continuous_atts=['LSAT', 'UGPA'])
    m_res_df['cfST'] = cf_st.run(target_att=feat_trgt, target_val=feat_trgt_vals,
                                 sensitive_att=feat_prot, sensitive_val=feat_prot_vals,
                                 include_centers=False, k=k, alpha=alpha, tau=tau)

    temp_k.append(m_res_df[m_res_df['cfST'] > tau].shape[0])
    temp_p.append(round(m_res_df[m_res_df['cfST'] > tau].shape[0] / n_pro * 100, 2))
    temp_k_pos.append(m_res_df[m_res_df['cfST'] < tau].shape[0])
    temp_p_pos.append(round(m_res_df[m_res_df['cfST'] < tau].shape[0] / n_pro * 100, 2))

    # Counterfactual Situation Testing (including ctr and tst centers)
    test_df = df.copy()
    test_cfdf = cf_df.copy()
    cf_st = SituationTesting()

    cf_st.setup_baseline(test_df, test_cfdf, nominal_atts=['Gender'], continuous_atts=['LSAT', 'UGPA'])
    m_res_df['cfST_w'] = cf_st.run(target_att=feat_trgt, target_val=feat_trgt_vals,
                                   sensitive_att=feat_prot, sensitive_val=feat_prot_vals,
                                   include_centers=True, k=k, alpha=alpha, tau=tau)

    temp_k.append(m_res_df[m_res_df['cfST_w'] > tau].shape[0])
    temp_p.append(round(m_res_df[m_res_df['cfST_w'] > tau].shape[0] / n_pro * 100, 2))
    temp_k_pos.append(m_res_df[m_res_df['cfST_w'] < tau].shape[0])
    temp_p_pos.append(round(m_res_df[m_res_df['cfST_w'] < tau].shape[0] / n_pro * 100, 2))

    # Counterfactual Fairness
    m_res_df['CF'] = cf_st.res_counterfactual_unfairness

    temp_k.append(m_res_df[m_res_df['CF'] == 1].shape[0])
    temp_p.append(round(m_res_df[m_res_df['CF'] == 1].shape[0] / n_pro * 100, 2))
    temp_k_pos.append(m_res_df[m_res_df['CF'] == 2].shape[0])
    temp_p_pos.append(round(m_res_df[m_res_df['CF'] == 2].shape[0] / n_pro * 100, 2))
    del test_df

    dic_res_k[k] = temp_k
    dic_res_p[k] = temp_p
    dic_res_k_pos[k] = temp_k_pos
    dic_res_p_pos[k] = temp_p_pos

    k_m_res.append(m_res_df)

print('DONE')

for k in dic_res_k.keys():
    res_k[f'k={k}'] = dic_res_k[k]
print(res_k)

for k in dic_res_p.keys():
    res_p[f'k={k}'] = dic_res_p[k]
print(res_p)

res_k.to_csv(resu_path + f'\\res_{do}_LawSchool.csv', sep='|', index=True)
res_p.to_csv(resu_path + f'\\res_{do}_LawSchool.csv', sep='|', index=True, mode='a')

for k in dic_res_k_pos.keys():
    res_k_pos[f'k={k}'] = dic_res_k_pos[k]
print(res_k_pos)

for k in dic_res_p_pos.keys():
    res_p_pos[f'k={k}'] = dic_res_p_pos[k]
print(res_p_pos)

res_k_pos.to_csv(resu_path + f'\\res_pos_{do}_LawSchool.csv', sep='|', index=True)
res_p_pos.to_csv(resu_path + f'\\res_pos_{do}_LawSchool.csv', sep='|', index=True, mode='a')

########################################################################################################################
# Single discrimination: do(Race:= White)
########################################################################################################################

do = 'White'
org_cf_df = \
    pd.read_csv(data_path + '\\counterfactuals\\' + f'cf_LawSchool_lev3_do{do}.csv', sep='|').reset_index(drop=True)
cf_df = org_cf_df[['Sex', 'Race', 'scf_LSAT', 'scf_UGPA']].copy()
cf_df = cf_df.rename(columns={'Sex': 'Gender', 'scf_LSAT': 'LSAT', 'scf_UGPA': 'UGPA'})

# add the decision maker
cf_df['Score'] = b1*cf_df['UGPA'] + b2*cf_df['LSAT']
cf_df['Y'] = np.where(cf_df['Score'] >= min_score, 1, 0)

# store do:=White results
w_res_df = df[['Gender', 'Race', 'Y']].copy()
w_res_df['cf_Y'] = cf_df[['Y']].copy()
# store for all k
k_w_res = []

# attribute-specific params
feat_trgt = 'Y'
feat_trgt_vals = {'positive': 1, 'negative': 0}
# list of relevant features
feat_rlvt = ['LSAT', 'UGPA']
# protected feature
feat_prot = 'Race'
# values for the protected feature: use 'non_protected' and 'protected' accordingly
feat_prot_vals = {'non_protected': 'White', 'protected': 'NonWhite'}

# for percentages of complainants:
n_pro = df[df['Race'] == 'NonWhite'].shape[0]

# run experiments
for k in k_list:

    temp_k = []
    temp_p = []
    temp_k_pos = []
    temp_p_pos = []

    # Standard Situation Testing
    test_df = df.copy()
    st = SituationTesting()

    st.setup_baseline(test_df, nominal_atts=['Gender'], continuous_atts=['LSAT', 'UGPA'])
    w_res_df['ST'] = st.run(target_att=feat_trgt, target_val=feat_trgt_vals,
                            sensitive_att=feat_prot, sensitive_val=feat_prot_vals,
                            k=k, alpha=alpha, tau=tau)

    temp_k.append(w_res_df[w_res_df['ST'] > tau].shape[0])
    temp_p.append(round(w_res_df[w_res_df['ST'] > tau].shape[0] / n_pro * 100, 2))
    temp_k_pos.append(w_res_df[w_res_df['ST'] < tau].shape[0])
    temp_p_pos.append(round(w_res_df[w_res_df['ST'] < tau].shape[0] / n_pro * 100, 2))

    # Counterfactual Situation Testing
    test_df = df.copy()
    test_cfdf = cf_df.copy()
    cf_st = SituationTesting()

    cf_st.setup_baseline(test_df, test_cfdf, nominal_atts=['Gender'], continuous_atts=['LSAT', 'UGPA'])
    w_res_df['cfST'] = cf_st.run(target_att=feat_trgt, target_val=feat_trgt_vals,
                                 sensitive_att=feat_prot, sensitive_val=feat_prot_vals,
                                 include_centers=False, k=k, alpha=alpha, tau=tau)

    temp_k.append(w_res_df[w_res_df['cfST'] > tau].shape[0])
    temp_p.append(round(w_res_df[w_res_df['cfST'] > tau].shape[0] / n_pro * 100, 2))
    temp_k_pos.append(w_res_df[w_res_df['cfST'] < tau].shape[0])
    temp_p_pos.append(round(w_res_df[w_res_df['cfST'] < tau].shape[0] / n_pro * 100, 2))

    # Counterfactual Situation Testing (including ctr and tst centers)
    test_df = df.copy()
    test_cfdf = cf_df.copy()
    cf_st = SituationTesting()

    cf_st.setup_baseline(test_df, test_cfdf, nominal_atts=['Gender'], continuous_atts=['LSAT', 'UGPA'])
    w_res_df['cfST_w'] = cf_st.run(target_att=feat_trgt, target_val=feat_trgt_vals,
                                   sensitive_att=feat_prot, sensitive_val=feat_prot_vals,
                                   include_centers=True, k=k, alpha=alpha, tau=tau)

    temp_k.append(w_res_df[w_res_df['cfST_w'] > tau].shape[0])
    temp_p.append(round(w_res_df[w_res_df['cfST_w'] > tau].shape[0] / n_pro * 100, 2))
    temp_k_pos.append(w_res_df[w_res_df['cfST_w'] < tau].shape[0])
    temp_p_pos.append(round(w_res_df[w_res_df['cfST_w'] < tau].shape[0] / n_pro * 100, 2))

    # Counterfactual Fairness
    w_res_df['CF'] = cf_st.res_counterfactual_unfairness

    temp_k.append(w_res_df[w_res_df['CF'] == 1].shape[0])
    temp_p.append(round(w_res_df[w_res_df['CF'] == 1].shape[0] / n_pro * 100, 2))
    temp_k_pos.append(w_res_df[w_res_df['CF'] == 2].shape[0])
    temp_p_pos.append(round(w_res_df[w_res_df['CF'] == 2].shape[0] / n_pro * 100, 2))
    del test_df

    dic_res_k[k] = temp_k
    dic_res_p[k] = temp_p
    dic_res_k_pos[k] = temp_k_pos
    dic_res_p_pos[k] = temp_p_pos

    k_w_res.append(w_res_df)

print('DONE')

for k in dic_res_k.keys():
    res_k[f'k={k}'] = dic_res_k[k]
print(res_k)

for k in dic_res_p.keys():
    res_p[f'k={k}'] = dic_res_p[k]
print(res_p)

res_k.to_csv(resu_path + f'\\res_{do}_LawSchool.csv', sep='|', index=True)
res_p.to_csv(resu_path + f'\\res_{do}_LawSchool.csv', sep='|', index=True, mode='a')

for k in dic_res_k_pos.keys():
    res_k_pos[f'k={k}'] = dic_res_k_pos[k]
print(res_k_pos)

for k in dic_res_p_pos.keys():
    res_p_pos[f'k={k}'] = dic_res_p_pos[k]
print(res_p_pos)

res_k_pos.to_csv(resu_path + f'\\res_pos_{do}_LawSchool.csv', sep='|', index=True)
res_p_pos.to_csv(resu_path + f'\\res_pos_{do}_LawSchool.csv', sep='|', index=True, mode='a')

########################################################################################################################
# Multiple discrimination: do(Gender:= Female) + do(Race:= White)
########################################################################################################################

# can run for each k... use the lists k_m_res and k_w_res | below looks at latest runs (highest k)
res_multiple = dict()

# for stST
res_multiple['stST'] = pd.merge(left=m_res_df[m_res_df['stST'] > tau], right=w_res_df[w_res_df['stST'] > tau],
                                how='inner', left_index=True, right_index=True).shape[0]
# for stST +
res_multiple['stST (+)'] = pd.merge(left=m_res_df[m_res_df['stST'] < tau], right=w_res_df[w_res_df['stST'] < tau],
                                    how='inner', left_index=True, right_index=True).shape[0]
# for cfST
res_multiple['cfST'] = pd.merge(left=m_res_df[m_res_df['cfST'] > tau], right=w_res_df[w_res_df['cfST'] > tau],
                                how='inner', left_index=True, right_index=True).shape[0]
# for cfST +
res_multiple['cfST (+)'] = pd.merge(left=m_res_df[m_res_df['cfST'] < tau], right=w_res_df[w_res_df['cfST'] < tau],
                                    how='inner', left_index=True, right_index=True).shape[0]
# for stST_w
res_multiple['cfST_w'] = pd.merge(left=m_res_df[m_res_df['cfST_w'] > tau], right=w_res_df[w_res_df['cfST_w'] > tau],
                                  how='inner', left_index=True, right_index=True).shape[0]
# for stST_w +
res_multiple['cfST_w (+)'] = pd.merge(left=m_res_df[m_res_df['cfST_w'] < tau], right=w_res_df[w_res_df['cfST_w'] < tau],
                                      how='inner', left_index=True, right_index=True).shape[0]
# for Counterfactual Fairness
res_multiple['CF'] = pd.merge(left=m_res_df[m_res_df['CF'] == 1], right=w_res_df[w_res_df['CF'] == 1],
                              how='inner', left_index=True, right_index=True).shape[0]
# for Counterfactual Fairness w +
res_multiple['CF (+)'] = pd.merge(left=m_res_df[m_res_df['CF'] == 2], right=w_res_df[w_res_df['CF'] == 2],
                                  how='inner', left_index=True, right_index=True).shape[0]

print(res_multiple)

########################################################################################################################
# Intersectional discrimination: do(Gender:= Female) & do(Race:= White)
########################################################################################################################

do = 'MaleWhite'
org_cf_df = \
    pd.read_csv(data_path + '\\counterfactuals\\' + f'cf_LawSchool_lev3_do{do}.csv', sep='|').reset_index(drop=True)

cf_df = org_cf_df[['GenderRace', 'scf_LSAT', 'scf_UGPA']].copy()
cf_df = cf_df.rename(columns={'scf_LSAT': 'LSAT', 'scf_UGPA': 'UGPA'})

# add the decision maker
cf_df['Score'] = b1*cf_df['UGPA'] + b2*cf_df['LSAT']
cf_df['Y'] = np.where(cf_df['Score'] >= min_score, 1, 0)

# add the intersectional var to df
df['GenderRace'] = df['Gender'] + '-' + df['Race']

# store do:=White results
int_res_df = df[['Gender', 'Race', 'Y']].copy()
int_res_df['cf_Y'] = cf_df[['Y']].copy()
# store for all k
k_int_res = []

# attribute-specific params
feat_trgt = 'Y'
feat_trgt_vals = {'positive': 1, 'negative': 0}
# list of relevant features
feat_rlvt = ['LSAT', 'UGPA']
# protected feature
feat_prot = 'GenderRace'
# values for the protected feature: use 'non_protected' and 'protected' accordingly
feat_prot_vals = {
    'non_protected': ['Female-White', 'Male-NonWhite', 'Male-NonWhite', 'Male-White'],
    'protected': 'Female-NonWhite'
                 }

# for percentages of complainants:
n_pro = df[df['GenderRace'] == 'Female-NonWhite'].shape[0]

# run experiments
for k in k_list:

    temp_k = []
    temp_p = []
    temp_k_pos = []
    temp_p_pos = []

    # Standard Situation Testing
    test_df = df.copy()
    st = SituationTesting()

    st.setup_baseline(test_df, nominal_atts=['Gender'], continuous_atts=['LSAT', 'UGPA'])
    int_res_df['ST'] = st.run(target_att=feat_trgt, target_val=feat_trgt_vals,
                              sensitive_att=feat_prot, sensitive_val=feat_prot_vals,
                              k=k, alpha=alpha, tau=tau)

    temp_k.append(int_res_df[int_res_df['ST'] > tau].shape[0])
    temp_p.append(round(int_res_df[int_res_df['ST'] > tau].shape[0] / n_pro * 100, 2))
    temp_k_pos.append(int_res_df[int_res_df['ST'] < tau].shape[0])
    temp_p_pos.append(round(int_res_df[int_res_df['ST'] < tau].shape[0] / n_pro * 100, 2))

    # Counterfactual Situation Testing
    test_df = df.copy()
    test_cfdf = cf_df.copy()
    cf_st = SituationTesting()

    cf_st.setup_baseline(test_df, test_cfdf, nominal_atts=['Gender'], continuous_atts=['LSAT', 'UGPA'])
    int_res_df['cfST'] = cf_st.run(target_att=feat_trgt, target_val=feat_trgt_vals,
                                   sensitive_att=feat_prot, sensitive_val=feat_prot_vals,
                                   include_centers=False, k=k, alpha=alpha, tau=tau)

    temp_k.append(int_res_df[int_res_df['cfST'] > tau].shape[0])
    temp_p.append(round(int_res_df[int_res_df['cfST'] > tau].shape[0] / n_pro * 100, 2))
    temp_k_pos.append(int_res_df[int_res_df['cfST'] < tau].shape[0])
    temp_p_pos.append(round(int_res_df[int_res_df['cfST'] < tau].shape[0] / n_pro * 100, 2))

    # Counterfactual Situation Testing (including ctr and tst centers)
    test_df = df.copy()
    test_cfdf = cf_df.copy()
    cf_st = SituationTesting()

    cf_st.setup_baseline(test_df, test_cfdf, nominal_atts=['Gender'], continuous_atts=['LSAT', 'UGPA'])
    int_res_df['cfST_w'] = cf_st.run(target_att=feat_trgt, target_val=feat_trgt_vals,
                                     sensitive_att=feat_prot, sensitive_val=feat_prot_vals,
                                     include_centers=True, k=k, alpha=alpha, tau=tau)

    temp_k.append(int_res_df[int_res_df['cfST_w'] > tau].shape[0])
    temp_p.append(round(int_res_df[int_res_df['cfST_w'] > tau].shape[0] / n_pro * 100, 2))
    temp_k_pos.append(int_res_df[int_res_df['cfST_w'] < tau].shape[0])
    temp_p_pos.append(round(int_res_df[int_res_df['cfST_w'] < tau].shape[0] / n_pro * 100, 2))

    # Counterfactual Fairness
    int_res_df['CF'] = cf_st.res_counterfactual_unfairness

    temp_k.append(int_res_df[int_res_df['CF'] == 1].shape[0])
    temp_p.append(round(int_res_df[int_res_df['CF'] == 1].shape[0] / n_pro * 100, 2))
    temp_k_pos.append(int_res_df[int_res_df['CF'] == 2].shape[0])
    temp_p_pos.append(round(int_res_df[int_res_df['CF'] == 2].shape[0] / n_pro * 100, 2))
    del test_df

    dic_res_k[k] = temp_k
    dic_res_p[k] = temp_p
    dic_res_k_pos[k] = temp_k_pos
    dic_res_p_pos[k] = temp_p_pos

    k_int_res.append(int_res_df)

print('DONE')

for k in dic_res_k.keys():
    res_k[f'k={k}'] = dic_res_k[k]
print(res_k)

for k in dic_res_p.keys():
    res_p[f'k={k}'] = dic_res_p[k]
print(res_p)

res_k.to_csv(resu_path + f'\\res_{do}_LawSchool.csv', sep='|', index=True)
res_p.to_csv(resu_path + f'\\res_{do}_LawSchool.csv', sep='|', index=True, mode='a')

for k in dic_res_k_pos.keys():
    res_k_pos[f'k={k}'] = dic_res_k_pos[k]
print(res_k_pos)

for k in dic_res_p_pos.keys():
    res_p_pos[f'k={k}'] = dic_res_p_pos[k]
print(res_p_pos)

res_k_pos.to_csv(resu_path + f'\\res_pos_{do}_LawSchool.csv', sep='|', index=True)
res_p_pos.to_csv(resu_path + f'\\res_pos_{do}_LawSchool.csv', sep='|', index=True, mode='a')

#
# EOF
#