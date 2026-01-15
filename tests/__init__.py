import os

from dotenv import load_dotenv
from google.cloud import firestore
from google.oauth2 import service_account

import infra

load_dotenv()  # loads from .env in current working dir

cdr = os.path.dirname(os.path.abspath(__file__))
admin_sdk = os.path.join(cdr, './admin_sdk.json')

cred = service_account.Credentials.from_service_account_file(admin_sdk)
infra.database = firestore.Client(credentials=cred)
