from app.integrations.job_sources.linkedin import LinkedInAdapter
from app.integrations.job_sources.naukri import NaukriAdapter
from app.integrations.job_sources.internshala import InternshalaAdapter
from app.integrations.job_sources.indeed import IndeedAdapter
from app.integrations.job_sources.wellfound import WellfoundAdapter

__all__ = [
    "LinkedInAdapter",
    "NaukriAdapter",
    "InternshalaAdapter",
    "IndeedAdapter",
    "WellfoundAdapter",
]