-- PRIMARY DATABASE STRUCTURE
SET
	SEARCH_PATH TO APP,
	PUBLIC;

-- Picklists
CREATE TABLE APP.DECISION_MAKERS (
	ID BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	NAME TEXT NOT NULL UNIQUE
);

DROP TABLE APP.DECISION_MAKERS

-- Creates a table with one TEXT column per CSV header (sanitized)
CREATE TABLE app.decision_makers_full (
  "internal_id" TEXT,
  "property_management_firm" TEXT,
  "contact_owner" TEXT,
  "first_name" TEXT,
  "last_name" TEXT,
  "name" TEXT,
  "job_title" TEXT,
  "lead_source" TEXT,
  "contact_association_membership" TEXT,
  "email" TEXT,
  "phone" TEXT
);


CREATE TABLE APP.DIVISIONS (
	ID BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	NAME TEXT NOT NULL UNIQUE
);

CREATE TABLE APP.OPPORTUNITY_STAGES (
	CODE TEXT PRIMARY KEY, -- 'PROPOSAL_SENT', 'VERBAL_APPROVAL'
	LABEL TEXT NOT NULL UNIQUE
);

-- Key/Value config for tunable params
CREATE TABLE APP.CONFIG_PARAMS (KEY TEXT PRIMARY KEY, VALUE TEXT NOT NULL);

-- Historic probability matrix (descriptive analytics)
CREATE TABLE APP.HISTORIC_PROBABILITY_MATRIX (
	ID BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	DECISION_MAKER_ID BIGINT NOT NULL REFERENCES APP.DECISION_MAKERS (ID) ON DELETE CASCADE,
	DIVISION_ID BIGINT NOT NULL REFERENCES APP.DIVISIONS (ID) ON DELETE CASCADE,
	AVG_PROP_TURNAROUND_DAYS INTEGER,
	EST_REVENUE_BUCKET TEXT, -- e.g., '0-100k','100-500k','500k+'
	GROSS_PROFIT_BUCKET TEXT, -- e.g., '<15%','15-25%','25%+'
	OBSERVED_WIN_RATE NUMERIC(6, 5), -- 0..1
	SAMPLES_COUNT INTEGER DEFAULT 0,
	UNIQUE (
		DECISION_MAKER_ID,
		DIVISION_ID,
		EST_REVENUE_BUCKET,
		GROSS_PROFIT_BUCKET
	)
);

-- Optional persistence of user-entered opportunities
CREATE TABLE APP.OPPORTUNITIES (
	ID BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	DECISION_MAKER_ID BIGINT NOT NULL REFERENCES APP.DECISION_MAKERS (ID) ON DELETE RESTRICT,
	DIVISION_ID BIGINT NOT NULL REFERENCES APP.DIVISIONS (ID) ON DELETE RESTRICT,
	STAGE_CODE TEXT NOT NULL REFERENCES APP.OPPORTUNITY_STAGES (CODE) ON DELETE RESTRICT,
	ESTIMATED_REVENUE NUMERIC(14, 2) NOT NULL CHECK (ESTIMATED_REVENUE >= 0),
	GROSS_PROFIT_PCT NUMERIC(6, 5) NOT NULL CHECK (
		GROSS_PROFIT_PCT >= 0
		AND GROSS_PROFIT_PCT <= 1
	),
	WIN_PROBABILITY NUMERIC(6, 5) NOT NULL CHECK (
		WIN_PROBABILITY >= 0
		AND WIN_PROBABILITY <= 1
	),
	PROBABILITY_OF_AWARD NUMERIC(6, 5), -- optional denorm
	EXPECTED_VALUE NUMERIC(14, 2), -- optional denorm
	EXPECTED_GROSS_PROFIT NUMERIC(14, 2), -- optional denorm
	CREATED_AT TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Helpful indexes
CREATE INDEX ON APP.OPPORTUNITIES (STAGE_CODE);

CREATE INDEX ON APP.OPPORTUNITIES (DECISION_MAKER_ID);

CREATE INDEX ON APP.OPPORTUNITIES (DIVISION_ID);

---------------------------------------------------

INSERT INTO app.opportunity_stages (code, label) VALUES
('PROPOSAL_SENT','Proposal Sent'),
('VERBAL_APPROVAL','Verbal Approval')
ON CONFLICT DO NOTHING;

INSERT INTO app.config_params (key, value) VALUES
('prop_sent_base_win_rate','0.30'),
('prop_verbal_base_win_rate','0.75'),
('win_probability_min','0'),
('win_probability_max','1'),
('avg_prop_turnaround_days','14')
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;

-- Example picklists; replace with your real values
INSERT INTO app.decision_makers (name) VALUES
('CFO'), ('COO'), ('VP Ops'), ('Facilities Director')
ON CONFLICT DO NOTHING;

INSERT INTO app.divisions (name) VALUES
('Asphalt'), ('Concrete'), ('Coatings'), ('CS Denver'), 
('CS Mountains'), ('CS Unit Renovatinos'), ('DCPS Contracting'), 
('DCPS Roofing'), ('Metal Fabrication'), ('Ancillary'), 
('Maintenance/Irrigation (Maint/IRR)'), ('Snow'), ('Sweeping')
ON CONFLICT DO NOTHING;
