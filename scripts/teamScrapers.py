import requests
from bs4 import BeautifulSoup
import pandas as pd

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.expand_frame_repr', True)

login_url = 'http://fantasypros.com/login'
data = {
    'username': 'danielseese@gmail.com',
    'password': 'RyannCharlee365_'
}

def PenDiff(year): #Penalty Differential by team by year
    """
    ['Team', 'Yd +/-'='Penalty Yardage Differential', 'Pen'='Penalties enforced', 'Yds'='Penalty Yards',
      'Off'='Offsetting', 'Dec'='Declined', 'Tot'='Total Penalties', 'FD'='First downs by penalty',
        'Pen', 'Yds', 'Off', 'Dec', 'Tot', 'FD' These are all by opponent +, previous are all by team -]
    """
    url = f"https://www.footballdb.com/statistics/penalty-differential.html?yr={year}"
    headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/123.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com"
    }

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')

    tables = soup.find_all('table')

    if tables:
        table = tables[0]  # Adjust this index based on the structure
        headers = [th.text.strip() for th in table.find_all('th')]
        headers = headers[4:]
        rows = []
        for tr in table.find_all('tr')[1:]:  # Skip header
            cells = [td.text.strip() for td in tr.find_all('td')]
            if cells:
                rows.append(cells)

        # Convert to DataFrame
        PenDiffDF = pd.DataFrame(rows, columns=headers)
        #print(df.columns)
        return PenDiffDF

def TurnDiff(year): #Turnover Differential is calculated by subtracting the total number of giveaways (interceptions & fumbles lost) from the total number of takeaways (interceptions & opponent fumble recoveries).
    """
    ['Team', 'Gms', 'Diff'='Turnover Differential', 
    Takeaways---'Int', 'Fum','Tot',
      Giveaways --'Int', 'Fum', 'Tot']
    """
    url = f"https://www.footballdb.com/statistics/turnovers.html?yr={year}"
    headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/123.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com"
    }

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')

    tables = soup.find_all('table')

    if tables:
        table = tables[0]  # Adjust this index based on the structure
        headers = [th.text.strip() for th in table.find_all('th')]
        headers = headers[5:]
        rows = []
        for tr in table.find_all('tr')[1:]:  # Skip header
            cells = [td.text.strip() for td in tr.find_all('td')]
            if cells:
                rows.append(cells)

        # Convert to DataFrame
        TurnDiffdf = pd.DataFrame(rows, columns=headers)
        return TurnDiffdf

# def PlaySelection(): #2024 summary of all offensive plays from scrimmage 
#     """
#     ['Team', 'Gms', 'Plays', 'Rush', 'Rush%', 'Pass', 'Pass%']
#     """
#     url = "https://www.footballdb.com/statistics/play-selection.html"
#     headers = {
#     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
#                   "AppleWebKit/537.36 (KHTML, like Gecko) "
#                   "Chrome/123.0.0.0 Safari/537.36",
#     "Accept-Language": "en-US,en;q=0.9",
#     "Referer": "https://www.google.com"
#     }

#     response = requests.get(url, headers=headers)
#     soup = BeautifulSoup(response.content, 'html.parser')

#     tables = soup.find_all('table')

#     if tables:
#         table = tables[0]  # Adjust this index based on the structure
#         headers = [th.text.strip() for th in table.find_all('th')]
#         headers = headers[0:]
#         rows = []
#         for tr in table.find_all('tr')[1:]:  # Skip header
#             cells = [td.text.strip() for td in tr.find_all('td')]
#             if cells:
#                 rows.append(cells)

#         # Convert to DataFrame
#         df = pd.DataFrame(rows, columns=headers)
#         #print(df.head())
#         return df

def PlaySelection():  # 2024 summary of all offensive plays from scrimmage
    """
    ['Team', 'Gms', 'Plays', 'Rush', 'Rush%', 'Pass', 'Pass%']
    """
    url = "https://www.footballdb.com/statistics/play-selection.html"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/123.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com"
    }

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')

    tables = soup.find_all('table')

    if tables:
        table = tables[0]  # Adjust this index if needed
        headers = [th.text.strip() for th in table.find_all('th')]

        rows = []
        for tr in table.find_all('tr')[1:]:  # Skip header
            tds = tr.find_all('td')
            if not tds:
                continue
            team = tds[0].find('a').text.strip() if tds[0].find('a') else tds[0].text.strip()
            other_data = [td.text.strip() for td in tds[1:]]
            row = [team] + other_data
            rows.append(row)

        df = pd.DataFrame(rows, columns=headers)
        return df

def TeamScoring(year): #overall offense statistics, including team rushing yardage, team passing yardage and total team yardage by year
    """
    ['Team', 'Gms', 'TotPts'='Total points scored', 'Pts/G', 'RushYds'='Total team rushing yards',
      'RYds/G', 'PassYds'='Net team passing yards',
       'PYds/G', 'TotYds'= 'Total team yards', 'Yds/G']
    """
    url = f"https://www.footballdb.com/statistics/nfl/team-stats/offense-totals/{year}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/123.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com"
    }

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')

    table = soup.find('table')

    headers = [th.text.strip() for th in table.find_all('th')][1:]

    rows = []
    for tr in table.find_all('tr'):
        tds = tr.find_all('td')
        if not tds:
            continue

        # Extract the team name from the <a> tag in the first cell
        team_link = tds[0].find('a')
        team_name = team_link.text.strip() if team_link else tds[0].text.strip()

        data_cells = [td.text.strip() for td in tds[1:]]
        rows.append([team_name] + data_cells)

    df = pd.DataFrame(rows, columns=['Team'] + headers)
    #print(df.head())
    return df

def scrapDVOA(year,pos): #team defense vs position, positional stats and fantasy pts against
    """
    ['Tm','G','Cmp','Att','Yds','TD','Int','2PP'='2pt conversions passes','Sk'='times sacked',
    'Att','Yds'='Rushing yds gained','TD','FantPt','DKPt','FDPt','FantPt'='fantsy pt per game',
    'DKPt'='dk pts per game','FDPt'='fanduel pts per game']
    """
    url = f'https://www.pro-football-reference.com/years/{year}/fantasy-points-against-{pos}.htm'
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find('table', {'id': 'fantasy_def'})
    rows = table.find_all('tr')
    data = []
    for row in rows:
        cols = [col.get_text(strip=True) for col in row.find_all(['td', 'th'])]
        data.append(cols)
    df = pd.DataFrame(data[0:])
    df = df.drop(index=0)
    return(df.head())

def teamDEFData(year): #Team defense stats pts allowed, yd allowed per play......by year
    """
    ['Rk', 'Tm', 'G', 'PA'='pts allowed by team', 'Yds'='yards allowed', 'Ply'='offensive plays total',
      'Y/P'='yards per off play', 'TO', 'FL', '1stD', 'Cmp', 'Att', 'Yds'='yds gained by passing',
      'TD', 'Int', 'NY/A'='net yds gained per pass attempt', '1stD'='by pssing', 'Att', 'Yds'='rushing yds gained',
        'TD', 'Y/A'='rushing yds per attempt', '1stD', 'Pen', 'Yds', '1stPy','Sc%'='percentage of drives ending in score',
          'TO%', 'EXP']
    """
    url = f'https://www.pro-football-reference.com/years/{year}/opp.htm'
    # Load multi-index headers (top 2 rows of the table header)
    df = pd.read_html(url, header=[0, 1])[0]

    # Flatten columns, removing 'Unnamed' entries
    clean_columns = []
    for col_tuple in df.columns:
        parts = [part for part in col_tuple if 'Unnamed' not in part]
        clean_name = ' '.join(parts).strip()
        clean_columns.append(clean_name)

    df.columns = clean_columns

    # Drop first row if it's a repeated header (check by presence of "Team" or "Tm")
    if df.iloc[0].astype(str).str.contains('Team|Tm', regex=True).any():
        df = df.drop(index=0).reset_index(drop=True)

    return df
    # headers = {'User-Agent': 'Mozilla/5.0'}
    # response = requests.get(url, headers=headers)
    # html = response.text
    # soup = BeautifulSoup(html, 'html.parser')
    # table = soup.find('table', {'id': 'team_stats'})
    # rows = table.find_all('tr')
    # data = []
    # for row in rows:
    #     cols = [col.get_text(strip=True) for col in row.find_all(['td', 'th'])]
    #     data.append(cols)
    # df = pd.DataFrame(data[0:])
    # df = df.drop(index=0)
    # return(df)

def advancedDEFData(year): #By team ,Yards after catch(yac), air yards per completion, blitz per dropback...... per year
    """
    ['Tm', 'G', 'Att', 'Cmp', 'Yds'='yards gained by passing', 'TD', 'DADOT'='average depth of target, when target as defender', 
    'Air'='air yards on completion', 'YAC'='yards after catch on completions', 'Bltz'='times blitzed qb',
      'Bltz%'=blitzes per dropback', 'Hrry'='qb hurries', 'Hrry%'='hurries per dropback', 'QBKD'='qb knockdowns',
     'QBKD%'='knockdowns per pass attempt', 'Sk'='sacks', 'Prss'='qb pressures', 'Prss%', 'MTkl'='missed tackles']
    """
    url = f'https://www.pro-football-reference.com/years/{year}/opp.htm'
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find('table', {'id': 'advanced_defense'})
    rows = table.find_all('tr')
    data = []
    for row in rows:
        cols = [col.get_text(strip=True) for col in row.find_all(['td', 'th'])]
        data.append(cols)
    df = pd.DataFrame(data[0:])
    df = df.drop(index=0)
    #print(df.head())
    return df

def passingDEFData(year): # By team 
    """
    ['Rk', 'Tm', 'G', 'Cmp', 'Att', 'Cmp%'='percentages of passes completed', 'Yds'='yds gained by passes', 
    'TD', 'TD%'='percentage of td thrown', 'Int', 'PD'='passes defended by df player',
       'Int%'='percentage of times intercepted', 'Y/A'='yards gained per pass attempt', 'AY/A'='adjusted yards gained per pass attempt',
         'Y/C'='yds gained per pass', 'Y/G'='yds gained per game', 'Rate'='passer rating', 'Sk', 'Yds'='yds lost due to sacks',
        'QBHits','TFL'='tackles for loss', 'Sk%'='percentage of times sacked', 'NY/A'='net yds gained per pass attempt',
        'ANY/A'='adjusted net yds per pass attempt', 'EXP'='expected pts']
    """
    url = f'https://www.pro-football-reference.com/years/{year}/opp.htm'
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    comments = soup.find_all(string=lambda text: isinstance(text, Comment))
    for comment in comments:
        comment_soup = BeautifulSoup(comment, 'html.parser')
        table = comment_soup.find('table', {'id': 'passing'})
        if table:
            df = pd.read_html(str(table))[0]
            return df
    
def rushingDEFData(year):
    """
    ['Rk', 'Tm', 'G', 'Att', 'Yds', 'TD', 'Y/A'='rushing yds per attempt', 'Y/G'='rushing yds per game', 'EXP']
    """
    url = f'https://www.pro-football-reference.com/years/{year}/opp.htm'
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    comments = soup.find_all(string=lambda text: isinstance(text, Comment))
    for comment in comments:
        comment_soup = BeautifulSoup(comment, 'html.parser')
        table = comment_soup.find('table', {'id': 'rushing'})
        if table:
            df = pd.read_html(str(table))[0]
            return df

def Schedule2025():
    """
    ['Week', 'Day', 'Date', 'VisTm', 'Pts', '@', 'HomeTm', 'Pts', 'Time']
    """
    url = 'https://www.pro-football-reference.com/years/2025/games.htm'
    df = pd.read_html(url, header=[0, 1])[0]
    # Flatten columns, removing 'Unnamed' entries
    clean_columns = []
    for col_tuple in df.columns:
        parts = [part for part in col_tuple if 'Unnamed' not in part]
        clean_name = ' '.join(parts).strip()
        clean_columns.append(clean_name)

    df.columns = clean_columns

    # Drop first row if it's a repeated header (check by presence of "Team" or "Tm")
    if df.iloc[0].astype(str).str.contains('Team|Tm', regex=True).any():
        df = df.drop(index=0).reset_index(drop=True)

    return df
    # headers = {'User-Agent': 'Mozilla/5.0'}
    # response = requests.get(url, headers=headers)
    # html = response.text
    # soup = BeautifulSoup(html, 'html.parser')
    # table = soup.find('table', {'id': 'games'})
    # rows = table.find_all('tr')
    # data = []
    # for row in rows:
    #     cols = [col.get_text(strip=True) for col in row.find_all(['td', 'th'])]
    #     data.append(cols)
    # df = pd.DataFrame(data[0:])
    # df = df.drop(index=0)
    # return df

def targetDistro(year):
    """
    ['Team','WR Targets','WR %','RB Targets','RB %','TE Targets','TE %','Total Targets']
    """
    with requests.Session() as s:
        response = s.post(login_url , data)
        url = f"https://www.fantasypros.com/nfl/reports/targets-distribution/?year={year}&start=1&end=18&show=totals"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/123.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.google.com"
        }

        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')

        tables = soup.find_all('table')

        if tables:
            table = tables[0]  # Adjust this index based on the structure
            headers = [th.text.strip() for th in table.find_all('th')]
            headers = headers[0:]
            rows = []
            for tr in table.find_all('tr')[1:]:  # Skip header
                cells = [td.text.strip() for td in tr.find_all('td')]
                if cells:
                    rows.append(cells)

            # Convert to DataFrame
            df = pd.DataFrame(rows, columns=headers)
            #print(df)
            return df
        else:
            print("No tables found.")

# def offPlays():
#     """
#     ['Team','Gms','Plays','Rush','Rush%','Pass','Pass%']
#     """
#     url = 'https://www.footballdb.com/statistics/play-selection.html'
#     headers = {
#     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
#                   '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
#     'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
#     'Accept-Language': 'en-US,en;q=0.5',
#     'Referer': 'https://www.google.com/'
#     }   
#     response = requests.get(url, headers=headers)
#     soup = BeautifulSoup(response.text, 'html.parser')

#     # Use CSS selector
#     #table = soup.select_one('table.statistics.scrollable-fixed')
#     #table = soup.find('table', class_=['statistics', 'scrollable-fixed'])
#     table = soup.find('table', {'class': 'statistics scrollable scrollable-fixed'})
#     if table:
#         df = pd.read_html(str(table))[0]
#         return df
#         #print(df.head)
#     else:
#         print("Table not found.")
#         return None

# df = offPlays()
# if df is not None:
#     print(df.head())

def offPlays(): 
    """
    ['Team','Gms','Plays','Rush','Rush%','Pass','Pass%']
    """
    url = 'https://www.footballdb.com/statistics/play-selection.html'
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/123.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com"
    }

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')

    table = soup.find('table')

    headers = [th.text.strip() for th in table.find_all('th')][1:]

    rows = []
    for tr in table.find_all('tr'):
        tds = tr.find_all('td')
        if not tds:
            continue

        # Extract the team name from the <a> tag in the first cell
        team_link = tds[0].find('a')
        team_name = team_link.text.strip() if team_link else tds[0].text.strip()

        data_cells = [td.text.strip() for td in tds[1:]]
        rows.append([team_name] + data_cells)

    df = pd.DataFrame(rows, columns=['Team'] + headers)
    #print(df.head())
    return df      
