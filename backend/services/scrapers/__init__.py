"""Job board scraper parsers package."""

from services.scrapers.arbeitsagentur import ArbeitsagenturParser
from services.scrapers.base import JobBoardParser
from services.scrapers.generic import GenericJobParser
from services.scrapers.indeed import IndeedParser
from services.scrapers.softgarden import SoftgardenParser
from services.scrapers.stepstone import StepStoneParser
from services.scrapers.xing import XingParser

__all__ = [
    "ArbeitsagenturParser",
    "GenericJobParser",
    "IndeedParser",
    "JobBoardParser",
    "SoftgardenParser",
    "StepStoneParser",
    "XingParser",
]
