"""
序列化器 - 用于API数据序列化/反序列化
"""
from rest_framework import serializers
from .models import (
    CarInfo, StatBrandPrice, StatAgePrice,
    StatPriceDistribution, PredictionRecord
)


class CarInfoSerializer(serializers.ModelSerializer):
    """二手车信息序列化器"""
    class Meta:
        model = CarInfo
        fields = '__all__'
        read_only_fields = ['id', 'create_time']


class CarInfoListSerializer(serializers.ModelSerializer):
    """二手车列表序列化器（精简字段）"""
    class Meta:
        model = CarInfo
        fields = ['id', 'car_id', 'brand', 'series', 'model', 'price',
                  'age', 'mileage', 'gearbox', 'fuel_type', 'city']


class StatBrandPriceSerializer(serializers.ModelSerializer):
    """品牌价格统计序列化器"""
    class Meta:
        model = StatBrandPrice
        fields = '__all__'


class StatAgePriceSerializer(serializers.ModelSerializer):
    """车龄价格统计序列化器"""
    class Meta:
        model = StatAgePrice
        fields = '__all__'


class StatPriceDistributionSerializer(serializers.ModelSerializer):
    """价格分布序列化器"""
    class Meta:
        model = StatPriceDistribution
        fields = '__all__'


class PredictionRequestSerializer(serializers.Serializer):
    """价格预测请求序列化器"""
    brand = serializers.CharField(max_length=64, required=True, help_text='品牌，如：大众、宝马、丰田')
    age = serializers.IntegerField(min_value=0, max_value=30, required=True, help_text='车龄（年）')
    mileage = serializers.FloatField(min_value=0, max_value=50, required=True, help_text='里程（万公里）')
    gearbox = serializers.ChoiceField(choices=['手动', '自动'], required=False, default='自动', help_text='变速箱')
    displacement = serializers.CharField(max_length=32, required=False, default='2.0L', help_text='排量，如：1.5T、2.0L')
    fuel_type = serializers.ChoiceField(
        choices=['汽油', '柴油', '纯电动', '混合动力', '插电混动'],
        required=False, default='汽油', help_text='燃油类型'
    )
    city = serializers.CharField(max_length=64, required=False, default='北京', help_text='所在城市')
    original_price = serializers.FloatField(min_value=0, max_value=500, required=False, default=15.0,
                                              help_text='新车指导价（万元）')
    model_type = serializers.ChoiceField(choices=['sklearn', 'spark_mllib'], required=False, default='sklearn',
                                           help_text='预测模型类型')

    def validate_age(self, value):
        if value < 0 or value > 30:
            raise serializers.ValidationError("车龄必须在0-30年之间")
        return value

    def validate_mileage(self, value):
        if value < 0 or value > 50:
            raise serializers.ValidationError("里程必须在0-50万公里之间")
        return value


class PredictionResponseSerializer(serializers.Serializer):
    """价格预测响应序列化器"""
    predicted_price = serializers.FloatField(help_text='预测价格（万元）')
    model_type = serializers.CharField(help_text='使用的模型')
    input_params = serializers.DictField(help_text='输入参数')
    confidence = serializers.FloatField(required=False, help_text='置信度（0-1）')
    price_range = serializers.DictField(required=False, help_text='价格区间估计')


class PredictionRecordSerializer(serializers.ModelSerializer):
    """预测记录序列化器"""
    class Meta:
        model = PredictionRecord
        fields = '__all__'
        read_only_fields = ['id', 'predicted_price', 'model_type', 'create_time']


class DashboardSummarySerializer(serializers.Serializer):
    """数据看板概览序列化器"""
    total_cars = serializers.IntegerField(help_text='车辆总数')
    total_brands = serializers.IntegerField(help_text='品牌数量')
    avg_price = serializers.FloatField(help_text='平均售价（万元）')
    total_predictions = serializers.IntegerField(help_text='预测次数')
    latest_predictions = serializers.ListField(help_text='最近预测记录')
