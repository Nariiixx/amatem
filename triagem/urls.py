from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="triagem_dashboard"),
    path("importar/", views.importar_planilha, name="triagem_importar"),
    path("pedido/<int:pedido_id>/atualizar/", views.atualizar_pedido, name="triagem_atualizar"),
    path("treinar-modelo/", views.treinar_modelo_local, name="triagem_treinar_modelo"),
    path("classificar-modelo/", views.classificar_modelo_local, name="triagem_classificar_modelo"),
]
