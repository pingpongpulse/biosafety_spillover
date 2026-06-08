import os
import importlib.util

raw_bio_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bio_content.py")
spec = importlib.util.spec_from_file_location("raw_bio", raw_bio_path)
raw_bio = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(raw_bio)
    GLOBAL_IMP_BIO = raw_bio.GLOBAL_IMP_BIO
    SHAP_BIO = raw_bio.SHAP_BIO
except Exception as e:
    print(f"Failed to load raw_bio_content: {e}")
    GLOBAL_IMP_BIO = {}
    SHAP_BIO = {}

def get_shap_explanation(feature_name: str, shap_value: float, raw_value: float) -> dict:
    """
    Returns both the GLOBAL biological reasoning (what the model learned overall)
    and the INSTANCE reasoning (what applies to this specific evaluation based on the value).
    """
    global_reason = ""
    instance_reason = ""
    signal = ""
    
    if feature_name == "is_dna":
        global_reason = "DNA/RNA status is the strongest biological divider because RNA viruses generally replicate with polymerases that lack proofreading accuracy. This generates more variation, allowing faster immune escape and adaptation, driving many high-consequence pathogens."
        if raw_value == 0: # RNA
            instance_reason = "RNA Status: Generates genetic diversity rapidly through error-prone polymerases, supporting immune escape and adaptation (e.g., SARS-CoV-2, Ebola). This acts as a biologically plausible high-risk signal."
            signal = "HIGH containment signal"
        else: # DNA
            instance_reason = "DNA Status: Generally more stable genomes due to stronger proofreading. This stability makes them more predictable and manageable under standard laboratory precautions, constraining rapid evolutionary change."
            signal = "LOWER containment signal"
            
    elif feature_name == "infects_humans":
        global_reason = "A virus confirmed to infect humans immediately becomes more relevant to laboratory containment because exposure can translate into actual human disease rather than theoretical hazard. WHO biosafety emphasizes risk to laboratory workers."
        if raw_value == 1:
            instance_reason = "Confirmed Human Infection: Accidental exposure has a direct route to human disease. Laboratory handling must assume human susceptibility, strongly linking biological hazard to real-world biosafety decision-making."
            signal = "HIGH containment signal"
        else:
            instance_reason = "No Confirmed Human Infection: Reduces immediate containment concern due to no documented evidence. However, this may reflect limited sampling rather than true biological inability."
            signal = "LOWER confidence signal"
            
    elif feature_name == "taxonomic_family_enc":
        global_reason = "Viral family captures inherited biological properties not always visible from one trait alone, such as replication strategy, virion structure, host tropism, and typical disease phenotype. Family biology acts as a compact summary of evolutionary history."
        if shap_value > 0:
            instance_reason = "High-Risk Family: Membership in this family reflects shared replication strategies and disease patterns associated with severe containment work (e.g., Filoviridae or Paramyxoviridae)."
            signal = "HIGH containment signal"
        else:
            instance_reason = "Lower-Risk Family: Membership in this family is commonly associated with manageable disease, stable laboratory handling, or widespread background exposure (e.g., Papillomaviridae)."
            signal = "LOWER containment signal"
            
    elif feature_name == "genome_type_enc":
        global_reason = "Specific Baltimore genome subtype refines the broader DNA/RNA distinction. ssRNA- viruses often require virus-encoded polymerases and include severe zoonoses, while dsDNA viruses often have more stable replication patterns."
        if shap_value > 0:
            instance_reason = "High-Risk Genome Architecture: Replication dynamics, immune evasion, and host switching are major concerns for this genome subtype, carrying a recognizable high-risk biological signature."
            signal = "HIGH containment signal"
        else:
            instance_reason = "Stable Genome Architecture: Associated with more stable replication or lower severe-disease precedent. Indicates that the genome architecture does not strongly resemble the highest-risk viral groups."
            signal = "LOWER containment signal"

    elif feature_name == "is_enveloped":
        global_reason = "Viral envelopes are biologically important because they carry glycoproteins that mediate host-cell attachment, membrane fusion, tissue tropism, and immune escape, supporting efficient entry."
        if raw_value == 1:
            instance_reason = "Enveloped: The lipid membrane and surface proteins mediate receptor binding, fusion, and cell entry, signaling an enhanced ability to enter specific host tissues and evade immune barriers."
            signal = "MODERATE containment signal"
        else:
            instance_reason = "Non-Enveloped: Lacks membrane-fusion machinery associated with many severe systemic infections. Capsids can be environmentally stable, creating different exposure risks, but lowers severe-systemic signal."
            signal = "MIXED signal"

    elif feature_name == "is_zoonotic":
        global_reason = "Zoonotic viruses have crossed species barriers, which selects for traits linked to receptor flexibility, immune evasion, and ecological persistence. Host-virus coevolution shapes non-human immune-evasion strategies."
        if raw_value == 1:
            instance_reason = "Zoonotic Origin: Has ecological access to animal reservoirs and capacity to cross host barriers, illustrating receptor flexibility and repeated exposure opportunities."
            signal = "HIGH emergence & MODERATE containment signal"
        else:
            instance_reason = "Not Zoonotic: No documented animal-to-human pathway. This lowers emergence concern but must be interpreted cautiously as it heavily depends on surveillance quality."
            signal = "LOWER emergence signal"

    elif feature_name == "host_breadth":
        global_reason = "Host breadth reflects how many host species a virus can infect, which is a proxy for receptor flexibility and ecological opportunity. Broader host associations provide more routes for maintenance and repeated spillover."
        if shap_value > 0:
            instance_reason = f"Broad Host Breadth ({raw_value} taxa): Suggests receptor flexibility and ability to persist across multiple niches, increasing opportunities for adaptation, recombination, and repeated human exposure."
            signal = "HIGH emergence signal"
        else:
            instance_reason = f"Narrow Host Breadth ({raw_value} taxa): Appears restricted in hosts, reducing ecological pathways leading to human exposure. Reduces emergence breadth, though not necessarily disease severity."
            signal = "LOWER emergence signal"

    elif feature_name == "is_segmented":
        global_reason = "Segmented genomes allow reassortment, where two related viruses infecting the same cell can exchange genome segments and generate new combinations (antigenic shift) with pandemic potential."
        if raw_value == 1:
            instance_reason = "Segmented Genome: Allows whole-segment reassortment when related viruses co-infect, generating antigenically novel strains. Represents high evolutionary flexibility."
            signal = "EMERGENCE signal"
        else:
            instance_reason = "Non-Segmented Genome: Cannot exchange whole genome segments. Evolution occurs through slower point mutations. Reduces one pathway of sudden evolutionary change but does not remove biosafety concern."
            signal = "LOWER reassortment signal"

    elif feature_name == "is_vector_borne":
        global_reason = "The most biologically interesting finding: vector-borne transmission strongly affects ecological spread but does not automatically increase intrinsic biosafety severity. Vectors increase geographic reach but are neutral to containment severity."
        if raw_value == 1:
            instance_reason = "Vector-Borne: Arthropods connect the virus to new hosts and regions, amplifying transmission opportunities. This strongly supports spillover but contributes almost nothing to containment severity."
            signal = "PRIMARY spillover signal, NEUTRAL containment signal"
        else:
            instance_reason = "Non-Vector-Borne: Severe containment risk can arise through direct contact, respiratory exposure, or bites. Lack of vector does not protect against high containment risk."
            signal = "NEUTRAL containment signal"
            
    else:
        global_reason = "Structural trait evaluated for containment relevance."
        instance_reason = f"Trait evaluation: {'Amplifies' if shap_value > 0 else 'Constrains'} biosafety severity."
        signal = "NEUTRAL"
        
    # Append the raw bio explanations
    raw_global = GLOBAL_IMP_BIO.get(feature_name, "")
    if raw_global:
        global_reason += " " + raw_global
        
    raw_instance_dict = SHAP_BIO.get(feature_name, {})
    raw_instance = raw_instance_dict.get("positive" if shap_value > 0 else "negative", "")
    if raw_instance:
        instance_reason += " " + raw_instance

    return {
        "global_reason": global_reason.strip(),
        "instance_reason": instance_reason.strip(),
        "signal": signal
    }

def calculate_confidence_deficit(features_dict: dict) -> dict:
    """
    Calculates the model's confidence based on missing data or "Disease X" profiles.
    """
    confidence = 100
    warnings = []
    
    if features_dict.get("infects_humans", 0) == 0:
        confidence -= 35
        warnings.append("Missing Clinical Data: The virus lacks confirmed human infection priors. This forces the model to evaluate purely theoretical hazard without known human susceptibility.")
        
    if features_dict.get("taxonomic_family_enc", 0) == 0 or features_dict.get("taxonomic_family_enc") is None:
        confidence -= 40
        warnings.append("Lineage Unmapped: The model is forced to evaluate pure structural hazard without evolutionary precedents. Extreme values (99.8% or 0.5%) reflect perfect structural alignment with decision tree terminal leaves.")
        
    if confidence == 100:
        return {"score": 100, "status": "High Confidence", "warnings": []}
    elif confidence >= 60:
        return {"score": confidence, "status": "Moderate Confidence", "warnings": warnings}
    else:
        return {"score": confidence, "status": "Low Confidence (Data Gap)", "warnings": warnings}
