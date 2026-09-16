"""
二手车价格评估系统 - 数据模型
注意：car_info、stat_* 表由大数据模块写入，Django只做读取
      prediction_record 由Django写入
"""
from django.db import models


class CarInfo(models.Model):
    """二手车车辆信息表（只读，由Sqoop/Spark写入）"""
    car_id = models.CharField(max_length=64, unique=True, verbose_name='车辆编号')
    brand = models.CharField(max_length=64, verbose_name='品牌')
    series = models.CharField(max_length=128, null=True, blank=True, verbose_name='车系')
    model = models.CharField(max_length=256, null=True, blank=True, verbose_name='车型')
    price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='售价(万元)')
    original_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, verbose_name='新车指导价')
    age = models.IntegerField(null=True, verbose_name='车龄(年)')
    mileage = models.DecimalField(max_digits=10, decimal_places=2, null=True, verbose_name='里程(万公里)')
    gearbox = models.CharField(max_length=32, null=True, blank=True, verbose_name='变速箱')
    displacement = models.CharField(max_length=32, null=True, blank=True, verbose_name='排量')
    fuel_type = models.CharField(max_length=32, null=True, blank=True, verbose_name='燃油类型')
    color = models.CharField(max_length=32, null=True, blank=True, verbose_name='颜色')
    city = models.CharField(max_length=64, null=True, blank=True, verbose_name='城市')
    register_date = models.DateField(null=True, verbose_name='上牌日期')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'car_info'
        verbose_name = '二手车信息'
        verbose_name_plural = verbose_name
        ordering = ['-create_time']

    def __str__(self):
        return f"{self.brand} {self.series} - {self.price}万"


class StatBrandPrice(models.Model):
    """品牌价格统计表（Spark写入，Django读取）"""
    brand = models.CharField(max_length=64, unique=True, verbose_name='品牌')
    car_count = models.IntegerField(default=0, verbose_name='车辆数量')
    avg_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, verbose_name='平均售价')
    min_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, verbose_name='最低售价')
    max_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, verbose_name='最高售价')
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'stat_brand_price'
        verbose_name = '品牌价格统计'
        verbose_name_plural = verbose_name
        ordering = ['-avg_price']

    def __str__(self):
        return f"{self.brand} - 均价{self.avg_price}万"


class StatAgePrice(models.Model):
    """车龄价格统计表（Spark写入，Django读取）"""
    age = models.IntegerField(unique=True, verbose_name='车龄(年)')
    car_count = models.IntegerField(default=0, verbose_name='车辆数量')
    avg_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, verbose_name='平均售价')
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'stat_age_price'
        verbose_name = '车龄价格统计'
        verbose_name_plural = verbose_name
        ordering = ['age']

    def __str__(self):
        return f"车龄{self.age}年 - 均价{self.avg_price}万"


class StatPriceDistribution(models.Model):
    """价格分布统计表（Spark写入，Django读取）"""
    price_range = models.CharField(max_length=64, unique=True, verbose_name='价格区间')
    car_count = models.IntegerField(default=0, verbose_name='车辆数量')
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'stat_price_distribution'
        verbose_name = '价格分布统计'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.price_range} - {self.car_count}辆"


class PredictionRecord(models.Model):
    """价格预测记录表（Django写入）"""
    MODEL_CHOICES = [
        ('sklearn', 'Scikit-learn 随机森林'),
        ('spark_mllib', 'Spark MLlib 随机森林'),
    ]

    brand = models.CharField(max_length=64, verbose_name='品牌')
    age = models.IntegerField(verbose_name='车龄(年)')
    mileage = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='里程(万公里)')
    gearbox = models.CharField(max_length=32, null=True, blank=True, verbose_name='变速箱')
    displacement = models.CharField(max_length=32, null=True, blank=True, verbose_name='排量')
    fuel_type = models.CharField(max_length=32, null=True, blank=True, verbose_name='燃油类型')
    city = models.CharField(max_length=64, null=True, blank=True, verbose_name='城市')
    original_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, verbose_name='新车指导价')
    predicted_price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='预测价格(万元)')
    model_type = models.CharField(max_length=32, choices=MODEL_CHOICES, default='sklearn', verbose_name='模型类型')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='预测时间')

    class Meta:
        db_table = 'prediction_record'
        verbose_name = '价格预测记录'
        verbose_name_plural = verbose_name
        ordering = ['-create_time']

    def __str__(self):
        return f"{self.brand} - 预测{self.predicted_price}万 ({self.create_time})"
