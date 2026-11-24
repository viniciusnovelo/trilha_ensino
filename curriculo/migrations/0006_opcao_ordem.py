from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('curriculo', '0005_materia_disciplina_materia'),
    ]

    operations = [
        migrations.AddField(
            model_name='opcao',
            name='ordem',
            field=models.PositiveIntegerField(
                default=1,
                help_text=(
                    'Posição de exibição da alternativa dentro da questão.'
                ),
            ),
        ),
        migrations.AlterModelOptions(
            name='opcao',
            options={
                'ordering': ['ordem', 'id'],
                'verbose_name': 'Opção',
                'verbose_name_plural': 'Opções',
            },
        ),
    ]
