# App `triagem` — instalação

## 1. Copiar a pasta
Copie a pasta `triagem/` inteira para a raiz do seu projeto Django (mesmo nível de `manage.py`).

## 2. Instalar dependências
```bash
pip install openpyxl scikit-learn joblib --break-system-packages
```
(ou dentro da sua venv, sem a flag)

Nenhuma dessas bibliotecas exige chave de API nem cobra por uso — tudo roda
localmente, no seu próprio servidor.

## 3. settings.py
```python
INSTALLED_APPS = [
    ...
    'triagem',
]
```

## 4. urls.py do projeto
```python
from django.urls import path, include

urlpatterns = [
    ...
    path('triagem/', include('triagem.urls')),
]
```

## 5. Migrations
```bash
python manage.py makemigrations triagem
python manage.py migrate
```

## 6. Cadastrar a equipe de suporte
Pelo admin (`/admin/`) ou shell, crie os 3 membros de `SuporteMembro`.
Um deles precisa ter "Nívea" (ou "Nivea") no nome — é usado automaticamente
para sugerir a atribuição quando `obs2 == infraecommerce`.

```python
python manage.py shell
>>> from triagem.models import SuporteMembro
>>> SuporteMembro.objects.create(nome="Suporte 1")
>>> SuporteMembro.objects.create(nome="Suporte 2")
>>> SuporteMembro.objects.create(nome="Nívea")
```

## 7. Acessar
`http://localhost:8000/triagem/`

## Observações sobre a lógica

- **Merge por importação**: a chave é a coluna `posicao`. Se ela não existir na
  linha, cai no fallback `codcli + data_pedido + hora_pedido`. Ao importar um
  novo arquivo: quem já existe é atualizado, quem é novo entra, quem sumiu do
  arquivo novo é **excluído**.
- **Categoria manual**: se você mudar a categoria de um pedido pelo card, ela
  fica marcada como `categoria_manual=True` e passa a ser preservada nas
  próximas importações (não é sobrescrita pela regra automática).
- **Regra `codcob=DEP`**: por padrão usa uma heurística simples baseada em
  palavras-chave em `obs`/`obs2` (procura "prazo" ou "recompo"). Isso já
  funciona sozinho, sem custo nenhum.

## Classificador local gratuito (opcional)

Se a heurística não for precisa o suficiente, dá pra treinar um modelinho
próprio, 100% local (scikit-learn), sem depender de nenhuma API paga:

1. Use o sistema normalmente. Quando a heurística classificar um pedido DEP
   errado, corrija a categoria pelo próprio card (isso marca
   `categoria_manual=True` e vira um exemplo de treino).
2. Depois de corrigir alguns pedidos (pelo menos 5 por categoria, em 2+
   categorias), clique em **"Treinar modelo"** no dashboard — ou rode:
   ```bash
   python manage.py treinar_triagem
   ```
3. Clique em **"Classificar DEP pendentes"** pra aplicar o modelo treinado
   nos pedidos DEP que ainda não foram classificados manualmente.

O modelo é salvo em `triagem/modelo_triagem.joblib`. Quanto mais correções
manuais você fizer ao longo do tempo, melhor ele fica — é só re-treinar de
vez em quando (`python manage.py treinar_triagem`).
- **Atraso**: qualquer pedido com `data_pedido` há mais de 2 dias corridos
  ganha o selo vermelho no card e entra na contagem do sino no topo.
