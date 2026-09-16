from django.contrib import admin
from .models import CarInfo, PredictionRecord, StatBrandPrice, StatAgePrice, StatPriceDistribution


@admin.register(CarInfo)
class CarInfoAdmin(admin.ModelAdmin):
    list_display = ['car_id', 'brand', 'series', 'price', 'age', 'mileage', 'city', 'create_time']
    list_filter = ['brand', 'gearbox', 'fuel_type', 'city']
    search_fields = ['car_id', 'brand', 'series', 'model']
    ordering = ['-create_time']


@admin.register(PredictionRecord)
class PredictionRecordAdmin(admin.ModelAdmin):
    list_display = ['id', 'brand', 'age', 'mileage', 'predicted_price', 'model_type', 'create_time']
    list_filter = ['brand', 'model_type']
    search_fields = ['brand']
    ordering = ['-create_time']


@admin.register(StatBrandPrice)
class StatBrandPriceAdmin(admin.ModelAdmin):
    list_display = ['brand', 'car_count', 'avg_price', 'min_price', 'max_price']
    ordering = ['-avg_price']


@admin.register(StatAgePrice)
class StatAgePriceAdmin(admin.ModelAdmin):
    list_display = ['age', 'car_count', 'avg_price']
    ordering = ['age']


@admin.register(StatPriceDistribution)
class StatPriceDistributionAdmin(admin.ModelAdmin):
    list_display = ['price_range', 'car_count']
