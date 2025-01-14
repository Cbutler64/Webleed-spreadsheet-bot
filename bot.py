#!/usr/bin/env python3
import pandas as pd
from wb_leaderboard import get_leaderboard
import gspread
from datetime import datetime
import time 
from pytz import timezone
import os

#Global variables
season_teams={
  'Zhou Pals': [69772, 302373, 205644, 103349, 294085, 163286, 81997, 308407],
  'Big Whoop Energy': [246662, 250098, 79017, 284207, 79689, 191606, 321731, 347179],
  'Ultralite Delights':[151071, 184251, 206169, 192617, 7815, 316390, 139781, 351991],
  'Mob-lin Mode': [118267, 146875, 145593, 149797, 274323, 164453, 279000, 312536],
  'ViFly Villians': [23482, 14813, 223054, 19607, 131929, 115709, 66598, 323564],
  'Pterofractyls': [226240, 304889, 135387, 123636, 266362, 226254, 226497, 288713],
  'NB Super Swarm': [283563, 5580, 83933, 13691, 213752, 78135, 341466, 9273]
}
sheet_id = "1YpQ3DsRvVJblOb4ISRs3ofQ93W9yVnv9k-66wgL1Zqo"


#Weekly variables
current_track = 2
track_id = '1696'
sheet_cutoff = "2025-01-26 00:00:00"


def update_spreadsheet(leaderboard):
  #dump leaderboard to sheet
  gc = gspread.oauth()
  sh = gc.open_by_key(sheet_id)
  worksheet = sh.worksheet("Track " + str(current_track) )
  worksheet.update([leaderboard.columns.values.tolist()] + leaderboard.values.tolist(), 'A2:F200')
  #columns for teams are hardcoded - may need to change if spreadsheet format changes
  trialColumns = ["I","L","O","R","U","X","AA"];
  scoreColumns = ["J","M","P","S","V","Y","AB"];
  team_dfs = {}
  worksheet = sh.worksheet("Track " + str(current_track)) 
  name_lookup = sh.worksheet("Team IDs (For automation)")
  #lookup player proper names by id
  player_lookup = pd.DataFrame(name_lookup.get("A1:C60"))
  player_lookup.columns = player_lookup.iloc[0]
  player_lookup = player_lookup.iloc[1:]
  player_lookup['User ID'] = player_lookup['User ID'].astype(int)

  #do the loopdy loop and pull - and your sheets be lookin cool
  for team_name, user_ids in season_teams.items():
      # Filter the main dataframe for the user_ids in the current team
      team_df = leaderboard[leaderboard['Userid'].isin(user_ids)].copy()
      # Add missing user_ids with a default lap_time of 1000
      missing_ids = set(user_ids) - set(team_df['Userid'])
      for missing_id in missing_ids:
          team_df = pd.concat([team_df, pd.DataFrame({'Userid': [missing_id], 'Lap Time': [1000]})], ignore_index=True)
      # Add player names by lookup from the player_lookup dataframe
      team_df = team_df.merge(player_lookup[['User ID', 'Player Name']], how='left', left_on='Userid', right_on='User ID')
      team_df.drop(columns=['User ID'], inplace=True)
      # Store the team's dataframe in the dictionary
      team_dfs[team_name] = team_df

  #Drop unused columns and inject data into spreadsheet
  for idx, (team_name, team_df) in enumerate(team_dfs.items()):
      team_df = team_df.drop(columns=['Position', 'Model ID', "Country", "Userid", "Player Name_x"])
      range = trialColumns[idx]+"3" + ":" + scoreColumns[idx] + "10"
      team_df = team_df[["Player Name_y", "Lap Time"]]
      worksheet.update(team_df.values.tolist(), range)


def refresh_leaderboard(track_id):
  #grab leaderboard, check for changes, run update speadsheet if there are changes
  leaderboard = get_leaderboard(track_id)
  if not os.path.exists("leaderboard.csv"):
    leaderboard.to_csv("leaderboard.csv", index=False)
    update_spreadsheet(leaderboard)
  else:
    old_leaderboard = pd.read_csv("leaderboard.csv")
    old_leaderboard.index += 1
    if not old_leaderboard.compare(leaderboard).empty:
      print("Leaderboard changed detected sending data...")
      update_spreadsheet(leaderboard)
      print("Sent!")
    else:
      print("No leaderboard changes detected.")

def check_sheet_cutoff(target_date_str, target_format: str = "%Y-%m-%d %H:%M:%S"):
    # Parse the target date into EST timezone
    est = timezone("US/Eastern")
    target_date = datetime.strptime(target_date_str, target_format)
    target_date = est.localize(target_date)

    # Get the current UTC time and convert to EST
    current_utc = datetime.now()
    current_est = current_utc.astimezone(est)
    # Compare the two dates
    return current_est < target_date

while(check_sheet_cutoff(sheet_cutoff)): 
    print('Loading...') 
    refresh_leaderboard(track_id)
    time.sleep(300)
