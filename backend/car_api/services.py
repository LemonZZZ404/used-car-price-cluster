"""
服务层 - 模型加载与预测服务
负责：加载sklearn模型、执行预测、Redis缓存
"""
import os
import json
import hashlib
import logging
import joblib
import numpy as np
import pandas as pd
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger('car_api')


class ModelService:
    """机器学习模型服务（单例模式）"""

    _instance = None
    _model = None
    _model_loaded = False
    _explainer = None
    _preprocessor = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_instance(cls):
        return cls()

    def load_model(self):
        """加载sklearn随机森林模型"""
        if self._model_loaded and self._model is not None:
            return self._model

        model_path = settings.SKLEARN_MODEL_PATH
        logger.info(f"[ModelService] 正在加载模型: {model_path}")

        if not os.path.exists(model_path):
            logger.error(f"[ModelService] 模型文件不存在: {model_path}")
            # 尝试备选路径
            alt_paths = [
                os.path.join(settings.BASE_DIR, 'ml', 'models', 'rf_price_model.joblib'),
                os.path.join(settings.BASE_DIR, '..', 'ml', 'models', 'rf_price_model.joblib'),
                '/opt/used-car/ml/models/rf_price_model.joblib',
            ]
            for alt in alt_paths:
                if os.path.exists(alt):
                    model_path = alt
                    logger.info(f"[ModelService] 使用备选路径: {alt}")
                    break
            else:
                logger.error("[ModelService] 所有路径均未找到模型文件，将使用兜底预测")
                self._model_loaded = True
                self._model = None
                return None

        try:
            self._model = joblib.load(model_path)
            self._model_loaded = True
            logger.info(f"[ModelService] 模型加载成功，类型: {type(self._model)}")
        except Exception as e:
            logger.error(f"[ModelService] 模型加载失败: {e}")
            self._model = None
            self._model_loaded = True

        return self._model

    def _generate_cache_key(self, params):
        """生成缓存key"""
        params_str = json.dumps(params, sort_keys=True, ensure_ascii=False)
        return f"predict:{hashlib.md5(params_str.encode()).hexdigest()}"

    def predict(self, params):
        """
        执行价格预测
        params: dict，包含 brand, age, mileage, gearbox, displacement, fuel_type, city, original_price
        返回: dict {predicted_price, model_type, confidence, price_range}
        """
        # 1. 检查缓存
        cache_key = self._generate_cache_key(params)
        cached = cache.get(cache_key)
        if cached:
            logger.info(f"[ModelService] 缓存命中: {cache_key}")
            return cached

        # 2. 加载模型
        model = self.load_model()

        # 3. 构建特征DataFrame（与训练时特征顺序一致）
        feature_cols = ['brand', 'gearbox', 'fuel_type', 'displacement', 'city',
                        'age', 'mileage', 'original_price']
        feature_data = {
            'brand': [params.get('brand', '大众')],
            'gearbox': [params.get('gearbox', '自动')],
            'fuel_type': [params.get('fuel_type', '汽油')],
            'displacement': [params.get('displacement', '2.0L')],
            'city': [params.get('city', '北京')],
            'age': [float(params.get('age', 3))],
            'mileage': [float(params.get('mileage', 5.0))],
            'original_price': [float(params.get('original_price', 15.0))],
        }
        X = pd.DataFrame(feature_data)[feature_cols]

        # 4. 预测
        if model is not None:
            try:
                prediction = model.predict(X)[0]
                predicted_price = round(float(prediction), 2)
                model_type = 'sklearn'
                confidence = 0.85  # 模型整体置信度，可根据R2调整
            except Exception as e:
                logger.error(f"[ModelService] 预测失败，使用兜底: {e}")
                predicted_price = self._fallback_predict(params)
                model_type = 'fallback'
                confidence = 0.5
        else:
            predicted_price = self._fallback_predict(params)
            model_type = 'fallback'
            confidence = 0.5

        # 5. 价格区间估计（±10%）
        price_range = {
            'min': round(predicted_price * 0.9, 2),
            'max': round(predicted_price * 1.1, 2),
            'unit': '万元'
        }

        # 5.1 SHAP 影响因子解释（哪些特征推高/拉低了价格）
        explain = self._explain_prediction(model, X)

        result = {
            'predicted_price': predicted_price,
            'model_type': model_type,
            'confidence': confidence,
            'price_range': price_range,
            'explain': explain,
            'input_params': params
        }

        # 6. 写入缓存（10分钟）
        try:
            cache.set(cache_key, result, timeout=600)
        except Exception as e:
            logger.warning(f"[ModelService] 缓存写入失败: {e}")

        logger.info(f"[ModelService] 预测完成: {params.get('brand')} "
                    f"车龄{params.get('age')}年 -> {predicted_price}万元 "
                    f"(模型: {model_type})")

        return result

    def _explain_prediction(self, model, X):
        """
        SHAP 特征影响因子解释
        返回: [{feature, label, impact, direction}]，按影响绝对值降序
        """
        try:
            if model is None or not hasattr(model, 'named_steps'):
                return None
            if self._explainer is None:
                import shap
                regressor = model.named_steps.get('regressor')
                preprocessor = model.named_steps.get('preprocessor')
                if regressor is None or preprocessor is None:
                    return None
                # 基于树的解释器，不需要背景数据（tree_path_dependent）
                self._explainer = shap.TreeExplainer(
                    regressor,
                    feature_perturbation='tree_path_dependent'
                )
                self._preprocessor = preprocessor
            if self._explainer is None:
                return None

            Xt = self._preprocessor.transform(X)
            shap_values = self._explainer.shap_values(Xt)[0]

            # 特征名：数值3列 + 类别one-hot列
            num_names = ['age', 'mileage', 'original_price']
            cat_encoder = self._preprocessor.named_transformers_['cat'].named_steps['onehot']
            cat_names = list(cat_encoder.get_feature_names_out(
                ['brand', 'gearbox', 'fuel_type', 'displacement', 'city']
            ))
            names = num_names + cat_names

            # 归并到原始字段（one-hot 的多个列合并到所属字段）
            label_map = {
                'age': '车龄', 'mileage': '行驶里程', 'original_price': '新车价格',
                'brand': '品牌', 'gearbox': '变速箱', 'fuel_type': '燃油类型',
                'displacement': '排量', 'city': '城市'
            }
            raw_fields = list(label_map.keys())
            impacts = {f: 0.0 for f in raw_fields}
            for name, v in zip(names, shap_values):
                if name in impacts:
                    impacts[name] = float(v)
                else:
                    prefix = name.split('_')[0]
                    if prefix in impacts:
                        impacts[prefix] += float(v)

            # 过滤影响过小的特征，按绝对值降序
            explain = []
            for f in raw_fields:
                v = impacts[f]
                if abs(v) >= 0.05:
                    explain.append({
                        'feature': f,
                        'label': label_map[f],
                        'impact': round(v, 2),
                        'direction': 'up' if v > 0 else 'down'
                    })
            explain.sort(key=lambda x: abs(x['impact']), reverse=True)
            return explain
        except Exception as e:
            logger.warning(f"[ModelService] SHAP 解释失败: {e}")
            return None

    def _fallback_predict(self, params):
        """
        兜底预测：当模型不可用时，基于折旧规则估算
        公式：价格 = 新车指导价 × 折旧率 × 里程因子 × 随机波动
        """
        original_price = float(params.get('original_price', 15.0))
        age = float(params.get('age', 3))
        mileage = float(params.get('mileage', 5.0))

        # 车龄折旧率
        if age <= 1:
            depreciation = 0.82
        elif age <= 3:
            depreciation = 0.65
        elif age <= 5:
            depreciation = 0.50
        elif age <= 8:
            depreciation = 0.38
        elif age <= 12:
            depreciation = 0.26
        else:
            depreciation = 0.15

        # 里程因子
        mileage_factor = max(0.6, 1.0 - mileage * 0.015)

        # 品牌溢价系数（简化）
        brand = params.get('brand', '')
        premium_brands = ['宝马', '奔驰', '奥迪', '雷克萨斯', '保时捷', '特斯拉', '蔚来', '理想']
        brand_factor = 1.05 if brand in premium_brands else 1.0

        predicted = original_price * depreciation * mileage_factor * brand_factor
        return round(max(predicted, 0.5), 2)

    def get_model_info(self):
        """获取模型信息"""
        model = self.load_model()
        info = {
            'model_loaded': model is not None,
            'model_type': 'sklearn_random_forest' if model else 'fallback',
            'model_path': settings.SKLEARN_MODEL_PATH,
        }
        if model is not None and hasattr(model, 'named_steps'):
            regressor = model.named_steps.get('regressor')
            if regressor:
                info['n_estimators'] = regressor.n_estimators
                info['max_depth'] = regressor.max_depth
        return info


# 全局单例
model_service = ModelService.get_instance()
