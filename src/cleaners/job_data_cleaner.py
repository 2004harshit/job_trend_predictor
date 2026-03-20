from .base_cleaner import DataCleaner
from .strategies.feature_cleaning_strategy import FeatureCleaningStrategy
from .strategies.skill_cleaning_strategy import SkillsCleaningStrategy
from .strategies.posted_date_cleaning_strategy import PostedDateCleaningStrategy
import pandas as pd
import yaml
import logging
import importlib
from typing import Dict


class JobDataCleaner(DataCleaner):
    """
    Concrete implementation of DataCleaner for job market data.

    Applies column-specific cleaning strategies based on a YAML config file.
    Uses the Strategy pattern to delegate cleaning logic to specialised classes.

    Design contract (strict):
    ─────────────────────────
    1. Accepts DataFrames from ANY source (CSV or SQL) with ANY column casing.
       e.g. CSV: 'Title', 'Star_Skills', 'Industry Type'
            SQL: 'title', 'star_skills', 'industry_type'

    2. On entry, ALL column names are immediately lowercased.
       This is the only normalisation step — no canonical mapping, no renaming.

    3. All strategies operate on these lowercased column names.

    4. All output columns (both original and newly generated) remain lowercase.
       e.g. title → title_cleaned
            education → ug_degree, ug_specialization, pg_degree, pg_specialization
            star_skills + normal_skills → combined_skills, skill_count

    Special cases:
    - TitleCleaningStrategy      : requires job_list from config
    - RoleCleaningStrategy       : requires job_list from config
    - SkillsCleaningStrategy     : reads two columns (star_skills + normal_skills)
    - PostedDateCleaningStrategy : reads two columns (posted_date + scraped_at)

    Attributes:
        strategy_registry (Dict[str, FeatureCleaningStrategy]):
            Maps lowercase column name → instantiated strategy object
        config_path (str): Path to the YAML configuration file
        config (dict):     Loaded configuration dictionary

    Example:
        >>> cleaner = JobDataCleaner("config/cleaning_config.yaml")
        >>> df = pd.read_csv("jobs.csv")     # Title, Star_Skills, Industry Type ...
        >>> df = cleaner.clean_all(df)       # → title, star_skills, industry type ...
        >>>                                  #   + title_cleaned, combined_skills, etc.
    """

    # ------------------------------------------------------------------ #
    #  Strategy class registry                                              #
    # ------------------------------------------------------------------ #

    _STRATEGY_CLASSES: Dict[str, str] = {
        "TitleCleaningStrategy":          "strategies.title_cleaning_strategy.TitleCleaningStrategy",
        "CompanyCleaningStrategy":        "strategies.company_cleaning_strategy.CompanyCleaningStrategy",
        "LocationCleaningStrategy":       "strategies.location_cleaning_strategy.LocationCleaningStrategy",
        "SalaryCleaningStrategy":         "strategies.salary_cleaning_strategy.SalaryCleaningStrategy",
        "ExperienceCleaningStrategy":     "strategies.experience_cleaning_strategy.ExperienceCleaningStrategy",
        "EducationCleaningStrategy":      "strategies.education_cleaning_strategy.EducationCleaningStrategy",
        "SkillsCleaningStrategy":         "strategies.skill_cleaning_strategy.SkillsCleaningStrategy",
        "DepartmentCleaningStrategy":     "strategies.department_cleaning_strategy.DepartmentCleaningStrategy",
        "TimestampCleaningStrategy":      "strategies.timestamp_cleaning_strategy.TimestampCleaningStrategy",
        "DescriptionCleaningStrategy":    "strategies.description_cleaning_strategy.DescriptionCleaningStrategy",
        "EmploymentTypeCleaningStrategy": "strategies.employment_type_cleaning_strategy.EmploymentTypeCleaningStrategy",
        "IndustryTypeCleaningStrategy":   "strategies.industry_type_cleaning_strategy.IndustryTypeCleaningStrategy",
        "LastApplyDateCleaningStrategy":  "strategies.last_apply_date_cleaning_strategy.LastApplyDateCleaningStrategy",
        "PostedDateCleaningStrategy":     "strategies.posted_date_cleaning_strategy.PostedDateCleaningStrategy",
        "RoleCategoryCleaningStrategy":   "strategies.role_category_cleaning_strategy.RoleCategoryCleaningStrategy",
        "RoleCleaningStrategy":           "strategies.role_type_cleaning_strategy.RoleCleaningStrategy",
    }

    # Strategies that require job_list injected from config at construction time
    _JOB_LIST_STRATEGIES = {"TitleCleaningStrategy", "RoleCleaningStrategy"}

    # ------------------------------------------------------------------ #
    #  Init                                                                 #
    # ------------------------------------------------------------------ #

    def __init__(self, config_path: str):
        self.strategy_registry: Dict[str, FeatureCleaningStrategy] = {}
        self.config_path: str = config_path
        self.config: dict = self._load_config(config_path)
        self.logger = logging.getLogger(__name__)

        # All mapping keys stored lowercase — matches lowercased DataFrame columns.
        # e.g. config key "Title"           → stored as "title"
        #      config key "Employment Type" → stored as "employment type"
        #      config key "Star_Skills"     → stored as "star_skills"
        self.column_mappings: Dict[str, str] = {
            k.lower(): v
            for k, v in self.config.get("column_mappings", {}).items()
        }

        # Skills source column names — lowercased to match lowercased DataFrame.
        # config:  star_skills_col: Star_Skills  → stored as "star_skills"
        self.skills_columns: Dict[str, str] = {
            k: v.lower() if isinstance(v, str) else v
            for k, v in self.config.get("skills_columns", {}).items()
        }

        # Posted date source column names — lowercased.
        # config:  posted_date_col: Posted_Date  → stored as "posted_date"
        self.posted_date_columns: Dict[str, str] = {
            k: v.lower() if isinstance(v, str) else v
            for k, v in self.config.get("posted_date_columns", {}).items()
        }

        self._initialize_strategies()

    # ------------------------------------------------------------------ #
    #  Config loading                                                       #
    # ------------------------------------------------------------------ #

    def _load_config(self, config_path: str) -> dict:
        """
        Load and parse the YAML configuration file.

        Raises:
            ValueError: If the file cannot be read or is not a YAML mapping
        """
        try:
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
        except Exception as e:
            raise ValueError(f"Failed to load config from '{config_path}': {e}")

        if not isinstance(config, dict):
            raise ValueError(
                f"Config file '{config_path}' must contain a YAML mapping at the top level."
            )
        return config

    # ------------------------------------------------------------------ #
    #  Strategy initialisation                                              #
    # ------------------------------------------------------------------ #

    def _initialize_strategies(self) -> None:
        """
        Instantiate and register all cleaning strategies defined in config.

        Raises:
            ValueError: If a strategy name is unknown, or required config keys
                        are missing (e.g. job_list for TitleCleaningStrategy)
        """
        if not self.column_mappings:
            raise ValueError("Config must contain a non-empty 'column_mappings' section.")

        for column_lower, strategy_name in self.column_mappings.items():
            strategy_class = self._import_strategy(strategy_name)
            # Registry key is already lowercase (set in __init__)
            self.strategy_registry[column_lower] = self._build_strategy(
                strategy_name, strategy_class
            )

    def _import_strategy(self, strategy_name: str):
        """
        Dynamically import a strategy class by its registered name.

        Returns:
            Uninstantiated strategy class

        Raises:
            ValueError: If strategy_name is not in _STRATEGY_CLASSES
        """
        module_path = self._STRATEGY_CLASSES.get(strategy_name)
        if not module_path:
            raise ValueError(
                f"Unknown strategy '{strategy_name}'. "
                f"Registered strategies: {list(self._STRATEGY_CLASSES.keys())}"
            )

        module_str, class_name = module_path.rsplit(".", 1)
        module = importlib.import_module(f".{module_str}", package=__package__)
        return getattr(module, class_name)

    def _build_strategy(
        self, strategy_name: str, strategy_class
    ) -> FeatureCleaningStrategy:
        """
        Instantiate a strategy, injecting constructor arguments where required.

        - TitleCleaningStrategy and RoleCleaningStrategy require job_list.
        - All other strategies use a no-arg constructor.

        Raises:
            ValueError: If job_list is missing from config for strategies that need it
        """
        if strategy_name in self._JOB_LIST_STRATEGIES:
            job_list = self.config.get("job_list", [])
            if not job_list:
                raise ValueError(
                    f"Config must contain a non-empty 'job_list' for {strategy_name}."
                )
            return strategy_class(job_list=job_list)

        return strategy_class()

    # ------------------------------------------------------------------ #
    #  Column lowercasing                                                   #
    # ------------------------------------------------------------------ #

    def _lowercase_columns(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Lowercase every column name in the DataFrame.

        This is the ONLY normalisation step. It handles any source (CSV or SQL)
        regardless of original casing, spaces, or underscores in column names.

        Examples of what happens:
            CSV 'Title'           → 'title'
            CSV 'Star_Skills'     → 'star_skills'
            CSV 'Industry Type'   → 'industry type'
            CSV 'Employment Type' → 'employment type'
            SQL 'title'           → 'title'           (unchanged, already lowercase)
            SQL 'industry_type'   → 'industry_type'   (unchanged, already lowercase)

        Note: CSV 'Industry Type' → 'industry type' (space preserved)
              SQL 'industry_type' → 'industry_type'  (underscore preserved)
              These are DIFFERENT keys. If your config uses 'Industry Type' (with space),
              SQL data with 'industry_type' (underscore) will not match. To handle both,
              list both variants in config or pre-rename SQL columns before passing in.

        Args:
            data: Raw DataFrame from any source

        Returns:
            Copy of DataFrame with all column names lowercased

        Raises:
            TypeError:  If input is not a DataFrame
            ValueError: If lowercasing creates duplicate column names
                        (two source columns differed only by case)
        """
        if not isinstance(data, pd.DataFrame):
            raise TypeError(
                f"Expected pd.DataFrame, got {type(data).__name__}"
            )

        lowercased = [str(col).lower() for col in data.columns]

        # Guard: collision check — two columns that differ only by case
        if len(set(lowercased)) != len(lowercased):
            from collections import Counter
            dupes = [col for col, count in Counter(lowercased).items() if count > 1]
            raise ValueError(
                f"Column name collision after lowercasing: {dupes}. "
                f"Source DataFrame has columns that differ only by case."
            )

        data = data.copy()
        data.columns = lowercased
        return data

    # ------------------------------------------------------------------ #
    #  Public cleaning interface                                            #
    # ------------------------------------------------------------------ #

    def clean(self, data: pd.DataFrame, column: str) -> pd.DataFrame:
        """
        Apply the registered cleaning strategy for one column.

        Assumes data columns are already lowercased (clean_all() handles this
        automatically; if calling clean() directly, lowercase first).

        Output column naming:
        ┌─────────────────────────────────────────────────────────────────┐
        │ Single-column strategy (returns pd.Series):                     │
        │   '{column}_cleaned'   — e.g. 'title_cleaned', 'salary_cleaned' │
        │                                                                 │
        │ Multi-column strategy (returns pd.DataFrame):                   │
        │   Each sub-column name lowercased from strategy output          │
        │   Education  → 'ug_degree', 'ug_specialization',               │
        │                'pg_degree', 'pg_specialization'                 │
        │   Skills     → 'combined_skills', 'skill_count'                │
        │   Experience → 'min_experience', 'max_experience'              │
        │   Salary     → 'min_salary', 'max_salary', 'avg_salary'        │
        │   Location   → 'location_cities', 'primary_location',          │
        │                'location_count', 'is_remote'                   │
        │   Department → 'department_cleaned', 'primary_department',     │
        │                'department_count'                               │
        │   PostedDate → 'posted_date_parsed', 'days_since_posted'       │
        └─────────────────────────────────────────────────────────────────┘

        Args:
            data:   DataFrame with lowercased column names
            column: Column to clean (lowercased internally, case-insensitive)

        Returns:
            DataFrame with new cleaned column(s) appended (all lowercase)

        Raises:
            ValueError: If no strategy is registered, or column validation fails
            TypeError:  If strategy returns an unexpected type
        """
        col = str(column).lower()

        strategy = self.strategy_registry.get(col)
        if not strategy:
            raise ValueError(
                f"No strategy registered for column '{col}'. "
                f"Registered columns: {list(self.strategy_registry.keys())}"
            )

        # ------------------------------------------------------------------ #
        #  Resolve feature input per strategy type                             #
        # ------------------------------------------------------------------ #

        if isinstance(strategy, SkillsCleaningStrategy):
            if not self._validate_skills_columns(data):
                star = self.skills_columns.get("star_skills_col", "star_skills")
                normal = self.skills_columns.get("normal_skills_col", "normal_skills")
                raise ValueError(
                    f"SkillsCleaningStrategy requires columns '{star}' and '{normal}'. "
                    f"Available: {list(data.columns)}"
                )
            feature = self._get_skills_dataframe(data)

        elif isinstance(strategy, PostedDateCleaningStrategy):
            if not self._validate_posted_date_columns(data):
                posted = self.posted_date_columns.get("posted_date_col", "posted_date")
                scraped = self.posted_date_columns.get("scraped_at_col", "scraped_at")
                raise ValueError(
                    f"PostedDateCleaningStrategy requires columns '{posted}' and '{scraped}'. "
                    f"Available: {list(data.columns)}"
                )
            feature = self._get_posted_date_dataframe(data)

        else:
            if not self.validate(data, col):
                raise ValueError(
                    f"Validation failed for column '{col}': "
                    f"column is missing or all-null."
                )
            feature = data[col]

        # ------------------------------------------------------------------ #
        #  Run strategy                                                         #
        # ------------------------------------------------------------------ #

        cleaned_feature = strategy.clean_feature(feature)

        # ------------------------------------------------------------------ #
        #  Write results back — ALL output column names lowercased             #
        # ------------------------------------------------------------------ #

        if isinstance(cleaned_feature, pd.Series):
            # e.g. 'title' → 'title_cleaned'
            data[f"{col}_cleaned"] = cleaned_feature

        elif isinstance(cleaned_feature, pd.DataFrame):
            # Lowercase each sub-column name from the strategy output.
            # e.g. strategy returns 'UG_Degree' → written as 'ug_degree'
            #      strategy returns 'Combined_Skills' → written as 'combined_skills'
            for sub_col in cleaned_feature.columns:
                data[sub_col.lower()] = cleaned_feature[sub_col]

        else:
            raise TypeError(
                f"Strategy '{type(strategy).__name__}' returned unexpected "
                f"type: {type(cleaned_feature).__name__}. "
                f"Expected pd.Series or pd.DataFrame."
            )

        return data

    def clean_all(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Full pipeline entry point: lowercase columns → apply all strategies.

        Accepts DataFrames from any source (CSV or SQL, any casing).
        After this call, ALL columns in the output are lowercase.

        Args:
            data: Raw DataFrame from CSV or SQL (any column casing)

        Returns:
            DataFrame with:
            - All original columns lowercased
            - All new cleaned columns appended (also lowercase)

        Raises:
            TypeError:   If data is not a DataFrame
            ValueError:  If column lowercasing produces duplicates
            RuntimeError: If any strategy fails mid-pipeline
        """
        # Step 1: lowercase all column names — handles CSV and SQL uniformly
        data = self._lowercase_columns(data)
        self.logger.info(f"Columns after lowercasing: {list(data.columns)}")

        # Step 2: apply each registered strategy in config order
        for col in self.strategy_registry:
            try:
                data = self.clean(data, col)
            except Exception as e:
                raise RuntimeError(
                    f"Pipeline failed on column '{col}': {e}"
                ) from e

        self.logger.info(f"clean_all complete. Output columns: {list(data.columns)}")
        return data

    # ------------------------------------------------------------------ #
    #  Private helpers                                                      #
    # ------------------------------------------------------------------ #

    def _validate_skills_columns(self, data: pd.DataFrame) -> bool:
        """Check both skills source columns exist in the lowercased DataFrame."""
        if not self.validate_dataframe(data):
            return False
        star_col = self.skills_columns.get("star_skills_col")
        normal_col = self.skills_columns.get("normal_skills_col")
        if not star_col or not normal_col:
            return False
        return star_col in data.columns and normal_col in data.columns

    def _validate_posted_date_columns(self, data: pd.DataFrame) -> bool:
        """Check both posted-date source columns exist in the lowercased DataFrame."""
        if not self.validate_dataframe(data):
            return False
        posted_col = self.posted_date_columns.get("posted_date_col")
        scraped_col = self.posted_date_columns.get("scraped_at_col")
        if not posted_col or not scraped_col:
            return False
        return posted_col in data.columns and scraped_col in data.columns

    def _get_posted_date_dataframe(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Build the two-column sub-DataFrame for PostedDateCleaningStrategy.

        Column names used here are lowercase (e.g. 'posted_date', 'scraped_at').
        PostedDateCleaningStrategy.REQUIRED_COLUMNS must be updated to lowercase:
            REQUIRED_COLUMNS = {"posted_date", "scraped_at"}
        and the apply lambda updated accordingly (Bug 6 fix).
        """
        posted_col = self.posted_date_columns.get("posted_date_col")
        scraped_col = self.posted_date_columns.get("scraped_at_col")

        if not posted_col or not scraped_col:
            raise ValueError(
                "Config must define 'posted_date_columns.posted_date_col' and "
                "'posted_date_columns.scraped_at_col'."
            )

        missing = {posted_col, scraped_col} - set(data.columns)
        if missing:
            raise ValueError(
                f"Posted date columns missing from DataFrame: {missing}"
            )

        return data[[posted_col, scraped_col]].copy()

    def _get_skills_dataframe(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Build the two-column sub-DataFrame for SkillsCleaningStrategy.

        SkillsCleaningStrategy.REQUIRED_COLUMNS = {"Star_Skills", "Normal_Skills"}.
        We rename the lowercase DataFrame columns to match exactly what the
        strategy expects internally. The strategy's output column names
        (Combined_Skills, Skill_Count) are then lowercased on write-back in clean().
        """
        star_col = self.skills_columns.get("star_skills_col")      # e.g. "star_skills"
        normal_col = self.skills_columns.get("normal_skills_col")  # e.g. "normal_skills"

        if not star_col or not normal_col:
            raise ValueError(
                "Config must define 'skills_columns.star_skills_col' and "
                "'skills_columns.normal_skills_col'."
            )

        missing = {star_col, normal_col} - set(data.columns)
        if missing:
            raise ValueError(
                f"Skills source columns missing from DataFrame: {missing}"
            )

        # Rename to what SkillsCleaningStrategy.REQUIRED_COLUMNS expects
        return data[[star_col, normal_col]].rename(columns={
            star_col: "Star_Skills",
            normal_col: "Normal_Skills",
        })

    def _get_strategy(self, column: str) -> FeatureCleaningStrategy:
        """Retrieve registered strategy for a column name (case-insensitive)."""
        return self.strategy_registry.get(str(column).lower())


if __name__ == "__main__":
    pass