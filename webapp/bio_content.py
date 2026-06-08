"""
BioRiskNet v2 — Bio-first research content
All explanations sourced from virology literature, WHO/CDC biosafety frameworks, and Olival 2017.
"""

GENOME_BIO = {
    "ssRNA-": (
        "Negative-sense single-stranded RNA viruses must first carry or encode an RNA-dependent RNA polymerase "
        "to convert their genome into readable messenger RNA after entering the host cell. This group includes "
        "Ebola virus, Marburg virus, Lassa virus, Nipah virus, Rabies lyssavirus, and Influenza A — many combining "
        "rapid replication, immune evasion, and severe disease potential. From a biosafety perspective, ssRNA− status "
        "is concerning because these viruses often show high adaptability, zoonotic origin, and limited therapeutic options."
    ),
    "ssRNA+": (
        "Positive-sense single-stranded RNA viruses have genomes that can function directly as messenger RNA after entry, "
        "allowing rapid early protein production. Examples include SARS-CoV-2, Dengue virus, Zika virus, Chikungunya, "
        "Hepatitis C virus, and Poliovirus. Their biosafety relevance comes from fast replication and high mutation rates, "
        "but containment level varies widely depending on transmission route, disease severity, and vaccine availability."
    ),
    "dsDNA": (
        "Double-stranded DNA viruses generally have more stable genomes because DNA replication is typically associated "
        "with stronger proofreading and lower mutation rates. Examples include Adenovirus, Herpes simplex virus, "
        "Variola virus, Human papillomavirus, and Poxviruses. Many are vaccine-preventable or clinically manageable, "
        "although Variola virus demonstrates that DNA stability does not automatically mean low biosafety risk."
    ),
    "dsRNA": (
        "Double-stranded RNA viruses, such as Rotavirus and Reoviruses, require specialized replication mechanisms "
        "because host cells do not normally use dsRNA as genetic material. The presence of dsRNA can strongly activate "
        "innate immune pathways including interferon responses. Their biosafety risk depends less on genome type alone "
        "and more on host range, transmission route, and clinical severity."
    ),
    "ssDNA": (
        "Single-stranded DNA viruses are typically smaller and depend heavily on host-cell replication machinery, "
        "constraining their biological behavior compared with rapidly mutating RNA viruses. Examples include "
        "Parvoviruses and Circoviruses. In biosafety terms, ssDNA status often contributes less strongly to high "
        "containment classification unless paired with efficient human infection or severe disease."
    ),
    "other":   "Ambisense or complex genome architecture — limited biosafety precedent. Evaluate alongside family and host range.",
    "unknown": "Genome type not recorded in ICTV MSL 2025 for this organism — classification relies on other biological traits.",
}

GLOBAL_IMP_BIO = {
    "is_dna": (
        "RNA viruses generally replicate with polymerases that lack the proofreading accuracy typical of DNA replication. "
        "RNA-dependent RNA polymerases generate more variation, allowing faster immune escape, host switching, and "
        "adaptation. This explains why most RG3–4 viruses — Ebola, Marburg, Lassa, SARS-CoV-2, Nipah, Rabies — "
        "are RNA viruses, whereas many lower-risk groups include stable DNA viruses such as Adenovirus or HPV."
    ),
    "infects_humans": (
        "A virus confirmed to infect humans immediately becomes relevant to laboratory containment because exposure "
        "can translate into actual human disease. WHO and CDC biosafety guidance both emphasize risk to laboratory "
        "workers and consequences of accidental exposure. Viruses such as SARS-CoV-2, Rabies lyssavirus, "
        "Influenza A H1N1, Ebola virus, and Marburg virus require careful handling precisely because human "
        "susceptibility is established."
    ),
    "taxonomic_family_enc": (
        "Viral family captures inherited biological properties not always visible from one trait alone — replication "
        "strategy, virion structure, host tropism, and typical disease phenotype. Filoviridae includes Ebola and Marburg, "
        "strongly associated with severe hemorrhagic disease and high-containment work, while Papillomaviridae includes "
        "viruses managed under lower containment because infection is often localized and clinically familiar."
    ),
    "genome_type_enc": (
        "Specific Baltimore genome subtype refines the broader DNA/RNA distinction. ssRNA− viruses — Marburg, Ebola, "
        "Lassa, Nipah, Rabies, Influenza A — require virus-encoded polymerases and include several severe zoonotic "
        "pathogens. In contrast, dsDNA viruses such as Adenovirus and HPV often show more stable replication, "
        "though exceptions like Variola virus show subtype must be interpreted alongside clinical severity."
    ),
    "is_enveloped": (
        "Viral envelopes carry glycoproteins mediating host-cell attachment, membrane fusion, tissue tropism, and immune "
        "escape. HIV, Ebola virus, SARS-CoV-2, Nipah virus, and Influenza A use surface proteins to alter entry pathways "
        "and evade host recognition. However, envelope alone does not determine biosafety level — Norovirus and "
        "Adenovirus can also be highly transmissible or environmentally stable without an envelope."
    ),
    "is_zoonotic": (
        "Zoonotic viruses have crossed species barriers or maintain animal reservoirs that can repeatedly expose humans "
        "to new viral diversity. Cross-species transmission often selects for receptor flexibility, immune evasion, and "
        "ecological persistence. SARS-CoV-2, Nipah, Rabies, Lassa, and Influenza A all illustrate how animal-associated "
        "viruses become major biosafety concerns once human infection is established."
    ),
    "host_breadth": (
        "Host breadth reflects how many host species a virus can infect, serving as a proxy for receptor flexibility "
        "and ecological opportunity. Influenza A and Rabies lyssavirus demonstrate how broad host associations provide "
        "more routes for maintenance, reassortment, or repeated spillover. However, broad host range does not always "
        "mean severe human disease — it contributes more to emergence than to containment severity."
    ),
    "is_segmented": (
        "Segmented genomes allow reassortment: when two related viruses infect the same cell, they can exchange genome "
        "segments and generate new combinations. Influenza A is the canonical example — reassortment between avian, "
        "swine, and human lineages can generate pandemic-capable strains. Its lower weight likely occurs because "
        "segmentation increases novelty but does not by itself determine whether the resulting virus requires RG4-level containment."
    ),
    "is_vector_borne": (
        "This is the most biologically significant finding: vector-borne transmission strongly affects ecological spread "
        "but does not automatically increase intrinsic biosafety severity. Dengue, Zika, and Chikungunya can expand "
        "geographically through mosquitoes, yet they are not classified like Marburg or Ebola — which may be "
        "non-vector-borne but cause severe high-consequence disease. Vectors increase exposure opportunity and geographic "
        "reach, but WHO Risk Group classification is more strongly tied to disease severity, treatment availability, "
        "and containment consequences."
    ),
}

BIO_RISK = {
    "is_dna": {
        0: (
            "🔴 RNA Virus",
            "RNA viruses rely on RNA-dependent RNA polymerases, which have higher error rates than DNA replication systems. "
            "This generates genetic diversity supporting immune escape, host switching, and rapid adaptation — especially "
            "in Ebola virus, Marburg virus, Lassa virus, SARS-CoV-2, Nipah virus, Rabies lyssavirus, and Influenza A. "
            "Because many severe zoonotic and high-containment viruses are RNA viruses, RNA status is a strong upward "
            "biosafety signal.",
            "HIGH containment signal"
        ),
        1: (
            "🟢 DNA Virus",
            "DNA viruses generally have more stable genomes because DNA replication is often associated with stronger "
            "proofreading and lower mutation rates. This stability can make many DNA viruses more predictable and "
            "manageable through vaccines or established containment procedures, as seen with Adenovirus, HPV, and "
            "Herpesviruses. However, Variola virus shows that a DNA virus can still require extreme control when "
            "disease severity and public health consequences are high.",
            "LOWER containment signal — with exceptions"
        ),
    },
    "is_enveloped": {
        1: (
            "🔴 Enveloped",
            "Enveloped viruses carry lipid membranes decorated with viral glycoproteins mediating attachment, fusion, "
            "and immune escape. HIV, Ebola virus, SARS-CoV-2, Nipah virus, and Influenza A use envelope-associated "
            "proteins to alter entry pathways and evade host recognition. Envelope-mediated entry can support efficient "
            "infection of human cells, but containment risk still depends on severity, transmission, and countermeasures.",
            "MODERATE containment signal"
        ),
        0: (
            "🟢 Non-enveloped",
            "Non-enveloped viruses lack a lipid membrane and often rely on structurally resistant capsids to survive "
            "outside the host. Norovirus, Adenovirus, and HPV illustrate how non-enveloped viruses can remain stable "
            "in the environment and transmit efficiently. This reduces some cell-entry complexity, but environmental "
            "stability creates its own exposure risks.",
            "MIXED — stability can compensate"
        ),
    },
    "is_segmented": {
        1: (
            "🟡 Segmented Genome",
            "A segmented genome allows reassortment when two related viruses infect the same host cell and exchange "
            "segments. Influenza A is the canonical example: reassortment between avian, swine, and human strains can "
            "generate novel antigenic combinations with pandemic potential. This trait is especially relevant for "
            "emergence risk, although segmentation alone does not determine the highest containment tier.",
            "EMERGENCE signal — pandemic risk"
        ),
        0: (
            "🟢 Non-segmented",
            "Non-segmented viruses evolve through point mutation and selection rather than whole-segment reassortment. "
            "This constrains the speed of large antigenic shifts compared with Influenza A. However, non-segmented "
            "viruses — Ebola virus, Marburg virus, SARS-CoV-2, Rabies lyssavirus — can still be highly dangerous "
            "because severe disease does not require genome segmentation.",
            "LOWER reassortment signal — not inherently safer"
        ),
    },
    "is_vector_borne": {
        1: (
            "⚠️ Vector-borne — KEY FINDING",
            "Vector-borne viruses use arthropods such as mosquitoes or ticks to move between hosts, increasing geographic "
            "reach and ecological exposure. Dengue virus, Zika virus, Yellow fever virus, and Chikungunya virus show how "
            "vectors can amplify outbreak potential across climate-dependent regions. The BioRiskNet core finding: "
            "vector transmission strongly supports spillover and spread but contributes almost nothing to intrinsic "
            "biosafety severity — Dengue can spread widely while Marburg is not mosquito-borne yet requires BSL-4.",
            "PRIMARY spillover signal · ZERO containment severity signal"
        ),
        0: (
            "🟢 Non-vector-borne",
            "Absence of vector transmission should not be interpreted as safety. Marburg virus, Ebola virus, SARS-CoV-2, "
            "Nipah virus, Rabies lyssavirus, and Lassa virus are not primarily mosquito-borne yet pose serious laboratory "
            "and public health hazards through direct contact, respiratory exposure, or reservoir-associated routes. "
            "Vectors expand ecological reach; severe containment risk can arise through completely different mechanisms.",
            "NEUTRAL containment severity signal"
        ),
    },
    "is_zoonotic": {
        1: (
            "🔴 Zoonotic",
            "Zoonotic viruses have demonstrated capacity to move between animal reservoirs and humans, implying some "
            "compatibility with human receptors, immune environments, or exposure pathways. SARS-CoV-2, Nipah, "
            "Rabies lyssavirus, Lassa, Ebola, and Influenza A illustrate how animal-associated viruses can become "
            "major biosafety concerns once human infection occurs. Host-virus coevolution means these viruses often "
            "carry immune-evasion strategies shaped in non-human reservoirs before entering humans.",
            "HIGH emergence signal · MODERATE containment signal"
        ),
        0: (
            "🟢 Not Zoonotic",
            "A virus with no known zoonotic origin may be strictly human-adapted, restricted to non-human hosts, or "
            "under-detected in current surveillance. Lower ecological emergence risk is expected when there is no "
            "evidence of animal-to-human movement, but absence of evidence does not prove absence of risk. "
            "Human-adapted viruses can still require careful containment if they cause severe disease or transmit efficiently.",
            "LOWER emergence signal — surveillance-dependent"
        ),
    },
    "infects_humans": {
        1: (
            "🔴 Confirmed Human Infection",
            "Confirmed human infection is a core biosafety concern because laboratory exposure has a direct route to "
            "human disease. If a virus is known to infect humans — as with SARS-CoV-2, Rabies lyssavirus, Influenza A, "
            "Ebola virus, and Marburg virus — laboratory handling must assume human susceptibility. This trait directly "
            "links biological hazard to real-world WHO and CDC biosafety containment decisions.",
            "HIGH containment signal"
        ),
        0: (
            "🟡 Not Confirmed",
            "No confirmed human infection reduces immediate containment concern — there is no documented evidence the "
            "virus naturally infects humans. However, this may reflect limited sampling rather than true biological "
            "inability. A virus may be absent from human-host databases yet still deserve caution if it belongs to a "
            "high-risk family or shares concerning genome traits with known human pathogens.",
            "LOWER confidence — not absolute safety"
        ),
    },
}

SHAP_BIO = {
    "is_dna": {
        "positive": (
            "RNA genome status contributed toward higher containment classification because RNA replication generates "
            "diversity rapidly through error-prone polymerases. This can help viruses adapt to new hosts, escape immune "
            "pressure, and produce outbreak-prone variants, as seen with SARS-CoV-2, Influenza A, Ebola virus, "
            "Lassa virus, and Nipah virus. An RNA genome is a biologically plausible high-risk signal."
        ),
        "negative": (
            "DNA genome status contributed toward lower containment because it suggests greater genomic stability and "
            "slower evolutionary change. Adenovirus, HPV, and many Herpesviruses illustrate how DNA viruses can be "
            "well-characterised and often manageable under standard laboratory precautions. This does not mean DNA "
            "viruses are harmless, but it reduces the signal associated with rapid adaptation."
        ),
    },
    "infects_humans": {
        "positive": (
            "Confirmed human infection increased containment concern because accidental exposure has a direct route to "
            "human disease. If a virus is known to infect humans — as with SARS-CoV-2, Rabies lyssavirus, Influenza A, "
            "Ebola virus, and Marburg virus — laboratory handling must assume human susceptibility. This trait strongly "
            "links biological hazard to real-world biosafety decision-making."
        ),
        "negative": (
            "No confirmed human infection reduced immediate containment concern — no documented evidence that the virus "
            "naturally infects humans. However, this may reflect limited sampling rather than true biological inability. "
            "For poorly studied animal viruses, this should be interpreted cautiously, especially if other traits "
            "resemble known zoonotic viruses."
        ),
    },
    "taxonomic_family_enc": {
        "positive": (
            "Membership in a high-risk viral family contributed toward higher containment because family-level biology "
            "reflects shared replication strategy, virion structure, tissue tropism, and disease patterns. Filoviridae "
            "(Ebola, Marburg) is strongly associated with severe haemorrhagic disease. Arenaviridae and Paramyxoviridae "
            "also contain serious zoonotic pathogens such as Lassa virus and Nipah virus."
        ),
        "negative": (
            "Membership in a lower-risk or clinically familiar family contributed toward lower containment when that "
            "lineage is associated with manageable disease or established containment procedures. Papillomaviridae, "
            "Adenoviridae, and Polyomaviridae contain many viruses important medically but not treated like RG4 agents. "
            "This reflects established biological precedent rather than one isolated property."
        ),
    },
    "genome_type_enc": {
        "positive": (
            "This genome subtype — particularly ssRNA− — contributed toward higher containment because it encompasses "
            "multiple severe zoonotic viruses: Ebola, Marburg, Lassa, Nipah, Rabies lyssavirus, and Influenza A. "
            "These viruses combine error-prone replication, immune evasion, and in many cases limited therapeutics. "
            "A virus with this genome architecture carries a recognisable high-risk biological signature."
        ),
        "negative": (
            "This genome subtype contributed toward lower containment because it is associated with more stable "
            "replication or lower severe-disease precedent. dsDNA and ssDNA viruses often show slower evolutionary "
            "change than RNA viruses, and many — Adenovirus, HPV, Parvoviruses — are managed under lower containment. "
            "The genome architecture does not strongly resemble the highest-risk viral groups."
        ),
    },
    "is_enveloped": {
        "positive": (
            "Envelope status contributed toward higher containment because envelope glycoproteins mediate receptor "
            "binding, membrane fusion, cell entry, and immune escape. HIV, Ebola virus, SARS-CoV-2, Nipah virus, "
            "and Influenza A depend on envelope-associated proteins for host-cell entry and pathogenesis. An envelope "
            "may signal enhanced ability to enter specific host tissues and evade immune barriers."
        ),
        "negative": (
            "Lack of an envelope contributed toward lower containment by removing membrane-fusion machinery associated "
            "with many severe systemic infections. However, non-enveloped viruses — Norovirus, Adenovirus, HPV — can "
            "still be transmissible or persistent because their capsids are environmentally stable. This should be "
            "read as a lower severe-systemic-virus signal, not as absence of hazard."
        ),
    },
    "is_zoonotic": {
        "positive": (
            "Zoonotic origin contributed toward higher containment because the virus has ecological access to animal "
            "reservoirs and some capacity to cross host barriers. SARS-CoV-2, Nipah virus, Lassa virus, Rabies "
            "lyssavirus, Influenza A, Ebola virus, and Marburg virus show how zoonotic viruses can create serious "
            "laboratory and public health risks. Cross-species movement often reflects receptor flexibility and "
            "immune tolerance."
        ),
        "negative": (
            "Absence of known zoonotic origin contributed toward lower emergence concern — no documented "
            "animal-to-human pathway. This may apply to host-restricted, human-adapted, or poorly sampled viruses. "
            "The biological interpretation should remain cautious because zoonotic status depends heavily on "
            "surveillance quality."
        ),
    },
    "host_breadth": {
        "positive": (
            "Broad host breadth contributed toward higher concern because it suggests receptor flexibility and the "
            "ability to persist across multiple ecological niches. Influenza A can circulate across birds, pigs, and "
            "humans, while Rabies lyssavirus is maintained across diverse mammals. A broad host range increases "
            "opportunities for adaptation, reassortment, and repeated human exposure."
        ),
        "negative": (
            "Narrow host breadth contributed toward lower emergence concern because the virus appears restricted in "
            "hosts it can infect. A narrow host range reduces ecological pathways leading to human exposure. However, "
            "narrow-host viruses such as Marburg virus can still be extremely dangerous once human infection occurs — "
            "this trait lowers emergence breadth more than disease severity."
        ),
    },
    "is_segmented": {
        "positive": (
            "Segmentation contributed toward higher emergence concern because genome segments can reassort when two "
            "related viruses infect the same host cell. Influenza A demonstrates this clearly — reassortment can "
            "generate antigenically novel strains with pandemic potential. The biological meaning is evolutionary "
            "flexibility rather than guaranteed severe disease."
        ),
        "negative": (
            "A non-segmented genome contributed toward lower reassortment concern because the virus cannot exchange "
            "whole genome segments in the way Influenza A does. Evolution can still occur through mutation and "
            "selection, as seen with SARS-CoV-2, Ebola virus, and Rabies lyssavirus. This reduces one pathway of "
            "sudden evolutionary change but does not remove biosafety concern."
        ),
    },
    "is_vector_borne": {
        "positive": (
            "⚠️ KEY FINDING — Vector-borne status contributed almost nothing to this containment classification, "
            "even though vectors like mosquitoes and ticks can connect viruses to new hosts and new geographic regions. "
            "Dengue virus, Zika virus, Yellow fever virus, and Chikungunya virus show how arthropods amplify "
            "transmission opportunity. BioRiskNet's central finding: vectors increase spread potential more than "
            "intrinsic danger after infection."
        ),
        "negative": (
            "⚠️ KEY FINDING — Non-vector-borne status does not protect against high containment risk. Marburg virus, "
            "Ebola virus, Nipah virus, SARS-CoV-2, Rabies lyssavirus, and Lassa virus are not primarily mosquito-borne, "
            "yet they can require serious biosafety controls because of severe disease, human infectivity, or limited "
            "countermeasures. This confirms that vector transmission is mainly an ecological spread trait, "
            "not a direct severity trait."
        ),
    },
}

CONFIDENCE_EXPLAIN = {
    "high": (
        "✅ High confidence — the virus has a biologically coherent profile that strongly resembles a known containment "
        "category. For example, Marburg virus combines ssRNA− genome type, Filoviridae membership, envelope status, and "
        "confirmed human infection, making its high-containment placement biologically unambiguous."
    ),
    "moderate": (
        "🟡 Moderate confidence — the virus contains mixed biological signals, such as RNA status but limited "
        "human-infection evidence, or envelope status combined with a lower-risk family background. SARS-CoV-2 in this "
        "dataset is a good example: ecological traits supported RG3 placement even though some taxonomic fields were "
        "missing or unmatched."
    ),
    "low": (
        "⚠️ Low confidence — key biological information is likely missing: genome type, taxonomic family, confirmed "
        "human infection, or host breadth carry most of the containment signal. Without these values, it is harder "
        "to decide whether the virus resembles Adenovirus-like lower-risk patterns or Ebola/Marburg-like higher-risk "
        "patterns. Add more feature data to improve this result."
    ),
}

SPILLOVER_EXPLAIN = {
    "high": (
        "Ecological profile strongly matches animal-to-human emergence — broad host breadth, zoonotic history, "
        "mammalian associations, or vector involvement. Olival-style ecology supports this: viruses linked to multiple "
        "hosts have more opportunities to encounter humans and adapt across species boundaries. Influenza A, "
        "Rabies lyssavirus, Nipah virus, and SARS-CoV-2 illustrate how host range and animal reservoirs increase "
        "emergence risk."
    ),
    "medium": (
        "Mixed ecological profile — the virus has some animal associations or host flexibility, but not enough "
        "evidence to indicate strong human emergence potential. It may be zoonotic but narrow in host range, or broad "
        "in host associations but lacking confirmed human infection. This tier should guide targeted surveillance "
        "rather than immediate high-alert classification."
    ),
    "low": (
        "Available ecology does not strongly suggest animal-to-human emergence under current evidence. This may "
        "reflect true host restriction, limited contact with humans, or incomplete surveillance data. Low spillover "
        "probability should reduce surveillance priority relative to viruses like Nipah, Influenza A, or SARS-CoV-2, "
        "but should not be interpreted as permanent biological safety."
    ),
}
