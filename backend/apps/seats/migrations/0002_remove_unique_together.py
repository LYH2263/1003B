from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('seats', '0001_initial'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='seatreservation',
            unique_together=set(),
        ),
    ]
