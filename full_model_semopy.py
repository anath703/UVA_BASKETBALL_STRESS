# This script will prepare all data and create an SEM. The user can determine how many rolling and forward periods to use and whether to scale the data.
# The user can also enter the model specification to use



# Import libraries
import pandas as pd
from semopy import ModelMeans
from semopy import Model
import os
import re
from semopy import report
from sklearn.preprocessing import StandardScaler

#controls
rolling_period= 5 #how many days to use when calculating rolling data
fforward_period= 5 #up to how many days to forward fill missing data
scale= True #scale data

#model specification
physical_mod_string= 'physical_readiness =~ Physical_Performance_Capability+ Countermovement_Depth_cm+   Muscular_Stress_Score +  Overall_Recovery '
emotional_mod_string= 'emotional_readiness=~ Mental_Performance_Capability + Hours_of_Sleep_Previous_Night+ Lack_of_Activation_Score + Negative_Emotional_State_Score' 
game_perf_mod_string= 'game_performance=~ TS_Perc +Game_Score +  TRB_Perc' 
additional_covariances=  'Mental_Performance_Capability ~~  Negative_Emotional_State_Score\n'
structural_phys_string= ''

###########Data Cleaning/Preparation#################



columns_selected = [] #which data to use. based on paramaters in the model sepcificaiton above

# Use regular expression to find variable names and add them to the list
for match in re.finditer(r'\b\w+\b', physical_mod_string.split('~')[1].strip()):
    columns_selected.append(match.group(0))

for match in re.finditer(r'\b\w+\b', emotional_mod_string.split('~')[1].strip()):
    columns_selected.append(match.group(0))

if structural_phys_string:  
    for match in re.finditer(r'\b\w+\b', structural_phys_string.split('~')[1].strip()):
        columns_selected.append(match.group(0))    

#removing duplicates
columns_selected= [*set(columns_selected)]



columns_selected_game = []

for match in re.finditer(r'\b\w+\b', game_perf_mod_string.split('~')[1].strip()):
    columns_selected_game.append(match.group(0))

#adding player_id and date
columns_selected.append('Player_ID')
columns_selected.append('Date')    
columns_selected_game.append('Date')
columns_selected_game.append('Player_ID')

# Set data folder path
data_folder = '/Users/anoopnath/Desktop/MSDS/Capstone'

# Read initial datasets
catapult = pd.read_csv(data_folder+'/capstone_catapult.csv')
dari = pd.read_csv(data_folder+'/capstone_dari.csv')
force = pd.read_csv(data_folder+'/capstone_forcedecks.csv')
oura = pd.read_csv(data_folder+'/capstone_oura.csv')
rpe = pd.read_csv(data_folder+'/capstone_rpe.csv')
wellness = pd.read_csv(data_folder+'/capstone_wellness.csv')
advanced= pd.read_csv(data_folder+'/advanced_stats_anon.csv')
basic= pd.read_csv(data_folder+'/basic_stats_anon.csv')
games= pd.read_csv(data_folder+'/capstone_games_data.csv')



# force with selected columns
columns_selected_force = ['Date', 'About', 'Countermovement Depth [cm]', 'Eccentric Duration [s]']
force = force[columns_selected_force]
#taking absolute value since they're negative
force['Countermovement Depth [cm]'] = abs(force['Countermovement Depth [cm]']) 


# Convert 'Date' columns to datetime format
catapult['Date'] = pd.to_datetime(catapult['Date'])
dari['Date'] = pd.to_datetime(dari['Date'])
force['Date'] = pd.to_datetime(force['Date'])
oura['Date'] = pd.to_datetime(oura['Date'])
rpe['Date'] = pd.to_datetime(rpe['Date'])
wellness['Date'] = pd.to_datetime(wellness['Date'])
advanced['Date'] = pd.to_datetime(advanced['Date'])
basic['Date'] = pd.to_datetime(basic['Date'])

advanced['Net_Rating']= advanced['ORtg']-advanced['DRtg']
basic['Game_Score']= basic['PTS'] + 0.4*basic['FG'] + 0.7*basic['ORB']+ 0.3*basic['DRB']+ basic['STL']+ 0.7*basic['AST']\
 +0.7*basic['BLK']-0.7*basic['FGA']-0.4* (basic['FTA']-basic['FT'])-0.4*basic['PF']-basic['TOV']   
#filter to only include data for players who played 10+mins

advanced = advanced.rename(columns={'eFG%':'eFG_Perc', 'ORB%':'ORB_Perc','DRB%':'DRB_Perc', 'USG%':'USG_Perc', 'TRB%':'TRB_Perc','AST%':'AST_Perc', 'STL%':'STL_Perc', 'BLK%':'BLK_Perc', 'TOV%':'TOV_Perc', 'TS%':'TS_Perc', 'About': 'Player_ID'})

basic = basic.rename(columns={'About':'Player_ID'})
game_stats= pd.merge(basic,advanced, how='outer', on=['Date', 'Player_ID', 'MP'])
game_stats= game_stats[game_stats['MP']>=10]

# Group by date and player, averaging multiple entries per player per day
force = force.groupby(['Date', 'About']).mean().reset_index()

# Replace string values with corresponding integers in wellness DataFrame
wellness = wellness.replace("does not apply at all", 0)
wellness = wellness.replace("fully applies", 6)
wellness = wellness.replace("Not Sore", 0)



# Convert relevant columns to int32 data type
wellness = wellness.astype({'Physical Performance Capability': 'int32',
                            'Mental Performance Capability': 'int32',
                            'Emotional Balance': 'int32',
                            'Overall Recovery': 'int32'})

# Merge DataFrames
wellness_and_catapult = pd.merge(wellness, catapult, how='outer', on=['Date', 'About'])
wellness_catapult_and_force = pd.merge(wellness_and_catapult, force, how='outer', on=['Date', 'About'])

# # Convert 'Date' column to datetime format
# wellness_catapult_and_force['Date'] = pd.to_datetime(wellness_catapult_and_force['Date'])


# Rename columns
wellness_catapult_and_force = wellness_catapult_and_force.rename(columns={'About': 'Player_ID', 'Countermovement Depth [cm]': 'Countermovement_Depth_cm', 'Eccentric Duration [s]': 'Eccentric_Duration_s'})


# Remove spaces from column names
wellness_catapult_and_force.columns = wellness_catapult_and_force.columns.str.replace(" ", "_")


# Create DataFrame with selected columns
df = wellness_catapult_and_force[columns_selected]

# Find duplicate rows for the same player and date
duplicates = df[df.duplicated(subset=['Player_ID', 'Date'], keep=False)]

df = df.drop_duplicates(subset=['Player_ID', 'Date'])


# Define custom function to forward-fill up to x days
def forward_fill(group):
    group = group.set_index('Date').asfreq('D')  # Set a daily frequency for the Date index
    return group.fillna(method='ffill', limit=fforward_period)

# Apply forward-fill function to each player's data
df_filled = df.groupby('Player_ID').apply(forward_fill)

# Reset index to remove groupby multi-level index and drop the extra 'Player_ID' column
df_filled= df_filled.drop(columns=['Player_ID'])
df_filled = df_filled.reset_index()



#for testing if the forward fill worked correctly
# df[df['Player_ID']==103].to_csv(data_folder+"/before.csv", index=False)
# df_filled[df_filled['Player_ID']==103].to_csv(data_folder+"/after.csv", index=False)


# Calculate x-day rolling average for each player and each measure
#df_rolling = df_filled.groupby('Player_ID').rolling(window=rolling_period, on='Date').mean().reset_index(drop=False)
df_rolling = df_filled.groupby('Player_ID').rolling(window=rolling_period, min_periods=1, on='Date').mean().reset_index(drop=False)
df_rolling = df_rolling.drop('level_1', axis=1)

# calculate % of NAs 
df_rolling['Perc_NAs_training_and_wellness'] = df_rolling.isna().sum(axis=1)/(df_rolling.shape[1]-2)




#merging with game_stats
df_rolling= pd.merge(df_rolling,game_stats[columns_selected_game], how='outer', on=['Date', 'Player_ID'])


# Filter out rows with lots of NAS
df_rolling_filtered = df_rolling[df_rolling['Perc_NAs_training_and_wellness'] <0.5]
df_rolling_filtered= df_rolling_filtered.drop(columns=['Perc_NAs_training_and_wellness'])
corrs= df_rolling_filtered.drop(columns=['Player_ID', 'Date']).corr()

#drop columns not needed for model fitting
df_rolling_filtered= df_rolling_filtered.drop(columns=['Player_ID', 'Date'])

#scaling
if scale:
    std_scaler = StandardScaler()
    col_names= list(df_rolling_filtered.columns)
    df_rolling_filtered = std_scaler.fit_transform(df_rolling_filtered.to_numpy())
    df_rolling_filtered = pd.DataFrame(df_rolling_filtered, columns= col_names)
    
# Save the filtered DataFrame to a CSV file
df_rolling_filtered.to_csv(data_folder+"/wellness_catapult_and_force.csv", index=False)

# Set the PATH environment variable. I needed this to run semopy but you might not need it
os.environ['PATH'] = '/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:' + os.environ['PATH']



# Define Full SEM model
mod = f"""
{physical_mod_string}
{emotional_mod_string}
{game_perf_mod_string}
# structural part
game_performance~emotional_readiness+ physical_readiness
{structural_phys_string}
#additional covariances
emotional_readiness~~physical_readiness
{additional_covariances}
#rolling_period= {rolling_period}
#fforward_period={fforward_period}
#scale= {scale}
"""

# Fit the model
#model = Model(mod)
model = ModelMeans(mod)

model.fit(df_rolling_filtered)

# Create Full SEM report
rpt = report(model, "full_model")

#get factor scores
factors = model.predict_factors(df_rolling_filtered)
factors= factors.dropna()

########################################################################