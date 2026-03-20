-- PostgreSQL Database Schema for Job Trend Predictor
-- Execute this script to create the database structure

-- Create database (optional - usually done separately)
-- CREATE DATABASE job_trend_predictor;

-- Connect to the database
-- \c job_trend_predictor;

-- Drop existing tables if they exist (for fresh start)
DROP TABLE IF EXISTS job_listings CASCADE;

-- Create job_listings table
CREATE TABLE job_listings (
    id SERIAL PRIMARY KEY,
    job_type VARCHAR(255) NOT NULL,
    skills TEXT,
    min_experience INTEGER,
    max_experience INTEGER,
    location VARCHAR(255),
    salary_lakhs DECIMAL(10, 2),
    company VARCHAR(255),
    posted_date DATE,
    no_of_applicants INTEGER,
    no_of_openings INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX idx_job_listings_job_type ON job_listings(job_type);
CREATE INDEX idx_job_listings_location ON job_listings(location);
CREATE INDEX idx_job_listings_salary ON job_listings(salary_lakhs);
CREATE INDEX idx_job_listings_experience ON job_listings(min_experience, max_experience);
CREATE INDEX idx_job_listings_posted_date ON job_listings(posted_date);

-- Create trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_job_listings_updated_at 
    BEFORE UPDATE ON job_listings 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create a view for job statistics (optional)
CREATE VIEW job_stats AS
SELECT 
    job_type,
    COUNT(*) as total_jobs,
    AVG(salary_lakhs) as avg_salary,
    MIN(salary_lakhs) as min_salary,
    MAX(salary_lakhs) as max_salary,
    AVG(min_experience) as avg_min_experience,
    COUNT(DISTINCT location) as unique_locations,
    SUM(no_of_applicants) as total_applicants,
    SUM(no_of_openings) as total_openings
FROM job_listings
GROUP BY job_type;

-- Create a function to get job data with proper column names
CREATE OR REPLACE FUNCTION get_job_data_with_columns()
RETURNS TABLE (
    "Job_Type" VARCHAR(255),
    "Skills" TEXT,
    "Min_Experience" INTEGER,
    "Max_Experience" INTEGER,
    "Location" VARCHAR(255),
    "Salary_Lakhs" DECIMAL(10, 2),
    "Company" VARCHAR(255),
    "Posted_Date" DATE,
    "No of applicant applied cleaned" INTEGER,
    "No of job opening cleaned " INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        jl.job_type::VARCHAR(255),
        jl.skills::TEXT,
        jl.min_experience::INTEGER,
        jl.max_experience::INTEGER,
        jl.location::VARCHAR(255),
        jl.salary_lakhs::DECIMAL(10, 2),
        jl.company::VARCHAR(255),
        jl.posted_date::DATE,
        jl.no_of_applicants::INTEGER,
        jl.no_of_openings::INTEGER
    FROM job_listings jl;
END;
$$ LANGUAGE plpgsql;

-- Create a function to get job data by domain
CREATE OR REPLACE FUNCTION get_job_data_by_domain(domain_name VARCHAR(255), limit_count INTEGER DEFAULT NULL)
RETURNS TABLE (
    "Job_Type" VARCHAR(255),
    "Skills" TEXT,
    "Min_Experience" INTEGER,
    "Max_Experience" INTEGER,
    "Location" VARCHAR(255),
    "Salary_Lakhs" DECIMAL(10, 2),
    "Company" VARCHAR(255),
    "Posted_Date" DATE,
    "No of applicant applied cleaned" INTEGER,
    "No of job opening cleaned " INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        jl.job_type::VARCHAR(255),
        jl.skills::TEXT,
        jl.min_experience::INTEGER,
        jl.max_experience::INTEGER,
        jl.location::VARCHAR(255),
        jl.salary_lakhs::DECIMAL(10, 2),
        jl.company::VARCHAR(255),
        jl.posted_date::DATE,
        jl.no_of_applicants::INTEGER,
        jl.no_of_openings::INTEGER
    FROM job_listings jl
    WHERE LOWER(jl.job_type) = LOWER(domain_name)
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- Create a function to get database statistics
CREATE OR REPLACE FUNCTION get_database_stats()
RETURNS TABLE (
    total_records BIGINT,
    unique_domains BIGINT,
    unique_locations BIGINT,
    avg_salary DECIMAL(10, 2),
    min_salary DECIMAL(10, 2),
    max_salary DECIMAL(10, 2),
    median_salary DECIMAL(10, 2)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::BIGINT,
        COUNT(DISTINCT job_type)::BIGINT,
        COUNT(DISTINCT location)::BIGINT,
        AVG(salary_lakhs)::DECIMAL(10, 2),
        MIN(salary_lakhs)::DECIMAL(10, 2),
        MAX(salary_lakhs)::DECIMAL(10, 2),
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY salary_lakhs)::DECIMAL(10, 2)
    FROM job_listings;
END;
$$ LANGUAGE plpgsql;

-- Sample data insertion (optional - for testing)
INSERT INTO job_listings (job_type, skills, min_experience, max_experience, location, salary_lakhs, company, posted_date, no_of_applicants, no_of_openings) VALUES
('Data Scientist', 'python, machine learning, statistics', 0, 3, 'Bangalore', 12.50, 'TechCorp', '2023-01-01', 50, 10),
('Software Engineer', 'java, spring, sql', 1, 4, 'Hyderabad', 8.75, 'StartupInc', '2023-01-02', 30, 15),
('ML Engineer', 'python, tensorflow, deep learning', 2, 5, 'Pune', 15.00, 'DataCo', '2023-01-03', 40, 8),
('Data Analyst', 'sql, excel, python', 0, 2, 'Chennai', 6.25, 'AnalyticsLtd', '2023-01-04', 60, 12),
('Backend Developer', 'python, django, postgresql', 1, 3, 'Mumbai', 10.00, 'DevOps', '2023-01-05', 25, 6);

-- Grant permissions (adjust as needed)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO your_user;

-- Comments for documentation
COMMENT ON TABLE job_listings IS 'Main table storing job listings data';
COMMENT ON COLUMN job_listings.job_type IS 'Type of job role (e.g., Data Scientist, Software Engineer)';
COMMENT ON COLUMN job_listings.skills IS 'Required skills for the job';
COMMENT ON COLUMN job_listings.min_experience IS 'Minimum years of experience required';
COMMENT ON COLUMN job_listings.max_experience IS 'Maximum years of experience preferred';
COMMENT ON COLUMN job_listings.location IS 'Job location';
COMMENT ON COLUMN job_listings.salary_lakhs IS 'Salary in Indian Lakhs per annum';
COMMENT ON COLUMN job_listings.company IS 'Company name';
COMMENT ON COLUMN job_listings.posted_date IS 'Date when job was posted';
COMMENT ON COLUMN job_listings.no_of_applicants IS 'Number of applicants for the job';
COMMENT ON COLUMN job_listings.no_of_openings IS 'Number of job openings';

-- Create user with limited permissions for API (optional)
-- CREATE USER api_user WITH PASSWORD 'your_secure_password';
-- GRANT SELECT ON job_listings TO api_user;
-- GRANT SELECT ON job_stats TO api_user;
-- GRANT EXECUTE ON FUNCTION get_job_data_with_columns() TO api_user;
-- GRANT EXECUTE ON FUNCTION get_job_data_by_domain(VARCHAR(255), INTEGER) TO api_user;
-- GRANT EXECUTE ON FUNCTION get_database_stats() TO api_user;
