import Robogame as rg
import networkx as nx
import altair as alt
import time, json
import pandas as pd
import numpy as np
import nx_altair as nxa
import matplotlib.pyplot as plt
import streamlit as st

st.title("BEJK Robogames Dashboard")

node_num = st.number_input("Enter Robot ID of Interest: ", step = 1)





game = rg.Robogame("bob")
game.setReady()
while(True):
    gametime = game.getGameTime()
    timetogo = gametime['gamestarttime_secs'] - gametime['servertime_secs']
    
    if ('Error' in gametime):
        print("Error"+str(gametime))
        break
    if (timetogo <= 0):
        print("Let's go!")
        break
        
    print("waiting to launch... game will start in " + str(int(timetogo)))
    time.sleep(1) # sleep 1 second at a time, wait for the game to start

robot_interest = st.text_input(
        label='Robot Interest',
        value='',
        placeholder='Enter ID,ID,ID (no spaces)'
    )

bets = st.text_input(
    label='Bets',
    value='',
    placeholder='Enter ID:Bet,ID:Bet (no spaces)'
)
if bets != '':

    bets_list = bets.split(',')
    bets_dict = {}
    for x in bets_list:
        bet = x.split(':')
        bets_dict[bet[0]] = int(bet[1])
    game.setBets(bets_dict)

    interest_list = robot_interest.split(',')
    game.setRobotInterest(interest_list)

robots = game.getRobotInfo()
network = game.getNetwork()


new_links = []
node_id = int(node_num)
for d in network['links']:
    if d['source'] == node_id:
        new_links.append(d)
new_nodes = []
for link in new_links:
    for n in network['nodes']:
        if n['id'] == link['target']:
            new_nodes.append(n)
node_network = {'directed': False,
               'graph': [],
               'links': new_links,
               'multigraph': False,
               'nodes': new_nodes}

nodenet = nx.node_link_graph(node_network)
node_pos = nx.kamada_kawai_layout(nodenet)
for n in nodenet.nodes():
    nodenet.nodes[n]['id'] = n
    nodenet.nodes[n]['name'] = robots.iloc[n]['name']
    nodenet.nodes[n]['winningTeam'] = robots.iloc[n]['winningTeam']
draw = nxa.draw_networkx(G=nodenet, pos=node_pos, node_tooltip=['id', 'name', 'winningTeam'], node_color='winningTeam')

def make_viz(node):
    game.getHints()
    robots = game.getRobotInfo()
    hints = game.getAllPredictionHints()
    hints_df = pd.DataFrame(hints)
    prod = robots[robots.Productivity >0]
    unprod = robots[robots.Productivity < 0]
    line = alt.Chart(hints_df).mark_line().transform_filter(
        alt.datum['id'] == node
    ).encode(
        x=alt.X('time:Q'),
        y=alt.Y('value:Q'),
        color = 'id:N'
    ).properties(
        width=800,
        height=500
    )
    circles = alt.Chart(hints_df).mark_point().transform_filter(
        alt.datum['id'] == node
    ).encode(
        x=alt.X('time:Q'),
        y=alt.Y('value:Q'),
        color = 'id:N',
        tooltip = ['id', 'time', 'value']
    )
    v_line = alt.Chart(robots).mark_rule(color='black').transform_filter(
        alt.datum['id'] == node
    ).encode(
        x='expires',
        tooltip = ['id', 'expires']
    )
    lines = alt.layer(line, circles, v_line)
    return lines
# node_num = st.number_input("Enter Robot ID of Interest: ", step = 1)
viz_line = make_viz(node_num)


tree = game.getTree()
genealogy = nx.tree_graph(tree)
from networkx.drawing.nx_pydot import graphviz_layout
position = nx.nx_agraph.graphviz_layout(G=genealogy, prog='dot')
for n in genealogy.nodes():
    genealogy.nodes[n]['id'] = n
    genealogy.nodes[n]['name'] = robots.iloc[n]['name']
    genealogy.nodes[n]['winningTeam'] = robots.iloc[n]['winningTeam']
cond = alt.condition(alt.datum.id == node_num, if_true=alt.value(1.0), if_false=alt.value(0.5))
robot_tree = nxa.draw_networkx(G=genealogy, pos=position, node_tooltip=['id', 'name', 'winningTeam'],
                               node_color='winningTeam')
robot_tree = robot_tree.encode(opacity=cond)

prod = robots[robots.Productivity >0]
unprod = robots[robots.Productivity < 0]
pos=alt.Chart(prod).mark_bar().encode(
    alt.X("id:N", sort = '-y', title = ''),
    alt.Y('Productivity', scale=alt.Scale(domain=[0, 100]), title = '')
)
neg=alt.Chart(prod).mark_bar(color = 'red').encode(
    alt.X("id:N", sort = '-y'),
    alt.Y('Productivity'),
    tooltip = ['id', 'Productivity']
)
bar = alt.layer(pos, neg).properties(width = 800)

draw & viz_line & robot_tree & bar