"""BioRiskNet v2 — Interactive Demo"""
import streamlit as st
import pickle, json
import pandas as pd
import numpy as np
import shap, warnings
warnings.filterwarnings("ignore")
from bio_content import (GENOME_BIO, GLOBAL_IMP_BIO, BIO_RISK, SHAP_BIO,
                         CONFIDENCE_EXPLAIN, SPILLOVER_EXPLAIN)

st.set_page_config(page_title="BioRiskNet v2", page_icon="🦠", layout="wide")

@st.cache_resource
def load_models():
    with open("models/xgboost_rg_classifier.pkl","rb") as f: rg = pickle.load(f)
    with open("results/spillover_model.pkl","rb") as f: sp = pickle.load(f)
    with open("models/encoder_mappings.json") as f: enc = json.load(f)
    expl = shap.TreeExplainer(rg)
    return rg, sp, enc, expl

rg_model, sp_model, enc, explainer = load_models()
GENOME_MAP   = enc["genome_type"]
FAMILY_MAP   = enc["taxonomic_family"]
FEATURE_COLS = enc["_feature_cols"]

GLOBAL_IMP = {
    "is_dna":42.7,"infects_humans":11.5,"taxonomic_family_enc":11.3,
    "genome_type_enc":11.2,"is_enveloped":7.5,"is_zoonotic":6.7,
    "host_breadth":5.7,"is_segmented":3.5,"is_vector_borne":0.0
}
FEAT_LABELS = {
    "is_dna":"DNA/RNA Status","infects_humans":"Infects Humans",
    "taxonomic_family_enc":"Taxonomic Family","genome_type_enc":"Genome Type",
    "is_enveloped":"Enveloped","is_zoonotic":"Zoonotic",
    "host_breadth":"Host Breadth","is_segmented":"Segmented",
    "is_vector_borne":"Vector-borne"
}
RG_COLORS={1:"#2ecc71",2:"#f39c12",3:"#e67e22",4:"#e74c3c"}
RG_BSL={1:"BSL-1",2:"BSL-2",3:"BSL-3",4:"BSL-4"}
RG_DESC={
    1:"Minimal risk. Standard lab practices sufficient.",
    2:"Moderate risk. Effective treatment and prevention available.",
    3:"Serious/severe disease. BSL-3 containment required.",
    4:"Extreme risk. No treatment or vaccine. Full BSL-4 required."
}

def html_bar(pct, color, label=""):
    fill = max(int(pct * 2.2), 2)
    return (f'<div style="display:flex;align-items:center;gap:8px;margin:3px 0">'
            f'<div style="width:220px;background:#1e1e2e;border-radius:4px;height:18px">'
            f'<div style="width:{fill}px;background:{color};border-radius:4px;height:18px"></div></div>'
            f'<span style="color:white;font-size:13px">{label}</span></div>')

def build_rg_row(u):
    return pd.DataFrame([{
        "genome_type_enc":      GENOME_MAP.get(u.get("genome_type","unknown"),6),
        "taxonomic_family_enc": FAMILY_MAP.get(u.get("family","unknown"),47),
        "is_dna":u["is_dna"],"is_enveloped":u["is_enveloped"],
        "is_segmented":u["is_segmented"],"is_vector_borne":u["is_vector_borne"],
        "is_zoonotic":u["is_zoonotic"],"infects_humans":u["infects_humans"],
        "host_breadth":u["host_breadth"],
    }], columns=FEATURE_COLS)

def build_sp_row(u):
    row={"vIsTypeSpecies":0,"ReverseZoonoses":0,"vGenomeAveLength":12016.0,
         "vGenomeMinLength":12017.0,"vGenomeMaxLength":12450.0,
         "vWOKcites":11.0,"vPubMedCites":9.0,"vCytoReplicTF":1,"vSSoDS":1,"human_host":0}
    row["vDNAoRNA"]=0 if u["is_dna"]==1 else 1
    row["vEnvelope"]=0 if u["is_enveloped"]==1 else 1
    row["vSegmentedTF"]=1 if u["is_segmented"]==1 else 0
    row["vVectorYNna"]=1 if u["is_vector_borne"]==1 else 0
    ih=u["infects_humans"]; row["IsHoSa"]=int(ih) if not np.isnan(ih) else 0
    hb=u["host_breadth"]; row["host_count"]=float(hb) if not np.isnan(hb) else 1.0
    row["vSSoDS"]=0 if u.get("genome_type","").startswith("ds") else 1
    row["human_host"]=row["IsHoSa"]
    cols=['vIsTypeSpecies','ReverseZoonoses','IsHoSa','vGenomeAveLength',
          'vGenomeMinLength','vGenomeMaxLength','vWOKcites','vPubMedCites',
          'vCytoReplicTF','vSegmentedTF','vVectorYNna','vSSoDS','vDNAoRNA',
          'vEnvelope','host_count','human_host']
    return pd.DataFrame([row], columns=cols)

# ── Sidebar ───────────────────────────────────────────────────────────────────
st.title("🦠 BioRiskNet v2")
st.markdown("**Interpretable WHO Biosafety Risk Group & Zoonotic Spillover Prediction**")
st.caption("934 viral pathogens · 9 verified biological features · ICTV + Virus-Host DB + Olival 2017")
st.divider()

with st.sidebar:
    st.header("🔬 Virus Features")
    virus_name  = st.text_input("Virus name", value="Unknown Virus")
    genome_type = st.selectbox("Genome type", ["ssRNA-","ssRNA+","dsDNA","dsRNA","ssDNA","other","unknown"])
    family      = st.selectbox("Taxonomic family", ["unknown"]+sorted([k for k in FAMILY_MAP if k!="unknown"]))
    st.subheader("Biological Properties")
    is_dna_r = st.radio("Genome chemistry",          ["RNA","DNA"],                   horizontal=True)
    is_env_r = st.radio("Envelope status",            ["Enveloped","Non-enveloped"],  horizontal=True)
    is_seg_r = st.radio("Segmented genome?",          ["No","Yes","Unknown"],          horizontal=True)
    is_vec_r = st.radio("Vector-borne?",              ["No","Yes","Unknown"],          horizontal=True)
    is_zoo_r = st.radio("Zoonotic origin?",           ["No","Yes","Unknown"],          horizontal=True)
    is_hum_r = st.radio("Confirmed human infection?", ["No","Yes","Unknown"],          horizontal=True)
    host_breadth = st.number_input("Host breadth (# host species)", 0, 200, 1)
    def tri(v): return {0:0.0,1:1.0,2:np.nan}[["No","Yes","Unknown"].index(v)]
    user={
        "genome_type":genome_type,"family":family,
        "is_dna":0.0 if is_dna_r=="RNA" else 1.0,
        "is_enveloped":1.0 if is_env_r=="Enveloped" else 0.0,
        "is_segmented":tri(is_seg_r),"is_vector_borne":tri(is_vec_r),
        "is_zoonotic":tri(is_zoo_r),"infects_humans":tri(is_hum_r),
        "host_breadth":float(host_breadth) if host_breadth>0 else np.nan,
    }
    run = st.button("🔍 Analyse Virus", type="primary", use_container_width=True)

if not run:
    st.info("👈 Fill in the virus features in the sidebar and click **Analyse Virus**")
    st.stop()

# ── Predictions ───────────────────────────────────────────────────────────────
rg_row   = build_rg_row(user)
sp_row   = build_sp_row(user)
raw_pred = rg_model.predict(rg_row)[0]
pred_rg  = int(raw_pred)+1
rg_proba = rg_model.predict_proba(rg_row)[0]
conf     = rg_proba[raw_pred]
sp_prob  = float(sp_model.predict_proba(sp_row)[0][1])
sp_label = "🔴 HIGH" if sp_prob>0.65 else ("🟡 MEDIUM" if sp_prob>0.35 else "🟢 LOW")

# ── Result cards ──────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)
with col1:
    c=RG_COLORS[pred_rg]
    st.markdown("### 🧫 WHO Risk Group")
    st.markdown(
        f'<div style="background:{c}22;border-left:5px solid {c};padding:1rem;border-radius:8px">'
        f'<div style="font-size:2rem;font-weight:bold;color:{c}">RG{pred_rg} — {RG_BSL[pred_rg]}</div>'
        f'<div style="color:#ccc;margin-top:4px">{RG_DESC[pred_rg]}</div></div>',unsafe_allow_html=True)
    st.markdown(f"\n**Confidence: {conf:.1%}**")
    if conf>=0.70: st.caption(CONFIDENCE_EXPLAIN["high"])
    elif conf>=0.45: st.caption(CONFIDENCE_EXPLAIN["moderate"])
    else: st.caption(CONFIDENCE_EXPLAIN["low"])
    st.markdown("**Probability across Risk Groups:**")
    for i,p in enumerate(rg_proba,1):
        st.markdown(html_bar(round(p*100,1),RG_COLORS[i],f"RG{i}  {p:.1%}"),unsafe_allow_html=True)

with col2:
    sc="#e74c3c" if sp_prob>0.65 else ("#f39c12" if sp_prob>0.35 else "#2ecc71")
    st.markdown("### 🌍 Zoonotic Spillover Risk")
    st.markdown(
        f'<div style="background:{sc}22;border-left:5px solid {sc};padding:1rem;border-radius:8px">'
        f'<div style="font-size:2rem;font-weight:bold;color:{sc}">{sp_label}</div>'
        f'<div style="color:#ccc;margin-top:4px">Spillover probability: <b>{sp_prob:.1%}</b></div></div>',
        unsafe_allow_html=True)
    st.markdown("")
    st.markdown(html_bar(round(sp_prob*100,1),sc,f"{sp_prob:.1%}"),unsafe_allow_html=True)
    st.caption("Olival 2017 ecological feature model (Virus-Host DB + ecological traits)")
    st.markdown("")
    if sp_prob>0.65: st.info(SPILLOVER_EXPLAIN["high"])
    elif sp_prob>0.35: st.warning(SPILLOVER_EXPLAIN["medium"])
    else: st.success(SPILLOVER_EXPLAIN["low"])

st.divider()

# ── Feature Scorecard ─────────────────────────────────────────────────────────
st.markdown("## 🧬 Feature Scorecard — Biological Reasoning per Trait")
st.caption("Each trait is explained in biological terms: what its value means for containment risk and spillover potential.")

# Genome type
with st.expander(f"**Genome Type: `{genome_type}`** — RG classification weight: 11.2%", expanded=True):
    st.markdown(GENOME_BIO.get(genome_type, "Genome type not characterised."))

# Binary features
scorecard = [
    ("DNA/RNA Status",     "is_dna",         0.0 if is_dna_r=="RNA" else 1.0, "42.7%"),
    ("Envelope Status",    "is_enveloped",    1.0 if is_env_r=="Enveloped" else 0.0, "7.5%"),
    ("Segmented Genome",   "is_segmented",    tri(is_seg_r), "3.5%"),
    ("Vector-borne",       "is_vector_borne", tri(is_vec_r), "0.0% RG | ↑ Spillover"),
    ("Zoonotic Origin",    "is_zoonotic",     tri(is_zoo_r), "6.7%"),
    ("Infects Humans",     "infects_humans",  tri(is_hum_r), "11.5%"),
]
for label, feat, val, weight in scorecard:
    is_nan = isinstance(val, float) and np.isnan(val)
    with st.expander(f"**{label}** — RG weight: {weight}"):
        if is_nan:
            st.caption("⚪ Not reported — XGBoost handles missing values natively via learned sparse routing.")
        elif feat in BIO_RISK:
            iv = int(val)
            if iv in BIO_RISK[feat]:
                icon, text, signal = BIO_RISK[feat][iv]
                st.markdown(f"{icon}")
                st.markdown(text)
                st.caption(f"Signal: **{signal}**")

# Host breadth
hb = user["host_breadth"]
with st.expander(f"**Host Breadth** — RG weight: 5.7% | #1 spillover predictor (Olival 2017)"):
    if np.isnan(hb):
        st.caption("⚪ Not reported.")
    else:
        hb_cat = "broad" if hb > 10 else "narrow"
        st.markdown(f"**{int(hb)} confirmed host species** — {'broad' if hb>10 else 'narrow'} host range.")
        bio = GLOBAL_IMP_BIO["host_breadth"]
        st.markdown(bio)
        if hb <= 1:
            st.caption("⚠️ Note: Marburg virus has host breadth = 1 yet requires BSL-4. Narrow host range lowers *emergence breadth*, not disease severity.")

st.divider()

# ── Global Weight Chart ───────────────────────────────────────────────────────
st.markdown("## 📊 What the Model Learned Across 934 Viruses")
st.caption("Percentage contribution of each biological trait to WHO Risk Group classification. Computed as XGBoost gain importance from the trained model.")

sorted_imp = sorted(GLOBAL_IMP.items(), key=lambda x: x[1])
for feat, imp in sorted_imp:
    label = FEAT_LABELS.get(feat, feat)
    color = "#e74c3c" if imp==max(GLOBAL_IMP.values()) else ("#3498db" if feat=="is_vector_borne" else "#7f8c8d")
    note  = " ← KEY: 0% despite primary spillover role" if feat=="is_vector_borne" else (" ← Dominant predictor" if imp==max(GLOBAL_IMP.values()) else "")
    fill  = max(int(imp * 5), 1)
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:10px;margin:4px 0">'
        f'<div style="width:160px;text-align:right;color:white;font-size:13px">{label}</div>'
        f'<div style="width:220px;background:#1e1e2e;border-radius:4px;height:20px">'
        f'<div style="width:{fill}px;background:{color};border-radius:4px;height:20px"></div></div>'
        f'<span style="color:white;font-size:13px">{imp}%{note}</span></div>',
        unsafe_allow_html=True)

st.markdown("")
st.markdown("**Why each trait has this weight — the biological explanation:**")
for feat, imp in sorted(GLOBAL_IMP.items(), key=lambda x: -x[1]):
    label = FEAT_LABELS.get(feat, feat)
    bio   = GLOBAL_IMP_BIO.get(feat, "")
    with st.expander(f"**{label}** — {imp}%"):
        st.markdown(bio)

st.divider()

# ── SHAP Bio Section ──────────────────────────────────────────────────────────
st.markdown("## 🔬 Per-Prediction Analysis — Why *This Virus* Got This Classification")
st.markdown(
    "The bars below show how much each biological trait contributed to the Risk Group prediction "
    "**for this specific virus**. A trait can push toward higher containment (🔴) or lower (🔵), "
    "depending on its value. Each row also explains the **biological mechanism** behind that push."
)
try:
    sv_all = explainer.shap_values(rg_row)
    sv = sv_all[raw_pred][0] if isinstance(sv_all, list) else \
         (sv_all[0,:,raw_pred] if len(sv_all.shape)==3 else sv_all[0])
    shap_df = pd.DataFrame({"feature":FEATURE_COLS,"shap":sv}).sort_values("shap",ascending=False)
    max_abs = max(abs(shap_df["shap"]).max(), 0.001)

    st.markdown(f"**{virus_name} → Predicted RG{pred_rg} ({conf:.1%} confidence)**")
    for _, row_s in shap_df.iterrows():
        feat   = row_s["feature"]
        sv_v   = row_s["shap"]
        label  = FEAT_LABELS.get(feat, feat)
        direction = "positive" if sv_v >= 0 else "negative"
        bar_pct   = abs(sv_v) / max_abs * 100
        color     = "#e74c3c" if sv_v > 0.005 else ("#3498db" if sv_v < -0.005 else "#7f8c8d")
        arrow     = "▲ Raised containment classification" if sv_v > 0.005 else \
                    ("▼ Lowered containment classification" if sv_v < -0.005 else "● Negligible influence")
        bio_text  = SHAP_BIO.get(feat,{}).get(direction,"")
        val_raw   = rg_row.iloc[0][feat]
        val_disp  = f"{val_raw:.2f}" if not (isinstance(val_raw,float) and np.isnan(val_raw)) else "missing"

        with st.expander(f"**{label}** — `{sv_v:+.4f}`  |  {arrow}  |  value: `{val_disp}`"):
            fill = max(int(bar_pct * 2.0), 2)
            st.markdown(
                f'<div style="width:{fill}px;max-width:420px;background:{color};'
                f'border-radius:4px;height:16px;margin-bottom:8px"></div>',
                unsafe_allow_html=True)
            if sv_v > 0.005: st.error(f"This trait pushed toward **higher** containment (RG{pred_rg} direction)")
            elif sv_v < -0.005: st.success(f"This trait pushed toward **lower** containment")
            else: st.info("This trait had negligible influence on this prediction")
            if bio_text:
                st.markdown(f"**Biological reasoning:** {bio_text}")

except Exception as e:
    st.warning(f"Per-prediction analysis could not be computed: {e}")

st.divider()
st.info(
    "🔑 **Core Finding:** `Vector-borne` = **0% weight** in Risk Group classification | primary spillover predictor.\n\n"
    "This quantitatively demonstrates that *biosafety severity* and *ecological emergence potential* are partially "
    "independent biological problems. Dengue (vector-borne, RG2) has high spillover potential but available treatment. "
    "Marburg (non-vector-borne, RG4) is rare but requires full BSL-4 containment. "
    "The same biological traits do not predict both."
)
st.caption("BioRiskNet v2 · Biosafety and Ethics · RV College of Engineering · June 2026")
