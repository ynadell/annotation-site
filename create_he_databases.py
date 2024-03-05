import sqlite3
import os

task_to_dbpath = {
    'idx2Sentence': 'idx2Sentence_nltk.db',
    'idx2HumanDetect': 'idx2HumanDetect_gpt-3o5-turbo-1106Tem0.db',
    'idx2TraitDetect: tender-mindedness': 'idx2TraitDetect_tender-mindedness_gpt-3o5-turbo-1106Tem0.db', 
    'idx2MetricScore: Trait Score': 'idx2MetricScore_tender-mindedness_Trait Score_gpt-3o5-turbo-1106Tem0.db',
}            

db_folder = '../../Text2Survey/2-DATA_DB/2-ReviewBucket1000/Group_s1000000_e1009999_SH_Physician/rs42_chunk_1_Task/'
db_folder_new = db_folder.replace('2-DATA_DB', '3-DATA_HE') 

for taskname, dbfile in task_to_dbpath.items():
    # Specify your database file name
    db_file = os.path.join(db_folder_new, dbfile)

    # Connect to the SQLite database
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # SQL command to drop an existing table
    drop_table_command = """
    DROP TABLE IF EXISTS TaskAction;
    """

    # SQL command to create a new table
    create_table_command = """
    CREATE TABLE TaskAction (
        annotator_id TEXT PRIMARY KEY,
        annotator_name TEXT,
        raw_text_id TEXT,
        raw_text TEXT,
        subject_human TEXT,
        taskname TEXT,
        task_args TEXT,
        result TEXT,
        resultmisc TEXT,
        resultname TEXT,
        fullresultname TEXT,
        DT TIMESTAMP,
        time_of_annotation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """

    try:
        # Execute the command to drop the existing table
        cursor.execute(drop_table_command)
        print("Existing table dropped successfully.")
        
        # Execute the command to create a new table
        cursor.execute(create_table_command)
        print("New table created successfully.")
        
        # Commit the changes
        conn.commit()
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    finally:
        # Close the connection to the database
        conn.close()