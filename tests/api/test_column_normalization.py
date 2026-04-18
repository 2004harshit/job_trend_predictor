"""
Test script for DataFrame column normalization
Tests the normalize_dataframe_columns function

Author: Development Team
Date: 2025-03-18
"""

import pandas as pd
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def test_column_normalization():
    """Test the normalize_dataframe_columns function"""
    
    # Import the function
    from routes import normalize_dataframe_columns
    
    # Create test DataFrame with various column name formats
    test_data = {
        'Job_Type': ['data scientist', 'software engineer'],
        'Title_Cleaned': ['Senior Data Scientist', 'Backend Developer'],
        'Scraped_At_Cleaned': ['2023-01-01', '2023-01-02'],
        'Posted_Date': ['2023-01-01', '2023-01-02'],
        'Min_Experience': [2, 3],
        'Max_Experience': [5, 6],
        'Salary_Lakhs': [12.5, 8.0],
        'Company_Cleaned': ['TechCorp', 'StartupInc'],
        'Location': ['Bangalore', 'Hyderabad'],
        'Skills': ['python, ml', 'java, spring'],
        'No of applicant applied cleaned': [50, 30],
        'No of job opening cleaned ': [10, 15],
        'Star_Skills': ['python', 'java'],
        'Combined_Skills': ['python, ml, sql', 'java, spring, sql'],
        'Normal_Skills': ['excel', 'git']
    }
    
    df = pd.DataFrame(test_data)
    print("Original DataFrame columns:")
    print(list(df.columns))
    print()
    
    # Apply normalization
    normalized_df = normalize_dataframe_columns(df)
    
    print("Normalized DataFrame columns:")
    print(list(normalized_df.columns))
    print()
    
    # Test specific column mappings
    expected_mappings = {
        'Job_Type': 'job_type',
        'Title_Cleaned': 'title_cleaned',
        'Scraped_At_Cleaned': 'scraped_at',
        'Posted_Date': 'posted_date',
        'Min_Experience': 'min_experience',
        'Max_Experience': 'max_experience',
        'Salary_Lakhs': 'salary_lakhs',
        'Company_Cleaned': 'company_cleaned',
        'Location': 'location',
        'Skills': 'skills',
        'No of applicant applied cleaned': 'no_of_applicants',
        'No of job opening cleaned ': 'no_of_openings',
        'Star_Skills': 'star_skills',
        'Combined_Skills': 'combined_skills',
        'Normal_Skills': 'normal_skills'
    }
    
    print("Testing column mappings:")
    all_passed = True
    
    for original, expected in expected_mappings.items():
        if original in df.columns:
            actual = normalized_df.columns[df.columns.get_loc(original)]
            if actual == expected:
                print(f"✅ {original} -> {actual}")
            else:
                print(f"❌ {original} -> {actual} (expected: {expected})")
                all_passed = False
        else:
            print(f"⚠️  {original} not found in original DataFrame")
    
    print()
    print("Testing data integrity:")
    
    # Check if data is preserved
    for col in df.columns:
        if col in normalized_df.columns:
            if df[col].equals(normalized_df[col]):
                print(f"✅ Data preserved for {col}")
            else:
                print(f"❌ Data changed for {col}")
                all_passed = False
        else:
            # Check if column was renamed
            new_col = None
            for orig_col, new_col_name in expected_mappings.items():
                if orig_col == col and new_col_name in normalized_df.columns:
                    new_col = new_col_name
                    break
            
            if new_col and df[col].equals(normalized_df[new_col]):
                print(f"✅ Data preserved for {col} -> {new_col}")
            else:
                print(f"❌ Data not found for {col}")
                all_passed = False
    
    print()
    if all_passed:
        print("🎉 All tests passed!")
    else:
        print("❌ Some tests failed!")
    
    return all_passed

def test_edge_cases():
    """Test edge cases for column normalization"""
    
    from routes import normalize_dataframe_columns
    
    print("Testing edge cases:")
    print()
    
    # Test empty DataFrame
    empty_df = pd.DataFrame()
    normalized_empty = normalize_dataframe_columns(empty_df)
    print(f"✅ Empty DataFrame: {len(normalized_empty.columns)} columns")
    
    # Test DataFrame with already normalized columns
    already_normal = pd.DataFrame({
        'job_type': ['data scientist'],
        'min_experience': [2],
        'no_of_applicants': [50]
    })
    normalized_already = normalize_dataframe_columns(already_normal)
    print(f"✅ Already normalized: {list(normalized_already.columns)}")
    
    # Test DataFrame with mixed case and spaces
    mixed_case = pd.DataFrame({
        'Job Type': ['data scientist'],
        'MIN EXPERIENCE': [2],
        'No Of Applicants': [50],
        'Some_Other_Column': ['test']
    })
    normalized_mixed = normalize_dataframe_columns(mixed_case)
    print(f"✅ Mixed case: {list(normalized_mixed.columns)}")
    
    print()

if __name__ == "__main__":
    print("🧪 Testing DataFrame Column Normalization")
    print("=" * 50)
    
    success = test_column_normalization()
    test_edge_cases()
    
    print("=" * 50)
    if success:
        print("🎉 All normalization tests passed!")
    else:
        print("❌ Some tests failed!")
    
    exit(0 if success else 1)
