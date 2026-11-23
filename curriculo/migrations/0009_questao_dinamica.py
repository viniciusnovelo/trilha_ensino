from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('curriculo', '0008_alter_disciplina_ativo_alter_disciplina_icone_and_more')]
    operations = [
        migrations.AddField(
            model_name='questao', name='tipo_resposta',
            field=models.CharField(choices=[('choice', 'Múltipla escolha'), ('numeric', 'Numérica')], default='choice', max_length=12),
        ),
        migrations.AddField(
            model_name='questao', name='dados_dinamicos',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name='questao', name='codigo_fonte',
            field=models.CharField(blank=True, max_length=80, null=True, unique=True),
        ),
    ]