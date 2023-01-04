import warnings
import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import requests
from bs4 import BeautifulSoup
from fpdf import FPDF

warnings.filterwarnings('ignore')


def directory(path: str) -> None:
    """Create a directory if it doesn't exist"""

    if not os.path.exists(path):
        os.mkdir(path)


def extract_api(url: str, headers: dict) -> pd.DataFrame:
    """Extract data from API with given url and headers"""
    return pd.DataFrame(requests.get(url=url, headers=headers).json())


def get_dfs(team: str, season: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Get all the dataframes needed for the report"""

    # Read the API key from the config file
    file = open("config.txt", "r")
    # Read the file
    API_KEY = file.read()[10:]
    # Close the file
    file.close()

    headers = {'Ocp-Apim-Subscription-Key': API_KEY}

    url_players = f"https://api.sportsdata.io/v3/nba/scores/json/Players/{team}"
    df_players = extract_api(url_players, headers)

    url_schedules = "https://api.sportsdata.io/v3/nba/scores/json/Games/2022"
    df_schedules = extract_api(url_schedules, headers)
    df_schedules = df_schedules[(df_schedules['AwayTeam'] == team) | (df_schedules['HomeTeam'] == team)]
    df_schedules['Winner'] = df_schedules.apply(lambda x: x['AwayTeam'] if x['AwayTeamScore'] > x['HomeTeamScore'] else x['HomeTeam'], axis=1)
    df_schedules.reset_index(inplace=True)

    url_player_stats = f"https://api.sportsdata.io/v3/nba/stats/json/PlayerSeasonStatsByTeam/{season}/{team}"
    df_player_stats = extract_api(url_player_stats, headers)

    url_teams = "https://api.sportsdata.io/v3/nba/scores/json/teams"
    df_team = extract_api(url_teams, headers)
    df_team = df_team[df_team['Key'] == team]  # We filter the df to get only the demanded team
    df_team['TeamName'] = df_team['City'] + ' ' + df_team['Name']  # We create a new column with the team name
    df_team.reset_index(inplace=True)

    return (df_players, df_schedules, df_player_stats, df_team)


def get_team_info(df_team: pd.DataFrame) -> tuple[list, str]:
    """Get team colors and name"""

    # We get the colors for the style of the report
    colors = [f"#{df_team.loc[0,'PrimaryColor']}", f"#{df_team.loc[0,'SecondaryColor']}"]
    # We get the team name
    name = df_team.loc[0, 'TeamName']
    return (colors, name)


def graphs(df_players: pd.DataFrame, df_schedules: pd.DataFrame, df_player_stats: pd.DataFrame, path: str, colors: list, name: str) -> None:
    """Create all the graphs for the report using the obtained dataframes"""

    # 1.1 Table of Players
    df_table_players = df_players[['Position', 'Height', 'Weight', 'BirthDate', 'BirthCountry', 'College', 'Salary']]  # 'PhotoUrl'
    df_table_players.loc[:, 'BirthDate'] = [df_table_players.loc[i, 'BirthDate'][:10] for i in range(len(df_table_players['BirthDate']))]
    # We convert the height from feet to cm
    df_table_players.loc[:, 'Height'] = [str(round(df_table_players.loc[i, 'Height']*2.54, 1))+' cm' for i in range(len(df_table_players['Height']))]
    player_names = [df_players.loc[i, 'FirstName'] + ' ' + df_players.loc[i, 'LastName'] for i in range(len(df_players['FirstName']))]

    fig, ax = plt.subplots(figsize=(20, 10))
    ax.axis('tight')
    ax.axis('off')
    plt.table(cellText=df_table_players.values, colLabels=df_table_players.columns, loc='center',
              cellLoc='center', colLoc='center', bbox=[0, 0, 1, 1], rowLabels=player_names,
              rowColours=[colors[0]] * len(df_table_players), colColours=[colors[0]] * len(df_table_players.columns))
    # plt.show()
    fig.savefig(f'{path}/table_players.png')
    plt.close()


    # 1.2 Pyplot PieChart on Win Rate
    win_rate = len(df_schedules[df_schedules['Winner'] == team]) / len(df_schedules)

    labels = ['Win', 'Lose']
    sizes = [win_rate, 1 - win_rate]
    explode = (0.1, 0)
    fig, ax = plt.subplots()
    ax.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%', shadow=True, startangle=90, colors=['green', 'red'])
    ax.axis('equal')
    plt.title(f'Win Rate - {name}')
    # plt.show()
    fig.savefig(f'{path}/win_rate.png', bbox_inches='tight')
    plt.close()


    # 1.3 Pyplot PieChart on Win Rate Home
    win_rate_home = len(df_schedules[(df_schedules['Winner'] == team) & (df_schedules['HomeTeam'] == team)]) / len(df_schedules[df_schedules['HomeTeam'] == team])

    labels = ['Win', 'Lose']
    sizes = [win_rate_home, 1 - win_rate_home]
    explode = (0.1, 0)
    fig, ax = plt.subplots()
    ax.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%', shadow=True, startangle=90, colors=['green', 'red'])
    ax.axis('equal')
    plt.title(f'Win Rate Home - {name}')
    # plt.show()
    fig.savefig(f'{path}/win_rate_home.png', bbox_inches='tight')
    plt.close()


    # 1.4 Pyplot PieChart on Win Rate Away
    win_rate_away = len(df_schedules[(df_schedules['Winner'] == team) & (df_schedules['AwayTeam'] == team)]) / len(df_schedules[df_schedules['AwayTeam'] == team])

    labels = ['Win', 'Lose']
    sizes = [win_rate_away, 1 - win_rate_away]
    explode = (0.1, 0)
    fig, ax = plt.subplots()
    ax.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%', shadow=True, startangle=90, colors=['green', 'red'])
    ax.axis('equal')
    plt.title(f'Win Rate Away - {name}')
    # plt.show()
    fig.savefig(f'{path}/win_rate_away.png', bbox_inches='tight')
    plt.close()


    # 2.1 Season Points
    df_player_stats['Points'] = df_player_stats['Points'].astype(int)
    df_player_stats.sort_values(by='Points', ascending=False, inplace=True)

    fig = plt.figure(figsize=(10, 5))
    plt.bar(df_player_stats['Name'], df_player_stats['Points'], color=colors[0])
    plt.title('Points')
    plt.xlabel('Player')
    plt.ylabel('Points')
    plt.xticks(rotation=70)
    # plt.show()
    fig.savefig(f'{path}/points.png', bbox_inches='tight')
    plt.close()


    # 2.2 Points per minute
    df_player_stats['PointsPerMinute'] = df_player_stats['Points'] / df_player_stats['Minutes']
    df_player_stats.sort_values(by='PointsPerMinute', ascending=False, inplace=True)

    fig = plt.figure(figsize=(10, 5))
    plt.bar(df_player_stats['Name'], df_player_stats['PointsPerMinute'], color=colors[1])
    plt.xlabel('Player')
    plt.ylabel('Points Per Minute')
    plt.title('Points Per Minute')
    plt.xticks(rotation=70)
    # plt.show()
    fig.savefig(f'{path}/points_per_minute.png', bbox_inches='tight')
    plt.close()


    # 3.1 Grouped barplot on Shot Accuracy
    df_player_stats['TwoPointerAccuracy'] = df_player_stats['TwoPointersMade'] / df_player_stats['TwoPointersAttempted']
    df_player_stats['ThreePointerAccuracy'] = df_player_stats['ThreePointersMade'] / df_player_stats['ThreePointersAttempted']
    df_player_stats.sort_values(by='TwoPointerAccuracy', ascending=False, inplace=True)

    x = np.arange(len(df_player_stats['Name']))
    width = 0.35

    fig, ax = plt.subplots(1, 1, figsize=(10, 5))
    rects1 = ax.bar(x - width/2, df_player_stats['TwoPointerAccuracy'], width, label='Two Pointers', color=colors[0], edgecolor='black')
    rects2 = ax.bar(x + width/2, df_player_stats['ThreePointerAccuracy'], width, label='Three Pointers', color=colors[1], edgecolor='black')

    ax.set_ylabel('Percentage')
    ax.set_title('Shot Accuracy')
    ax.set_xticks(x, labels=df_player_stats['Name'], rotation=70)
    ax.legend()
    fig.tight_layout()
    # plt.show()
    fig.savefig(f'{path}/shot_accuracy.png', bbox_inches='tight')
    plt.close()


    # 3.2 Grouped barplot on Shots Scored
    df_player_stats.sort_values(by='TwoPointersMade', ascending=False, inplace=True)

    x = np.arange(len(df_player_stats['Name']))
    width = 0.35

    fig, ax = plt.subplots(1, 1, figsize=(10, 5))
    rects1 = ax.bar(x - width/2, df_player_stats['TwoPointersMade'], width, label='Two Pointers', color=colors[0], edgecolor='black')
    rects2 = ax.bar(x + width/2, df_player_stats['ThreePointersMade'], width, label='Three Pointers', color=colors[1], edgecolor='black')

    ax.set_ylabel('Scored')
    ax.set_title('Shots Scored')
    ax.set_xticks(x, labels=df_player_stats['Name'], rotation=70)
    ax.legend()
    fig.tight_layout()
    # plt.show()
    fig.savefig(f'{path}/shots_made.png', bbox_inches='tight')
    plt.close()


    # 3.3 Barplot on free throw percentage
    free_throws = df_player_stats[['Name', 'FreeThrowsPercentage']]
    free_throws = free_throws[free_throws['FreeThrowsPercentage'] > 0]
    free_throws.sort_values(by='FreeThrowsPercentage', ascending=False, inplace=True)

    fig, ax = plt.subplots(1, 1, figsize=(10, 5))
    plt.barh(free_throws['Name'], free_throws['FreeThrowsPercentage'], color=colors[0])
    plt.xlabel('Player')
    plt.ylabel('Free Throw Percentage')
    plt.title('Free Throw Percentage')
    plt.xlim(right=100)
    # plt.show()
    fig.savefig(f'{path}/free_throw_percentage.png', bbox_inches='tight')
    plt.close()


    # 4.1 Defense statistics
    df_player_stats['Steals'] = df_player_stats['Steals'].astype(int)
    df_player_stats['BlockedShots'] = df_player_stats['BlockedShots'].astype(int)
    df_player_stats['Defense'] = df_player_stats['Steals'] + df_player_stats['BlockedShots']
    df_player_stats.sort_values(by='Defense', ascending=False, inplace=True)

    fig = plt.figure(figsize=(10, 5))
    plt.bar(df_player_stats['Name'], df_player_stats['Steals'], color=colors[0], edgecolor='black')
    plt.bar(df_player_stats['Name'], df_player_stats['BlockedShots'], bottom=df_player_stats['Steals'], color=colors[1], edgecolor='black')
    plt.xlabel('Player')
    plt.ylabel('Defensive Statistics')
    plt.title('Defensive Statistics')
    plt.legend(['Steals', 'Blocked Shots'])
    plt.xticks(rotation=70)
    # plt.show()
    fig.savefig(f'{path}/defense.png', bbox_inches='tight')
    plt.close()


    # 4.2 Defense statistics by minute played
    df_player_stats['Steals'] = df_player_stats['Steals'].astype(int)
    df_player_stats['BlockedShots'] = df_player_stats['BlockedShots'].astype(int)
    df_player_stats['Defense'] = (df_player_stats['Steals'] + df_player_stats['BlockedShots']) / df_player_stats['Minutes']
    df_player_stats.sort_values(by='Defense', ascending=False, inplace=True)

    fig = plt.figure(figsize=(10, 5))
    plt.bar(df_player_stats['Name'], df_player_stats['Steals'] / df_player_stats['Minutes'], color=colors[0], edgecolor='black')
    plt.bar(df_player_stats['Name'], df_player_stats['BlockedShots'] / df_player_stats['Minutes'], bottom=df_player_stats['Steals'] / df_player_stats['Minutes'], color=colors[1], edgecolor='black')
    plt.xlabel('Player')
    plt.ylabel('Defensive Statistics')
    plt.title('Defensive Statistics by minute played')
    plt.legend(['Steals', 'Blocked Shots'])
    plt.xticks(rotation=70)
    # plt.show()
    fig.savefig(f'{path}/defense_by_minute.png', bbox_inches='tight')
    plt.close()


    # 5.1 Stacked Barplot on Two Pointers Made
    df_player_stats['TwoPointersMade'] = df_player_stats['TwoPointersMade'].astype(int)
    df_player_stats['TwoPointersAttempted'] = df_player_stats['TwoPointersAttempted'].astype(int)
    df_player_stats.sort_values(by='TwoPointersAttempted', ascending=False, inplace=True)

    fig, ax = plt.subplots(figsize=(10, 5))
    plt.title('Two Pointers')
    plt.bar(df_player_stats['Name'], df_player_stats['TwoPointersAttempted'], color='red')
    plt.bar(df_player_stats['Name'], df_player_stats['TwoPointersMade'], color='green')
    plt.xlabel('Player')
    plt.ylabel('Two Pointers')
    plt.legend(['Missed', 'Scored'])
    plt.xticks(rotation=70)
    # plt.show()
    fig.savefig(f'{path}/two_pointers.png', bbox_inches='tight')
    plt.close()


    # 5.2 Stacked Barplot on Three Pointers Made
    df_player_stats['ThreePointersMade'] = df_player_stats['ThreePointersMade'].astype(int)
    df_player_stats['ThreePointersAttempted'] = df_player_stats['ThreePointersAttempted'].astype(int)
    df_player_stats.sort_values(by='ThreePointersAttempted', ascending=False, inplace=True)

    fig, ax = plt.subplots(1, 1, figsize=(10, 5))
    plt.title('Three Pointers')
    ax.bar(df_player_stats['Name'], df_player_stats['ThreePointersAttempted'], color='red')
    ax.bar(df_player_stats['Name'], df_player_stats['ThreePointersMade'], color='green')
    ax.legend(['Missed', 'Scored'])
    plt.xlabel('Player')
    plt.ylabel('Three Pointers')
    plt.xticks(rotation=70)
    # plt.show()
    fig.savefig(f'{path}/three_pointers.png', bbox_inches='tight')
    plt.close()

    plt.close('all')


def web_scraping_nba_logos(name: str, path: str) -> None:
    """Obtain NBA team logos through Web Scraping"""

    # As the format of the photos in the df is svg, I have had
    # to look for another way to get the logos of the teams
    # I have had to search in the code of different websites until
    # I found one that gave me the logos in png format. Then, I
    # have used web scraping to obtain the logosfrom the website

    logo_name = name + ' Transparent Logo'
    url = "https://loodibee.com/nba/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    logo_wall = soup.find('div', class_='logos-layout column-3')
    teams = logo_wall.find_all('img',)
    logos_dict = {}
    for team in teams:
        if 'srcset' in team.attrs:
            logos_dict[team['alt']] = team['srcset']
    logo = logos_dict[logo_name].split(' ')[-2]
    response = requests.get(logo)
    with open(f'{path}/logo_{name.replace(" ", "_")}.png', 'wb') as file:
        file.write(response.content)


def predict_winner(name: str) -> dict:
    """Predict the winner of the next match of a given team"""

    url = 'https://www.sportytrader.es/cuotas/baloncesto/usa/nba-306/'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    bets = soup.find('div', class_="px-box mb-10")
    # print(bets.prettify())
    matches = bets.find_all('div', class_="cursor-pointer border rounded-md mb-4 px-1 py-2 flex flex-col lg:flex-row relative")
    name_web_scraping = name.split(' ')[-1]
    next_match_info = {}
    for match in matches:
        if name_web_scraping in match.span.a.text:
            teams = match.span.a.text.split(' - ')
            teams = [teams[0][1:], teams[1][:-1]]
            if 'LA ' in teams[0]:
                teams[0] = teams[0].replace('LA', 'Los Angeles')
            elif 'LA ' in teams[1]:
                teams[1] = teams[1].replace('LA', 'Los Angeles')

            odds = match.find_all('span', class_='px-1 h-booklogosm font-bold bg-primary-yellow text-white leading-8 rounded-r-md w-14 md:w-18 flex justify-center items-center text-base')
            odds = [odds[0].text, odds[1].text]
            date = match.span.span.text
            next_match_info = {'teams': teams, 'odds': odds, 'date': date}

    return next_match_info


class PDF(FPDF):

    def Title(self, title, coords, size, color, border=0, center=False):
        self.set_font('Arial', 'B', size)
        self.set_text_color(color[0], color[1], color[2])
        self.set_xy(coords[0], coords[1])
        if not center:
            self.cell(80, 10, title, border=border)
        else:
            self.cell(80, 10, title, border=border, align='C')

    def Cover(self, name, season):
        self.add_page()
        self.set_font('Arial', 'B', 30)
        self.set_xy(35, 60)
        self.multi_cell(150, 30, f'{name}\n{season}-{int(season)+1} Season', border=1, align='C')
        self.image(f'{path}/logo_{name.replace(" ", "_")}.png', 60, 130, 100)
        self.set_font('Arial', 'B', 12)
        self.set_xy(35, 250)
        self.multi_cell(150, 10, 'Author\nIgnacio Bayón Jiménez-Ugarte', align='C')


def pdf(name: str, season: str, path: str, next_match_info: dict):
    pdf = PDF()
    pdf.set_author('Ignacio Bayón Jiménez-Ugarte')
    pdf.set_title(f'{name} - {season} Season')
    pdf.Cover(name, season)

    # GENERAL STATISTICS PAGE
    pdf.add_page()
    pdf.Title('General Statistics', coords=(40, 10), size=20, color=(0, 0, 0))
    pdf.Title("Players' General Information", coords=(20, 30), size=16, color=(0, 51, 102))
    pdf.image(f'{path}/table_players.png', 10, 45, 200)
    pdf.Title('Win Rate', coords=(20, 170), size=16, color=(0, 51, 102))
    pdf.image(f'{path}/win_rate.png', 0, 185, 120)
    pdf.Title('Win Rate Home vs Away', coords=(120, 140), size=14, color=(0, 51, 102))
    pdf.image(f'{path}/win_rate_home.png', 120, 155, 80)
    pdf.Title('Loss Rate Home vs Away', coords=(120, 220), size=14, color=(0, 51, 102))
    pdf.image(f'{path}/win_rate_away.png', 120, 235, 80)

    # Points Statistics Page
    pdf.add_page()
    pdf.Title('Points Statistics', coords=(40, 10), size=20, color=(0, 0, 0))
    pdf.Title('- Points', coords=(20, 30), size=16, color=(0, 51, 102))
    pdf.image(f'{path}/points.png', 20, 45, 160)
    pdf.Title('- Points Per Minute', coords=(20, 160), size=16, color=(0, 51, 102))
    pdf.image(f'{path}/points_per_minute.png', 20, 175, 160)

    # Shot Statistics Page
    pdf.add_page()
    pdf.Title('Shot Statistics', coords=(40, 10), size=20, color=(0, 0, 0))
    pdf.Title('- Shot Accuracy', coords=(20, 30), size=16, color=(0, 51, 102))
    pdf.image(f'{path}/shot_accuracy.png', 40, 45, 130)
    pdf.Title('Total Field Shots Made', coords=(20, 120), size=16, color=(0, 51, 102))
    pdf.image(f'{path}/shots_made.png', 40, 135, 130)
    pdf.Title('- Free Throw Percentage', coords=(20, 210), size=16, color=(0, 51, 102))
    pdf.image(f'{path}/free_throw_percentage.png', 40, 225, 130)

    # Two Pointers vs Three Pointers Page
    pdf.add_page()
    pdf.Title('Shot Statistics', coords=(40, 10), size=20, color=(0, 0, 0))
    pdf.Title('- Two Pointers', coords=(20, 30), size=16, color=(0, 51, 102))
    pdf.image(f'{path}/two_pointers.png', 20, 45, 160)
    pdf.Title('- Three Pointers', coords=(20, 160), size=16, color=(0, 51, 102))
    pdf.image(f'{path}/three_pointers.png', 20, 175, 160)

    # Defense Statistics Page
    pdf.add_page()
    pdf.Title('Defensive Statistics', coords=(40, 10), size=20, color=(0, 0, 0))
    pdf.Title('- Defense', coords=(20, 30), size=16, color=(0, 51, 102))
    pdf.image(f'{path}/defense.png', 20, 45, 160)
    pdf.Title('- Defensive Stats by Minute', coords=(20, 160), size=16, color=(0, 51, 102))
    pdf.image(f'{path}/defense_by_minute.png', 20, 175, 160)

    # Next Match Page
    if len(next_match_info) != 0:
        pdf.add_page()
        pdf.Title('Next Match Prediction', coords=(40, 10), size=20, color=(0, 0, 0))
        pdf.Title(next_match_info['teams'][0], coords=(25, 30), size=16, color=(0, 51, 102), border=1, center=True)
        pdf.Title(next_match_info['teams'][1], coords=(105, 30), size=16, color=(0, 51, 102), border=1, center=True)
        web_scraping_nba_logos(next_match_info['teams'][0], path)
        web_scraping_nba_logos(next_match_info['teams'][1], path)
        pdf.image(f'{path}/logo_{next_match_info["teams"][0].replace(" ", "_")}.png', 30, 45, 70)
        pdf.image(f'{path}/logo_{next_match_info["teams"][1].replace(" ", "_")}.png', 110, 45, 70)
        pdf.Title(next_match_info['odds'][0], coords=(25, 110), size=16, color=(0, 51, 102), center=True)
        pdf.Title(next_match_info['odds'][1], coords=(105, 110), size=16, color=(0, 51, 102), center=True)
        if float(next_match_info['odds'][0]) < float(next_match_info['odds'][1]):
            winner = next_match_info['teams'][0]
        else:
            winner = next_match_info['teams'][1]
        pdf.Title(f'The Predicted Winner is: {winner}', coords=(25, 130), size=14, color=(0, 51, 102))

    else:
        # If there are no matches left
        pdf.add_page()
        pdf.Title('Next Match Prediction', coords=(40, 10), size=20, color=(0, 0, 0))
        pdf.Title('No matches left', coords=(20, 30), size=16, color=(0, 51, 102))

    # Save PDF
    pdf.output(f'{name.replace(" ", "_")}_{season}.pdf', 'F')


if __name__ == "__main__":
    # Team Name and Season
    team = 'BOS'
    season = '2022'
    path = f'{team}_{season}_images'

    # Create a Directory with the Team Code to store the images
    directory(path)

    # Get DataFrames
    (df_players, df_schedules, df_player_stats, df_team) = get_dfs(team, season)

    # Get Team Colors and Name
    (colors, name) = get_team_info(df_team)

    # Get Team Logo
    web_scraping_nba_logos(name, path)

    # Create Graphs
    graphs(df_players, df_schedules, df_player_stats, path, colors, name)

    # Predict Next Match
    next_match_info = predict_winner(name)

    # Create PDF
    pdf(name, season, path, next_match_info)
