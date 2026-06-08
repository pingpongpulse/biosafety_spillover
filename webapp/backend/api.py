from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import pandas as pd
import numpy as np
import xgboost as xgb
import pickle
import json
import shap
import os
from bio_content import get_shap_explanation, calculate_confidence_deficit

app = FastAPI(title="BioRiskNet API")

# Allow CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load Models
base_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(os.path.dirname(base_dir))

rg_model_path = os.path.join(root_dir, "models", "xgboost_rg_classifier.pkl")
sp_model_path = os.path.join(root_dir, "results", "spillover_model.pkl")
enc_path = os.path.join(root_dir, "models", "encoder_mappings.json")

try:
    with open(rg_model_path, "rb") as f:
        rg_model = pickle.load(f)
    with open(sp_model_path, "rb") as f:
        sp_model = pickle.load(f)
    with open(enc_path, "r") as f:
        enc = json.load(f)
        feature_cols = enc["_feature_cols"]
except Exception as e:
    print(f"Error loading models: {e}")
    rg_model, sp_model, enc, feature_cols = None, None, None, []

# Explainer for RG
try:
    explainer = shap.TreeExplainer(rg_model)
except:
    explainer = None

class PredictRequest(BaseModel):
    is_dna: Optional[int] = None
    is_enveloped: Optional[int] = None
    is_segmented: Optional[int] = None
    is_vector_borne: Optional[int] = None
    is_zoonotic: Optional[int] = None
    infects_humans: Optional[int] = None
    host_breadth: Optional[float] = None
    genome_type_enc: Optional[int] = None
    taxonomic_family_enc: Optional[int] = None

@app.post("/predict")
async def predict(req: PredictRequest):
    if not rg_model:
        raise HTTPException(status_code=500, detail="Models not loaded")
    
    data = req.dict()
    df = pd.DataFrame([data])
    
    # RG Predict
    rg_X = df[feature_cols].copy().astype(float)
    rg_proba = rg_model.predict_proba(rg_X)[0]
    pred_rg = int(np.argmax(rg_proba) + 1)
    
    # Spillover Predict formatting
    sp_dict = {
        "vIsTypeSpecies": 0, "ReverseZoonoses": 0, "vGenomeAveLength": 12016.0,
        "vGenomeMinLength": 12017.0, "vGenomeMaxLength": 12450.0,
        "vWOKcites": 11.0, "vPubMedCites": 9.0, "vCytoReplicTF": 1, "vSSoDS": 1,
        "human_host": 0
    }
    sp_dict["vDNAoRNA"] = 0 if data.get("is_dna") == 1 else 1 if data.get("is_dna") == 0 else None
    sp_dict["vEnvelope"] = 0 if data.get("is_enveloped") == 1 else 0 if data.get("is_enveloped") == 0 else None
    sp_dict["vSegmentedTF"] = 1 if data.get("is_segmented") == 1 else 0 if data.get("is_segmented") == 0 else None
    sp_dict["vVectorYNna"] = 1 if data.get("is_vector_borne") == 1 else 0 if data.get("is_vector_borne") == 0 else None
    sp_dict["IsHoSa"] = data.get("infects_humans")
    sp_dict["host_count"] = data.get("host_breadth")
    sp_dict["human_host"] = data.get("infects_humans")
    
    cols = ['vIsTypeSpecies','ReverseZoonoses','IsHoSa','vGenomeAveLength',
            'vGenomeMinLength','vGenomeMaxLength','vWOKcites','vPubMedCites',
            'vCytoReplicTF','vSegmentedTF','vVectorYNna','vSSoDS','vDNAoRNA',
            'vEnvelope','host_count','human_host']
    sp_row = pd.DataFrame([sp_dict], columns=cols).fillna(0).astype(float)
    sp_prob = float(sp_model.predict_proba(sp_row)[0][1])
    
    # Confidence
    confidence_data = calculate_confidence_deficit(data)
    
    return {
        "rg_prediction": pred_rg,
        "rg_probabilities": {f"RG{i+1}": float(p) for i, p in enumerate(rg_proba)},
        "spillover_probability": sp_prob,
        "confidence": confidence_data,
        "raw_json": {
            "rg_proba": rg_proba.tolist(),
            "sp_proba": sp_prob,
            "inputs": data
        }
    }

@app.post("/explain")
async def explain(req: PredictRequest):
    if not explainer:
        raise HTTPException(status_code=500, detail="SHAP Explainer not loaded")
        
    data = req.dict()
    df = pd.DataFrame([data])
    rg_X = df[feature_cols].copy().astype(float)
    
    shap_values = explainer(rg_X)
    
    explanations_by_class = {}
    for class_idx in range(4):
        class_shap = shap_values[:, :, class_idx]
        base_val = float(class_shap[0].base_values)
        vals = class_shap[0].values
        
        explanations = []
        for feat, val in zip(feature_cols, vals):
            raw_v = data.get(feat, 0)
            bio_dict = get_shap_explanation(feat, val, raw_v)
            explanations.append({
                "feature": feat,
                "raw_value": raw_v,
                "shap_value": float(val),
                "bio_translation": bio_dict
            })
            
        explanations_by_class[f"RG{class_idx + 1}"] = {
            "base_value": base_val,
            "features": sorted(explanations, key=lambda x: abs(x["shap_value"]), reverse=True)
        }
        
    return explanations_by_class

@app.get("/discordance")
async def get_discordance():
    # Load the pre-calculated csv
    csv_path = os.path.join(root_dir, "results", "tables", "dual_model_discordance_scores.csv")
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        return df.to_dict(orient="records")
    return []
