from datetime import date

today = date.today().isoformat()
end_date = "2050-12-31"

url = f"https://v3.football.api-sports.io/fixtures?team=55&from={today}&to={end_date}"
headers = {"x-apisports-key": API_FOOTBALL_KEY}

response = requests.get(url, headers=headers).json()
fixtures = response.get("response", [])
