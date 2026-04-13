from django.urls import path
from . import views

app_name = 'evm'

urlpatterns = [
    path('', views.index, name='index'),
    path('cast-vote/<str:booth_id>/', views.cast_vote, name='cast_vote'),
    path('close-voting/<str:booth_id>/', views.close_voting, name='close_voting'),
    path('publish-result/<str:booth_id>/', views.publish_result, name='publish_result'),
    path('verify-chain/<str:booth_id>/', views.verify_chain_view, name='verify_chain'),
    path('status/<str:booth_id>/', views.booth_status, name='status'),
    path('signals/<str:booth_id>/', views.booth_signals, name='signals'),
    path('results/<str:booth_id>/', views.booth_results, name='results'),
    path('ledger/', views.ledger_view, name='ledger'),
    path('ledger/blocks/<str:booth_id>/', views.ledger_blocks, name='ledger_blocks'),
]

