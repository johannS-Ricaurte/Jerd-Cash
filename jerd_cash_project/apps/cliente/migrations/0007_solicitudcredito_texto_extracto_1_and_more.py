from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cliente', '0006_solicitudcredito_plazo_meses'),
    ]

    operations = [
        migrations.AddField(
            model_name='solicitudcredito',
            name='texto_extracto_1',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='solicitudcredito',
            name='texto_extracto_2',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='solicitudcredito',
            name='texto_extracto_3',
            field=models.TextField(blank=True, default=''),
        ),
    ]