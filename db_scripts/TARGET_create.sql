-- Created by Vertabelo (http://vertabelo.com)
-- Last modification date: 2016-11-07 22:58:29.343

-- tables
-- Table: Alteration
CREATE TABLE Alteration (
    alt_id integer NOT NULL CONSTRAINT Alteration_pk PRIMARY KEY,
    feature text NOT NULL,
    alt_type text,
    alt text,
    gene_name text
);

-- Table: Assertion
CREATE TABLE Assertion (
    assertion_id integer NOT NULL CONSTRAINT Assertion_pk PRIMARY KEY,
    last_updated text NOT NULL,
    disease text NOT NULL,
    stage integer,
    therapy_name text,
    therapy_type text,
    therapy_sensitivity boolean,
    predictive_implication text,
    favorable_prognosis boolean,
    description text
);

-- Table: Assertion_To_Alteration
CREATE TABLE Assertion_To_Alteration (
    aa_id integer NOT NULL CONSTRAINT Assertion_To_Alteration_pk PRIMARY KEY,
    assertion_id integer NOT NULL,
    alt_id integer NOT NULL,
    CONSTRAINT Assertion_To_Alteration_Assertion FOREIGN KEY (assertion_id)
    REFERENCES Assertion (assertion_id),
    CONSTRAINT Assertion_To_Alteration_Alteration FOREIGN KEY (alt_id)
    REFERENCES Alteration (alt_id)
);

-- Table: Assertion_To_Source
CREATE TABLE Assertion_To_Source (
    ats_id integer NOT NULL CONSTRAINT Assertion_To_Source_pk PRIMARY KEY,
    assertion_id integer NOT NULL,
    source_id integer NOT NULL,
    CONSTRAINT Assertion_To_Source_Assertion FOREIGN KEY (assertion_id)
    REFERENCES Assertion (assertion_id),
    CONSTRAINT Assertion_To_Source_Source FOREIGN KEY (source_id)
    REFERENCES Source (source_id)
);

-- Table: Source
CREATE TABLE Source (
    source_id integer NOT NULL CONSTRAINT Source_pk PRIMARY KEY,
    source_type text NOT NULL,
    cite_text text NOT NULL,
    doi text
);

-- End of file.

