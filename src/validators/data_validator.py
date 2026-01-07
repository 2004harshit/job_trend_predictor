from abc import ABC, abstractmethod
import pandas as pd
from typing import List, Dict, Tuple
from datetime import datetime
import re
import json
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataValidator(ABC):
    """Abstract base class for data validation"""
    
    @abstractmethod
    def validate_data(self, data: pd.DataFrame, features: List[str]) -> Tuple[pd.DataFrame, pd.DataFrame, Dict]:
        """
        Validate data and separate into valid and invalid rows
        
        Returns:
            Tuple of (valid_df, invalid_df, validation_report)
        """
        pass


class FeatureBasedDataValidator(DataValidator):
    """Validator for specific features: timestamp, URL, description"""
    
    def __init__(self, 
                 validated_path: str = "data/processed/validated",
                 rejected_path: str = "data/processed/rejected"):
        """
        Initialize validator with output paths
        
        Args:
            validated_path: Directory to save valid data
            rejected_path: Directory to save rejected data
        """
        self.validated_path = Path(validated_path)
        self.rejected_path = Path(rejected_path)
        
        # Create directories if they don't exist
        self.validated_path.mkdir(parents=True, exist_ok=True)
        self.rejected_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Validator initialized")
        logger.info(f"  Valid data → {self.validated_path}")
        logger.info(f"  Rejected data → {self.rejected_path}")
    
    
    @staticmethod
    def is_timestamp(timestamp: str) -> bool:
        """
        Validate if string is a valid timestamp.
        Expected format: YYYY-MM-DD HH:MM:SS or ISO 8601 (T separator)
        
        Args:
        timestamp: String to validate
        
        Returns:
        True if valid timestamp, False otherwise
        """

        if not isinstance(timestamp, str):
            return False

        timestamp = timestamp.strip()

        # List of formats to check
        formats = [
            "%Y-%m-%dT%H:%M:%S.%f",    # 2025-12-03T21:54:43.757232 (Your format)
            "%Y-%m-%d %H:%M:%S",       # 2025-01-15 14:30:00
            "%Y-%m-%d %H:%M:%S.%f",    # 2025-01-15 14:30:00.123456
            "%d-%m-%Y %H:%M:%S",       # 15-01-2025 14:30:00
            "%Y/%m/%d %H:%M:%S",       # 2025/01/15 14:30:00
        ]

        # 1. Try built-in ISO parser first (efficient for ISO 8601)
        try:
            datetime.fromisoformat(timestamp)
            return True
        except ValueError:
            pass

        # 2. Fallback to specific custom formats
        for fmt in formats:
            try:
                datetime.strptime(timestamp, fmt)
                return True
            except ValueError:
                continue

        return False
    
    
    
    @staticmethod
    def is_job_url(job_url: str) -> bool:
        """
        Validate if string is a valid job URL
        
        Expected: Naukri.com job URLs
        
        Args:
            job_url: String to validate
            
        Returns:
            True if valid URL, False otherwise
        """
        if not isinstance(job_url, str):
            return False
        
        # Remove whitespace
        job_url = job_url.strip()
        
        # Check basic URL structure
        url_pattern = r'^https?://(www\.)?naukri\.com/.+$'
        
        if not re.match(url_pattern, job_url, re.IGNORECASE):
            return False
        
        # Additional checks
        if len(job_url) < 30:  # URLs are typically longer
            return False
        
        if ' ' in job_url:  # URLs shouldn't have spaces
            return False
        
        return True
    
    
    @staticmethod
    def is_description(description: str) -> bool:
        """
        Validate if string is a valid job description
        
        Expected: Long text (200-5000 chars), multiple sentences
        
        Args:
            description: String to validate
            
        Returns:
            True if valid description, False otherwise
        """
        if not isinstance(description, str):
            return False
        
        # Check if "NA" or empty
        if description.strip().upper() in ['NA', 'N/A', 'NOT AVAILABLE', '']:
            return False
        
        # Should NOT be a URL (catch misalignment)
        if description.startswith('http'):
            return False
        
        # Should NOT look like a timestamp
        if re.match(r'\d{4}-\d{2}-\d{2}', description[:10]):
            return False

        return True
    
    
    def validate_row(self, row: pd.Series, feature_cols: Dict[str, str]) -> Dict:
        """
        Validate a single row
        
        Args:
            row: DataFrame row
            feature_cols: Dict mapping feature type to column name
                         e.g., {'url': 'Job_URL', 'timestamp': 'Scraped_At', ...}
        
        Returns:
            Dict with validation results
        """
        results = {
            'is_valid': True,
            'issues': []
        }
        
        # Validate timestamp
        timestamp_col = feature_cols.get('timestamp', 'Scraped_At')
        if timestamp_col in row.index:
            if not self.is_timestamp(row[timestamp_col]):
                results['is_valid'] = False
                results['issues'].append(f"Invalid timestamp: {row[timestamp_col]}")
        
        # Validate URL
        url_col = feature_cols.get('url', 'Job_URL')
        if url_col in row.index:
            if not self.is_job_url(row[url_col]):
                results['is_valid'] = False
                results['issues'].append(f"Invalid URL: {str(row[url_col])[:50]}...")
        
        # Validate description
        desc_col = feature_cols.get('description', 'Description')
        if desc_col in row.index:
            if not self.is_description(row[desc_col]):
                results['is_valid'] = False
                results['issues'].append(f"Invalid description (length: {len(str(row[desc_col]))})")
        
        return results
    
    
    def validate_data(self, 
                     data: pd.DataFrame, 
                     features: List[str] = None) -> Tuple[pd.DataFrame, pd.DataFrame, Dict]:
        """
        Validate entire dataset and separate valid/invalid rows
        
        Args:
            data: DataFrame to validate
            features: List of column names [url_col, timestamp_col, description_col]
                     Default: ['Job_URL', 'Scraped_At', 'Description']
        
        Returns:
            Tuple of (valid_df, invalid_df, report_dict)
        """
        if features is None:
            features = ['Job_URL', 'Scraped_At', 'Description']
        
        logger.info("="*80)
        logger.info("Starting data validation")
        logger.info("="*80)
        logger.info(f"Total rows to validate: {len(data)}")
        logger.info(f"Features to validate: {features}")
        
        # Map feature types to column names
        feature_cols = {
            'url': features[0],
            'timestamp': features[1],
            'description': features[2]
        }
        
        # Create copy to avoid modifying original
        df = data.copy()
        
        # Initialize validation columns
        df['is_valid_data'] = True
        df['validation_issues'] = ''
        
        # Validate each row
        invalid_count = 0
        issue_summary = {}
        
        for idx, row in df.iterrows():
            validation_result = self.validate_row(row, feature_cols)
            
            if not validation_result['is_valid']:
                invalid_count += 1
                df.at[idx, 'is_valid_data'] = False
                df.at[idx, 'validation_issues'] = ' | '.join(validation_result['issues'])
                
                # Track issue types
                for issue in validation_result['issues']:
                    issue_type = issue.split(':')[0]
                    issue_summary[issue_type] = issue_summary.get(issue_type, 0) + 1
        
        # Split into valid and invalid
        df_valid = df[df['is_valid_data']].copy()
        df_invalid = df[~df['is_valid_data']].copy()
        
        # Create validation report
        validation_report = {
            'validation_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_rows': len(data),
            'valid_rows': len(df_valid),
            'invalid_rows': len(df_invalid),
            'invalid_percentage': (len(df_invalid) / len(data) * 100) if len(data) > 0 else 0,
            'features_validated': features,
            'issue_summary': issue_summary,
            'invalid_row_indices': df_invalid.index.tolist()[:100]  # First 100 for brevity
        }
        
        # Log summary
        logger.info("\n" + "="*80)
        logger.info("VALIDATION SUMMARY")
        logger.info("="*80)
        logger.info(f"✅ Valid rows:   {validation_report['valid_rows']:,} ({100-validation_report['invalid_percentage']:.2f}%)")
        logger.info(f"❌ Invalid rows: {validation_report['invalid_rows']:,} ({validation_report['invalid_percentage']:.2f}%)")
        
        if issue_summary:
            logger.info("\nIssue Breakdown:")
            for issue_type, count in sorted(issue_summary.items(), key=lambda x: x[1], reverse=True):
                logger.info(f"  {issue_type}: {count} rows")
        
        # Save files
        self._save_results(df_valid, df_invalid, validation_report)
        
        logger.info("="*80)
        
        return df_valid, df_invalid, validation_report
    
    
    def _save_results(self, 
                     df_valid: pd.DataFrame, 
                     df_invalid: pd.DataFrame, 
                     report: Dict):
        """
        Save validation results to files
        
        Args:
            df_valid: Valid rows
            df_invalid: Invalid rows
            report: Validation report dictionary
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save valid data (remove validation columns)
        valid_file = self.validated_path / f"jobs_validated_{timestamp}.csv"
        df_valid_clean = df_valid.drop(columns=['is_valid_data', 'validation_issues'], errors='ignore')
        df_valid_clean.to_csv(valid_file, index=False)
        logger.info(f"\n✅ Valid data saved: {valid_file}")
        
        # Save invalid data (keep validation columns for debugging)
        if len(df_invalid) > 0:
            invalid_file = self.rejected_path / f"validation_rejected_{timestamp}.csv"
            df_invalid.to_csv(invalid_file, index=False)
            logger.info(f"❌ Invalid data saved: {invalid_file}")
        
        # Save validation report
        report_file = self.rejected_path / f"validation_report_{timestamp}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"📊 Validation report saved: {report_file}")


# Usage example
if __name__ == "__main__":
    # Initialize validator
    validator = FeatureBasedDataValidator(
        validated_path="data/processed/validated",
        rejected_path="data/processed/rejected"
    )
    
    # Load data
    df = pd.read_csv(r"D:\DATA SCIENCE AND ML\Project\job_trend_predictor\etl_pipeline\data\raw\scraped_data.csv")
    
    # Validate with actual column names
    df_valid, df_invalid, report = validator.validate_data(
        data=df,
        features=['Job_URL', 'Scraped_At', 'Description']  # ✅ Corrected column names
    )
    
    # Check results
    print(f"\n✅ Valid: {len(df_valid)} rows")
    print(f"❌ Invalid: {len(df_invalid)} rows")
    
    # Show sample invalid rows
    if len(df_invalid) > 0:
        print("\nSample invalid rows:")
        print(df_invalid[['Job_URL', 'Scraped_At', 'Description', 'validation_issues']].head())