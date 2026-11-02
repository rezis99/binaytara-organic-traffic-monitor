"""
Binaytara SEO Monitor — Authentication
Service-account credentials shared by GA4 and GSC clients.
Retry-wrapped to handle transient SSL/connection errors on
Streamlit Community Cloud.
"""

import streamlit as st
from google.oauth2 import service_account
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from googleapiclient.discovery import build
from utils import retry_on_ssl

SCOPES = [
    "https://www.googleapis.com/auth/analytics.readonly",
    "https://www.googleapis.com/auth/webmasters.readonly",
]


@st.cache_resource(show_spinner=False)
def _credentials():
    """Build credentials once per app lifecycle."""
    info = dict(st.secrets["gcp_service_account"])
    return service_account.Credentials.from_service_account_info(info, scopes=SCOPES)


@st.cache_resource(show_spinner=False)
@retry_on_ssl(max_retries=3, delay=2.0)
def ga4_client() -> BetaAnalyticsDataClient:
    """Return a GA4 Data API client (retries on SSL failures)."""
    return BetaAnalyticsDataClient(credentials=_credentials())


@st.cache_resource(show_spinner=False)
@retry_on_ssl(max_retries=3, delay=2.0)
def gsc_service():
    """Return a GSC Search Analytics service (retries on SSL failures)."""
    return build("searchconsole", "v1", credentials=_credentials(), cache_discovery=False)
