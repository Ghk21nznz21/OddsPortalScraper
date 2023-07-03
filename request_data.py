'''
Recives requests to be made (country, league_name, first year of request)
Loops requests from that first year untill current + future
Determines links for each request and delegates to LeagueSeasonPages
'''
import time
from dataclasses import dataclass, field
from datetime import date, timedelta, datetime

import pandas as pd
from selenium.webdriver.support.ui import Select

from Data.FetchNewData.OddsPortal.league_season import ManageSeasonPages

DATA_DIR = 'Data/NewData'


from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


@dataclass
class ManageRequests:
    ''' 
    @param requests: list[country:str, max_leagues: int, last_n_years: int]
            country --> name of the country to fetch data
            max_leagues --> fetch data from the top N leagues of that country
            last_n_years --> last N seasons/years of that to fetch 
        
    For each League will get data from every page of every season requested
    '''
    requests: list[str, str, int]
    games: list = field(init=False)

    def __post_init__(self):
        self.games = []
        self.DRIVER = webdriver.Chrome()

    def loop_requests(self):
        ''' Loop all requests wanted. Saving for every finished league /checkpoint '''
        for country, max_leagues, last_n_years in self.requests:
            print('Started')
            country = country.lower()
            for i in range(max_leagues):
                # Need to restore the driver to the country url (to find the leagues table)
                self.DRIVER.get(f"https://www.oddsportal.com/soccer/{country}")
                self.remove_add()
                # Get the top N leagues from this country 
                ul_element = self.DRIVER.find_element(
                    By.XPATH, "/html/body/div[1]/div/div[1]/div/main/div[2]/div[4]/div[2]/ul")
                li_elements = ul_element.find_elements(By.TAG_NAME, "li")
                if li_elements[i]:
                    li_elements[i].find_element(By.TAG_NAME, "a").click()
                    self.league(last_n_years)

    def league(self, last_n_years: int):
        ''' Gets all games from this league (*seasons, *pages) '''        
        self.remove_add()
        # Fetch all future matches 
        self.games.extend(self._get_games())
        self.DRIVER.execute_script("window.scrollTo(0, 0)")
        time.sleep(1)
     
        # Go to Past Matches/Archive"   
        Xpath = ''.join([
            "//a[contains(@class, 'h-8') and contains(@class, 'px-3') and contains(@class, 'px-3')",
            "and contains(@class, 'cursor-pointer') and contains(@class, 'flex-center')",
            "and contains(@class, 'bg-gray-medium') and contains(@href, 'result')]"
        ])
        results_button = WebDriverWait(self.DRIVER, 10).until(
            EC.element_to_be_clickable((By.XPATH, Xpath))
        )
        results_button.click()
        
        ## Loop seasons 
        season_divs = self.DRIVER.find_elements(
            By.XPATH, 
            "/html/body/div[1]/div/div[1]/div/main/div[2]/div[4]/div[2]/div[2]/a"
        )
        self.DRIVER.execute_script("window.scrollTo(0, 0)")  
        self.all_season_pages() 
        season_divs = "/html/body/div[1]/div/div[1]/div/main/div[2]/div[4]/div[2]/div[2]/a"
        # Starts at 1 (which is the current season and already runned this one, above)
        for i in range(2, last_n_years + 1):
            # to match initial location must scroll up first 
            self.DRIVER.execute_script("window.scrollTo(0, 0)")   
            try:
                season_div = self.DRIVER.find_element(By.XPATH, f'{season_divs}[{i}]')
                season_div.click()
            except TimeoutException:
                # This season dosent exist
                print('Failed Season', season_div.text)
                continue
            else:
                # loop season pages 
                self.all_season_pages()  
        # CHECKPOINT 
        df = pd.DataFrame(self.games, columns=[
                'Date', 'Team1_Name', 'Result',
                'Odd_V1', 'Odd_X', 'Odd_V2'])
        df.to_csv(f'{DATA_DIR}/OddsPortal.csv', index=False, mode='a')
        
            
    def all_season_pages(self):
        ''' Get all matches from every page of this season '''
        try: 
            WebDriverWait(self.DRIVER, 10).until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div.flex.flex-col.w-full.text-xs.eventRow"))
            )
        except TimeoutException:
            # No games on this season
            return None  
        time.sleep(1)  
        self.games.extend(self._get_games())
        not_end_page = self.next_button()
        while not_end_page:
            self.games.extend(self._get_games())
            not_end_page = self.next_button()
        return None 

    def remove_add(self):
        '''Remove ad that apears when whe enter oddsportal website '''
        try:
            add_button = WebDriverWait(self.DRIVER, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="onetrust-reject-all-handler"]'))
            )
            add_button.click()
            time.sleep(2)  # Wait for the ad to close completely
        except TimeoutException:
            # If the ad button is not found, no add is visible 
            pass

    def next_button(self):
        ''' Runs for every page after get_games --> already at page bottom '''
        Xpath = "/html/body/div[1]/div/div[1]/div/main/div[2]/div[5]/div[4]/div/div[3]/a[1]"
        return_value = True
        try: 
            next_page_button = WebDriverWait(self.DRIVER, 5).until(
                EC.presence_of_element_located((By.XPATH, Xpath))
            )
        except TimeoutException:
            return_value = False
        else: 
            next_page_button.click()
        finally:
            self.DRIVER.execute_script("window.scrollTo(0, 0)") 
            time.sleep(1)
            return return_value

    def _get_games(self):
        ''' Scroll to end and fetch all uploaded games 
        Saves games of that page  --> 
            date
            home team name
            result 
            odds
        '''
        # scroll to end
        for _ in range(3): 
            ActionChains(self.DRIVER).send_keys(Keys.END).perform()
            time.sleep(1)   # wait window to update 
            
        # fetch games 
        games = []
        print('hi')
        wait = WebDriverWait(self.DRIVER, 5)
        try:
            elements = wait.until(EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "div.flex.flex-col.w-full.text-xs.eventRow")))
        except TimeoutError:
            # no games 
            return games 
        else:
            for element in elements:
                # Only Count the direct Children Div
                # 2 Divs --> date, game info , last div = game
                # 1 Div --> game info (same date as row above)
                div_elements = element.find_elements(By.XPATH, "./div[contains(@class, 'border-black-borders')]")
                
                #div_elements = element.find_elements(By.CSS_SELECTOR, "> div.border-black-borders")
                size = len(div_elements)
                if size > 1:  
                    game_date = div_elements[0].text.split('\n')[0]
                    game_date = self.handle_date_format(date)
                row = div_elements[-1].text.split('\n')
                if len(row) == 8:
                    # dosent have a result --> future game, or game never happened
                    _, team1, _, _, v1, x, v2, _ = row
                    result = None 
                    if game_date < date.today():
                        # Cancelled or Interruped 
                        continue
                elif len(row) == 10:
                    _, team1, team1_result, _, team2_result, \
                        _, v1, x, v2, _ = row 
                    result = self.declare_winner(team1_result, team2_result)
                else:
                    print('ERROR', row)
                print(game_date, team1, result, v1, x, v2)
                games.append([game_date, team1, result, v1, x, v2])
        return games

    @staticmethod
    def handle_date_format(game_date: str):
        ''' String format to -> year-month-day'''
        substring = game_date.split(" ")[0]
        if 'Yesterday' in substring:
            yesterday = date.today() - timedelta(days=1)
            return yesterday.strftime('%Y-%m-%d')
        if 'Today' in substring:
            return date.today().strftime('%Y-%m-%d')
        if 'Tomorrow' in substring:
            tomorrow = date.today() + timedelta(days=1)
            return tomorrow.strftime('%Y-%m-%d')
        return datetime.strptime(game_date, '%d %B %Y').strftime('%Y--%m-%d')

    @staticmethod
    def declare_winner(v1: str, v2) -> int:
        ''' 
        @param v1: number of goals
        @param v2: number of goals
        @return: match outcome 
            1 = home team won
            0 = draw
            2 = away team won
        '''
        try:
            v1 = int(v1)
            v2 = int(v2)
        except ValueError:
            return None
        if v1 == v2:
            return 0
        if v1 > v2:
            return 1
        return 2