# knowledge_base.py
# Central constants used by the Recommendation Engine

# Skills required per domain
DOMAIN_REQUIRED_SKILLS = {
    "Data Scientist": ["Python", "SQL", "Machine Learning", "Statistics", "Pandas"],
    "Machine Learning Engineer": ["Python", "TensorFlow", "PyTorch", "Machine Learning", "Statistics", "Docker"],
    "Web Developer": ["HTML", "CSS", "JavaScript", "React", "Node.js"],
    "Full Stack Developer": ["HTML", "CSS", "JavaScript", "React", "Node.js", "Python", "SQL"],
    "Backend Engineer": ["Java", "Python", "SQL", "Docker", "APIs"],
    "Front End Developer": ["HTML", "CSS", "JavaScript", "React", "TypeScript"],
    "Data Analyst": ["SQL", "Python", "Excel", "Tableau", "Statistics", "Pandas"],
    "Data Engineer": ["Python", "SQL", "Spark", "Airflow", "Docker", "Cloud"],
    "DevOps Engineer": ["Linux", "Docker", "Kubernetes", "CI/CD", "AWS", "Terraform"],
    "Cloud Engineer": ["AWS", "Linux", "Docker", "Terraform", "Networking"],
    "AI Engineer": ["Python", "Machine Learning", "TensorFlow", "APIs", "Docker", "LLMs"],
    "QA Automation": ["Selenium", "Python", "Testing Concepts", "Jira"],
    "Software Engineer": ["Python", "Java", "SQL", "Data Structures", "Algorithms", "Git"],
}

# Domains with heavy mathematics requirements
DOMAIN_MATH_HEAVY = {
    "Data Scientist": True,
    "Machine Learning Engineer": True,
    "Web Developer": False,
    "Full Stack Developer": False,
    "Backend Engineer": False,
    "Front End Developer": False,
    "Data Analyst": True,
    "Data Engineer": False,
    "DevOps Engineer": False,
    "Cloud Engineer": False,
    "AI Engineer": True,
    "QA Automation": False,
    "Software Engineer": False,
}

# Whether a domain commonly supports remote/location-flexible work
DOMAIN_LOCATION_FLEXIBLE = {
    "Data Scientist": True,
    "Machine Learning Engineer": True,
    "Web Developer": True,
    "Full Stack Developer": True,
    "Backend Engineer": True,
    "Front End Developer": True,
    "Data Analyst": True,
    "Data Engineer": True,
    "DevOps Engineer": True,
    "Cloud Engineer": True,
    "AI Engineer": True,
    "QA Automation": False,   # Often requires on-site hardware/labs
    "Software Engineer": True,
}

# Entry barrier: 1 = Easy entry, 10 = Very high barrier
DOMAIN_ENTRY_BARRIER = {
    "Data Scientist": 8,
    "Machine Learning Engineer": 9,
    "Web Developer": 4,
    "Full Stack Developer": 6,
    "Backend Engineer": 6,
    "Front End Developer": 4,
    "Data Analyst": 5,
    "Data Engineer": 7,
    "DevOps Engineer": 7,
    "Cloud Engineer": 7,
    "AI Engineer": 9,
    "QA Automation": 3,
    "Software Engineer": 6,
}

# Competition level: 1 = Low competition, 10 = Hyper competitive
DOMAIN_COMPETITION = {
    "Data Scientist": 9,
    "Machine Learning Engineer": 8,
    "Web Developer": 8,
    "Full Stack Developer": 7,
    "Backend Engineer": 6,
    "Front End Developer": 7,
    "Data Analyst": 7,
    "Data Engineer": 5,
    "DevOps Engineer": 5,
    "Cloud Engineer": 5,
    "AI Engineer": 6,
    "QA Automation": 4,
    "Software Engineer": 8,
}

# Approximate average salary range in LPA for freshers (India market)
DOMAIN_FRESHER_SALARY_RANGE = {
    "Data Scientist": (4.0, 9.0),
    "Machine Learning Engineer": (5.0, 10.0),
    "Web Developer": (2.5, 6.0),
    "Full Stack Developer": (3.5, 8.0),
    "Backend Engineer": (3.5, 7.5),
    "Front End Developer": (2.5, 6.0),
    "Data Analyst": (3.0, 7.0),
    "Data Engineer": (4.0, 9.0),
    "DevOps Engineer": (4.0, 8.0),
    "Cloud Engineer": (4.5, 9.0),
    "AI Engineer": (5.0, 12.0),
    "QA Automation": (2.5, 5.5),
    "Software Engineer": (3.5, 7.5),
}

# All supported domains (canonical list for the UI selectbox)
ALL_DOMAINS = list(DOMAIN_REQUIRED_SKILLS.keys())