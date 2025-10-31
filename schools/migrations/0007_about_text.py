from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('schools', '0006_alter_galleryimage_options_school_about_text_and_more'),  # Use whatever comes after 0005
    ]

    operations = [
        migrations.AddField(
            model_name='school',
            name='about_text',
            field=models.TextField(blank=True, null=True),
        ),
    ]