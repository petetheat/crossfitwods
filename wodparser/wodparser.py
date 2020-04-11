from bs4 import BeautifulSoup
import sys
import requests
import pandas as pd
import re
import networkx as nx
import matplotlib.pyplot as plt
from collections import Counter


class WodParser:
    def __init__(self, dates):
        self.wods_raw, self.failed_dates = self.get_wods(dates)
        self.wods_clean = self.clean_wods()

        self.wods = []

        for i in self.wods_clean.keys():
            if list(self.wods_clean[i]):
                self.wods.append(list(self.wods_clean[i]))

        self.df, self.movements = self.get_df()

    def get_wods(self, dates):
        wods = {}
        n_dates = len(dates)
        failed_dates = []
        for i, da in enumerate(dates):
            url = r'https://www.crossfit.com/workout/%s' % da.strftime('%Y/%m/%d')

            r = requests.get(url)
            data = r.text
            soup = BeautifulSoup(data, features="lxml")
            x = soup.find_all('div', {"class": 'content'})
            try:
                wod = x[0].select('p')[0].get_text() + x[0].select('p')[1].get_text()
                if x[0].select('p')[0].get_text() != 'Rest Day':
                    wods[da.strftime('%Y/%m/%d')] = wod
            except:
                try:
                    x = soup.find_all('div', {"class": '_6zX5t4v71r1EQ1b1O0nO2 jYZW249J9cFebTPrzuIl0'})
                    wod = x[0].select('p')[0].get_text() + x[0].select('p')[1].get_text()
                    if x[0].select('p')[0].get_text() != 'Rest Day':
                        wods[da.strftime('%Y/%m/%d')] = wod
                except:
                    print('\nSomething did not work for %s' % da.strftime('%Y/%m/%d'))
                    failed_dates.append(da.strftime('%Y/%m/%d'))

            sys.stdout.write("\rParsing %4.1f%%" % ((i + 1) / n_dates * 100))

        return wods, failed_dates

    def clean_wods(self):
        print('yo')
        wod_regex1 = '(pull|push|muscle|(ghd\s)?sit|handstand push)[-]?up|(front[\s]?|back[\s]?|overhead[\s]?|single(-|\s)leg[\s]?|one(-|\s)legged[\s]?)?squat(\sclean|\ssnatch)?|wall(-|[\s])?ball|(sumo\s)?dead[\s]?lift'
        wod_regex2 = '|(shoulder|push|bench|sots|split)\s(press|jerk)|(hip|back)[\s]?extension|knee[s]?(-|\s)to(-|\s)elbow|sprint|rope\sclimb|dip|swim|bike|handstand\swalk|turkish\sget[-]?up|wall(-|\s)?walk|(kettlebell\sswing)'
        wod_regex3 = '|(bent\sover(\sbarbell)?\s)?row|pistol|(power\s|dumbbell\s)?(clean|snatch(es)?)(\sbalance|(\sand\s|\s&\s)jerk)?|(box\s)?step(-|\s)up|(single|double|triple)[-]?under|thruster'
        wod_regex4 = '|run|burpee(\s)?(box(-|\s)jump[\s]?(over)?)?|(walking\s)?lunge|(broad)[-]?jump|(toes(-|\s)to(-|\s)bar)|plank|l(-|\s)sit'

        wod_regex = wod_regex1 + wod_regex2 + wod_regex3 + wod_regex4

        wods_clean = {}

        for w in self.wods_raw.keys():
            matches = re.finditer(wod_regex, self.wods_raw[w], re.MULTILINE | re.IGNORECASE)

            wod_movements = set()
            for matchNum, match in enumerate(matches, start=1):
                wod_movements.add(match.group().lower())

            wod_movements = [mv.replace(' ', '').strip() for mv in wod_movements]
            wod_movements = [mv.replace('-', '').strip() for mv in wod_movements]
            wod_movements = [mv.replace('snatches', 'snatch') for mv in wod_movements]
            wod_movements = [mv.replace('bentoverbarbell', 'bentover') for mv in wod_movements]
            wod_movements = [mv.replace('singlelegsquat', 'pistols') for mv in wod_movements]
            wod_movements = [mv.replace('oneleggedsquat', 'pistols') for mv in wod_movements]
            wod_movements = [mv.replace('pistols', 'pistol') for mv in wod_movements]
            wod_movements = [mv.replace('&', 'and') for mv in wod_movements]
            wods_clean[w] = wod_movements

        return wods_clean

    def get_df(self):
        movement_counter = Counter()
        for wod in self.wods:
            for movement in wod:
                movement_counter[movement] += 1

        df = pd.DataFrame(movement_counter.most_common(), columns=['Movement', 'Counts'])
        df['Percentage'] = df['Counts'] / len(self.wods) * 100

        movements = list(movement_counter.keys())

        return df, movements

    def plot(self):
        fig, ax = plt.subplots(figsize=(20, 20))
        mygraph = nx.Graph()

        options = {'node_color': 'red',
                   'node_size': 100,
                   'width': 1,
                   'edge_color': '#8c8c8b'}

        # add nodes
        for movement in self.movements:
            mygraph.add_node(movement)

        edges = []
        for movement in self.movements:
            for wod in self.wods:
                if movement in wod:
                    for second_movement in wod:
                        if movement != second_movement:
                            edges.append((movement, second_movement))

        for edge in edges:
            mygraph.add_edge(edge[0], edge[1])

        pos = nx.spring_layout(mygraph)
        nx.draw(mygraph, pos, ax=ax, **options)

        for i in pos:
            ax.text(pos[i][0], pos[i][1], i, fontsize=12)

        # show graph
        plt.show()


if __name__ == "__main__":
    w = WodParser()
