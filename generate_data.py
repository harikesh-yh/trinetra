"""TRINETRA synthetic FIR data generator.

Builds a referentially-consistent SQLite database on the FIR schema, with PLANTED
structures so every analytics feature has something to demonstrate:

  * co-accused networks + repeat offenders (graph engine, repeat-offender tracking)
  * geographic hotspots (hotspot map / forecast)
  * time-window spikes (anomaly watch)
  * false-case clusters, cstype=B (detection-quality)
  * response-lag outliers (response-lag module)
  * demographic victimization patterns + seasonality (socio-economic, trends)

Usage:
    python generate_data.py [--db trinetra.db] [--cases 4000] [--seed 42]

Re-running drops and rebuilds the database.
"""
from __future__ import annotations

import argparse
import os
import random
import sqlite3
from datetime import date, datetime, timedelta

from faker import Faker

from app.data.karnataka_geo import DISTRICTS, STATIONS

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA = os.path.join(HERE, "app", "schema.sql")

# ---------- Reference vocab ----------
GENDERS = ["Male", "Female", "Other"]
RELIGIONS = ["Hindu", "Muslim", "Christian", "Jain", "Sikh", "Buddhist", "Other"]
CASTES = ["General", "OBC", "SC", "ST"]
OCCUPATIONS = [
    "Daily Wage Labourer", "Student", "Farmer", "IT Professional", "Shopkeeper",
    "Homemaker", "Driver", "Unemployed", "Government Employee", "Business Owner",
]
CASE_CATEGORIES = ["FIR", "UDR", "PAR", "ZeroFIR"]
GRAVITY = ["Heinous", "Non-Heinous"]
CASE_STATUS = ["Under Investigation", "Chargesheeted", "Closed", "Pending Trial"]
RANKS = ["PC", "HC", "ASI", "SI", "PSI", "PI", "DySP", "SP"]
DESIGNATIONS = ["Constable", "Investigating Officer", "Station House Officer", "Inspector"]
ACTS = ["IPC", "Arms Act", "NDPS Act", "IT Act", "MV Act", "Karnataka Police Act"]

# Crime taxonomy: major head -> [(subhead, gravity, base_weight)]
CRIME_TAXONOMY = {
    "Body Offences": [
        ("Murder", "Heinous", 2),
        ("Attempt to Murder", "Heinous", 3),
        ("Hurt / Assault", "Non-Heinous", 12),
        ("Kidnapping", "Heinous", 2),
    ],
    "Property Offences": [
        ("Chain Snatching", "Non-Heinous", 14),
        ("House Burglary", "Non-Heinous", 12),
        ("Vehicle Theft", "Non-Heinous", 16),
        ("Robbery", "Heinous", 6),
        ("Pickpocketing", "Non-Heinous", 9),
    ],
    "Economic Offences": [
        ("Cheating / Fraud", "Non-Heinous", 8),
        ("Online Financial Fraud", "Non-Heinous", 10),
    ],
    "Crimes Against Women": [
        ("Domestic Violence", "Non-Heinous", 7),
        ("Eve Teasing / Harassment", "Non-Heinous", 6),
    ],
    "Narcotics": [
        ("Drug Possession", "Non-Heinous", 5),
        ("Drug Trafficking", "Heinous", 2),
    ],
}

SECTION_BY_SUBHEAD = {
    "Murder": ("IPC", "302", "Murder"),
    "Attempt to Murder": ("IPC", "307", "Attempt to murder"),
    "Hurt / Assault": ("IPC", "323", "Voluntarily causing hurt"),
    "Kidnapping": ("IPC", "363", "Kidnapping"),
    "Chain Snatching": ("IPC", "379", "Theft"),
    "House Burglary": ("IPC", "457", "Lurking house-trespass"),
    "Vehicle Theft": ("IPC", "379", "Theft"),
    "Robbery": ("IPC", "392", "Robbery"),
    "Pickpocketing": ("IPC", "379", "Theft"),
    "Cheating / Fraud": ("IPC", "420", "Cheating"),
    "Online Financial Fraud": ("IT Act", "66D", "Cheating by personation using computer"),
    "Domestic Violence": ("IPC", "498A", "Cruelty by husband or relatives"),
    "Eve Teasing / Harassment": ("IPC", "354", "Assault on woman"),
    "Drug Possession": ("NDPS Act", "20", "Possession of narcotics"),
    "Drug Trafficking": ("NDPS Act", "21", "Trafficking of narcotics"),
}

BRIEF_TEMPLATES = {
    "Chain Snatching": [
        "Complainant reported that two persons on a motorcycle snatched a gold chain near {loc} and fled towards {dir}.",
        "Victim's gold chain weighing approx {wt} grams snatched by miscreants on a bike at {loc}.",
    ],
    "Vehicle Theft": [
        "Two-wheeler parked outside {loc} found missing. Owner suspects organized theft ring.",
        "Car stolen from {loc} parking; CCTV shows two suspects breaking the lock.",
    ],
    "House Burglary": [
        "House at {loc} broken into while occupants away; cash and jewellery missing.",
        "Burglars entered through rear window at {loc} and decamped with valuables.",
    ],
    "Robbery": [
        "Armed group robbed a shop at {loc} at gunpoint and escaped with cash.",
        "Complainant waylaid near {loc} and robbed of phone and wallet.",
    ],
    "Murder": [
        "Body found near {loc}; suspected homicide, investigation underway.",
        "Victim assaulted fatally at {loc} following a dispute.",
    ],
    "Online Financial Fraud": [
        "Complainant defrauded of money via fake investment link traced to {loc}.",
        "UPI fraud reported; victim transferred funds to fraudster posing as bank official.",
    ],
    "Domestic Violence": [
        "Complainant alleges cruelty and harassment by in-laws at residence in {loc}.",
    ],
    "Drug Trafficking": [
        "Suspects apprehended near {loc} with commercial quantity of contraband.",
    ],
}
DEFAULT_BRIEF = "Incident reported at {loc}; case registered and investigation initiated."
DIRECTIONS = ["north", "south", "east", "the highway", "the market", "the bypass"]


def weighted_choice(pairs):
    items, weights = zip(*pairs)
    return random.choices(items, weights=weights, k=1)[0]


def build_database(db_path: str, n_cases: int, seed: int):
    random.seed(seed)
    fake = Faker("en_IN")
    Faker.seed(seed)

    if os.path.exists(db_path):
        os.remove(db_path)
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    with open(SCHEMA, encoding="utf-8") as f:
        cur.executescript(f.read())

    # ----- Masters -----
    cur.execute("INSERT INTO State VALUES (1, 'Karnataka')")
    gender_ids = {g: i + 1 for i, g in enumerate(GENDERS)}
    cur.executemany("INSERT INTO GenderMaster VALUES (?, ?)", [(i, g) for g, i in gender_ids.items()])
    religion_ids = {r: i + 1 for i, r in enumerate(RELIGIONS)}
    cur.executemany("INSERT INTO ReligionMaster VALUES (?, ?)", [(i, r) for r, i in religion_ids.items()])
    caste_ids = {c: i + 1 for i, c in enumerate(CASTES)}
    cur.executemany("INSERT INTO CasteMaster VALUES (?, ?)", [(i, c) for c, i in caste_ids.items()])
    occ_ids = {o: i + 1 for i, o in enumerate(OCCUPATIONS)}
    cur.executemany("INSERT INTO OccupationMaster VALUES (?, ?)", [(i, o) for o, i in occ_ids.items()])
    cat_ids = {c: i + 1 for i, c in enumerate(CASE_CATEGORIES)}
    cur.executemany("INSERT INTO CaseCategory VALUES (?, ?)", [(i, c) for c, i in cat_ids.items()])
    grav_ids = {g: i + 1 for i, g in enumerate(GRAVITY)}
    cur.executemany("INSERT INTO GravityOffence VALUES (?, ?)", [(i, g) for g, i in grav_ids.items()])
    status_ids = {s: i + 1 for i, s in enumerate(CASE_STATUS)}
    cur.executemany("INSERT INTO CaseStatusMaster VALUES (?, ?)", [(i, s) for s, i in status_ids.items()])
    rank_ids = {r: i + 1 for i, r in enumerate(RANKS)}
    cur.executemany("INSERT INTO Rank VALUES (?, ?)", [(i, r) for r, i in rank_ids.items()])
    desig_ids = {d: i + 1 for i, d in enumerate(DESIGNATIONS)}
    cur.executemany("INSERT INTO Designation VALUES (?, ?)", [(i, d) for d, i in desig_ids.items()])
    act_ids = {a: i + 1 for i, a in enumerate(ACTS)}
    cur.executemany("INSERT INTO Act VALUES (?, ?)", [(i, a) for a, i in act_ids.items()])
    cur.execute("INSERT INTO UnitType VALUES (1, 'Police Station'), (2, 'Sub-Division'), (3, 'District HQ')")

    # Sections (one per subhead)
    section_ids = {}
    sid = 1
    for subhead, (actname, sectno, desc) in SECTION_BY_SUBHEAD.items():
        cur.execute("INSERT INTO Section VALUES (?, ?, ?, ?)", (sid, sectno, act_ids[actname], desc))
        section_ids[subhead] = sid
        sid += 1

    # Crime heads / subheads
    major_ids, minor_ids, subhead_gravity = {}, {}, {}
    mh_id, sh_id = 1, 1
    subhead_weight = []  # (subhead, weight) for global mix
    for major, subs in CRIME_TAXONOMY.items():
        cur.execute("INSERT INTO CrimeHead VALUES (?, ?)", (mh_id, major))
        major_ids[major] = mh_id
        for subhead, grav, weight in subs:
            cur.execute("INSERT INTO CrimeSubHead VALUES (?, ?, ?)", (sh_id, subhead, mh_id))
            minor_ids[subhead] = sh_id
            subhead_gravity[subhead] = grav
            subhead_weight.append((subhead, weight))
            sh_id += 1
        mh_id += 1
    subhead_to_major = {sh: mj for mj, subs in CRIME_TAXONOMY.items() for sh, _, _ in subs}

    # Districts + Units + Courts
    district_ids, courts_by_district = {}, {}
    did = 1
    for dname, (lat, lng) in DISTRICTS.items():
        cur.execute("INSERT INTO District VALUES (?, ?, 1, ?, ?)", (did, dname, lat, lng))
        cur.execute("INSERT INTO Court VALUES (?, ?, ?)", (did, f"{dname} District Court", did))
        courts_by_district[did] = did
        district_ids[dname] = did
        did += 1

    units = []  # (UnitID, name, district_id, lat, lng)
    uid = 1
    for dname, stations in STATIONS.items():
        ddid = district_ids[dname]
        # district HQ unit (parent)
        hq_id = uid
        dlat, dlng = DISTRICTS[dname]
        cur.execute("INSERT INTO Unit VALUES (?, ?, 3, ?, NULL, ?, ?)",
                    (uid, f"{dname} HQ", ddid, dlat, dlng))
        uid += 1
        for name, lat, lng in stations:
            cur.execute("INSERT INTO Unit VALUES (?, ?, 1, ?, ?, ?, ?)",
                        (uid, name, ddid, hq_id, lat, lng))
            units.append((uid, name, ddid, lat, lng))
            uid += 1

    # Employees (officers) per unit
    employees_by_unit = {}
    eid = 1
    for u in units:
        unit_id = u[0]
        ids = []
        for _ in range(random.randint(3, 6)):
            cur.execute(
                "INSERT INTO Employee VALUES (?, ?, ?, ?, ?)",
                (eid, fake.name(), random.randint(1, len(RANKS)),
                 random.randint(1, len(DESIGNATIONS)), unit_id),
            )
            ids.append(eid)
            eid += 1
        employees_by_unit[unit_id] = ids

    # ----- Planted hotspot/anomaly config -----
    # Pick a hotspot station (Koramangala) for chain snatching surge, and a station
    # for a vehicle-theft anomaly spike in a specific month.
    unit_by_name = {u[1]: u for u in units}
    hotspot_unit = unit_by_name.get("Koramangala PS", units[0])
    anomaly_unit = unit_by_name.get("Whitefield PS", units[1])
    falsecase_unit = unit_by_name.get("Electronic City PS", units[2])
    lag_unit = unit_by_name.get("Indiranagar PS", units[3])

    today = date(2026, 6, 30)
    start = today - timedelta(days=365)
    anomaly_month = (2026, 4)  # April spike for vehicle theft at anomaly_unit

    # ----- Repeat offenders (stable identities for the graph) -----
    accused_master = []  # AccusedMasterID
    am_id = 1
    # A pool of "career" repeat offenders that recur across many cases.
    repeat_offenders = []
    for _ in range(25):
        cur.execute("INSERT INTO AccusedMaster VALUES (?, ?, ?, ?)",
                    (am_id, fake.name_male(), random.randint(19, 45), gender_ids["Male"]))
        repeat_offenders.append(am_id)
        accused_master.append(am_id)
        am_id += 1
    # Two planted gangs (co-accused cliques) for community detection.
    gang_a = repeat_offenders[:5]
    gang_b = repeat_offenders[5:9]

    def new_one_off_accused():
        nonlocal am_id
        cur.execute("INSERT INTO AccusedMaster VALUES (?, ?, ?, ?)",
                    (am_id, fake.name(), random.randint(18, 60),
                     gender_ids[weighted_choice([("Male", 8), ("Female", 2)])]))
        accused_master.append(am_id)
        rid = am_id
        am_id += 1
        return rid

    # ----- Generate cases -----
    case_rows = []
    complainant_id = victim_id = accused_id = assoc_id = cs_id = arrest_id = 1
    occ_rows = []
    serial_by_unit = {}

    for case_no in range(1, n_cases + 1):
        # choose station with hotspot weighting
        if random.random() < 0.10:
            u = hotspot_unit
            subhead = "Chain Snatching"
        elif random.random() < 0.06:
            u = anomaly_unit
            subhead = "Vehicle Theft"
        else:
            u = random.choice(units)
            subhead = weighted_choice(subhead_weight)
        unit_id, uname, ddid, ulat, ulng = u
        major = subhead_to_major[subhead]

        # date with seasonality (more property crime in festival months Oct-Nov)
        day_offset = random.randint(0, 365)
        reg_date = start + timedelta(days=day_offset)
        # Plant an April vehicle-theft SPIKE at anomaly_unit: most (not all) of these
        # cases land in April, leaving a year-round baseline in other months so the
        # z-score anomaly detector has something to compare against.
        if unit_id == anomaly_unit[0] and subhead == "Vehicle Theft" and random.random() < 0.8:
            reg_date = date(anomaly_month[0], anomaly_month[1], random.randint(1, 28))

        # incident slightly before registration; plant response-lag outliers
        base_lag = random.randint(0, 3)
        if unit_id == lag_unit[0] and random.random() < 0.4:
            base_lag = random.randint(20, 60)  # outlier lag
        incident_from = reg_date - timedelta(days=base_lag)
        info_received = reg_date - timedelta(days=max(0, base_lag - random.randint(0, 1)))

        # jitter coords around station
        lat = ulat + random.uniform(-0.01, 0.01)
        lng = ulng + random.uniform(-0.01, 0.01)

        serial = serial_by_unit.get(unit_id, 0) + 1
        serial_by_unit[unit_id] = serial
        year = reg_date.year
        crime_no = f"1{ddid:04d}{unit_id:04d}{year:04d}{serial:05d}"

        loc = uname.replace(" PS", "")
        brief = random.choice(BRIEF_TEMPLATES.get(subhead, [DEFAULT_BRIEF])).format(
            loc=loc, dir=random.choice(DIRECTIONS), wt=random.randint(8, 60))

        officer = random.choice(employees_by_unit[unit_id])
        status = weighted_choice([(s, w) for s, w in zip(CASE_STATUS, [4, 3, 2, 2])])

        cur.execute(
            """INSERT INTO CaseMaster VALUES
               (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (case_no, crime_no, f"CC/{case_no}/{year}", reg_date.isoformat(),
             officer, unit_id, cat_ids["FIR"], grav_ids[subhead_gravity[subhead]],
             major_ids[major], minor_ids[subhead], status_ids[status],
             courts_by_district[ddid], incident_from.isoformat(),
             incident_from.isoformat(), info_received.isoformat(), lat, lng, brief),
        )
        occ_rows.append((case_no, random.randint(0, 23)))

        # Act/Section association
        cur.execute("INSERT INTO ActSectionAssociation VALUES (?, ?, ?, ?)",
                    (assoc_id, case_no, act_ids[SECTION_BY_SUBHEAD[subhead][0]],
                     section_ids[subhead]))
        assoc_id += 1

        # Complainant (socio-economic patterns: online fraud skews IT/student; DV skews women)
        if subhead == "Online Financial Fraud":
            occ = random.choice(["IT Professional", "Student", "Business Owner"])
        elif subhead in ("Domestic Violence", "Eve Teasing / Harassment"):
            occ = random.choice(["Homemaker", "Student", "Daily Wage Labourer"])
        else:
            occ = random.choice(OCCUPATIONS)
        comp_gender = "Female" if subhead in ("Domestic Violence", "Eve Teasing / Harassment") else \
            weighted_choice([("Male", 6), ("Female", 4)])
        cur.execute(
            "INSERT INTO ComplainantDetails VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (complainant_id, case_no, fake.name(), random.randint(18, 70),
             gender_ids[comp_gender], occ_ids[occ],
             religion_ids[random.choice(RELIGIONS)], caste_ids[random.choice(CASTES)]),
        )
        complainant_id += 1

        # Victim (for body/women crimes)
        if major in ("Body Offences", "Crimes Against Women"):
            cur.execute("INSERT INTO Victim VALUES (?, ?, ?, ?, ?)",
                        (victim_id, case_no, fake.name(), random.randint(15, 75),
                         gender_ids[weighted_choice([("Female", 6), ("Male", 4)])]))
            victim_id += 1

        # Accused: gang/repeat planting
        accused_persons = []
        r = random.random()
        if subhead in ("Chain Snatching", "Vehicle Theft", "Robbery") and r < 0.35:
            # gang involvement -> co-accused cliques
            gang = gang_a if random.random() < 0.5 else gang_b
            picks = random.sample(gang, k=random.randint(2, min(3, len(gang))))
            accused_persons.extend(picks)
        elif r < 0.55:
            # single repeat offender
            accused_persons.append(random.choice(repeat_offenders))
        # add some one-off accused
        for _ in range(random.randint(0, 2)):
            accused_persons.append(new_one_off_accused())
        accused_persons = list(dict.fromkeys(accused_persons))  # dedupe, keep order

        for i, amid in enumerate(accused_persons, start=1):
            cur.execute("INSERT INTO Accused VALUES (?, ?, ?, ?)",
                        (accused_id, case_no, amid, f"A{i}"))
            accused_id += 1

        # Arrest (if any accused and status advanced)
        if accused_persons and status in ("Chargesheeted", "Pending Trial") and random.random() < 0.7:
            cur.execute(
                "INSERT INTO ArrestSurrender VALUES (?, ?, ?, ?, ?, ?, ?)",
                (arrest_id, case_no, officer, courts_by_district[ddid],
                 (reg_date + timedelta(days=random.randint(1, 30))).isoformat(), ddid, 1),
            )
            for amid in accused_persons:
                cur.execute(
                    "INSERT OR IGNORE INTO inv_arrestsurrenderaccused VALUES (?, ?)",
                    (arrest_id, amid),
                )
            arrest_id += 1

        # Chargesheet / detection quality (cstype A/B/C). Plant false-case cluster.
        if unit_id == falsecase_unit[0]:
            cstype = weighted_choice([("A", 3), ("B", 5), ("C", 2)])  # high false-case
        else:
            cstype = weighted_choice([("A", 6), ("B", 1), ("C", 3)])
        cur.execute("INSERT INTO ChargesheetDetails VALUES (?, ?, ?, ?)",
                    (cs_id, case_no, cstype,
                     (reg_date + timedelta(days=random.randint(10, 90))).isoformat()))
        cs_id += 1

    cur.executemany("INSERT INTO Inv_OccuranceTime VALUES (?, ?)", occ_rows)

    con.commit()

    # quick counts for the log
    counts = {t: cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
              for t in ["CaseMaster", "Accused", "AccusedMaster", "ArrestSurrender",
                        "ChargesheetDetails", "ComplainantDetails", "Victim"]}
    con.close()
    return counts


def main():
    ap = argparse.ArgumentParser(description="Generate synthetic FIR data for TRINETRA")
    ap.add_argument("--db", default=os.path.join(HERE, "trinetra.db"))
    ap.add_argument("--cases", type=int, default=4000)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    print(f"[{datetime.now():%H:%M:%S}] Generating {args.cases} cases -> {args.db}")
    counts = build_database(args.db, args.cases, args.seed)
    print("Done. Row counts:")
    for t, c in counts.items():
        print(f"  {t:22s} {c}")


if __name__ == "__main__":
    main()
