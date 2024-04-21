import streamlit as st
import sqlite3
import pandas as pd 
import json 
import os
from datetime import date
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from datetime import datetime

SPREADSHEET_ID = '1QgiTl4XhDOKkbhQZJvwi9ZKsbw5z1YcFoj3QEeUOetw'
SERVICE_ACCOUNT_FILE = 'credentials.json'


credentials = Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
    scopes=['https://www.googleapis.com/auth/spreadsheets']
)
service = build('sheets', 'v4', credentials=credentials)


pd.set_option('display.max_rows', None)        # or set a large number if you want to limit it
pd.set_option('display.max_columns', None)     # or set a large number if you want to limit it
pd.set_option('display.max_colwidth', None)    # to display full content of each cell without truncation

def function_to_save_data(df, sent_selction_columns, data_frame, index, SentListColumn, metric_score):
    #NEW TABLE TO WRITE METRIC SCORE
    sent_selction_columns_copy = sent_selction_columns.copy()
    sent_selction_columns_copy.append(("metric_score"))
    sheet_metadata = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
    sheets = sheet_metadata.get('sheets', '')
    titles = [sheet['properties']['title'] for sheet in sheets]
    for metric in sent_selction_columns_copy:
        df_columns = data_frame.columns.tolist()
        #fix set shuffle
        common_columns_set = set(df_columns) - (set(sent_selction_columns_copy))
        common_columns = []
        for col in df_columns:
            if col in common_columns_set:
                common_columns.append(col)
        row = data_frame[list(common_columns)].iloc[index]
        row = row.to_dict()
        row[SentListColumn] = " && ".join(list(row[SentListColumn]))
        row["annotator_id"] = annotator_name + str(index)
        row["annotator_name"] = annotator_name
        utc_now = datetime.utcnow()
        row['time_of_annotation'] = utc_now.strftime('%Y-%m-%d %H:%M:%S')
        st.write(metric)
        # st.write(type(metric))
        if metric=='metric_score':
            row[metric] = metric_score
        else:
            row[metric] = " && ".join(list(df[metric]))
        st.write(row.keys())
        if metric not in titles:
            body = {
                "requests": [{
                    "addSheet": {
                        "properties": {
                            "title": f"{metric}"
                        }
                    }
                }]
            }
            service.spreadsheets().batchUpdate(spreadsheetId=SPREADSHEET_ID, body=body).execute()
            header = list(row.keys())
            request = service.spreadsheets().values().append(
                spreadsheetId=SPREADSHEET_ID,
                range=metric,
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body={'values': [header]}
            )
            response = request.execute()
        row = [[x for x in row.values()]]
        st.write(row)
        request = service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=metric,
            valueInputOption='RAW',
            insertDataOption='INSERT_ROWS',
            body={'values': row}
        )
        response = request.execute()
        print(response)


def display_dataframe_with_checkboxes(df, SentListColumn):
    # Create a dictionary to hold the checkbox states
    checkbox_states = {}

    # Display the column names
    st.write("DataFrame with Checkboxes:")
    col_names = st.columns(len(df.columns))
    for i, column_name in enumerate(df.columns):
        col_names[i].write(column_name)

    # Display the DataFrame with checkboxes
    for index, row in df.iterrows():
        cols = st.columns(len(df.columns))
        for i, (column_name, cell_value) in enumerate(row.items()):
            with cols[i]:
                # Display the sentence as text without a checkbox
                if column_name == SentListColumn:
                    st.markdown(str(cell_value))

                elif str(cell_value) == "-":  # Check if the value is "-" and display text without a checkbox
                    st.text(str(cell_value))
                    
                else:
                    # Display checkbox with the value on the same line
                    # st.write(str(cell_value), unsafe_allow_html=True)
                    checkbox_key = f"{column_name}_{index}"
                    # Display a checkbox on the same line
                    checked = st.checkbox(str(cell_value), key=checkbox_key)
                    checkbox_states[checkbox_key] = checked
    
    return checkbox_states


def function_to_query_data(data_frame, 
                           TEXT_ID, index,
                           SentListColumn, 
                           sent_selection_columns):

    # SentListColumn = 'Review-Tnltk'
    # sent_selection_columns = [
    #     'Review-Tnltk.HphyG4', 
    #     'Review-Tnltk.HphyG4.AopenG4',
    # ]
    review_row = data_frame.iloc[index]

    total_sentences = len(review_row[SentListColumn])
    sentences = review_row[SentListColumn].copy()

    column_to_sentencelist = {
        SentListColumn: sentences,
    }
    for sent_selection_column in sent_selection_columns:
        li = ['NaN'] * total_sentences
        for x in review_row[sent_selection_column]:
            li[x] = sentences[x]
        column_to_sentencelist[sent_selection_column] = li

    df_row = pd.DataFrame(column_to_sentencelist)
    return df_row       


if __name__ == "__main__":

    st.title("Annotation Site")
    data_frame = pd.read_pickle("new_llm_data.pkl")
    st.write(list(data_frame.columns))
    

    annotator_name = st.text_input('Annotator Name')
    TEXT_ID = st.text_input('TEXT_ID', 'ReviewID')
    index = int(st.text_input('index', '0'))
    
    SentListColumn = st.text_input('SentListColumn', 'Review-Tnltk')
    sent_selection_columns = st.text_input('sent_selection_columns', 'Review-Tnltk.HphyG4, Review-Tnltk.HphyG4.AopenG4')
    sent_selection_columns = sent_selection_columns.split(', ')
    
    text_id_value = data_frame.iloc[index][TEXT_ID]
    st.write('The text_id_value is', text_id_value)

    df = function_to_query_data(data_frame, 
                                TEXT_ID, index,
                                SentListColumn, 
                                sent_selection_columns)

    df = df.copy()
    checkbox_states = display_dataframe_with_checkboxes(df, SentListColumn)
    metric_score = st.text_input('Metric Score')

    set_of_null_values = {"NaN","nan","0","0.0"}

    if st.button('Submit'):

        #checks if name is blank or not
        if annotator_name == "":
            st.error("Please fill the annotator name")

        #checks if the metric score is filled or not
        if metric_score=="":
            st.error("Please fill metric score")
        
        for key in checkbox_states:

            column_name, row_index = key.rsplit('_', 1)
            row_index = int(row_index)

            #For debugging
            # if checkbox_states[key]:
            #     st.write(f"Checkbox for {column_name} in row {row_index} is checked and is {df[column_name].iloc[row_index]}")
            #     st.write(df[column_name])
            
            if checkbox_states[key]:
                i = sent_selection_columns.index(column_name)
                df[column_name].iloc[row_index] = str(df[column_name].iloc[row_index])

                if df[column_name].iloc[row_index] in set_of_null_values:
                    df[f"{column_name}"].iloc[row_index] = df[SentListColumn].iloc[row_index]
                else:
                    # st.write("IN ELSE, should make ",df[column_name].iloc[row_index]," null value")
                    for j in range(i, len(sent_selection_columns)):
                        df[f"{sent_selection_columns[j]}"].iloc[row_index] = "nan"

            #For debugging
            # if checkbox_states[key]:
            #     st.write(f"Checkbox for {column_name} in row {row_index} is now {df[column_name].iloc[row_index]}")
            
        print("function to save df is triggered")
        st.write(df)
        # df.to_csv('xxxx')
        function_to_save_data(df, sent_selection_columns, data_frame, index, SentListColumn, metric_score)


        d = {}
        d['annotator_name'] = annotator_name
        d['annotation_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        d[TEXT_ID] = text_id_value
        d['metric_score'] = metric_score
        sentences =  df[SentListColumn].tolist()
        d[SentListColumn] = sentences
        for column in sent_selection_columns:
            d[column] = [idx for idx, sent in enumerate(sentences) if sent in df[column].tolist()]

        st.write(d)
