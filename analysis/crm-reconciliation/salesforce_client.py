"""Thin simple_salesforce wrapper reading credentials from environment.

Uses the OAuth 2.0 JWT Bearer flow via a Connected App (a self-signed
certificate, no password grant at all). This project tried two other
paths first, in this order, both blocked by Salesforce platform defaults
on a fresh org: (1) plain SOAP login() -- disabled by default as part of
its phased retirement (full cutoff Summer '27); (2) OAuth 2.0
username-password flow -- also blocked by default on orgs created Summer
'23 or later, and the org-level toggle to re-enable it was itself locked
out in this org. JWT Bearer doesn't depend on either deprecated flow and
isn't on any current retirement path, so it's the actually-durable choice,
not just the third thing that happened to work.

simple_salesforce's SalesforceLogin() dispatches on which arguments are
present, checked in a fixed order (security_token -> username+password ->
organizationId -> username+password -> username+consumer_key+privatekey
[JWT] -> consumer_key+consumer_secret+custom-domain [client credentials]
-> SOAP fallback). To reach the JWT branch, `password` and
`security_token` must be genuinely omitted, not just falsy -- both live
in .env for reference/prior attempts, but must NOT be read here."""
import os
from dotenv import load_dotenv
from simple_salesforce import Salesforce

load_dotenv()


def get_client() -> Salesforce:
    username = os.environ["SALESFORCE_USERNAME"]
    consumer_key = os.environ["SALESFORCE_CONSUMER_KEY"]
    privatekey_file = os.environ.get(
        "SALESFORCE_JWT_PRIVATE_KEY_FILE",
        os.path.join(os.path.dirname(__file__), "salesforce_jwt.key"),
    )
    domain = os.environ.get("SALESFORCE_DOMAIN", "login")
    return Salesforce(
        username=username,
        consumer_key=consumer_key,
        privatekey_file=privatekey_file,
        domain=domain,
    )
