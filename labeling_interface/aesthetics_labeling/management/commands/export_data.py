import sqlite3
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import datetime
from django.core.management.base import BaseCommand, CommandError

datetime_format_string = "%Y-%m-%d %H:%M:%S.%f"

def export_text_answers(outfile):
    conn = sqlite3.connect('file:/u/sgoree/labeling_interface/labeling_interface/db.sqlite3?mode=ro', uri=True)
    c = conn.cursor()

    df = pd.DataFrame(
        c.execute("""
                  select user_id,email,question_1,question_2,question_3,question_4,completion_time
                  from aesthetics_labeling_textquestionresponse inner join aesthetics_labeling_participant 
                  on aesthetics_labeling_textquestionresponse.user_id = aesthetics_labeling_participant.id
                  """).fetchall(),
    columns=[
        'id',
        'email',
        'question_1',
        'question_2',
        'question_3',
        'question_4',
        'completion_time'

    ])

    questions = {
        'question_1': "how many choices are you given for each image pair? (just write a number. We're using this question to check for bot responses, if you answer strangely, you may not get paid.)",
        'question_2': "How are you choosing between images?",
        'question_3': "Do you find yourself relying more on the content of the images (like the objects or people pictured) or the style (like whether the picture is blurry or if it is colorful)?",
        'question_4': "Do you have any questions or comments for us?"
    }

    start_times = []
    for i in df.index:
        start_times.append(c.execute("""
        SELECT assigned_participant_id, MAX(finish_time)
        FROM aesthetics_labeling_comparisonassignment
        WHERE finish_time <= "{}" AND assigned_participant_id = {}
        """.format(df.loc[i,'completion_time'], df.loc[i, 'id'])).fetchall()[0][1])
    df['start_time'] = start_times
    df['duration'] = [(datetime.datetime.strptime(f, datetime_format_string)-datetime.datetime.strptime(s, datetime_format_string)).total_seconds()
                      if s is not None and f is not None else None
                      for i,(s,f) in df[['start_time', 'completion_time']].iterrows()
                     ]
    df.to_csv(outfile)
    
def export_comparisons(outfile):
    conn = sqlite3.connect('file:/u/sgoree/labeling_interface/labeling_interface/db.sqlite3?mode=ro', uri=True)
    c = conn.cursor()
    df = pd.DataFrame(
        c.execute("""
                  select assigned_participant_id,email,start_time,finish_time,reverse,label,image_a_id,image_b_id,common
                  from aesthetics_labeling_comparisonassignment
                  inner join aesthetics_labeling_participant on aesthetics_labeling_comparisonassignment.assigned_participant_id = aesthetics_labeling_participant.id
                  inner join aesthetics_labeling_comparison on aesthetics_labeling_comparisonassignment.comparison_id = aesthetics_labeling_comparison.id
                  where aesthetics_labeling_participant.ip != '' and label != 0
                  """).fetchall(),
        columns=[
            'participant_id',
            'email',
            'start_time',
            'finish_time',
            'reverse',
            'label',
            'image_a_id',
            'image_b_id',
            'common'
        ]
    )
    durations = []
    for i,(s,f) in df[['start_time', 'finish_time']].iterrows():
        if s is not None and f is not None:
            try:
                f_time = datetime.datetime.strptime(f, datetime_format_string)
            except ValueError as v:
                f_time = datetime.datetime.strptime(f, "%Y-%m-%d %H:%M:%S")
            try:
                s_time = datetime.datetime.strptime(s, datetime_format_string)
            except ValueError as v:
                s_time = datetime.datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
            durations.append((f_time-s_time).total_seconds())
        else:
            durations.append(None)
    df['duration'] = durations
    new_labels = []
    for i,(l,r) in df.loc[:,['label', 'reverse']].iterrows():
        if r == 1 and l == 2:
            new_labels.append(1)
        elif r == 1 and l == 1:
            new_labels.append(2)
        else:
            new_labels.append(l)
    df['label_with_reversed_taken_into_account'] = new_labels
    df.to_csv(outfile)

def export_image_data(outfile):
    conn = sqlite3.connect('file:/u/sgoree/labeling_interface/labeling_interface/db.sqlite3?mode=ro', uri=True)
    c = conn.cursor()
    df = pd.DataFrame(c.execute("""select * from aesthetics_labeling_image""").fetchall(), columns=('id','path','reported_by_user'))
    
    df['path'] = [s.split('/')[-1] for s in df['path']]
    
    df.to_csv(outfile)
    
class Command(BaseCommand):
    help = ('export data to two files using the current datetime')
        
    def handle(self, *args, **options):
        time_str = datetime.datetime.now().strftime("%Y-%m-%d-%H:%M:%S")
        export_text_answers('text_answers_export' + time_str + '.csv')
        export_comparisons('comparisons_export' + time_str + '.csv')
        export_image_data('images_export' + time_str + '.csv')