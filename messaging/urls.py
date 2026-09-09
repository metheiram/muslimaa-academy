from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    path('', views.inbox, name='inbox'),
    path('sent/', views.sent, name='sent'),
    path('compose/', views.compose, name='compose'),
    path('compose/<int:recipient_id>/', views.compose, name='compose_to'),
    path('user/<int:user_id>/', views.view_message_by_user, name='view_message_by_user'),
    path('<int:message_id>/', views.view_message, name='view_message'),
    path('<int:message_id>/reply/', views.reply_message, name='reply'),
    path('<int:message_id>/delete/', views.delete_message, name='delete_message'),
]
