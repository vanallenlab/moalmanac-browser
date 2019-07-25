-- Created by Vertabelo (http://vertabelo.com)
-- Last modification date: 2019-07-25 18:52:52.999

-- tables
-- Table: Assertion
CREATE TABLE Assertion (
    assertion_id integer NOT NULL CONSTRAINT Assertion_pk PRIMARY KEY,
    created_on text NOT NULL,
    last_updated text NOT NULL,
    disease text,
    oncotree_term text,
    oncotree_code text,
    context text,
    therapy_name text,
    therapy_type text,
    therapy_sensitivity boolean,
    therapy_resistance boolean,
    favorable_prognosis boolean,
    predictive_implication text,
    description text,
    validated boolean NOT NULL,
    submitted_by text NOT NULL
);

-- Table: Assertion_To_Feature
CREATE TABLE Assertion_To_Feature (
    atf_id integer NOT NULL CONSTRAINT Assertion_To_Feature_pk PRIMARY KEY,
    assertion_id integer NOT NULL,
    feature_id integer NOT NULL,
    CONSTRAINT Assertion_To_Feature_Assertion FOREIGN KEY (assertion_id)
    REFERENCES Assertion (assertion_id),
    CONSTRAINT Assertion_To_Feature_Feature FOREIGN KEY (feature_id)
    REFERENCES Feature (feature_id)
);

-- Table: Assertion_To_Source
CREATE TABLE Assertion_To_Source (
    ats_id integer NOT NULL CONSTRAINT Assertion_To_Source_pk PRIMARY KEY,
    assertion_id integer NOT NULL,
    source_id integer NOT NULL,
    CONSTRAINT Assertion_To_Source_Assertion FOREIGN KEY (assertion_id)
    REFERENCES Assertion (assertion_id)
    ON DELETE CASCADE,
    CONSTRAINT Assertion_To_Source_Source FOREIGN KEY (source_id)
    REFERENCES Source (source_id)
);

-- Table: Feature
CREATE TABLE Feature (
    feature_id integer NOT NULL CONSTRAINT Feature_pk PRIMARY KEY,
    feature_def_id integer NOT NULL,
    CONSTRAINT Feature_Feature_Definition FOREIGN KEY (feature_def_id)
    REFERENCES Feature_Definition (feature_def_id)
);

-- Table: Feature_Attribute
CREATE TABLE Feature_Attribute (
    attribute_id integer NOT NULL CONSTRAINT Feature_Attribute_pk PRIMARY KEY,
    feature_id integer NOT NULL,
    attribute_def_id integer NOT NULL,
    value text,
    CONSTRAINT Feature_Attribute_Feature FOREIGN KEY (feature_id)
    REFERENCES Feature (feature_id)
    ON DELETE CASCADE,
    CONSTRAINT Feature_Attribute_Feature_Attribute_Definition FOREIGN KEY (attribute_def_id)
    REFERENCES Feature_Attribute_Definition (attribute_def_id)
);

-- Table: Feature_Attribute_Definition
CREATE TABLE Feature_Attribute_Definition (
    attribute_def_id integer NOT NULL CONSTRAINT Feature_Attribute_Definition_pk PRIMARY KEY,
    feature_def_id integer NOT NULL,
    name text NOT NULL,
    readable_name text NOT NULL,
    type text NOT NULL,
    CONSTRAINT Feature_Attribute_Definition_Feature_Definition FOREIGN KEY (feature_def_id)
    REFERENCES Feature_Definition (feature_def_id)
    ON DELETE CASCADE
);

-- Table: Feature_Definition
CREATE TABLE Feature_Definition (
    feature_def_id integer NOT NULL CONSTRAINT Feature_Definition_pk PRIMARY KEY,
    name text NOT NULL,
    readable_name integer NOT NULL,
    CONSTRAINT Feature_Definition_ak_1 UNIQUE (name)
);

-- Table: Source
CREATE TABLE Source (
    source_id integer NOT NULL CONSTRAINT Source_pk PRIMARY KEY,
    source_type text NOT NULL,
    citation text,
    url text,
    doi text,
    pmid integer,
    nct text
);

-- Table: Version
CREATE TABLE Version (
    major integer NOT NULL CONSTRAINT Version_pk PRIMARY KEY,
    minor integer NOT NULL,
    patch integer NOT NULL
);

-- End of file.

