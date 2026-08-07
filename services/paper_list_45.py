"""
Daftar 45 judul paper dari file Khananda Raihansyah-257110201004-Paper summary.xlsx
dan detail-review.docx yang menjadi bahan Rangkuman Review.
Digunakan untuk memfilter data dari tabel paper_extractions.
"""

PAPER_TITLES_45 = [
    "Domain Specific Modeling (DSM) as a Service for the Internet of Things & Services",
    "Access-based Lightweight Physical Layer Authentication for the Internet of Things Devices",
    "Sense-Deliberate-Act Cognitive Agents for Sense-Compute-Control Applications in the Internet of Things & Services",
    "Fine Time Measurement for the Internet of Things: A Practical Approach Using ESP32",
    "Cloud Deployment Tradeoffs for the Analysis of Spatially-Distributed Systems of Internet-of-Things",
    "Climate Monitoring using Internet of X-Things",
    "Coverage and Deployment Analysis of Narrowband Internet of Things in the Wild",
    "Fair Pricing In Heterogeneous Internet of Things Wireless Access Networks Using Crowdsourcing",
    "IoTScent: Enhancing Forensic Capabilities in Internet of Things Gateways",
    "Blockchain-enabled Internet of Medical Things to Combat COVID-19",
    "RIS-aided Wireless-Powered Backscatter Communications for Sustainable Internet of Underground Things",
    "Wireless Laser Power Transfer for Low-altitude Uncrewed Aerial Vehicle-assisted Internet of Things: Paradigms, Challenges, and Solutions",
    "Massive Wireless Energy Transfer with Multiple Power Beacons for very large Internet of Things",
    "An Optimal Relay Scheme for Outage Minimization in Fog-based Internet-of-Things (IoT) Networks",
    "A Computationally Intelligent Hierarchical Authentication and Key Establishment Framework for Internet of Things",
    "Introducing Federated Learning into Internet of Things ecosystems -- preliminary considerations",
    "Energy Allocation for Multi-User Cooperative Molecular Communication Systems in the Internet of Bio-Nano Things",
    "Reconfigurable Intelligent Surface for Internet of Robotic Things",
    "Revisiting the Internet of Things: New Trends, Opportunities and Grand Challenges",
    "Topology-Driven Attribute Recovery for Attribute Missing Graph Learning in Social Internet of Things",
    "Cellular Communications in Ocean Waves for Maritime Internet of Things",
    "Local Differential Privacy based Federated Learning for Internet of Things",
    "Device Scheduling and Assignment in Hierarchical Federated Learning for Internet of Things",
    "AnoML-IoT: An End to End Re-configurable Multi-protocol Anomaly Detection Pipeline for Internet of Things",
    "A Trustworthy and Consistent Blockchain Oracle Scheme for Industrial Internet of Things",
    "Escaping Barren Plateaus in Variational Quantum Algorithms Using Negative Learning Rate in Quantum Internet of Things",
    "Integrating Usage Control into Distributed Ledger Technology for Internet of Things Privacy",
    "Energy-Efficient Real-Time Heart Monitoring on Edge-Fog-Cloud Internet-of-Medical-Things",
    "Efficient Prompting for LLM-based Generative Internet of Things",
    "On the Performance of Non-Terrestrial Networks to Support the Internet of Things",
    "R-PMAC: A Robust Preamble Based MAC Mechanism Applied in Industrial Internet of Things",
    "Physics-Enhanced Graph Neural Networks For Soft Sensing in Industrial Internet of Things",
    "Air-to-Ground Communications for Internet of Things: UAV-based Coverage Hole Detection and Recovery",
    "Energy-Efficient Index and Code Index Modulations for Spread CPM Signals in Internet of Things",
    "Adversarial Predictions of Data Distributions Across Federated Internet-of-Things Devices",
    "In Situ Motor Fault Diagnosis Using Enhanced Convolutional Neural Network in an Embedded System",
    "Development of an augmented reality-based scaffold to improve the learning experience of engineering students in embedded system course",
    "Real-Time Apple Detection System Using Embedded Systems With Hardware Accelerators: An Edge AI Application",
    "TensorFlow Lite Micro: Embedded Machine Learning on TinyML Systems",
    "Mobilenet-SSDv2: An Improved Object Detection Model for Embedded Systems",
    "Animal Behavior Classification via Deep Learning on Embedded Systems",
    "Teledrive: An Embodied AI based Telepresence System",
    "Multimodal system for skin cancer detection",
    "IsolateGPT: An Execution Isolation Architecture for LLM-Based Agentic Systems",
    "Development of an augmented reality\u2010based scaffold to improve the learning experience of engineering students in embedded system course",
]

# Normalisasi untuk pencocokan fuzzy (lowercase, strip)
PAPER_TITLES_45_NORMALIZED = [t.lower().strip() for t in PAPER_TITLES_45]
