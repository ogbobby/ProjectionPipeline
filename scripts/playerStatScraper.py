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

def redZonePassing(year):
    """
    ['Player', 'Tm', 'Cmp', 'Att', 'Cmp%'='inside 20', 'Yds', 'TD', 'Int', 'Cmp', 'Att',
      'Cmp%'='inside 10', 'Yds', 'TD', 'Int', 'Link']
    """
    url = f'https://www.pro-football-reference.com/years/{year}/redzone-passing.htm'
    df = pd.read_html(url, header=[0, 1])[0]
    df = df[df.columns[:-1]]
    # Flatten columns, removing 'Unnamed' entries
    clean_columns = []
    for col_tuple in df.columns:
        parts = [part for part in col_tuple if 'Unnamed' not in part]
        clean_name = ' '.join(parts).strip()
        clean_columns.append(clean_name)

    df.columns = clean_columns

    # Drop first row if it's a repeated header (check by presence of "Team" or "Tm")
    if df.iloc[0].astype(str).str.contains('Team|Tm', regex=True).any():
        df = df.drop(df.columns[column_index],axis=1)
        df = df.drop(index=0).reset_index(drop=True)
        #df[column] = df[column].str.replace(',', '').astype(float)

    return df
    # headers = {'User-Agent': 'Mozilla/5.0'}
    # response = requests.get(url, headers=headers)
    # html = response.text
    # soup = BeautifulSoup(html, 'html.parser')
    # table = soup.find('table', {'id': 'fantasy_rz'})
    # rows = table.find_all('tr')
    # data = []
    # for row in rows:
    #     cols = [col.get_text(strip=True) for col in row.find_all(['td', 'th'])]
    #     data.append(cols)
    # df = pd.DataFrame(data[0:])
    # df = df.drop(index=0)
    # return df

def redZoneRushing(year):
    """
    ['Player', 'Tm', 'Att', 'Yds', 'TD', '%Rush'='rushing attempts inside 20', 'Att', 'Yds', 'TD', '%Rush'='rushing attempts inside 10',
      'Att', 'Yds', 'TD', '%Rush'='rushing attempts inside 5', 'Link']
    """
    url = f'https://www.pro-football-reference.com/years/{year}/redzone-rushing.htm'
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find('table', {'id': 'fantasy_rz'})
    rows = table.find_all('tr')
    data = []
    for row in rows:
        cols = [col.get_text(strip=True) for col in row.find_all(['td', 'th'])]
        data.append(cols)
    df = pd.DataFrame(data[0:])
    df = df.drop(index=0)
    #return df
    print(df.head)

def redZoneReceiving(year):
    """
    ['Player', 'Tm', 'Tgt', 'Rec', 'Ctch%'='inside 20', 'Yds', 'TD', '%Tgt'='inside 20', 'Tgt'='inside 10', 'Rec', 'Ctch%', 'Yds', 'TD', '%Tgt'='inside 10']
    """
    url = f'https://www.pro-football-reference.com/years/{year}/redzone-receiving.htm'
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find('table', {'id': 'fantasy_rz'})
    rows = table.find_all('tr')
    data = []
    for row in rows:
        cols = [col.get_text(strip=True) for col in row.find_all(['td', 'th'])]
        data.append(cols)
    df = pd.DataFrame(data[0:])
    df = df.drop(index=0)
    return df

def boomBust(year):
    """
    ['Rank','Player (Team)','Games','Boom','Top 6','Top 12','Bust','Other']
    """
    with requests.Session() as s:
        response = s.post(login_url , data)
        url = f"https://www.fantasypros.com/nfl/reports/boom-bust-qb.php?year={year}"
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
            print(df)
        else:
            print("No tables found.")

def PosPtsperWeek(pos,year):
    """
    ['#', 'Player', 'Pos', 'Team', 'Week1', '2', '3', '4', '5', '6', '7', '8',
       '9', '10', '11', '12', '13', '14', '15', '16', '17', 'Week18', 'Avg',
       'Total']
    """
    with requests.Session() as s:
        response = s.post(login_url , data)
        url = f"https://www.fantasypros.com/nfl/reports/leaders/{pos}.php?year={year}"
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
            print(df.head())
        else:
            print("No tables found.")

def RBPtsperWeek(year):
    """
    ['#', 'Player', 'Pos', 'Team', 'Week1', '2', '3', '4', '5', '6', '7', '8',
       '9', '10', '11', '12', '13', '14', '15', '16', '17', 'Week18', 'Avg',
       'Total']
    """
    with requests.Session() as s:
        response = s.post(login_url , data)
        url = f"https://www.fantasypros.com/nfl/reports/leaders/rb.php?year={year}"
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
            print(df.head())
        else:
            print("No tables found.")

def WRPtsperWeek(year):
    """
    ['#', 'Player', 'Pos', 'Team', 'Week1', '2', '3', '4', '5', '6', '7', '8',
       '9', '10', '11', '12', '13', '14', '15', '16', '17', 'Week18', 'Avg',
       'Total']
    """
    with requests.Session() as s:
        response = s.post(login_url , data)    
        url = f"https://www.fantasypros.com/nfl/reports/leaders/wr.php?year={year}"
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
            print(df.head())
        else:
            print("No tables found.")


def TEPtsperWeek(year):
    """
    ['#', 'Player', 'Pos', 'Team', 'Week1', '2', '3', '4', '5', '6', '7', '8',
       '9', '10', '11', '12', '13', '14', '15', '16', '17', 'Week18', 'Avg',
       'Total']
    """
    with requests.Session() as s:
        response = s.post(login_url , data)
        url = f"https://www.fantasypros.com/nfl/reports/leaders/te.php?year={year}"
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
            print(df.head())
        else:
            print("No tables found.")

def MilliWinners():
    """
    ['Position','Player','Own %','Salary','Points']
    """
    url = 'https://hellorookie.com/draftkings-millionaire-maker-winners/'
    headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Referer': 'https://www.google.com/'
    }
    response = requests.get(url, headers=headers)
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find_all('table', {'class': 'milli'})
    table_data = []
    for i, table in enumerate(table):
        df = pd.read_html(str(table))[0]  # Reads the table into a DataFrame
        table_data.append(df)
        return df
    
def CoachWins(): #coaching wins
    url = "https://www.footballdb.com/coaches/index.html?type=reg&alltime=&sort=wins"
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
        df = pd.DataFrame(rows, columns=headers)
        print(df.head())
    else:
        print("No tables found.")