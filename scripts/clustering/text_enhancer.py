import pandas as pd
from tqdm import tqdm
from ..config import (
    TEXT_STRATEGY_MIN_SUMMARY_LENGTH,
    TEXT_STRATEGY_MIN_FIRST_MSG_LENGTH,
    TEXT_STRATEGY_TURNS_COUNT
)

def enhance_text(df_chat, df_msg):
    enhanced_texts = []
    strategy_used = []
    
    for idx, row in tqdm(df_chat.iterrows(), total=len(df_chat), desc="   Processing"):
        chat_id = row['id']
        raw_summary = row.get('summarizedMessage', None)
        summary = raw_summary

        if pd.notna(raw_summary) and len(str(raw_summary)) >= TEXT_STRATEGY_MIN_SUMMARY_LENGTH:
            enhanced_texts.append(str(raw_summary))
            strategy_used.append('summary')
        else:
            messages = df_msg[df_msg['chatId'] == chat_id]['plainText'].astype(str).tolist()
            
            if len(messages) == 0:
                enhanced_texts.append(str(summary) if pd.notna(summary) else '')
                strategy_used.append('empty')
            elif len(str(messages[0])) >= TEXT_STRATEGY_MIN_FIRST_MSG_LENGTH:
                enhanced_texts.append(str(messages[0]))
                strategy_used.append('first_msg')
            else:
                first_n_turns = [str(msg) for msg in messages[:TEXT_STRATEGY_TURNS_COUNT]]
                combined = ' '.join(first_n_turns)
                enhanced_texts.append(combined)
                strategy_used.append('3_turns')
    
    df_chat['enhanced_text'] = enhanced_texts
    df_chat['text_strategy'] = strategy_used
    
    return df_chat
