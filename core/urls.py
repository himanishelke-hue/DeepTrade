"""core URL Configuration"""
from django.contrib import admin
from django.urls import path, include
from app import views
from app import views_errors

urlpatterns = [
    # Health check — always responds 200, no auth
    path('health/', views_errors.health_check, name='health'),

    # Dashboard
    path('', views.index, name='home'),

    # Project Pages
    path('search/',   views.search,     name='search'),
    path('ticker/',   views.ticker,     name='ticker'),
    path('guide/',    views.guide,      name='guide'),
    path('quiz/',     views.quiz,       name='quiz'),
    path('ai-analyst/', views.ai_analyst, name='ai_analyst'),
    path('chatbot/',  views.chatbot,    name='chatbot'),
    path('predict/<str:ticker_value>/<int:number_of_days>/', views.predict, name='predict'),

    # Admin
    path('admin/', admin.site.urls),

    # Login System
    path('accounts/', include('allauth.urls')),
]

# Custom error handlers (Fix 7)
handler404 = 'app.views_errors.handler404'
handler500 = 'app.views_errors.handler500'
