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

def function_to_query_data(raw_text_id, task_to_dbpath, db_folder):
    result_dict = {}
    for taskname, dbfile in task_to_dbpath.items():
        database_path = os.path.join(db_folder, dbfile)
        print(database_path)
        conn = sqlite3.connect(database_path)
        print(database_path)
        df = pd.read_sql_query(f"SELECT * FROM TaskAction WHERE raw_text_id = '{raw_text_id}';", conn)
        if len(df) != 1:
            print(f'For task {taskname}, the raw_text_id {raw_text_id} is not available / not unique')
            result_dict[taskname] = '{}' 
        else:
            row = df.iloc[0].to_dict()
            result = row['result']
            result_dict[taskname] = result
    data = result_dict.copy()
    for key in data:
        print(key)
        data[key] = json.loads(data[key])
    df = pd.DataFrame.from_dict(data, orient='index').transpose()
    df = df.reindex(columns=[i for i in task_to_dbpath])

    for col in reversed(df.columns[1:]):
        prev_col = df.columns[df.columns.get_loc(col) - 1]
        df[col] = df.apply(lambda row: 0 if pd.notna(row[prev_col]) and pd.isna(row[col]) else row[col], axis=1)

    df = df.rename_axis("Sentence")

    return df.reset_index()

def function_to_save_data( df_new, db_folder_old ,db_folder_new, task_to_dbpath):
    result_dict = {}
    for taskname, dbfile in task_to_dbpath.items():
        database_path = os.path.join(db_folder_old, dbfile)
        conn = sqlite3.connect(database_path)
        df = pd.read_sql_query(f"SELECT * FROM TaskAction WHERE raw_text_id = '{raw_text_id}';", conn)
        if len(df)!=1 and taskname == "idx2MetricScore_TraitScore":
            database_path = os.path.join(db_folder_old, task_to_dbpath["idx2Sentence"])
            conn = sqlite3.connect(database_path)
            df = pd.read_sql_query(f"SELECT * FROM TaskAction WHERE raw_text_id = '{raw_text_id}';", conn)
            df.loc[:,"taskname"] = "idx2MetricScore"
        if len(df) != 1:
            print(f'For task {taskname}, the raw_text_id {raw_text_id} is not available / not unique')
            result_dict[taskname] = '{}'
        else:
            row = df.iloc[0].to_dict()
            new_res = df_new.set_index('Sentence')[taskname].to_dict()
            print(row["result"])
            print(f"should be for db {taskname}")
            print(new_res)
            new_res_string = json.dumps(new_res)
            row["result"] = new_res_string
            row["annotator_id"] = annotator_name+row["raw_text_id"]
            row["annotator_name"] = annotator_name
            utc_now = datetime.utcnow()
            row['time_of_annotation'] = utc_now.strftime('%Y-%m-%d %H:%M:%S')
            print("row is")
            row = [[x for x in row.values()]]
            print(row)
            request = service.spreadsheets().values().append(
                spreadsheetId=SPREADSHEET_ID,
                range=taskname,
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body={'values': row}
            )
            response = request.execute()
            print(response)

            # new_df = pd.DataFrame([row], index = [0])
            # database_path = os.path.join(db_folder_new, dbfile)
            # conn = sqlite3.connect(database_path)
            # new_df.to_sql('TaskAction', conn, index=False, if_exists='append')
            # conn.close()

def function_to_empty_db(checkbox_states, df, db_folder_new, task_to_dbpath):
    if st.button('Submit'):
        for key in checkbox_states:
            column_name, row_index = key.rsplit('_', 1)
            row_index = int(row_index)
            if checkbox_states[key]:
                st.write(df[column_name].iloc[row_index])
                for taskname, dbfile in task_to_dbpath.items():
                    database_path = os.path.join(db_folder_new, dbfile)
                    conn = sqlite3.connect(database_path)
                    print(database_path)
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM TaskAction")
                    conn.commit()
                    conn.close()

def display_dataframe_with_checkboxes(df):
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
                # if column_name == 'Sentence' or column_name == "idx2Sentence": #formatting wrong, display cells in streamlit
                if column_name == 'Sentence': #formatting wrong, display cells in streamlit
                    st.text(str(cell_value))

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

task_to_dbpath = {
    'idx2Sentence': 'idx2Sentence_nltk.db',
    'idx2HumanDetect': 'idx2HumanDetect_gpt-3o5-turbo-1106Tem0.db',
    'idx2TraitDetect_tender_mindedness': 'idx2TraitDetect_tender-mindedness_gpt-3o5-turbo-1106Tem0.db', 
    'idx2MetricScore_TraitScore': 'idx2MetricScore_tender-mindedness_Trait Score_gpt-3o5-turbo-1106Tem0.db',
}            

# db_folder = '/Users/ynadell/Desktop/CDHAI/CDHAI-LLM/Text2Survey/2-DATA_DB/2-ReviewBucket1000/Group_s1000000_e1009999_SH_Physician/rs42_chunk_1_Task/'
db_folder = '2-DATA_DB/2-ReviewBucket1000/Group_s1000000_e1009999_SH_Physician/rs42_chunk_1_Task/'
db_folder_new = db_folder.replace('2-DATA_DB', '3-DATA_HE') 
# raw_text_id = st.text_input('raw_text_id', '1001053_4844')
raw_text_id = st.text_input('raw_text_id', '1006579_44921')
annotator_name = st.text_input('Annotator Name')

st.write('The raw_text_id is', raw_text_id)

df = function_to_query_data(raw_text_id, task_to_dbpath, db_folder)
#removing metric score from display 
df.pop("idx2MetricScore_TraitScore")
checkbox_states = display_dataframe_with_checkboxes(df)
metric_score = st.text_input('Metric Score')

df_columns = df.columns[2:]


if st.button('Submit'):
    #checks if name is blank or not
    if annotator_name == "":
        st.error("Please fill the annotator name")
    if metric_score=="":
        st.error("Please fill metric score")
    else:
        for key in checkbox_states:
            column_name, row_index = key.rsplit('_', 1)
            row_index = int(row_index)
            if checkbox_states[key]:
                st.write(f"Checkbox for {column_name} in row {row_index} is checked and is {df[column_name].iloc[row_index]}")
            if checkbox_states[key]:
                for i in range(0,len(df_columns)):
                    column_name = df_columns[i]
                    df[column_name].iloc[row_index] = str(df[column_name].iloc[row_index])
                    if df[column_name].iloc[row_index] == "nan" or df[column_name].iloc[row_index] == "0" or df[column_name].iloc[row_index] == "0.0":
                        df[f"{column_name}"].iloc[row_index] = df["idx2Sentence"].iloc[row_index]
                    else:
                        st.write("IN ELSE")
                        for j in range(i+1,len(df_columns)):
                            df[f"{df_columns[j]}"].iloc[row_index] = "nan"
            if checkbox_states[key]:
                st.write(f"Checkbox for {column_name} in row {row_index} is now {df[column_name].iloc[row_index]}")
            
        #the below line is to copy the metric score assigned by the annotator to all the sentences in the dataframe
        df['idx2MetricScore_TraitScore'] = [f"{metric_score}" for _ in range(len(df['idx2Sentence']))]
        print("function to save df is triggered")

        function_to_save_data(df, db_folder ,db_folder_new, task_to_dbpath)