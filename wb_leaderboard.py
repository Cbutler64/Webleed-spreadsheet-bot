#!/usr/bin/env python3
#This is a module meant to be imported
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from urllib.parse import quote, unquote
import base64
from requests import Request, Session
import json
import pandas as pd

def velo_api(url,data):
  #Create Cipher
  key = 'BatCaveGGevaCtaB'.encode('utf-8')
  cipher = AES.new(key, AES.MODE_ECB)
  #Encrypt the utf encoded data string
  msg_en = cipher.encrypt(pad(data.encode('utf-8'),16))
  #base64 encode the encrypted string
  output = quote(base64.b64encode(msg_en),safe='')
  #add prefix to encrypted string
  payload = "post_data={}".format(str(output))
  #Standard Headers
  headers = {
  'User-Agent': 'UnityPlayer/2020.3.8f1 (UnityWebRequest/1.0, libcurl/7.52.0-DEV)',
  'Accept': '*/*',
  'Accept-Encoding': 'identity',
  'Connection': 'Keep-Alive',
  'Content-Type': 'application/x-www-form-urlencoded',
  'X-Unity-Version': '2020.3.8f1'
  }
  try:
      #make api call
    s = Session()
    req = Request('POST', url, data=payload, headers=headers)
    prepped = req.prepare()
    response = s.send(prepped)
    #base64 decode and then decrypt the response
    decipher = AES.new(key, AES.MODE_ECB)
    result = decipher.decrypt(base64.b64decode(response.text))
    result = unpad(result, 16)
    #decode decrypted response
    result = result.decode('utf-8').strip()
    #convert to json object
    final = json.loads(result)
    # print(final)
  except:
    print('Problem with api call')
    quit(1)
  return final

# @input: track_id
# @output: leaderboard results in pandas dataframe
def get_leaderboard(track_id):
  #Models may need to be updates on newer versions of Velocidrone
  validModels = [48, 52, 53, 54, 56, 57, 62, 112, 113, 116, 119, 120, 121]
  print("Grabbing data from track " + track_id)
  payload = "track_id="+track_id+"&sim_version=1.16&offset=0&count=200&protected_track_value=1&race_mode=6".format(track_id)
  url = 'https://velocidrone.co.uk/api/leaderboard/getLeaderBoard'
  final = velo_api(url,payload)
  if not final['tracktimes']:
    print('Invalid track_id')
    quit(1)
  final_df = pd.json_normalize(final, record_path =['tracktimes'])
  final_df['lap_time'] = pd.to_numeric(final_df['lap_time'])
  final_df = final_df[final_df['model_id'].isin(validModels)]
  final_df.reset_index(drop=True, inplace=True)
  final_df.index += 1
  final_df['position'] = final_df.index
  final_df = final_df[['playername', 'lap_time', "position", "model_id", "country", 'user_id']]
  final_df = final_df.rename({'playername': 'Player Name', 'lap_time': 'Lap Time', 'position': 'Position', 'model_id': 'Model ID', 'country': 'Country', 'user_id': 'Userid'}, axis='columns')
  return(final_df)