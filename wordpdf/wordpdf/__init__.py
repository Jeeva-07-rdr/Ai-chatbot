from django.db.backends.mysql.base import DatabaseWrapper
from django.db.backends.mysql.features import DatabaseFeatures

# Bypass Django 5.1+ MariaDB 10.6 minimum version check for XAMPP (MariaDB 10.4)
original_check = DatabaseWrapper.check_database_version_supported

def bypass_check(self):
    try:
        original_check(self)
    except Exception as e:
        if "MariaDB 10.6 or later is required" in str(e):
            pass # Ignore XAMPP MariaDB 10.4 error
        else:
            raise e

DatabaseWrapper.check_database_version_supported = bypass_check

# Disable RETURNING clauses since MariaDB 10.4 doesn't support them
DatabaseFeatures.can_return_columns_from_insert = False
DatabaseFeatures.can_return_rows_from_bulk_insert = False

