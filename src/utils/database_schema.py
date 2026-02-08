db_creation = "CREATE DATABASE JOB_DATA_DB"


raw_job_table_creation = """CREATE TABLE raw_job_data (
    id SERIAL PRIMARY KEY,
    
    -- Basic Job Info
    job_id VARCHAR(50),
    title VARCHAR(255),
    company VARCHAR(255),
    experience VARCHAR(150),        -- Keeps "0-5 years" as string
    salary VARCHAR(255),            -- Keeps "Not Disclosed" or "5LPA" as string
    location TEXT,
    education TEXT,
    
    -- Skills
    star_skills TEXT,
    normal_skills TEXT,
    
    -- Dates (kept as VARCHAR for safety in raw tables)
    posted_date VARCHAR(100),       
    last_apply_date VARCHAR(100),
    
    -- Statistics (New Fields)
    num_openings INT,               -- Set to VARCHAR if scraping "N/A" strings
    num_applicants INT,             -- Set to VARCHAR if scraping "Be the first" strings
    
    -- Expanded **details
    role VARCHAR(255),
    industry_type VARCHAR(255),
    department VARCHAR(255),
    employment_type VARCHAR(150),
    role_category VARCHAR(255),
    job_type VARCHAR(100),          -- e.g. Remote/Hybrid
    
    -- Metadata
    description TEXT,               -- Stores the full HTML or long text
    job_url VARCHAR(500) UNIQUE,            -- Prevents duplicate entries
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);  """


validated_job_table_creation = """CREATE TABLE validated_job_data (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(50),
    title VARCHAR(255),
    company VARCHAR(255),
    experience VARCHAR(150),
    salary VARCHAR(255),
    location TEXT,
    education TEXT,
    star_skills TEXT,
    normal_skills TEXT,
    posted_date VARCHAR(100),
    last_apply_date VARCHAR(100),
    num_openings INT,
    num_applicants INT,
    role VARCHAR(255),
    industry_type VARCHAR(255),
    department VARCHAR(255),
    employment_type VARCHAR(150),
    role_category VARCHAR(255),
    job_type VARCHAR(100),
    description TEXT,
    job_url TEXT UNIQUE,
    scraped_at TIMESTAMP,           -- Keeps the original scrape time
    validated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- Tracks when it was validated
);"""


rejected_job_table_creation = """CREATE TABLE rejected_job_data (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(50),
    title VARCHAR(255),
    company VARCHAR(255),
    experience VARCHAR(150),
    salary VARCHAR(255),
    location TEXT,
    education TEXT,
    star_skills TEXT,
    normal_skills TEXT,
    posted_date VARCHAR(100),
    last_apply_date VARCHAR(100),
    num_openings INT,
    num_applicants INT,
    role VARCHAR(255),
    industry_type VARCHAR(255),
    department VARCHAR(255),
    employment_type VARCHAR(150),
    role_category VARCHAR(255),
    job_type VARCHAR(100),
    description TEXT,
    job_url TEXT,                   -- Removed UNIQUE constraint so you can store multiple failed attempts
    scraped_at TIMESTAMP,
    rejection_reason TEXT,          -- New field: e.g., "Missing Title", "Duplicate URL"
    rejected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
); """


cleaned_job_table_creation = """CREATE TABLE cleaned_job_data (
    id SERIAL PRIMARY KEY,
    
    -- OPTIONAL: Link back to raw table for lineage
    raw_job_id INT REFERENCES raw_job_data(id),

    -- --- 1. ORIGINAL RAW FIELDS (For Reference/Context) ---
    title VARCHAR(255),
    company VARCHAR(255),
    experience VARCHAR(150),
    salary VARCHAR(255),
    location TEXT,
    education TEXT,
    star_skills TEXT,
    normal_skills TEXT,
    posted_date VARCHAR(100),
    last_apply_date VARCHAR(100),
    role VARCHAR(255),
    industry_type VARCHAR(255),
    department VARCHAR(255),
    employment_type VARCHAR(150),
    role_category VARCHAR(255),
    description TEXT,
    job_url TEXT,
    scraped_at VARCHAR(100), -- Kept as string from raw
    job_type VARCHAR(100),

    -- --- 2. CLEANED & STANDARDIZED FIELDS ---
    
    -- Basic Info Cleaned
    title_cleaned VARCHAR(255),
    company_cleaned VARCHAR(255),
    
    -- Experience Logic
    experience_range VARCHAR(50),   -- e.g., "3-5"
    min_experience INT,             -- e.g., 3
    max_experience INT,             -- e.g., 5
    
    -- Salary Logic (Using Numeric for calculations)
    salary_range VARCHAR(100),      -- e.g., "100000-500000"
    min_salary NUMERIC(15, 2),      
    max_salary NUMERIC(15, 2),
    avg_salary NUMERIC(15, 2),
    
    -- Location Cleaned
    location_cleaned TEXT,

    -- Education Cleaned
    education_cleaned TEXT,
    ug_degree VARCHAR(255),
    ug_specialization VARCHAR(255),
    pg_degree VARCHAR(255),
    pg_specialization VARCHAR(255),
    
    -- Skills Logic
    combined_skills TEXT,           -- All skills merged
    skill_count INT,                -- Number of skills found
    
    --Role & Industry Cleaned
    role_cleaned VARCHAR(255),
    industry_type_cleaned VARCHAR(255),
    employment_type_cleaned VARCHAR(150),
    role_category_cleaned VARCHAR(255),
    job_type_cleaned VARCHAR(100),

    -- Department Logic
    department_cleaned VARCHAR(255),
    primary_department VARCHAR(255), -- Main category if multiple exist
    department_count INT,
    
    -- Dates & Stats
    scraped_at_cleaned TIMESTAMP,    -- Converted to actual Time object
    num_openings_cleaned INT,        -- Converted to Number
    num_applicants INT,              -- Converted to Number
    
    -- Description (If you applied NLP cleaning)
    description_cleaned TEXT,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    cleaned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
); """