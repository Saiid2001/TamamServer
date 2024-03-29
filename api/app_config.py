import os

CLIENT_ID = "a5d55ddc-e701-4a9b-81e9-3210d0bf5ebc" # Application (client) ID of app registration

CLIENT_SECRET = "8e2B8aKiY2.W78R0zG3DlzNwF9~D_1wZH_" # Placeholder - for use ONLY during testing.
# In a production app, we recommend you use a more secure method of storing your secret,
# like Azure Key Vault. Or, use an environment variable as described in Flask's documentation:
# https://flask.palletsprojects.com/en/1.1.x/config/#configuring-from-environment-variables
# CLIENT_SECRET = os.getenv("CLIENT_SECRET")
# if not CLIENT_SECRET:
#     raise ValueError("Need to define CLIENT_SECRET environment variable")

AUTHORITY = "https://login.microsoftonline.com/common"  # For multi-tenant app
# AUTHORITY = "https://login.microsoftonline.com/Enter_the_Tenant_Name_Here"

REDIRECT_PATH = "/getAToken"  # Used for forming an absolute URL to your redirect URI.
                              # The absolute URL must match the redirect URI you set
                              # in the app's registration in the Azure portal.

# You can find more Microsoft Graph API endpoints from Graph Explorer
# https://developer.microsoft.com/en-us/graph/graph-explorer
ENDPOINT = 'https://graph.microsoft.com/v1.0/users'  # This resource requires no admin consent

# You can find the proper permission names from this document
# https://docs.microsoft.com/en-us/graph/permissions-reference
SCOPE = ["User.ReadBasic.All"]

SESSION_TYPE = "filesystem"  # Specifies the token cache should be stored in server-side session

CONFIRMATION_SECRET_KEY = "71936c948e54da7e642e83c9a2cdcf00"
# For email confirmation, placeholder key for use only during testing
# More secure method to store this during deployment is advisable
# Generated using import os; print(os.urandom(16).hex())

SECURITY_PASSWORD_SALT = "tablesalt"
# Used by itsdangerous along with the key to derive the key used in email confirmation