"""
car_api 应用路由配置
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CarInfoViewSet, StatBrandPriceViewSet, StatAgePriceViewSet,
    StatPriceDistributionViewSet, PredictionViewSet,
    dashboard_summary, model_analysis, train_start, train_status, health_check
)

router = DefaultRouter()
router.register(r'cars', CarInfoViewSet, basename='car')
router.register(r'stat/brand-price', StatBrandPriceViewSet, basename='stat-brand')
router.register(r'stat/age-price', StatAgePriceViewSet, basename='stat-age')
router.register(r'stat/price-distribution', StatPriceDistributionViewSet, basename='stat-dist')
router.register(r'prediction', PredictionViewSet, basename='prediction')

urlpatterns = [
    # 路由注册
    path('', include(router.urls)),

    # 看板概览
    path('dashboard/summary/', dashboard_summary, name='dashboard-summary'),

    # 模型分析（特征重要性 + 指标对比）
    path('model/analysis/', model_analysis, name='model-analysis'),

    # 模型训练（Celery 异步）
    path('train/start/', train_start, name='train-start'),
    path('train/status/', train_status, name='train-status'),

    # 健康检查
    path('health/', health_check, name='health-check'),
]
