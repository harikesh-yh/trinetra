-- TRINETRA FIR schema (SQLite). Modeled on the Karnataka Police FIR ER diagram.
-- Read-only analytical workload. Foreign keys are declared for clarity; the
-- synthetic generator inserts referentially consistent rows.

PRAGMA foreign_keys = ON;

-- ---------- Master / lookup tables ----------
CREATE TABLE State (
    StateID      INTEGER PRIMARY KEY,
    StateName    TEXT NOT NULL
);

CREATE TABLE District (
    DistrictID   INTEGER PRIMARY KEY,
    DistrictName TEXT NOT NULL,
    StateID      INTEGER REFERENCES State(StateID),
    Latitude     REAL,
    Longitude    REAL
);

CREATE TABLE UnitType (
    UnitTypeID   INTEGER PRIMARY KEY,
    UnitTypeName TEXT NOT NULL
);

-- Police station / unit hierarchy (self-referential via ParentUnitID).
CREATE TABLE Unit (
    UnitID       INTEGER PRIMARY KEY,
    UnitName     TEXT NOT NULL,
    UnitTypeID   INTEGER REFERENCES UnitType(UnitTypeID),
    DistrictID   INTEGER REFERENCES District(DistrictID),
    ParentUnitID INTEGER REFERENCES Unit(UnitID),
    Latitude     REAL,
    Longitude    REAL
);

CREATE TABLE Rank (
    RankID   INTEGER PRIMARY KEY,
    RankName TEXT NOT NULL
);

CREATE TABLE Designation (
    DesignationID   INTEGER PRIMARY KEY,
    DesignationName TEXT NOT NULL
);

CREATE TABLE Employee (
    EmployeeID    INTEGER PRIMARY KEY,
    EmployeeName  TEXT NOT NULL,
    RankID        INTEGER REFERENCES Rank(RankID),
    DesignationID INTEGER REFERENCES Designation(DesignationID),
    UnitID        INTEGER REFERENCES Unit(UnitID)
);

CREATE TABLE GenderMaster (
    GenderID   INTEGER PRIMARY KEY,
    GenderName TEXT NOT NULL
);

CREATE TABLE ReligionMaster (
    ReligionID   INTEGER PRIMARY KEY,
    ReligionName TEXT NOT NULL
);

CREATE TABLE CasteMaster (
    CasteID   INTEGER PRIMARY KEY,
    CasteName TEXT NOT NULL
);

CREATE TABLE OccupationMaster (
    OccupationID   INTEGER PRIMARY KEY,
    OccupationName TEXT NOT NULL
);

CREATE TABLE CaseCategory (
    CaseCategoryID   INTEGER PRIMARY KEY,
    CaseCategoryName TEXT NOT NULL   -- FIR / UDR / PAR / ZeroFIR
);

CREATE TABLE GravityOffence (
    GravityOffenceID   INTEGER PRIMARY KEY,
    GravityOffenceName TEXT NOT NULL  -- Heinous / Non-Heinous
);

CREATE TABLE CaseStatusMaster (
    CaseStatusID   INTEGER PRIMARY KEY,
    CaseStatusName TEXT NOT NULL  -- Under Investigation / Chargesheeted / Closed ...
);

CREATE TABLE Court (
    CourtID   INTEGER PRIMARY KEY,
    CourtName TEXT NOT NULL,
    DistrictID INTEGER REFERENCES District(DistrictID)
);

CREATE TABLE CrimeHead (
    CrimeMajorHeadID INTEGER PRIMARY KEY,
    CrimeHeadName    TEXT NOT NULL  -- e.g. Body Offences, Property Offences
);

CREATE TABLE CrimeSubHead (
    CrimeMinorHeadID INTEGER PRIMARY KEY,
    CrimeSubHeadName TEXT NOT NULL, -- e.g. Chain Snatching, House Burglary
    CrimeMajorHeadID INTEGER REFERENCES CrimeHead(CrimeMajorHeadID)
);

CREATE TABLE Act (
    ActID   INTEGER PRIMARY KEY,
    ActName TEXT NOT NULL  -- IPC, Arms Act, NDPS ...
);

CREATE TABLE Section (
    SectionID  INTEGER PRIMARY KEY,
    SectionNo  TEXT NOT NULL,
    ActID      INTEGER REFERENCES Act(ActID),
    Description TEXT
);

-- ---------- Transactional core ----------
CREATE TABLE CaseMaster (
    CaseMasterID        INTEGER PRIMARY KEY,
    CrimeNo             TEXT,   -- 1 cat + 4 district + 4 unit + 4 year + 5 serial
    CaseNo              TEXT,
    CrimeRegisteredDate TEXT,   -- ISO date
    PolicePersonID      INTEGER REFERENCES Employee(EmployeeID),
    PoliceStationID     INTEGER REFERENCES Unit(UnitID),
    CaseCategoryID      INTEGER REFERENCES CaseCategory(CaseCategoryID),
    GravityOffenceID    INTEGER REFERENCES GravityOffence(GravityOffenceID),
    CrimeMajorHeadID    INTEGER REFERENCES CrimeHead(CrimeMajorHeadID),
    CrimeMinorHeadID    INTEGER REFERENCES CrimeSubHead(CrimeMinorHeadID),
    CaseStatusID        INTEGER REFERENCES CaseStatusMaster(CaseStatusID),
    CourtID             INTEGER REFERENCES Court(CourtID),
    IncidentFromDate    TEXT,
    IncidentToDate      TEXT,
    InfoReceivedPSDate  TEXT,
    Latitude            REAL,
    Longitude           REAL,
    BriefFacts          TEXT
);

CREATE TABLE Inv_OccuranceTime (
    CaseMasterID INTEGER PRIMARY KEY REFERENCES CaseMaster(CaseMasterID),
    OccuranceHour INTEGER  -- 0..23, supports time-of-day analytics
);

CREATE TABLE ComplainantDetails (
    ComplainantID INTEGER PRIMARY KEY,
    CaseMasterID  INTEGER REFERENCES CaseMaster(CaseMasterID),
    Name          TEXT,
    AgeYear       INTEGER,
    GenderID      INTEGER REFERENCES GenderMaster(GenderID),
    OccupationID  INTEGER REFERENCES OccupationMaster(OccupationID),
    ReligionID    INTEGER REFERENCES ReligionMaster(ReligionID),
    CasteID       INTEGER REFERENCES CasteMaster(CasteID)
);

CREATE TABLE Victim (
    VictimID     INTEGER PRIMARY KEY,
    CaseMasterID INTEGER REFERENCES CaseMaster(CaseMasterID),
    Name         TEXT,
    AgeYear      INTEGER,
    GenderID     INTEGER REFERENCES GenderMaster(GenderID)
);

-- AccusedMaster holds a stable identity (person) so repeat offenders link across cases.
CREATE TABLE AccusedMaster (
    AccusedMasterID INTEGER PRIMARY KEY,
    Name            TEXT,
    AgeYear         INTEGER,
    GenderID        INTEGER REFERENCES GenderMaster(GenderID)
);

-- Accused row ties a person to a specific case (PersonID = A1, A2 ... within case).
CREATE TABLE Accused (
    AccusedID       INTEGER PRIMARY KEY,
    CaseMasterID    INTEGER REFERENCES CaseMaster(CaseMasterID),
    AccusedMasterID INTEGER REFERENCES AccusedMaster(AccusedMasterID),
    PersonID        TEXT  -- A1, A2 ...
);

CREATE TABLE ArrestSurrender (
    ArrestSurrenderID INTEGER PRIMARY KEY,
    CaseMasterID      INTEGER REFERENCES CaseMaster(CaseMasterID),
    IOID              INTEGER REFERENCES Employee(EmployeeID),
    CourtID           INTEGER REFERENCES Court(CourtID),
    ArrestDate        TEXT,
    DistrictID        INTEGER REFERENCES District(DistrictID),
    StateID           INTEGER REFERENCES State(StateID)
);

-- Junction: arrest <-> accused (many-to-many).
CREATE TABLE inv_arrestsurrenderaccused (
    ArrestSurrenderID INTEGER REFERENCES ArrestSurrender(ArrestSurrenderID),
    AccusedMasterID   INTEGER REFERENCES AccusedMaster(AccusedMasterID),
    PRIMARY KEY (ArrestSurrenderID, AccusedMasterID)
);

CREATE TABLE ActSectionAssociation (
    AssocID      INTEGER PRIMARY KEY,
    CaseMasterID INTEGER REFERENCES CaseMaster(CaseMasterID),
    ActID        INTEGER REFERENCES Act(ActID),
    SectionID    INTEGER REFERENCES Section(SectionID)
);

-- cstype: A = Chargesheet, B = False Case, C = Undetected
CREATE TABLE ChargesheetDetails (
    ChargesheetID   INTEGER PRIMARY KEY,
    CaseMasterID    INTEGER REFERENCES CaseMaster(CaseMasterID),
    cstype          TEXT,
    ChargesheetDate TEXT
);

-- ---------- Trust layer ----------
CREATE TABLE AuditLog (
    AuditID      INTEGER PRIMARY KEY AUTOINCREMENT,
    Username     TEXT,
    Role         TEXT,
    Scope        TEXT,
    Question     TEXT,
    Module       TEXT,
    SQLRun       TEXT,
    Timestamp    TEXT
);

-- ---------- Indexes for analytics ----------
CREATE INDEX idx_case_station ON CaseMaster(PoliceStationID);
CREATE INDEX idx_case_date    ON CaseMaster(CrimeRegisteredDate);
CREATE INDEX idx_case_minor   ON CaseMaster(CrimeMinorHeadID);
CREATE INDEX idx_accused_case ON Accused(CaseMasterID);
CREATE INDEX idx_accused_pers ON Accused(AccusedMasterID);
CREATE INDEX idx_cs_case      ON ChargesheetDetails(CaseMasterID);
