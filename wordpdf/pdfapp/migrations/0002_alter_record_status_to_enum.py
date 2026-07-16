from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pdfapp', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE conversion_history MODIFY COLUMN record_status ENUM('Active', 'Inactive') NOT NULL DEFAULT 'Active';",
            reverse_sql="ALTER TABLE conversion_history MODIFY COLUMN record_status VARCHAR(10) NOT NULL DEFAULT 'Active';"
        )
    ]
