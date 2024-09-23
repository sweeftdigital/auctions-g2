import os

# Set APP_ENV in env file to configure which settings
# will be used to configure the project.
# Defaults to DEV environment
APP_ENV = os.environ.get("APP_ENV", "dev")

if APP_ENV in ("dev", "prod"):
    exec("from .%s import *" % APP_ENV)
else:
    raise EnvironmentError("Invalid value for APP_ENV")
