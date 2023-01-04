# NBA TEAM ANALYSIS


## NBA Season Report using SportsData API and Matplotib's Pyplot and Next Match Prediction using Web Scraping through BeautifulSoup (ETL) loaded into a PDF File with FPDF

This project creates report which contains a given NBA team's season statistics and a prediction of the next match. The data for the statistics is extracted from the SportsData API. We call different endpoints to get the data needed: from the team's basic information to each player's individual field statistics. The information is displayed through different plots using Pyplot. Then we make a prediction of the next match's result using Web Scraping through BeautifulSoup. It is based on the ETL structure

<br />

***
## - **Code**

1. ETL - NBA Stats
    - EXTRACT
        - [SportsData API](https://sportsdata.io/) - API used to get the data for the team.
        We extract the data using the *get* funtion from the *requests* library. The data is in JSON format so we use the *.json()* function to convert it to a dictionary. We then convert it do a Pandas DataFrame for easier manipulation.

    - TRANSFORM
        - We transform the data mostly in the *get_dfs* function, where we create other columns such as the 'winner' in the 'df_schedule' DataFrame, or filter on the given team. 
        - The most important part of the transformation is done in the *graphs* function, where we create the plots for the report and load them into the images folder, previously created. The plotting is done using Matplotlib's Pyplot library. We create a plot for each statistic. The most used are pie and bar charts(normal, stacked and grouped), but a table is also used.
        - For the Team Logo we have created a function that uses web scraping to extract the teams's logo for the cover and the prediction (later explained)
    
    - LOAD
        - The data is loaded into a PDF File. We use the *Fpdf* library to create the file and create an FPDF class has two functions: 'Title' and 'Cover' that take different arguments for personalization. Then the PDF is created in the 'pdf' funcion, where all the pages are added.

<br />

2. ETL - Next Match Prediction
    - EXTRACT
        - [Sporty Trader](https://www.sportytrader.es/cuotas/baloncesto/usa/nba-306/) - Web Scraping
        We extract the data with the *requests* library

    - TRANFORM
        - We  convert the data into a soup object. then use the *find* and *find_all* functions to find the divs we need. We then return this data as a dictionary with the keys: 'teams', 'odds' and 'date'

    - LOAD
        - We load the data into the PDF file. We print the teams' logos and the odds for each team. We print the winner, which will be the team with the highest odds.

<br />

***
## - **Usage**

###     **Requirements**

*requiretments.txt* file is included in the repository. To install the requirements, run the following command:

> pip install -r requirements.txt

###     **Instructions**

The SportsData API key is blank, for usage you need to get your own API key from [SportsData](https://sportsdata.io/) and insert the key in the *config.txt* file as it follows: API KEY = your_key (witout quotation marks)

The team and season are initially set to the Boston Celtics 2022 season, but you can change them to any team and season you want introducing the code of the team and season in the main function.

###     **Example**

An example of the PDF file is included in the repository ([Example_Boston_Celtics_2022.pdf](Example_Boston_Celtics_2022.pdf)), as well as the images folder needed. 


<br />

**AUTHOR - Ignacio Bayón Jiménez-Ugarte**
