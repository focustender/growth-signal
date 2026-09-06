"""Thin simple_salesforce wrapper reading credentials from environment.

Uses the OAuth 2.0 username-password flow via a Connected App
(consumer_key/consumer_secret), not plain SOAP login() -- new Salesforce
orgs disable SOAP API login() by default as part of its phased retirement
(fully gone by Summer '27), so the OAuth flow is the durable choice here,
not just a workaround."""
import os
from dotenv import load_dotenv
from simple_salesforce import Salesforce

load_dotenv()


def get_client() -> Salesforce:
    username = os.environ["SALESFORCE_USERNAME"]
    password = os.environ["SALESFORCE_PASSWORD"]
    token = os.environ.get("SALESFORCE_SECURITY_TOKEN", "")
    consumer_key = os.environ["SALESFORCE_CONSUMER_KEY"]
    consumer_secret = os.environ["SALESFORCE_CONSUMER_SECRET"]
    domain = os.environ.get("SALESFORCE_DOMAIN", "login")
    return Salesforce(
        username=username,
        password=password,
        security_token=token,
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        domain=domain,
    )
