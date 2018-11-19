#!/usr/bin/env python
import pandas as pd
import matplotlib.pyplot as plt
import requests
import re
from datetime import datetime #, timedelta
import numpy as np
import holidays
import os

import infra.trello_api.trello_api as api
from resources.config import Config

def burnup_service(sprint_dt_start, trello_board):
    # When the card creation date is unknown, or is from a previous sprint, 
    # then we will use the sprint start date
    sprint_start = sprint_dt_start.strftime('%Y-%m-%dT%H:%M:%S.%fz')
    
    cards = api.get_cards(sprint_start, trello_board)
    
    # Create columns urgent and unplanned after the labels contained in the card
    cols = ['task', 'urgent', 'unplanned', 'idList', 'create_date', 
        'last_move_date']
    df = pd.DataFrame(columns=cols)

    for c in cards:    
        labels = [l['name'] for l in c['labels']]
        
        df.loc[len(df)] = [
            c['name'], 'URGENT' in labels, 'UNPLANNED' in labels,
            c['idList'], c['create_date'], c['last_move_date']]

    # Convert types of columns urgent, unplanned, last_move_date, create_date 
    # and task
    df.loc[:, 'task'] = df.loc[:, 'task'].astype(str)
    df[['create_date']] = pd.to_datetime(df[['create_date']].stack(), 
        format='%Y-%m-%dT%H:%M:%S.%fz').unstack()
    df[['last_move_date']] = pd.to_datetime(df[['last_move_date']].stack(), 
        format='%Y-%m-%dT%H:%M:%S.%fz').unstack()
    df['urgent'] = df['urgent'].astype(bool)
    df['unplanned'] = df['unplanned'].astype(bool)

    # Join the dataframe df with the lists dataframe by idList column, 
    # into the df variable.
    df_lists = _get_list_df()
    df = df_lists.join(df.set_index('idList'), on='idList', rsuffix='_2')

    # Normalize the date columns into day columns
    df['create_day'] = pd.to_datetime(df['create_date']).dt.normalize()
    df['last_move_day'] = pd.to_datetime(df['last_move_date']).dt.normalize()

    # Remove EPIC tasks from dataframe
    df = df[df['task'].str.extract('(EPIC)').isna()[0]]

    # Extract from task name the value for expected and final, and created the 
    # respective column for each task
    df.loc[:, 'expected'] = \
        df['task'].str.extract('^\((\d*\.\d+|\d+|\?)+\).*', expand=False)
    df.loc[:, 'final'] = \
        df['task'].str.extract('\[(\d*\.\d+|\d+)+\]$', expand=False)
    
    # Dump df to json
    df.to_json('./df.json', orient='table')

    df_points = _calc_points(df)
    # Dump df_points to json
    df_points.reset_index(drop=True).to_json('./df_plot.json', orient='table')

    df_group = _aggregate_points(sprint_dt_start, df_points)

    df_group = _drop_non_working_days(df_group)
    df_group.index = df_group.index.strftime('%d-%m')
    # Dump df_group to json
    df_group.to_json('./df_group.json', orient='table')

    _print_stats(df_points)
    

def _get_list_df():
    """
    Match lists' names to find if it is type 'SELECTED', 'RDY', 'DONE' and 
    'IN PROGRESS', and also the sprint for the list (which is either 1 number 
    or 2 separated by "/"). A dataframe is created with the idList, sprint 
    ]discovered and status.

    Lists with different names, such as "Regras", are ignored.
    """

    # Build a dictionary for the board lists (that aren't closed).
    board_lists = api.get_lists(Config.TRELLO_BOARD)
    lists = {}
    [lists.update({l['id']: l['name']}) for l in board_lists if not l['closed']]

    #FIXME: Remove this double equals?
    cols = ['idList', 'sprint', 'status']
    df_lists = pd.DataFrame(columns=cols)

    sprint_name = None

    for k, v in lists.items():
    #     print((k, v))
        sprint = None
        
        match = re.search('^SELECTED.*([0-9]{2})(/[0-9]{2})', v)
        status = 'SELECTED'
        if match is None:
            match = re.search('^SELECTED.*([0-9]{2})', v)
            status = 'SELECTED'
            
        if match is None:
            match = re.search('^RDY.*([0-9]{2})(/[0-9]{2})', v)
            status = 'RDY'
        if match is None:
            match = re.search('^RDY.*([0-9]{2})', v)
            status = 'RDY'
            
        if match is None:
            match = re.search('^DONE.*([0-9]{2})(/[0-9]{2})', v)
            status = 'DONE'
        if match is None:
            match = re.search('^DONE.*([0-9]{2})', v)
            status = 'DONE'
            
        if match is None:
            match = re.search('IN PROGRESS', v)
            status = 'IN PROGRESS'
            sprint = ''
            
        # If cannot match anything, the this list doesn't matter
        if match is None:
            continue
        
        # If a match has happened and sprint is None, then get the sprint for the list
        # "IN PROGRESS" match fill it with empty space because it doesn't come with sprint
        if match is not None and sprint is None:
            sprint = match.group(1)
            # print(match.groups())
            if len(match.groups()) > 1 and match.group(2) is not None:
                sprint += match.group(2)
                
            # Get sprint name just to use later in the plot
            if not sprint_name:
                sprint_name = sprint
        
        # Add to df_lists 
        if sprint is not None:
            df_lists.loc[len(df_lists)] = [k, sprint, status]
    
    return df_lists

def _calc_points(df):
    """
    Create dataframe dt_plot after the df to format the data for plotting.

    As the expected column may have "?" or NA value, we replace with the column 
    with final points value. If the final column does not contain any value, 
    then we drop these rows.

    We create a "day" column and depending on the status of the task it's set 
    differently. We consider the task in "RDY" or "DONE" as done, and the 
    "SELECTED" and "IN PROCESS" as not done.

    If the task is done but doesn't have any value in final column, we set it 
    as the expected column. The remaining that are NA we set as zero.

    The result is a dataframe with all expected and final values filled.
    """

    df_points = df[['task', 'expected', 'final', 'create_day', 'last_move_day', 
        'status', 'sprint', 'unplanned']]

    # Set missing expected points with final, if it exists
    without_points = \
        ((df_points['expected'] == '?') | (df_points['expected'].isna())) \
        & (~df_points['final'].isna())
    df_points.loc[without_points, 'expected'] = df_points.loc[without_points, 
        'final']

    # Drop when value of expected is NA or "?"
    df_points.dropna(subset=['expected'])
    df_points = df_points[df_points['expected'] != '?']

    df_points = df_points.set_index('task', drop=False)

    #In case a task without final value is RDY or DONE, we fill final values 
    # with expected, otherwise we fill it with zero
    is_done = df_points['status'].isin(['RDY', 'DONE'])
    df_points.loc[is_done, 'day'] = df_points.loc[is_done, 'last_move_day']
    df_points.loc[~is_done, 'day'] = df_points.loc[~is_done, 'create_day']
    df_points.loc[is_done, 'final'] = df_points.loc[is_done, 'final']\
        .fillna(df_points['expected'])
    df_points.loc[:, 'final'] = df_points['final'].fillna(0)

    df_points = df_points.set_index('day', drop=False)

    df_points.loc[:, 'expected'] = pd.to_numeric(df_points['expected'])
    df_points.loc[:, 'final'] = pd.to_numeric(df_points['final'])

    return df_points

def _aggregate_points(sprint_dt_start, df_points):
    """
    A new dataframe called df_group is created after the df_points with the sum of
    final values and grouped by day.
    """

    df_group = pd.DataFrame(columns=['expected','final'],
        index=pd.date_range(start=sprint_dt_start, periods=12, name='day'))
    
    df_group['expected'] = \
        df_points['expected'].groupby([df_points['create_day']]).sum()
    df_group['expected'] = df_group['expected'].fillna(0)

    df_group['final'] = \
        df_points['final'].groupby(df_points['last_move_day']).sum()
    df_group['final'] = df_group['final'].fillna(0)

    #TODO: VERIFY IF THERE IS final VALUES FOR SOME DATE BUT NO expected VALUE 
    # WITH THE SAME DATE IF IT DOES APPEAR IN GROUP BY
    df_group['expected'] = np.cumsum(df_group['expected'])
    df_group['final'] = np.cumsum(df_group['final'])

    return df_group

def _drop_non_working_days(df_group):
    """
    Drop weekend and non working days in Rio de Janeiro
    """
    # TODO: ALLOW TO CONFIGURE TO ANY CITY

    filters = lambda x: x if x.day.date() not in holidays.BR(state='RJ') \
            and x.day.dayofweek // 5 == 0 else None

    df_group = df_group.reset_index().\
        apply(filters, axis=1).\
        dropna().\
        set_index('day')
    
    return df_group

def _plot_burnup(df):
    fig, ax = plt.subplots(figsize=[9, 7])
    ax.plot(df.loc[:, ['expected', 'final']], drawstyle='steps-mid')
    plt.xticks(rotation=25)

    x = df.index
    y = np.linspace(0, df['expected'].max(), df.count()[0])
    ax.plot(x, y, dashes=[10, 5, 10, 5])

    ax.legend(['expected', 'accomplished', 'ideal'])
    plt.title('burnup sprint 45/46')
    plt.xticks(df.index)
    plt.show()

def _print_stats(df):
    """
    Prints in console stats from data
    """
    df_done = df[df['status'].isin(['RDY', 'DONE'])]
    df_not_done = df[~df['status'].isin(['RDY', 'DONE'])]
    
    print('Tasks: {}'.format(df.count().max()))

    print('Waiting tasks: {}'.format(df_not_done.count().max()))
    print('Waiting points (expected): {}'.format(df_not_done['expected'].sum()))

    print('Done tasks: {}'.format(df_done.count().max()))
    print('Done points (expected): {}'.format(df_done['expected'].sum()))
    print('Done points (informed): {}'.format(df_done['final'].sum()))