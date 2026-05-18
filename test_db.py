import requests
r = requests.get('https://api.telegra.ph/createAccount?short_name=BotDB').json()
t = r['result']['access_token']
p = requests.post('https://api.telegra.ph/createPage', json={'access_token':t,'title':'DB','content':'[{"tag":"p","children":["{}"]}]'}).json()
print('TOKEN:', t)
print('PATH:', p['result']['path'])
