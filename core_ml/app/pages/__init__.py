# This file makes the pages directory a Python package
# It can be empty or contain package-level imports

from . import home
from . import student_dashboard
from . import counselor_dashboard
from . import about

__all__ = ['home', 'student_dashboard', 'counselor_dashboard', 'about']