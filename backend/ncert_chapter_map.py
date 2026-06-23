"""
NCERT Subject Chapter Name Lookup Tables.

Maps (class_level: int, chapter_number: int) -> official NCERT chapter title.
"""

NCERT_PHYSICS_CHAPTERS: dict[tuple[int, int], str] = {
    # --- Class 11 ---
    (11, 1):  "Physical World",
    (11, 2):  "Units and Measurement",
    (11, 3):  "Motion in a Straight Line",
    (11, 4):  "Motion in a Plane",
    (11, 5):  "Laws of Motion",
    (11, 6):  "Work, Energy and Power",
    (11, 7):  "Systems of Particles and Rotational Motion",
    (11, 8):  "Gravitation",
    # Additional Class 11 chapters (if more PDFs are added later)
    (11, 9):  "Mechanical Properties of Solids",
    (11, 10): "Mechanical Properties of Fluids",
    (11, 11): "Thermal Properties of Matter",
    (11, 12): "Thermodynamics",
    (11, 13): "Kinetic Theory",
    (11, 14): "Oscillations",
    (11, 15): "Waves",

    # --- Class 12 ---
    (12, 1):  "Electric Charges and Fields",
    (12, 2):  "Electrostatic Potential and Capacitance",
    (12, 3):  "Current Electricity",
    (12, 4):  "Moving Charges and Magnetism",
    (12, 5):  "Magnetism and Matter",
    (12, 6):  "Electromagnetic Induction",
    # Additional Class 12 chapters (if more PDFs are added later)
    (12, 7):  "Alternating Current",
    (12, 8):  "Electromagnetic Waves",
    (12, 9):  "Ray Optics and Optical Instruments",
    (12, 10): "Wave Optics",
    (12, 11): "Dual Nature of Radiation and Matter",
    (12, 12): "Atoms",
    (12, 13): "Nuclei",
    (12, 14): "Semiconductor Electronics",
}


NCERT_CHEMISTRY_CHAPTERS: dict[tuple[int, int], str] = {
    # --- Class 11 ---
    (11, 1): "Some Basic Concepts of Chemistry",
    (11, 2): "Structure of Atom",
    (11, 3): "Classification of Elements and Periodicity in Properties",
    (11, 4): "Chemical Bonding and Molecular Structure",
    (11, 5): "Thermodynamics",
    (11, 6): "Equilibrium",
    (11, 7): "Redox Reactions",
    (11, 8): "Organic Chemistry: Some Basic Principles and Techniques",
    (11, 9): "Hydrocarbons",
    # --- Class 12 ---
    (12, 1): "Solutions",
    (12, 2): "Electrochemistry",
    (12, 3): "Chemical Kinetics",
    (12, 4): "The d- and f- Block Elements",
    (12, 5): "Coordination Compounds",
    (12, 6): "Haloalkanes and Haloarenes",
    (12, 7): "Alcohols, Phenols and Ethers",
    (12, 8): "Aldehydes, Ketones and Carboxylic Acids",
    (12, 9): "Amines",
    (12, 10): "Biomolecules",
}

NCERT_BIOLOGY_CHAPTERS: dict[tuple[int, int], str] = {
    # --- Class 11 ---
    (11, 1): "The Living World",
    (11, 2): "Biological Classification",
    (11, 3): "Plant Kingdom",
    (11, 4): "Animal Kingdom",
    (11, 5): "Morphology of Flowering Plants",
    (11, 6): "Anatomy of Flowering Plants",
    (11, 7): "Structural Organisation in Animals",
    (11, 8): "Cell: The Unit of Life",
    (11, 9): "Biomolecules",
    (11, 10): "Cell Cycle and Cell Division",
    (11, 11): "Photosynthesis in Higher Plants",
    (11, 12): "Respiration in Plants",
    (11, 13): "Plant Growth and Development",
    (11, 14): "Breathing and Exchange of Gases",
    (11, 15): "Body Fluids and Circulation",
    (11, 16): "Excretory Products and their Elimination",
    (11, 17): "Locomotion and Movement",
    (11, 18): "Neural Control and Coordination",
    (11, 19): "Chemical Coordination and Integration",
    # --- Class 12 ---
    (12, 1): "Sexual Reproduction in Flowering Plants",
    (12, 2): "Human Reproduction",
    (12, 3): "Reproductive Health",
    (12, 4): "Principles of Inheritance and Variation",
    (12, 5): "Molecular Basis of Inheritance",
    (12, 6): "Evolution",
    (12, 7): "Human Health and Disease",
    (12, 8): "Microbes in Human Welfare",
    (12, 9): "Biotechnology: Principles and Processes",
    (12, 10): "Biotechnology and its Applications",
    (12, 11): "Organisms and Populations",
    (12, 12): "Ecosystem",
    (12, 13): "Biodiversity and Conservation",
}

def get_chapter_name(subject: str, class_level: int, chapter_number: int) -> str:
    """Return the official NCERT chapter title, or a fallback string."""
    if subject == "Physics":
        mapping = NCERT_PHYSICS_CHAPTERS
    elif subject == "Chemistry":
        mapping = NCERT_CHEMISTRY_CHAPTERS
    elif subject == "Biology":
        mapping = NCERT_BIOLOGY_CHAPTERS
    else:
        mapping = {}

    return mapping.get(
        (class_level, chapter_number),
        f"{subject} Class {class_level} Chapter {chapter_number}"
    )


def parse_ncert_filename(filename: str) -> tuple[str, int, int, int] | None:
    """
    Parse a NCERT PDF filename like 'leph101.pdf' or 'lech206.pdf'.

    Returns (subject, class_level, chapter_number, raw_code) or None for supplementary files.

    Naming convention prefix:
      leph -> Physics
      lech -> Chemistry
      lebo -> Biology / Botany
      lezo -> Zoology
    """
    import re
    base = filename.lower().replace(".pdf", "")
    
    # Match generic prefix (4 chars) + class (1 or 2) + chapter (2 digits)
    # k = Class 11, l = Class 12
    match = re.fullmatch(r"([kl]e(?:ph|ch|bo|zo))([12])(\d{2})", base)
    if not match:
        return None  # supplementary or unrecognised
        
    prefix = match.group(1)
    if prefix.endswith("ph"):
        subject = "Physics"
    elif prefix.endswith("ch"):
        subject = "Chemistry"
    elif prefix.endswith("bo"):
        subject = "Biology"
    elif prefix.endswith("zo"):
        subject = "Zoology"
    else:
        subject = "Unknown"

    part = int(match.group(2))   # 1 or 2
    raw_ch = int(match.group(3)) # e.g. 01, 06
    class_level = 11 if prefix.startswith('k') else 12
    
    chapter_number = raw_ch      # 01 → 1, 06 → 6  (already 1-based)
    
    # Handle offsets for Book 2 files that restart numbering at 01
    if part == 2:
        if subject == "Chemistry" and class_level == 12:
            chapter_number += 5
            
    return subject, class_level, chapter_number, int(f"{part}{match.group(3)}")
