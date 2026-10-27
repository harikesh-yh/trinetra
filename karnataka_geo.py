"""Curated Karnataka geography: real districts and sample police-station points
with approximate lat/long. Used by the synthetic FIR generator and the map UI.

These coordinates are real-enough for demo purposes (district HQ towns and a few
well-known localities). They are NOT authoritative survey points.
"""

# District -> (district HQ lat, lng). A representative subset of Karnataka's 31 districts.
DISTRICTS = {
    "Bengaluru City": (12.9716, 77.5946),
    "Bengaluru Rural": (13.2257, 77.5750),
    "Mysuru": (12.2958, 76.6394),
    "Mangaluru (Dakshina Kannada)": (12.9141, 74.8560),
    "Hubballi-Dharwad": (15.3647, 75.1240),
    "Belagavi": (15.8497, 74.4977),
    "Kalaburagi": (17.3297, 76.8343),
    "Ballari": (15.1394, 76.9214),
    "Tumakuru": (13.3409, 77.1010),
    "Shivamogga": (13.9299, 75.5681),
    "Vijayapura": (16.8302, 75.7100),
    "Davanagere": (14.4644, 75.9218),
    "Udupi": (13.3409, 74.7421),
    "Hassan": (13.0072, 76.0962),
    "Mandya": (12.5223, 76.8954),
}

# A handful of named police stations per district with jittered coordinates.
# Structure: district -> list of (station_name, lat, lng).
STATIONS = {
    "Bengaluru City": [
        ("Cubbon Park PS", 12.9763, 77.5929),
        ("Koramangala PS", 12.9352, 77.6245),
        ("Whitefield PS", 12.9698, 77.7500),
        ("Jayanagar PS", 12.9250, 77.5938),
        ("Indiranagar PS", 12.9719, 77.6412),
        ("Electronic City PS", 12.8452, 77.6602),
    ],
    "Bengaluru Rural": [
        ("Devanahalli PS", 13.2437, 77.7117),
        ("Hoskote PS", 13.0707, 77.7984),
        ("Nelamangala PS", 13.0996, 77.3936),
    ],
    "Mysuru": [
        ("Devaraja PS", 12.3074, 76.6541),
        ("Krishnaraja PS", 12.3052, 76.6553),
        ("Nazarbad PS", 12.2958, 76.6628),
        ("Vijayanagar PS", 12.3206, 76.6203),
    ],
    "Mangaluru (Dakshina Kannada)": [
        ("Pandeshwar PS", 12.8657, 74.8426),
        ("Kadri PS", 12.8920, 74.8560),
        ("Surathkal PS", 13.0050, 74.7943),
    ],
    "Hubballi-Dharwad": [
        ("Hubballi City PS", 15.3500, 75.1300),
        ("Dharwad City PS", 15.4589, 75.0078),
        ("Gokul Road PS", 15.3411, 75.1010),
    ],
    "Belagavi": [
        ("Camp PS", 15.8702, 74.5260),
        ("Tilakwadi PS", 15.8527, 74.5012),
        ("Market PS", 15.8559, 74.5089),
    ],
    "Kalaburagi": [
        ("Brahmpur PS", 17.3290, 76.8290),
        ("Station Bazar PS", 17.3380, 76.8290),
    ],
    "Ballari": [
        ("Ballari City PS", 15.1400, 76.9200),
        ("Cowl Bazar PS", 15.1486, 76.9250),
    ],
    "Tumakuru": [
        ("Tumakuru Town PS", 13.3392, 77.1140),
        ("Kyathsandra PS", 13.3680, 77.1300),
    ],
    "Shivamogga": [
        ("Kote PS", 13.9300, 75.5700),
        ("Doddapet PS", 13.9255, 75.5680),
    ],
    "Vijayapura": [
        ("Gandhi Chowk PS", 16.8270, 75.7150),
        ("Adarsh Nagar PS", 16.8350, 75.7200),
    ],
    "Davanagere": [
        ("Davanagere Town PS", 14.4644, 75.9218),
        ("Vidyanagar PS", 14.4480, 75.9100),
    ],
    "Udupi": [
        ("Udupi Town PS", 13.3409, 74.7421),
        ("Malpe PS", 13.3500, 74.7050),
    ],
    "Hassan": [
        ("Hassan Town PS", 13.0072, 76.0962),
        ("Pension Mohalla PS", 13.0100, 76.1000),
    ],
    "Mandya": [
        ("Mandya West PS", 12.5223, 76.8954),
        ("Mandya East PS", 12.5260, 76.9010),
    ],
}


def all_stations():
    """Yield (district, station_name, lat, lng) for every station."""
    for district, stations in STATIONS.items():
        for name, lat, lng in stations:
            yield district, name, lat, lng
