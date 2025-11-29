"""
Comprehensive viewer for extracted job data
Shows all fields in a readable format
"""

import logging
import pandas as pd
import json
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# from airflow_automation.etl_pipeline.data_collection.extractors.NaukriExtractor import NaukriJobExtractor
from .NaukriExtractor import NaukriJobExtractor


def view_extracted_data():
    """Extract and display all job data with proper formatting"""
    
    logger.info("="*80)
    logger.info("NAUKRI JOB EXTRACTOR - DATA VIEWER")
    logger.info("="*80)
    
    # Initialize extractor
    extractor = NaukriJobExtractor(
        max_pages=2,
        per_page_limit=5,
        min_delay=1,
        max_delay=2,
        locations=['bangalore', 'bengaluru'],  # Include both variations
        logger=logger
    )
    
    # Extract jobs
    logger.info("\nExtracting jobs...")
    jobs = extractor.extract("python-developer")
    
    if not jobs:
        logger.error("❌ No jobs extracted!")
        return
    
    logger.info(f"✅ Extracted {len(jobs)} jobs\n")
    
    # Create DataFrame
    df = pd.DataFrame(jobs)
    
    # Display column information
    logger.info("="*80)
    logger.info("COLUMNS EXTRACTED")
    logger.info("="*80)
    for i, col in enumerate(df.columns, 1):
        logger.info(f"{i:2d}. {col}")
    
    # Display detailed data for each job
    logger.info("\n" + "="*80)
    logger.info("DETAILED JOB LISTINGS")
    logger.info("="*80)
    
    for idx, row in df.iterrows():
        logger.info(f"\n{'─'*80}")
        logger.info(f"JOB #{idx+1}")
        logger.info(f"{'─'*80}")
        
        # Core Information
        logger.info("\n📌 CORE INFORMATION:")
        logger.info(f"   Title:        {row.get('Title', 'NA')}")
        logger.info(f"   Company:      {row.get('Company', 'NA')}")
        logger.info(f"   Location:     {row.get('Location', 'NA')}")
        
        # Compensation & Requirements
        logger.info("\n💼 COMPENSATION & REQUIREMENTS:")
        logger.info(f"   Experience:   {row.get('Experience', 'NA')}")
        logger.info(f"   Salary:       {row.get('Salary', 'NA')}")
        logger.info(f"   Education:    {row.get('Education', 'NA')}")
        
        # Timing Information
        logger.info("\n⏰ TIMING INFORMATION:")
        logger.info(f"   Posted Date:     {row.get('Posted_Date', 'NA')}")
        logger.info(f"   Last Apply Date: {row.get('Last_Apply_Date', 'NA')}")
        logger.info(f"   Scraped At:      {row.get('Scraped_At', 'NA')}")
        
        # Skills
        logger.info("\n🎯 SKILLS:")
        star_skills = row.get('Star_Skills', [])
        normal_skills = row.get('Normal_Skills', [])
        
        if star_skills:
            logger.info(f"   ⭐ Key Skills: {', '.join(star_skills)}")
        if normal_skills:
            logger.info(f"   📚 Other Skills: {', '.join(normal_skills)}")
        
        # Additional Details
        additional_keys = [k for k in row.index if k not in [
            'Title', 'Company', 'Location', 'Experience', 'Salary', 'Education',
            'Posted_Date', 'Last_Apply_Date', 'Scraped_At', 'Star_Skills', 
            'Normal_Skills', 'Description', 'Job_URL', 'Job_Type'
        ]]
        
        if additional_keys:
            logger.info("\n📋 ADDITIONAL DETAILS:")
            for key in additional_keys:
                value = row.get(key, 'NA')
                if value and value != 'NA':
                    logger.info(f"   {key}: {value}")
        
        # Job Description (truncated)
        desc = row.get('Description', 'NA')
        if desc and desc != 'NA':
            desc_preview = desc[:200] + "..." if len(desc) > 200 else desc
            logger.info(f"\n📄 DESCRIPTION (Preview):\n   {desc_preview}")
        
        # URL
        logger.info(f"\n🔗 URL: {row.get('Job_URL', 'NA')}")
    
    # Summary Statistics
    logger.info("\n" + "="*80)
    logger.info("SUMMARY STATISTICS")
    logger.info("="*80)
    logger.info(f"Total Jobs:              {len(df)}")
    logger.info(f"Total Columns:           {len(df.columns)}")
    logger.info(f"Unique Companies:        {df['Company'].nunique()}")
    logger.info(f"Unique Locations:        {df['Location'].nunique()}")
    logger.info(f"\nData Completeness:")
    logger.info(f"  Posted Dates Found:    {(df['Posted_Date'] != 'NA').sum()}/{len(df)}")
    logger.info(f"  Apply Dates Found:     {(df['Last_Apply_Date'] != 'NA').sum()}/{len(df)}")
    
    # Save to CSV
    output_path = Path("extracted_jobs.csv")
    df.to_csv(output_path, index=False)
    logger.info(f"\n✅ Data saved to: {output_path}")
    
    # Save to JSON for inspection
    json_path = Path("extracted_jobs.json")
    df.to_json(json_path, orient='records', indent=2)
    logger.info(f"✅ JSON saved to: {json_path}")
    
    # Display sample as table
    logger.info("\n" + "="*80)
    logger.info("DATA TABLE (Sample)")
    logger.info("="*80)
    
    # Select important columns for display
    display_cols = ['Title', 'Company', 'Location', 'Experience', 'Salary', 'Posted_Date']
    available_cols = [col for col in display_cols if col in df.columns]
    
    logger.info("\n" + df[available_cols].to_string())
    
    return df


if __name__ == "__main__":
    try:
        df = view_extracted_data()
        print("\n✅ Data viewing completed successfully!")
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)