from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Initial migration — matches the live conversion_history table exactly.
    Table was renamed from pdfapp_conversionhistory and record_status was
    changed to ENUM('Active','Inactive') via raw SQL.
    This migration is fake-applied so Django state matches the database.
    """

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='ConversionHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('original_filename', models.CharField(max_length=255)),
                ('converted_filename', models.CharField(max_length=255)),
                ('conversion_type', models.CharField(max_length=100)),
                ('file_size', models.CharField(max_length=50)),
                ('result', models.CharField(default='Success', max_length=20)),
                ('download_url', models.CharField(max_length=512)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('record_status', models.CharField(
                    choices=[('Active', 'Active'), ('Inactive', 'Inactive')],
                    db_index=True,
                    default='Active',
                    max_length=10,
                )),
            ],
            options={
                'verbose_name': 'Conversion History',
                'verbose_name_plural': 'Conversion History',
                'db_table': 'conversion_history',
                'ordering': ['-created_at'],
            },
        ),
    ]
