from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('gamificacao', '0006_remove_progressomodulo_chave_disponivel')]
    operations = [
        migrations.AlterField(
            model_name='respostatentativa', name='texto_opcao_snapshot',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        migrations.AddField(
            model_name='respostatentativa', name='tipo_resposta_snapshot',
            field=models.CharField(default='choice', max_length=12),
        ),
        migrations.AddField(
            model_name='respostatentativa', name='resposta_snapshot',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name='respostatentativa', name='resposta_correta_snapshot',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name='respostatentativa', name='parametros_snapshot',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name='respostatentativa', name='feedback_snapshot',
            field=models.TextField(blank=True, default=''),
        ),
    ]