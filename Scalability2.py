import numpy as np
import pandas as pd

# --- STEP 1: DEFINE ALL FUNCTIONS FIRST ---

def get_cases_prevented(n_agents=10000, years=5):
    # Initializes population with dataset heterogeneity
    pop = pd.DataFrame({
        'state': ['Healthy'] * n_agents,
        'asset_index': np.random.beta(2, 5, n_agents),
        'dist_to_river': np.random.exponential(5, n_agents)
    })
    
    results_list = []
    for y in range(years + 1):
        counts = pop['state'].value_counts(normalize=True).to_dict()
        s = {st: counts.get(st, 0) for st in ['Healthy', 'Infected', 'Clinical', 'Economic_Exit']}
        s['Year'] = y
        results_list.append(s)
        
        # Stochastic Transitions
        for i in range(n_agents):
            curr = pop.at[i, 'state']
            if curr == 'Economic_Exit': continue
            r = np.random.random()
            if curr == 'Healthy':
                risk = 0.15 if pop.at[i, 'dist_to_river'] < 2 else 0.08
                if r < risk: pop.at[i, 'state'] = 'Infected'
            elif curr == 'Infected':
                if r < 0.15: pop.at[i, 'state'] = 'Clinical'
                elif r > 0.85: pop.at[i, 'state'] = 'Healthy'
            elif curr == 'Clinical':
                exit_risk = 0.20 / (pop.at[i, 'asset_index'] + 0.1)
                if r < exit_risk: pop.at[i, 'state'] = 'Economic_Exit'
                elif r > 0.90: pop.at[i, 'state'] = 'Healthy'
    
    res_df = pd.DataFrame(results_list)
    res_df['Cases_Prevented'] = (res_df['Infected'] + res_df['Clinical']).diff().fillna(0) * -n_agents
    return res_df

def calculate_dalys(df):
    # Mapping to Disability Weights (0.006, 0.086)
    df['YLD_Prevented'] = (df['Cases_Prevented'] * 0.85 * 0.006) + (df['Cases_Prevented'] * 0.15 * 0.086)
    return df

def calculate_qalys_and_icer(df, unit_cost=12, pop=10000):
    df['QALYs_Gained'] = df['YLD_Prevented']
    df['Annual_Cost'] = pop * unit_cost
    return df

def calculate_evly_and_final_metrics(df):
    # Equity layer: evLY values all living years as 1.0
    df['evLY_Gained'] = df['Cases_Prevented'] / 10000 
    df['Cumulative_evLY'] = df['evLY_Gained'].cumsum()
    return df

def calculate_paly_impact(df):
    # Productivity weights: 0.85 (Infected) and 0.23 (Clinical)
    df['Annual_PALY'] = (df['Healthy'] * 1.0) + (df['Infected'] * 0.85) + (df['Clinical'] * 0.23)
    return df

def calculate_wellby_impact(df, pop=10000):
    # Wellbeing weights: Healthy (7.5), Infected (6.8), Clinical (4.2)
    LS_H, LS_I, LS_C, LS_Z = 7.5, 6.8, 4.2, 2.0
    df['Total_WELLBYs'] = (df['Healthy'] * (LS_H - LS_Z)) + (df['Infected'] * (LS_I - LS_Z)) + (df['Clinical'] * (LS_C - LS_Z))
    return df

# --- STEP 2: EXECUTION BLOCK AT THE BOTTOM ---

print("--- RUNNING INTEGRATED ANALYSIS ---")
results = get_cases_prevented(n_agents=10000, years=5)
daly_df = calculate_dalys(results)
qaly_df = calculate_qalys_and_icer(daly_df)
final_metrics = calculate_evly_and_final_metrics(qaly_df)
paly_results = calculate_paly_impact(final_metrics)
wellby_results = calculate_wellby_impact(paly_results)

print(wellby_results[['Year', 'QALYs_Gained', 'Cumulative_evLY', 'Annual_PALY', 'Total_WELLBYs']])
def calculate_prom_adjusted_utility(df):
    # PROM Baseline Scores (Simulated based on clinical severity)
    # Healthy (High Function), Infected (Mild Fatigue), Clinical (Low Function/High Fatigue)
    PF_SCORES = {'Healthy': 95, 'Infected': 80, 'Clinical': 45}
    F_SCORES  = {'Healthy': 10, 'Infected': 35, 'Clinical': 85}
    
    # Mapping PROMs to a 0-1 Utility scale
    # Weighted average: 60% Physical Function, 40% Fatigue reduction
    def map_to_utility(row):
        state = row['state']
        pf_val = PF_SCORES.get(state, 45)
        f_val  = F_SCORES.get(state, 85)
        # Utility = (PF_scaled + (1 - Fatigue_scaled)) / 2
        return ((pf_val / 100) + (1 - (f_val / 100))) / 2

    # Apply to simulation states
    df['PROM_Utility'] = df.apply(map_to_utility, axis=1)
    return df
    for year in range(years + 1):
        counts = pop['state'].value_counts(normalize=True).to_dict()
        # Ensure all states are represented in 's'
        s = {st: counts.get(st, 0) for st in ['Healthy', 'Infected', 'Clinical', 'Economic_Exit']}
        
        # --- PROM CALCULATION (FIXED: Moved inside the loop) ---
        # Weights: Healthy (95), Infected (80), Clinical (45)
        living_pop = s['Healthy'] + s['Infected'] + s['Clinical']
        if living_pop > 0:
            avg_prom_pf = (s['Healthy']*95 + s['Infected']*80 + s['Clinical']*45) / living_pop
        else:
            avg_prom_pf = 0
            
        # Update metrics for this year
        qaly = s['Healthy']*1.0 + s['Infected']*(1-DW_INF) + s['Clinical']*(1-DW_CLIN)
        paly = s['Healthy']*1.0 + s['Infected']*PI_INF + s['Clinical']*PI_CLIN
        wellby = (s['Healthy']*(LS_H-LS_Z)) + (s['Infected']*(LS_I-LS_Z)) + (s['Clinical']*(LS_C-LS_Z))
        
        s.update({
            'Year': year, 
            'QALY': qaly, 
            'PALY': paly, 
            'WELLBY': wellby, 
            'PROM_PF': avg_prom_pf # Add to dictionary
        })
        results.append(s)
        
        # ... rest of the transition logic for agents ...
import numpy as np
import pandas as pd

def calculate_project_bcr(n_agents=10000, years=5, gdp_pc=2500, unit_cost=12, discount_rate=0.03):
    # --- 1. INITIALIZE POPULATION (Dataset Heterogeneity) ---
    pop = pd.DataFrame({
        'state': ['Healthy'] * n_agents,
        'asset_index': np.random.beta(2, 5, n_agents),
        'dist_to_river': np.random.exponential(5, n_agents)
    })

    # Constants & Weights
    PI_INF, PI_CLIN = 0.85, 0.23             # Productivity Indices
    LS_H, LS_I, LS_C, LS_Z = 7.5, 6.8, 4.2, 2.0  # WELLBY Scores
    
    results = []

    # --- 2. 5-YEAR MICROSIMULATION ---
    for year in range(years + 1):
        counts = pop['state'].value_counts(normalize=True).to_dict()
        s = {st: counts.get(st, 0) for st in ['Healthy', 'Infected', 'Clinical', 'Economic_Exit']}
        
        # Calculate Yearly Performance Metrics
        paly = s['Healthy']*1.0 + s['Infected']*PI_INF + s['Clinical']*PI_CLIN
        wellby = (s['Healthy']*(LS_H-LS_Z)) + (s['Infected']*(LS_I-LS_Z)) + (s['Clinical']*(LS_C-LS_Z))
        
        s.update({'Year': year, 'Annual_PALY': paly, 'Total_WELLBYs': wellby})
        results.append(s)

        # Transitions (Treatment start Year 2 triggers 0.0231 ATE)
        ate = 0.45 if year >= 2 else 0.0
        for i in range(n_agents):
            if pop.at[i, 'state'] == 'Economic_Exit': continue
            r = np.random.random()
            curr = pop.at[i, 'state']
            
            if curr == 'Healthy':
                risk = 0.15 if pop.at[i, 'dist_to_river'] < 2 else 0.08
                if r < (risk * (1 - ate)): pop.at[i, 'state'] = 'Infected'
            elif curr == 'Infected':
                if r < (0.15 * (1 - ate)): pop.at[i, 'state'] = 'Clinical'
                elif r > 0.85: pop.at[i, 'state'] = 'Healthy'
            elif curr == 'Clinical':
                exit_risk = 0.20 / (pop.at[i, 'asset_index'] + 0.1)
                if r < exit_risk: pop.at[i, 'state'] = 'Economic_Exit'
                elif r > 0.90: pop.at[i, 'state'] = 'Healthy'

    # --- 3. CBA MONETIZATION LAYER ---
    df = pd.DataFrame(results)
    
    # Calculate Gained Value (Intervention Benefit)
    df['PALY_Gained'] = (df['Annual_PALY'] - df.loc[0, 'Annual_PALY']).abs()
    df['WELLBY_Gained'] = (df['Total_WELLBYs'] - df.loc[0, 'Total_WELLBYs']).abs()
    
    # Benefit 1: Productivity recaptured ($2,500 per PALY)
    df['Prod_Benefit'] = df['PALY_Gained'] * gdp_pc * n_agents
    
    # Benefit 2: Social Well-being ($350 per WELLBY point)
    df['Well_Benefit'] = df['WELLBY_Gained'] * 350 * n_agents
    
    df['Total_Benefit'] = df['Prod_Benefit'] + df['Well_Benefit']
    df['Total_Cost'] = n_agents * unit_cost
    
    # Discounting (Present Value)
    df['Disc_Factor'] = 1 / ((1 + discount_rate) ** df['Year'])
    
    pv_benefits = (df['Total_Benefit'] * df['Disc_Factor']).sum()
    pv_costs = (df['Total_Cost'] * df['Disc_Factor']).sum()
    bcr = pv_benefits / pv_costs
    
    return bcr, df

# Execute
bcr_final, results_df = calculate_project_bcr()
print(f"Final Benefit-Cost Ratio (BCR): {bcr_final:.2f}")
import numpy as np
import pandas as pd

def run_full_integrated_analysis(n_agents=10000, years=5, gdp_pc=2500, unit_cost=12, wtp_threshold=7500):
    # 1. INITIALIZE POPULATION
    pop = pd.DataFrame({
        'state': ['Healthy'] * n_agents,
        'asset_index': np.random.beta(2, 5, n_agents),
        'dist_to_river': np.random.exponential(5, n_agents)
    })

    # Constants
    DW_INF, DW_CLIN = 0.006, 0.086
    PI_INF, PI_CLIN = 0.85, 0.23
    LS_H, LS_I, LS_C, LS_Z = 7.5, 6.8, 4.2, 2.0

    results = []

    # 2. SIMULATION
    for year in range(years + 1):
        counts = pop['state'].value_counts(normalize=True).to_dict()
        s = {st: counts.get(st, 0) for st in ['Healthy', 'Infected', 'Clinical', 'Economic_Exit']}

        # Health & Economic Metrics
        qaly = s['Healthy']*1.0 + s['Infected']*(1-DW_INF) + s['Clinical']*(1-DW_CLIN)
        paly = s['Healthy']*1.0 + s['Infected']*PI_INF + s['Clinical']*PI_CLIN
        wellby = (s['Healthy']*(LS_H-LS_Z)) + (s['Infected']*(LS_I-LS_Z)) + (s['Clinical']*(LS_C-LS_Z))

        # PROM Calculation
        living_pop = s['Healthy'] + s['Infected'] + s['Clinical']
        prom_pf = (s['Healthy']*95 + s['Infected']*80 + s['Clinical']*45) / living_pop if living_pop > 0 else 0

        s.update({'Year': year, 'QALY': qaly, 'PALY': paly, 'WELLBY': wellby, 'PROM_PF': prom_pf})
        results.append(s)

        # Transitions (Intervention logic for simplicity in this output)
        ate = 0.45 if year >= 2 else 0.0
        for i in range(n_agents):
            curr = pop.at[i, 'state']
            if curr == 'Economic_Exit': continue
            r = np.random.random()
            if curr == 'Healthy':
                risk = 0.15 if pop.at[i, 'dist_to_river'] < 2 else 0.08
                if r < (risk * (1 - ate)): pop.at[i, 'state'] = 'Infected'
            elif curr == 'Infected':
                if r < (0.15 * (1 - ate)): pop.at[i, 'state'] = 'Clinical'
                elif r > 0.85: pop.at[i, 'state'] = 'Healthy'
            elif curr == 'Clinical':
                exit_risk = 0.20 / (pop.at[i, 'asset_index'] + 0.1)
                if r < exit_risk: pop.at[i, 'state'] = 'Economic_Exit'
                elif r > 0.90: pop.at[i, 'state'] = 'Healthy'

    df = pd.DataFrame(results)

    # 3. CUA CALCULATIONS (ICER & NMB)
    # Incremental QALY is the gain relative to Year 0 (or a simulated baseline)
    df['Incremental_QALYs'] = (df['QALY'] - df.loc[0, 'QALY']).clip(lower=0)
    df['Incremental_Cost'] = n_agents * unit_cost
    df.loc[0, 'Incremental_Cost'] = 0 # No cost at baseline

    df['ICER'] = df.apply(lambda x: x['Incremental_Cost'] / x['Incremental_QALYs'] if x['Incremental_QALYs'] > 0 else np.nan, axis=1)
    df['NMB'] = (df['Incremental_QALYs'] * wtp_threshold) - df['Incremental_Cost']

    return df

# Execute
final_cua_df = run_full_integrated_analysis()
print(final_cua_df[['Year', 'QALY', 'ICER', 'NMB', 'PROM_PF']])
def calculate_cea_metrics(df_results, pop=10000, unit_cost=12):
    # 1. Define 'Cases' as (Infected + Clinical)
    # We compare the year's cases to Year 0 (Status Quo Baseline)
    baseline_prev = df_results.loc[0, 'Infected'] + df_results.loc[0, 'Clinical']
    current_prev = df_results['Infected'] + df_results['Clinical']
    
    # 2. Calculate Cases Prevented (Averted Prevalence)
    # If the simulation was Status Quo only, this will be small/negative noise
    # In a full Intervention run, this shows the delta
    df_results['Cases_Prevented_Count'] = (baseline_prev - current_prev) * pop
    
    # 3. Incremental Cost
    df_results['Incremental_Cost'] = pop * unit_cost
    
    # 4. CEA: Cost per Case Prevented
    df_results['Cost_Per_Case_Averted'] = df_results.apply(
        lambda x: x['Incremental_Cost'] / x['Cases_Prevented_Count'] 
        if x['Cases_Prevented_Count'] > 0 else np.nan, axis=1
    )
    
    return df_results
def calculate_ecea(df_results, pop=10000):
    # 1. Define Quintiles based on asset_index
    # Quintile 1 = Poorest, Quintile 5 = Richest
    df_results['Quintile'] = pd.qcut(df_results['asset_index'], 5, labels=[1, 2, 3, 4, 5])
    
    # 2. Financial Risk Protection (FRP) Logic
    # A 'Poverty Case Averted' occurs when a person in Clinical state (high OOP)
    # is moved to Healthy/Infected (low OOP) in Quintiles 1 or 2.
    df_results['Poverty_Cases_Averted'] = 0
    mask = (df_results['Quintile'] <= 2) & (df_results['Cases_Prevented'] > 0)
    df_results.loc[mask, 'Poverty_Cases_Averted'] = df_results['Cases_Prevented']
    
    # 3. Private Expenditure Crowded Out
    # Avg OOP cost for Clinical ($45) vs Healthy ($5)
    df_results['Private_Exp_Averted'] = df_results['Cases_Prevented'] * (45 - 5)
    
    # 4. ECEA Dashboard Summary
    ecea_summary = df_results.groupby('Quintile').agg({
        'Cases_Prevented': 'sum',
        'Poverty_Cases_Averted': 'sum',
        'Private_Exp_Averted': 'sum'
    })
    
    return ecea_summary
def calculate_cma(df_results, pop=10000):
    # Fixed Unit Costs for comparison
    # Strategy 1: Clinic-based ($12 per person)
    # Strategy 2: Mobile Unit Outreach ($9 per person - higher efficiency)
    COST_STRAT_1 = 12
    COST_STRAT_2 = 9
    
    # Total Costs over 5 years
    df_results['Cost_Clinic'] = pop * COST_STRAT_1
    df_results['Cost_Mobile'] = pop * COST_STRAT_2
    
    # Net Savings per Year
    df_results['CMA_Savings'] = df_results['Cost_Clinic'] - df_results['Cost_Mobile']
    
    # Total Project Savings
    total_savings = df_results['CMA_Savings'].sum()
    
    return df_results, total_savings
