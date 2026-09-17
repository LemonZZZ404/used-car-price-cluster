"""
视图层 - API接口
包含：车辆信息CRUD、统计数据接口、价格预测接口、看板概览接口、模型分析接口
"""
import json
import logging
import os
from django.conf import settings
from django.core.cache import cache
from django.db.models import Count, Avg, Q
from django.utils import timezone
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend

from .models import (
    CarInfo, StatBrandPrice, StatAgePrice,
    StatPriceDistribution, PredictionRecord
)
from .serializers import (
    CarInfoSerializer, CarInfoListSerializer,
    StatBrandPriceSerializer, StatAgePriceSerializer,
    StatPriceDistributionSerializer,
    PredictionRequestSerializer, PredictionResponseSerializer,
    PredictionRecordSerializer, DashboardSummarySerializer
)
from .services import model_service

logger = logging.getLogger('car_api')


class CarInfoViewSet(viewsets.ReadOnlyModelViewSet):
    """二手车信息接口（只读）"""
    queryset = CarInfo.objects.all()
    serializer_class = CarInfoSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['brand', 'gearbox', 'fuel_type', 'city', 'age']
    search_fields = ['brand', 'series', 'model', 'car_id']
    ordering_fields = ['price', 'age', 'mileage', 'create_time']
    ordering = ['-create_time']

    def get_serializer_class(self):
        if self.action == 'list':
            return CarInfoListSerializer
        return CarInfoSerializer

    @action(detail=False, methods=['get'])
    def brands(self, request):
        """获取所有品牌列表"""
        brands = CarInfo.objects.values_list('brand', flat=True).distinct().order_by('brand')
        return Response({'brands': list(brands), 'count': len(brands)})

    @action(detail=False, methods=['get'])
    def cities(self, request):
        """获取所有城市列表"""
        cities = CarInfo.objects.values_list('city', flat=True).distinct().order_by('city')
        return Response({'cities': list(cities), 'count': len(cities)})

    @action(detail=False, methods=['get'])
    def search(self, request):
        """高级搜索：品牌+价格区间+车龄区间"""
        brand = request.query_params.get('brand', '')
        min_price = request.query_params.get('min_price')
        max_price = request.query_params.get('max_price')
        min_age = request.query_params.get('min_age')
        max_age = request.query_params.get('max_age')

        qs = CarInfo.objects.all()
        if brand:
            qs = qs.filter(brand__icontains=brand)
        if min_price:
            qs = qs.filter(price__gte=float(min_price))
        if max_price:
            qs = qs.filter(price__lte=float(max_price))
        if min_age:
            qs = qs.filter(age__gte=int(min_age))
        if max_age:
            qs = qs.filter(age__lte=int(max_age))

        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = CarInfoListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = CarInfoListSerializer(qs, many=True)
        return Response(serializer.data)


class StatBrandPriceViewSet(viewsets.ReadOnlyModelViewSet):
    """品牌价格统计接口"""
    queryset = StatBrandPrice.objects.all()
    serializer_class = StatBrandPriceSerializer
    permission_classes = [AllowAny]
    ordering = ['-avg_price']

    @action(detail=False, methods=['get'])
    def top10(self, request):
        """获取均价Top10品牌（ECharts柱状图用）"""
        top10 = StatBrandPrice.objects.all().order_by('-avg_price')[:10]
        serializer = self.get_serializer(top10, many=True)
        # 转换为ECharts格式
        data = serializer.data
        echarts_data = {
            'xAxis': [item['brand'] for item in data],
            'series': [
                {'name': '平均售价', 'type': 'bar', 'data': [float(item['avg_price']) for item in data]},
                {'name': '车辆数量', 'type': 'line', 'yAxisIndex': 1, 'data': [item['car_count'] for item in data]}
            ]
        }
        return Response(echarts_data)


class StatAgePriceViewSet(viewsets.ReadOnlyModelViewSet):
    """车龄价格统计接口"""
    queryset = StatAgePrice.objects.all()
    serializer_class = StatAgePriceSerializer
    permission_classes = [AllowAny]
    ordering = ['age']

    @action(detail=False, methods=['get'])
    def chart(self, request):
        """车龄-价格散点/折线图数据（ECharts用）"""
        data = StatAgePrice.objects.all().order_by('age')
        serializer = self.get_serializer(data, many=True)
        items = serializer.data
        echarts_data = {
            'xAxis': [f"{item['age']}年" for item in items],
            'series': [
                {'name': '平均售价', 'type': 'line', 'smooth': True,
                 'data': [float(item['avg_price']) for item in items],
                 'areaStyle': {}},
                {'name': '车辆数量', 'type': 'bar', 'yAxisIndex': 1,
                 'data': [item['car_count'] for item in items]}
            ]
        }
        return Response(echarts_data)


class StatPriceDistributionViewSet(viewsets.ReadOnlyModelViewSet):
    """价格分布统计接口"""
    queryset = StatPriceDistribution.objects.all()
    serializer_class = StatPriceDistributionSerializer
    permission_classes = [AllowAny]

    @action(detail=False, methods=['get'])
    def chart(self, request):
        """价格分布饼图/直方图数据（ECharts用）"""
        # 按区间排序
        order = {'0-5万': 1, '5-10万': 2, '10-15万': 3, '15-20万': 4,
                 '20-30万': 5, '30-50万': 6, '50-100万': 7, '100万以上': 8}
        data = list(StatPriceDistribution.objects.all())
        data.sort(key=lambda x: order.get(x.price_range, 99))
        serializer = self.get_serializer(data, many=True)
        items = serializer.data

        total = sum(item['car_count'] for item in items)
        pie_data = [{'name': item['price_range'], 'value': item['car_count']} for item in items]

        echarts_data = {
            'xAxis': [item['price_range'] for item in items],
            'bar_series': [{'name': '车辆数量', 'type': 'bar',
                            'data': [item['car_count'] for item in items]}],
            'pie_data': pie_data,
            'total': total
        }
        return Response(echarts_data)


class PredictionViewSet(viewsets.ViewSet):
    """价格预测接口"""
    permission_classes = [AllowAny]

    @action(detail=False, methods=['post'], url_path='predict')
    def predict(self, request):
        """
        二手车价格预测接口
        接收车辆参数，返回预测价格
        """
        serializer = PredictionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        params = serializer.validated_data

        logger.info(f"[预测] 收到预测请求: {params}")

        try:
            # 调用模型服务预测
            result = model_service.predict(params)

            # 保存预测记录
            try:
                PredictionRecord.objects.create(
                    brand=params['brand'],
                    age=params['age'],
                    mileage=params['mileage'],
                    gearbox=params.get('gearbox'),
                    displacement=params.get('displacement'),
                    fuel_type=params.get('fuel_type'),
                    city=params.get('city'),
                    original_price=params.get('original_price'),
                    predicted_price=result['predicted_price'],
                    model_type=result['model_type']
                )
            except Exception as e:
                logger.warning(f"[预测] 保存预测记录失败: {e}")

            return Response({
                'code': 200,
                'message': '预测成功',
                'data': result
            })

        except Exception as e:
            logger.error(f"[预测] 预测失败: {e}", exc_info=True)
            return Response({
                'code': 500,
                'message': f'预测失败: {str(e)}',
                'data': None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='history')
    def history(self, request):
        """获取预测历史记录"""
        limit = int(request.query_params.get('limit', 20))
        records = PredictionRecord.objects.all()[:limit]
        serializer = PredictionRecordSerializer(records, many=True)
        return Response({
            'code': 200,
            'message': 'success',
            'data': serializer.data,
            'total': PredictionRecord.objects.count()
        })

    @action(detail=False, methods=['get'], url_path='model-info')
    def model_info(self, request):
        """获取模型信息"""
        info = model_service.get_model_info()
        return Response({'code': 200, 'message': 'success', 'data': info})


@api_view(['GET'])
@permission_classes([AllowAny])
def dashboard_summary(request):
    """
    数据看板概览接口
    返回：车辆总数、品牌数、平均价格、预测次数、最近预测
    使用 Redis 缓存 60 秒，避免百万级数据频繁聚合查询
    """
    cache_key = 'dashboard_summary_v1'
    cached = cache.get(cache_key)
    if cached is not None:
        return Response({'code': 200, 'message': 'success (cached)', 'data': cached})

    try:
        total_cars = CarInfo.objects.count()
        total_brands = CarInfo.objects.values('brand').distinct().count()
        avg_price = CarInfo.objects.aggregate(avg=Avg('price'))['avg']
        total_predictions = PredictionRecord.objects.count()

        # 最近5条预测
        latest = PredictionRecord.objects.all()[:5]
        latest_data = PredictionRecordSerializer(latest, many=True).data

        # 价格区间统计（如果统计有数据）
        price_dist = StatPriceDistribution.objects.all()
        dist_data = StatPriceDistributionSerializer(price_dist, many=True).data

        data = {
            'total_cars': total_cars,
            'total_brands': total_brands,
            'avg_price': round(float(avg_price), 2) if avg_price else 0,
            'total_predictions': total_predictions,
            'latest_predictions': latest_data,
            'price_distribution': dist_data
        }
        cache.set(cache_key, data, 60)
        return Response({'code': 200, 'message': 'success', 'data': data})
    except Exception as e:
        logger.error(f"[看板] 获取概览失败: {e}", exc_info=True)
        return Response({
            'code': 500,
            'message': f'获取数据失败: {str(e)}',
            'data': None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def model_analysis(request):
    """
    模型分析接口
    返回：Scikit-learn / Spark MLlib 训练指标对比 + 特征重要性
    数据来源：ml/models/ 下的 JSON 指标文件
    """
    try:
        model_dir = settings.MODEL_DIR

        def _read_json(name):
            path = os.path.join(model_dir, name)
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return None

        sklearn_metrics = _read_json('sklearn_metrics.json')
        spark_metrics = _read_json('spark_mllib_metrics.json')
        feature_importance = _read_json('feature_importance.json')

        if not sklearn_metrics:
            return Response({
                'code': 404,
                'message': '模型指标文件不存在，请先训练模型',
                'data': None
            }, status=status.HTTP_404_NOT_FOUND)

        # 特征重要性只取前12个用于图表展示
        if feature_importance:
            feature_importance = feature_importance[:12]

        data = {
            'sklearn_metrics': sklearn_metrics,
            'spark_metrics': spark_metrics,
            'feature_importance': feature_importance,
            'model_info': model_service.get_model_info(),
        }
        return Response({'code': 200, 'message': 'success', 'data': data})
    except Exception as e:
        logger.error(f"[模型分析] 获取数据失败: {e}", exc_info=True)
        return Response({
            'code': 500,
            'message': f'获取模型分析数据失败: {str(e)}',
            'data': None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def train_start(request):
    """
    触发异步模型重训（Celery 任务）
    返回：任务是否已提交
    """
    from .tasks import run_training_task
    status_file = os.path.join(settings.BASE_DIR.parent, 'ml', 'models', 'train_status.json')
    # 检查是否已有任务在跑
    if os.path.exists(status_file):
        try:
            with open(status_file, 'r', encoding='utf-8') as f:
                st = json.load(f)
            if st.get('status') == 'running':
                return Response({
                    'code': 400,
                    'message': '已有训练任务正在执行中，请稍候',
                    'data': st
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            pass

    try:
        result = run_training_task.delay()
        return Response({
            'code': 200,
            'message': '训练任务已提交，正在后台异步执行',
            'data': {'task_id': result.id, 'status': 'submitted'}
        })
    except Exception as e:
        logger.error(f"[训练] 提交任务失败: {e}", exc_info=True)
        return Response({
            'code': 500,
            'message': f'提交训练任务失败: {str(e)}（请确认 Celery Worker 已启动）',
            'data': None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def train_status(request):
    """
    查询训练任务状态
    返回：status( idle/running/success/error )、progress(0-100)、metrics
    """
    status_file = os.path.join(settings.BASE_DIR.parent, 'ml', 'models', 'train_status.json')
    if not os.path.exists(status_file):
        return Response({
            'code': 200,
            'message': 'success',
            'data': {
                'status': 'idle',
                'progress': 0,
                'message': '暂无训练记录，可点击"开始训练"触发模型重训',
                'metrics': {},
                'updated_at': None
            }
        })
    try:
        with open(status_file, 'r', encoding='utf-8') as f:
            st = json.load(f)
        return Response({'code': 200, 'message': 'success', 'data': st})
    except Exception as e:
        return Response({
            'code': 500,
            'message': f'读取训练状态失败: {str(e)}',
            'data': None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def stat_aggregate(request):
    """
    实时聚合接口（看板筛选联动）
    参数：brand / city / min_price / max_price（均可选）
    返回：筛选后的总量/均价 + 车龄-价格序列 + 价格分布（ECharts 格式）
    无筛选时走 Spark 预聚合表（stat_*），有筛选时实时聚合 car_info
    """
    brand = request.query_params.get('brand', '').strip()
    city = request.query_params.get('city', '').strip()
    min_price = request.query_params.get('min_price')
    max_price = request.query_params.get('max_price')

    has_filter = bool(brand or city or min_price or max_price)
    cache_key = f'stat_agg_{brand}_{city}_{min_price}_{max_price}'
    cached = cache.get(cache_key)
    if cached is not None:
        return Response({'code': 200, 'message': 'success (cached)', 'data': cached})

    try:
        if not has_filter:
            # 无筛选：直接使用 Spark 预聚合结果，零负担
            age_rows = StatAgePrice.objects.all().order_by('age')
            dist_rows = list(StatPriceDistribution.objects.all())
            order = {'0-5万': 1, '5-10万': 2, '10-15万': 3, '15-20万': 4,
                     '20-30万': 5, '30-50万': 6, '50-100万': 7, '100万以上': 8}
            dist_rows.sort(key=lambda x: order.get(x.price_range, 99))
            data = {
                'total_cars': CarInfo.objects.count(),
                'avg_price': round(float(CarInfo.objects.aggregate(a=Avg('price'))['a'] or 0), 2),
                'age_chart': {
                    'xAxis': [f"{r.age}年" for r in age_rows],
                    'series': [
                        {'name': '平均售价', 'type': 'line', 'smooth': True,
                         'data': [float(r.avg_price) for r in age_rows], 'areaStyle': {}},
                        {'name': '车辆数量', 'type': 'bar', 'yAxisIndex': 1,
                         'data': [r.car_count for r in age_rows]}
                    ]
                },
                'price_dist': {
                    'pie_data': [{'name': r.price_range, 'value': r.car_count} for r in dist_rows],
                    'total': sum(r.car_count for r in dist_rows)
                },
                'filters': {'brand': brand, 'city': city, 'min_price': min_price, 'max_price': max_price}
            }
        else:
            # 有筛选：实时聚合（brand/city 有索引，百万级秒回）
            q = Q()
            if brand:
                q &= Q(brand=brand)
            if city:
                q &= Q(city=city)
            if min_price:
                q &= Q(price__gte=float(min_price))
            if max_price:
                q &= Q(price__lte=float(max_price))
            qs = CarInfo.objects.filter(q)
            total = qs.count()
            avg = qs.aggregate(a=Avg('price'))['a']

            age_rows = qs.values('age').annotate(c=Count('id'), ap=Avg('price')).order_by('age')
            age_x, age_price, age_count = [], [], []
            for r in age_rows:
                if r['age'] is None:
                    continue
                age_x.append(f"{r['age']}年")
                age_price.append(round(float(r['ap']), 2))
                age_count.append(r['c'])

            ranges = [('0-5万', 0, 5), ('5-10万', 5, 10), ('10-15万', 10, 15),
                      ('15-20万', 15, 20), ('20-30万', 20, 30), ('30-50万', 30, 50),
                      ('50-100万', 50, 100), ('100万以上', 100, None)]
            dist = []
            for name, lo, hi in ranges:
                rq = Q(price__gte=lo)
                if hi:
                    rq &= Q(price__lt=hi)
                else:
                    rq &= Q(price__gte=100)
                dist.append({'name': name, 'value': qs.filter(rq).count()})

            data = {
                'total_cars': total,
                'avg_price': round(float(avg), 2) if avg else 0,
                'age_chart': {
                    'xAxis': age_x,
                    'series': [
                        {'name': '平均售价', 'type': 'line', 'smooth': True,
                         'data': age_price, 'areaStyle': {}},
                        {'name': '车辆数量', 'type': 'bar', 'yAxisIndex': 1, 'data': age_count}
                    ]
                },
                'price_dist': {'pie_data': dist, 'total': total},
                'filters': {'brand': brand, 'city': city, 'min_price': min_price, 'max_price': max_price}
            }
        cache.set(cache_key, data, 60)
        return Response({'code': 200, 'message': 'success', 'data': data})
    except Exception as e:
        logger.error(f"[统计] 聚合接口异常: {e}", exc_info=True)
        return Response({'code': 500, 'message': f'聚合失败: {str(e)}', 'data': None},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def market_compare(request):
    """
    市场行情对比接口（预测页用）
    参数：brand / age
    返回：全局均价、同品牌均价、同车龄均价（用于预测价对比）
    """
    brand = request.query_params.get('brand', '').strip()
    try:
        age = int(request.query_params.get('age', 0))
    except (TypeError, ValueError):
        age = 0

    cache_key = f'market_cmp_{brand}_{age}'
    cached = cache.get(cache_key)
    if cached is not None:
        return Response({'code': 200, 'message': 'success (cached)', 'data': cached})

    try:
        all_avg = CarInfo.objects.aggregate(a=Avg('price'))['a']
        brand_avg = None
        age_avg = None
        if brand:
            ba = CarInfo.objects.filter(brand=brand).aggregate(a=Avg('price'))['a']
            brand_avg = round(float(ba), 2) if ba else None
        if age is not None:
            aa = CarInfo.objects.filter(age=age).aggregate(a=Avg('price'))['a']
            age_avg = round(float(aa), 2) if aa else None
        data = {
            'all_avg': round(float(all_avg), 2) if all_avg else 0,
            'brand_avg': brand_avg,
            'age_avg': age_avg,
        }
        cache.set(cache_key, data, 120)
        return Response({'code': 200, 'message': 'success', 'data': data})
    except Exception as e:
        logger.error(f"[统计] 市场对比接口异常: {e}", exc_info=True)
        return Response({'code': 500, 'message': f'对比失败: {str(e)}', 'data': None},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """健康检查接口"""
    return Response({
        'status': 'ok',
        'service': '二手车价格评估系统API',
        'version': 'v1.0.0',
        'time': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
    })
