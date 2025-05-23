# -*- coding: utf-8 -*-
"""generate_prompts.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1UtTvZBYy2rbPxxeXZHLhz9aC3JKx5c-R
"""

!pip install jsonlines

from google.colab import drive
drive.mount('/content/drive')

import numpy as np
import pandas as pd
import jsonlines
import sys
import os
import json
import zipfile
os.chdir('/content/drive/My Drive/Colab Notebooks/centaur/')
os.listdir()
#sys.path.append("..")
#from utils import randomized_choice_options

# --- exp2 ---
# Read in the datasets
df_exp2 = pd.read_csv("dataExp2.csv")
cond_df_exp2 = pd.read_csv("SacrificialAllFramings.csv")

# Rename column Q674 to Endow_O_Q because of Qualtrics error
df_exp2 = df_exp2.rename(columns={"Q674": "Endow_O_Q"})

# Exclude those who didn't pass attention check
attention_cols_exp2 = ["Suicide_Attn", "Vet_Attn", "RAF_Attn", "Medicine_Attn", "Ransom_Attn", "Endow_Attn"]
# Convert the attention columns to numeric (if not already) and filter rows
mask = df_exp2[attention_cols_exp2].apply(pd.to_numeric, errors='coerce').eq(1).any(axis=1)
df_exp2 = df_exp2[mask].copy()

# Rename the first column to "participant" (assuming it is unnamed or not already set)
current_first_col = df_exp2.columns[0]
df_exp2 = df_exp2.rename(columns={current_first_col: "participant"})

# Select only participant and columns whose names end with '_Q'
q_cols = [col for col in df_exp2.columns if col.endswith("_Q")]
new_df_exp2 = df_exp2[["participant"] + q_cols].copy()

# Convert from wide to long format
long_df_exp2 = new_df_exp2.melt(id_vars=["participant"], var_name="condition", value_name="value")
# Remove rows with missing values
long_df_exp2 = long_df_exp2.dropna()

# Create the 'vignettes' column by taking text before the first underscore in 'condition'
long_df_exp2["vignettes"] = long_df_exp2["condition"].str.split("_").str[0]

# Create the 'cond' column based on patterns in 'condition'
def assign_cond(cond):
    if "_O_" in cond:
        return "omission"
    elif "_YN_" in cond:
        return "yesno"
    else:
        return "original"

long_df_exp2["cond"] = long_df_exp2["condition"].apply(assign_cond)

# Merge with the condition dataframe using vignettes and cond
exp2df = pd.merge(long_df_exp2, cond_df_exp2, on=["vignettes", "cond"], how="left")

# Replace values in 'value': if value equals 1 or 5 -> "Yes"; if equals 2 or 6 -> "No"
exp2df["value"] = exp2df["value"].replace({1: "yes", 5: "yes", 2: "no", 6: "no"})

print(exp2df)

# --- exp3 ---
# Read in the datasets
df_exp3 = pd.read_csv("dataExp3.csv")
cond_df_exp3 = pd.read_csv("SacrificialAllFramings_Exp3.csv")

# Update vignettes in cond_df_exp3: if vignettes == "Family Dog", change to "FamilyDog"
cond_df_exp3["vignettes"] = cond_df_exp3["vignettes"].replace({"Family Dog": "FamilyDog"})

# Subset rows: keep rows where at least one attention column equals 1.
attention_cols_exp3 = ["FamilyDog_Attn", "Roommate_Attn", "Outfit_Attn",
                         "Pregnant_Attn", "Christmas_Attn", "Notetaking_Attn"]
mask_exp3 = df_exp3[attention_cols_exp3].apply(pd.to_numeric, errors='coerce').eq(1).any(axis=1)
df_exp3 = df_exp3[mask_exp3].copy()

# Rename the first column to "participant"
current_first_col = df_exp3.columns[0]
df_exp3 = df_exp3.rename(columns={current_first_col: "participant"})

# Select participant and all columns that end with '_Q'
q_cols_exp3 = [col for col in df_exp3.columns if col.endswith("_Q")]
new_df_exp3 = df_exp3[["participant"] + q_cols_exp3].copy()

# Convert from wide to long format
long_df_exp3 = new_df_exp3.melt(id_vars=["participant"], var_name="condition", value_name="value")
# Remove rows with missing values
long_df_exp3 = long_df_exp3.dropna()

# Create the 'vignettes' column by taking text before the first underscore in 'condition'
long_df_exp3["vignettes"] = long_df_exp3["condition"].str.split("_").str[0]

# Create the 'cond' column based on patterns in 'condition'
long_df_exp3["cond"] = long_df_exp3["condition"].apply(assign_cond)

# Merge with the condition dataframe using vignettes and cond
exp3df = pd.merge(long_df_exp3, cond_df_exp3, on=["vignettes", "cond"], how="left")

# Replace values in 'value': if value equals 1 or 5 -> "Yes"; if equals 2 or 6 -> "No"
exp3df["value"] = exp3df["value"].replace({1: "yes", 5: "yes", 2: "no", 6: "no"})
print(exp3df)

# --- Merge experiments ---
# Read in cleaned data
exp2df = pd.read_csv("dfExp2_cleaned.csv")
exp3df = pd.read_csv("dfExp3_cleaned.csv")

# Concatenate the two dataframes vertically and drop the first column (if it's an unnecessary index)
combined_df = pd.concat([exp2df, exp3df], ignore_index=True)

# If the first column is a duplicate index, drop it.
if combined_df.columns[0] == "Unnamed: 0":
    combined_df = combined_df.drop(columns=["Unnamed: 0"])

# Add a new participant column as a row number starting from 1
combined_df["participant"] = np.arange(1, len(combined_df) + 1)

# Create a new column 'experiment' based on participant number
combined_df["experiment"] = np.where(combined_df["participant"] <= 490, "exp2", "exp3")
combined_df["value"] = combined_df["value"].replace({"Yes": "yes", "No": "no"})
# Write the final combined data to csv
print(combined_df)

df = combined_df
df['participant'] = pd.to_numeric(df['participant'], errors='coerce')
num_participants = df.participant.max() + 1
print(num_participants)

num_tasks = 1
num_trials = 1

with open('instructionsExp2.txt', 'r', encoding='utf-8') as file:
    prompt = file.read()
df['prompt'] = prompt

df['text'] = df['prompt'] + " " + df['description'] + "Your answer <<" + df['value'].astype(str) + ">>"

# Group by participant and experiment, combine texts per participant
grouped = df.groupby(['participant', 'experiment'])['text'].apply(lambda texts: ' '.join(texts)).reset_index()

# Convert grouped data to JSON lines format
json_lines = grouped.apply(lambda row: json.dumps({
    "text": row['text'],
    "experiment": row['experiment'],
    "participant": row['participant']
}), axis=1).tolist()

# Save to a JSONL file
jsonl_filename = 'prompts.jsonl'
with open(jsonl_filename, 'w', encoding='utf-8') as f:
    for line in json_lines:
        f.write(f"{line}\n")

# Zip the JSONL file
zip_filename = 'prompts.zip'
with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
    zipf.write(jsonl_filename)

print(f"JSONL file '{jsonl_filename}' zipped successfully as '{zip_filename}'.")