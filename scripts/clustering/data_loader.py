import pandas as pd

def load_data(filepath, sample_size=None):
    df_chat = pd.read_excel(filepath, sheet_name='UserChat data')
    df_msg = pd.read_excel(filepath, sheet_name='Message data')
    
    if sample_size and sample_size < len(df_chat):
        df_chat = df_chat.head(sample_size).copy()
        chat_ids = df_chat['id'].tolist()
        df_msg = df_msg[df_msg['chatId'].isin(chat_ids)].copy()
    
    df_msg = df_msg.sort_values(['chatId', 'createdAt'])
    
    return df_chat, df_msg
