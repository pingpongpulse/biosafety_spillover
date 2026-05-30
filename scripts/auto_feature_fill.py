import pandas as pd
import numpy as np
import os
import json
import time
from dotenv import load_dotenv
from groq import Groq

# ── Load Environment Variables Safely ────────────────────────────────────────
# This searches for a local .env file and injects its values into system memory
load_dotenv()

INPUT_PATH = 'data/processed/rg_dataset_features.csv'
BATCH_SIZE = 30  
MODEL_NAME = "llama-3.1-70b-versatile"  

# Fetch the credential from the system environment
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

if not GROQ_API_KEY:
    print("❌ Operational Error: 'GROQ_API_KEY' not found in system variables.")
    print("Verify that your '.env' file exists in the root directory and contains the correct key configuration.")
    exit()

print("=== Running Step 1.7 Live Groq API Extraction Engine via .env ===")

if not os.path.exists(INPUT_PATH):
    print(f"❌ Error: Target template '{INPUT_PATH}' missing.")
    exit()

# Load the master template
df = pd.read_csv(INPUT_PATH)

feature_cols = ['genome_type', 'transmission_route', 'host_range', 
                'environmental_stability', 'treatment_available', 'infectious_dose', 'zoonotic']

# Initialize the Groq Client with the secure variable
client = Groq(api_key=GROQ_API_KEY)

missing_mask = df[feature_cols].isna().all(axis=1)
indices_to_process = df[missing_mask].index.tolist()

print(f"Total rows in template: {len(df)}")
print(f"Rows remaining to process via LLM: {len(indices_to_process)}")

if len(indices_to_process) == 0:
    print("✅ All rows are already filled!")
    exit()

SYSTEM_PROMPT = """You are an expert biological data curation assistant. 
Your job is to analyze a list of pathogen names and return their biological profiles.
You must strictly follow the categorical schema values below:
- genome_type: ["DNA", "RNA", "dsDNA", "ssRNA+", "ssRNA-"]
- transmission_route: ["airborne", "contact", "vector", "fecal-oral", "droplet"]
- host_range: ["narrow", "broad", "human-only"]
- environmental_stability: ["low", "medium", "high"]
- treatment_available: ["yes", "no", "partial"]
- infectious_dose: ["low", "medium", "high"]
- zoonotic: ["yes", "no"]

Output Format: You must return ONLY a valid raw JSON array of objects, where each object represents a pathogen and contains the 'name' key and the 7 feature keys specified above. Do not wrap the response in markdown blocks (like ```json). Do not add conversational text or code explanations."""

for i in range(0, len(indices_to_process), BATCH_SIZE):
    batch_indices = indices_to_process[i:i + BATCH_SIZE]
    batch_names = df.loc[batch_indices, 'name'].tolist()
    
    print(f"\nProcessing batch {i//BATCH_SIZE + 1} ({len(batch_names)} pathogens)...")
    user_prompt = f"Provide the biological profiles for these specific pathogens: {json.dumps(batch_names)}"
    
    attempts = 0
    success = False
    while attempts < 3 and not success:
        try:
            attempts += 1
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                model=MODEL_NAME,
                temperature=0.0,  
                max_tokens=4000,
            )
            
            raw_response = chat_completion.choices[0].message.content.strip()
            
            if raw_response.startswith("```"):
                raw_response = raw_response.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            if raw_response.startswith("json"):
                raw_response = raw_response.split("json", 1)[1].strip()

            parsed_json = json.loads(raw_response)
            
            for item in parsed_json:
                p_name = item.get('name')
                match = df[df['name'] == p_name].index
                if not match.empty:
                    target_idx = match[0]
                    for col in feature_cols:
                        if col in item:
                            df.at[target_idx, col] = item[col]
            
            success = True
            print(f"  ✅ Batch successfully parsed and merged.")
            df.to_csv(INPUT_PATH, index=False)
            
        except Exception as e:
            print(f"  ❌ Attempt {attempts} failed: {e}")
            time.sleep(2)  
            
    time.sleep(1.5)

print(f"\n🎉 Metadata population complete! Check the populated template at: {INPUT_PATH}")