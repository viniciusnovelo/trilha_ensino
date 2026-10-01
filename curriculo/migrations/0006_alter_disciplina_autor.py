from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        (
            'curriculo',
            '0005_materia_disciplina_materia',
        ),
    ]

    operations = [
        migrations.AlterField(
            model_name='disciplina',
            name='autor',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='trilhas_criadas',
                to='auth.user',
            ),
        ),
    ]
