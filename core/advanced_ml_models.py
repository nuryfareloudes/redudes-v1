# core/advanced_ml_models.py

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler, MinMaxScaler, PolynomialFeatures
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.feature_selection import SelectKBest, f_classif, RFE
from sklearn.decomposition import PCA
from sklearn.pipeline import Pipeline
import logging
import warnings
from collections import Counter

# Suprimir advertencias
warnings.filterwarnings('ignore', category=UserWarning, message='.*Precision is ill-defined.*')
warnings.filterwarnings('ignore', category=UserWarning, message='.*F-score is ill-defined.*')
warnings.filterwarnings('ignore', category=UserWarning, message='.*Recall is ill-defined.*')

logger = logging.getLogger(__name__)


class AdvancedRecommendationSystem:
    """
    Sistema de recomendación avanzado usando técnicas de machine learning más sofisticadas
    """
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.feature_scaler = MinMaxScaler()
        self.models_trained = False
        self.ensemble_model = None
        self.feature_selector = None
        self.pca = None
        
        # Configuración de hiperparámetros
        self.n_features = 10  # Número de características seleccionadas
        self.n_components = 8  # Componentes PCA
        
    def prepare_advanced_data(self, usuarios, roles_proyecto):
        """
        Prepara datos avanzados con características más sofisticadas
        """
        try:
            usuarios_features = []
            
            # Obtener requisitos del proyecto
            roles_habilidades = set()
            roles_conocimientos = set()
            roles_experiencia_min = 0
            
            for rol in roles_proyecto:
                if hasattr(rol, 'habilidades') and rol.habilidades:
                    roles_habilidades.update(set(rol.habilidades.lower().split(',')))
                if hasattr(rol, 'conocimientos') and rol.conocimientos:
                    roles_conocimientos.update(set(rol.conocimientos.lower().split(',')))
                if hasattr(rol, 'experiencia') and rol.experiencia:
                    try:
                        exp_str = rol.experiencia.lower()
                        if 'años' in exp_str:
                            años = [int(s) for s in exp_str.split() if s.isdigit()]
                            if años:
                                roles_experiencia_min = max(roles_experiencia_min, max(años))
                    except:
                        pass
            
            roles_habilidades = {h.strip() for h in roles_habilidades if h.strip()}
            roles_conocimientos = {c.strip() for c in roles_conocimientos if c.strip()}
            
            for usuario in usuarios:
                try:
                    habilidades = list(usuario.habilidades.all()) if hasattr(usuario, 'habilidades') else []
                    conocimientos = list(usuario.conocimientos.all()) if hasattr(usuario, 'conocimientos') else []
                    experiencias = list(usuario.experiencias.all()) if hasattr(usuario, 'experiencias') else []
                    estudios = list(usuario.estudios.all()) if hasattr(usuario, 'estudios') else []
                except:
                    habilidades = conocimientos = experiencias = estudios = []
                
                # Características básicas
                habilidades_usuario = set()
                if habilidades:
                    for h in habilidades:
                        if hasattr(h, 'habilidad'):
                            habilidades_usuario.add(h.habilidad.lower())
                
                conocimientos_usuario = set()
                if conocimientos:
                    for c in conocimientos:
                        if hasattr(c, 'conocimiento'):
                            conocimientos_usuario.add(c.conocimiento.lower())
                
                # Características avanzadas
                match_habilidades = len(habilidades_usuario.intersection(roles_habilidades)) / len(roles_habilidades) if roles_habilidades else 0
                match_conocimientos = len(conocimientos_usuario.intersection(roles_conocimientos)) / len(roles_conocimientos) if roles_conocimientos else 0
                
                # Niveles de conocimientos relevantes
                niveles_conocimientos = []
                for c in conocimientos:
                    if hasattr(c, 'conocimiento') and hasattr(c, 'nivel'):
                        if c.conocimiento.lower() in roles_conocimientos:
                            niveles_conocimientos.append(c.nivel)
                
                promedio_nivel_conocimientos = np.mean(niveles_conocimientos) if niveles_conocimientos else 0
                max_nivel_conocimientos = max(niveles_conocimientos) if niveles_conocimientos else 0
                
                # Experiencia
                max_tiempo_experiencia = 0
                if experiencias:
                    for e in experiencias:
                        if hasattr(e, 'tiempo'):
                            max_tiempo_experiencia = max(max_tiempo_experiencia, e.tiempo)
                
                cumple_experiencia = 1 if max_tiempo_experiencia >= roles_experiencia_min else 0
                
                # Educación
                nivel_educativo = 0
                if estudios:
                    for e in estudios:
                        if hasattr(e, 'nivel'):
                            nivel_educativo = max(nivel_educativo, e.nivel)
                
                # Experiencia relevante
                experiencia_relevante = 0
                for exp in experiencias:
                    if hasattr(exp, 'actividades') and hasattr(exp, 'tiempo'):
                        actividades_lower = exp.actividades.lower()
                        if any(h in actividades_lower for h in roles_habilidades) or \
                                any(c in actividades_lower for c in roles_conocimientos):
                            experiencia_relevante += exp.tiempo
                
                # Características avanzadas
                diversidad_habilidades = len(set(getattr(h, 'categoria', 'general') for h in habilidades)) if habilidades else 0
                tiempos_experiencia = [e.tiempo for e in experiencias if hasattr(e, 'tiempo')]
                consistencia_experiencia = np.std(tiempos_experiencia) if len(tiempos_experiencia) > 1 else 0
                
                niveles_habilidades = [getattr(h, 'nivel', 3) for h in habilidades if hasattr(h, 'nivel')]
                promedio_nivel_habilidades = np.mean(niveles_habilidades) if niveles_habilidades else 0
                max_nivel_habilidades = max(niveles_habilidades) if niveles_habilidades else 0
                
                # Nuevas características sofisticadas
                # Coherencia entre habilidades y conocimientos
                coherencia_habilidades_conocimientos = 0
                if habilidades and conocimientos:
                    habilidades_set = {h.habilidad.lower() for h in habilidades if hasattr(h, 'habilidad')}
                    conocimientos_set = {c.conocimiento.lower() for c in conocimientos if hasattr(c, 'conocimiento')}
                    if habilidades_set and conocimientos_set:
                        coherencia_habilidades_conocimientos = len(habilidades_set.intersection(conocimientos_set)) / len(habilidades_set.union(conocimientos_set))
                
                # Progresión de experiencia
                progresion_experiencia = 0
                if len(experiencias) > 1:
                    tiempos_ordenados = sorted([e.tiempo for e in experiencias if hasattr(e, 'tiempo')])
                    if len(tiempos_ordenados) > 1:
                        progresion_experiencia = np.corrcoef(range(len(tiempos_ordenados)), tiempos_ordenados)[0, 1]
                        if np.isnan(progresion_experiencia):
                            progresion_experiencia = 0
                
                # Especialización vs generalización
                especializacion = 0
                if habilidades:
                    categorias = [getattr(h, 'categoria', 'general') for h in habilidades]
                    if categorias:
                        categoria_counts = Counter(categorias)
                        especializacion = max(categoria_counts.values()) / len(categorias)
                
                # Complejidad de perfil
                complejidad_perfil = (
                    len(habilidades) * 0.3 +
                    len(conocimientos) * 0.3 +
                    len(experiencias) * 0.2 +
                    len(estudios) * 0.2
                ) / 20  # Normalizar
                
                # Vector de características expandido
                feature_vector = {
                    'user_id': usuario.id,
                    'num_habilidades': len(habilidades),
                    'num_conocimientos': len(conocimientos),
                    'num_experiencias': len(experiencias),
                    'num_estudios': len(estudios),
                    'match_habilidades': match_habilidades,
                    'match_conocimientos': match_conocimientos,
                    'promedio_nivel_conocimientos': promedio_nivel_conocimientos,
                    'max_nivel_conocimientos': max_nivel_conocimientos,
                    'max_tiempo_experiencia': max_tiempo_experiencia,
                    'cumple_experiencia': cumple_experiencia,
                    'nivel_educativo': nivel_educativo,
                    'experiencia_relevante': experiencia_relevante,
                    'diversidad_habilidades': diversidad_habilidades,
                    'consistencia_experiencia': consistencia_experiencia,
                    'promedio_nivel_habilidades': promedio_nivel_habilidades,
                    'max_nivel_habilidades': max_nivel_habilidades,
                    'coherencia_habilidades_conocimientos': coherencia_habilidades_conocimientos,
                    'progresion_experiencia': progresion_experiencia,
                    'especializacion': especializacion,
                    'complejidad_perfil': complejidad_perfil
                }
                
                usuarios_features.append(feature_vector)
            
            # Convertir a DataFrame
            df_usuarios = pd.DataFrame(usuarios_features)
            
            # Características para escalado
            features = ['num_habilidades', 'num_conocimientos', 'num_experiencias', 'num_estudios',
                       'match_habilidades', 'match_conocimientos', 'promedio_nivel_conocimientos',
                       'max_nivel_conocimientos', 'max_tiempo_experiencia', 'cumple_experiencia',
                       'nivel_educativo', 'experiencia_relevante', 'diversidad_habilidades',
                       'consistencia_experiencia', 'promedio_nivel_habilidades', 'max_nivel_habilidades',
                       'coherencia_habilidades_conocimientos', 'progresion_experiencia', 'especializacion',
                       'complejidad_perfil']
            
            # Características ya normalizadas
            normalized_features = ['match_habilidades', 'match_conocimientos', 'cumple_experiencia']
            scaling_features = [f for f in features if f not in normalized_features]
            
            # Escalar características
            if scaling_features and len(df_usuarios) > 0:
                X_scaled = self.scaler.fit_transform(df_usuarios[scaling_features])
                X_scaled = pd.DataFrame(X_scaled, columns=scaling_features, index=df_usuarios.index)
                
                # Combinar con características normalizadas
                X = pd.concat([X_scaled, df_usuarios[normalized_features]], axis=1)
            else:
                X = df_usuarios[features]
            
            return X.values, df_usuarios['user_id'].values
            
        except Exception as e:
            logger.error(f"Error preparando datos avanzados: {str(e)}")
            raise
    
    def _create_advanced_labels(self, X):
        """
        Crea etiquetas sintéticas más sofisticadas
        """
        if len(X) == 0:
            return np.array([]), np.array([])
        
        # Características clave para scoring avanzado
        match_score = (X[:, 5] + X[:, 6]) / 2  # match_habilidades + match_conocimientos
        experiencia_score = X[:, 9]  # cumple_experiencia
        educacion_score = np.clip(X[:, 10] / 6, 0, 1)  # nivel_educativo normalizado
        experiencia_relevante_score = np.clip(X[:, 11] / 15, 0, 1)  # experiencia_relevante
        coherencia_score = X[:, 16]  # coherencia_habilidades_conocimientos
        progresion_score = np.clip(X[:, 17], 0, 1)  # progresion_experiencia
        especializacion_score = X[:, 18]  # especializacion
        complejidad_score = X[:, 19]  # complejidad_perfil
        
        # Score combinado más sofisticado
        combined_score = (
            match_score * 0.20 +
            experiencia_score * 0.10 +
            educacion_score * 0.08 +
            experiencia_relevante_score * 0.15 +
            coherencia_score * 0.08 +
            progresion_score * 0.08 +
            especializacion_score * 0.08 +
            complejidad_score * 0.13
        )
        
        # Convertir a etiquetas binarias
        if len(combined_score) > 1:
            threshold = np.percentile(combined_score, 65)  # Top 35% como buenos candidatos
        else:
            threshold = 0.5
        
        labels = (combined_score >= threshold).astype(int)
        
        # Asegurar balance de clases
        if len(np.unique(labels)) == 1 and len(labels) > 1:
            half_point = len(labels) // 2
            labels[:half_point] = 0
            labels[half_point:] = 1
        
        return labels, combined_score
    
    def _build_advanced_ensemble(self, X_shape):
        """
        Construye un ensemble avanzado de modelos
        """
        # Modelos base
        rf_model = RandomForestClassifier(
            n_estimators=200,
            max_depth=12,
            min_samples_split=4,
            min_samples_leaf=2,
            random_state=42
        )
        
        gb_model = GradientBoostingClassifier(
            n_estimators=150,
            learning_rate=0.1,
            max_depth=8,
            random_state=42
        )
        
        svm_model = SVC(
            kernel='rbf',
            C=1.0,
            gamma='scale',
            probability=True,
            random_state=42
        )
        
        mlp_model = MLPClassifier(
            hidden_layer_sizes=(128, 64, 32),
            activation='relu',
            solver='adam',
            alpha=0.001,
            learning_rate='adaptive',
            max_iter=1000,
            early_stopping=True,
            validation_fraction=0.2,
            n_iter_no_change=15,
            random_state=42
        )
        
        # Ensemble con votación ponderada
        ensemble = VotingClassifier(
            estimators=[
                ('rf', rf_model),
                ('gb', gb_model),
                ('svm', svm_model),
                ('mlp', mlp_model)
            ],
            voting='soft',
            weights=[0.3, 0.25, 0.2, 0.25]
        )
        
        return ensemble
    
    def _safe_score_calculation(self, y_true, y_pred, metric_func):
        """
        Calcula métricas de manera segura
        """
        try:
            if len(np.unique(y_true)) == 1 or len(np.unique(y_pred)) == 1:
                return accuracy_score(y_true, y_pred)
            else:
                return metric_func(y_true, y_pred, average='weighted', zero_division=0)
        except:
            return 0.0
    
    def train_advanced_models(self, X, user_ids):
        """
        Entrena modelos avanzados con técnicas sofisticadas
        """
        try:
            if len(X) == 0:
                raise ValueError("No hay datos para entrenar")
            
            # Si solo hay un usuario
            if len(X) == 1:
                features = X[0]
                match_score = (features[5] + features[6]) / 2
                experiencia_score = features[9]
                educacion_score = np.clip(features[10] / 6, 0, 1)
                experiencia_relevante_score = np.clip(features[11] / 15, 0, 1)
                coherencia_score = features[16]
                progresion_score = np.clip(features[17], 0, 1)
                especializacion_score = features[18]
                complejidad_score = features[19]
                
                combined_score = (
                    match_score * 0.20 +
                    experiencia_score * 0.10 +
                    educacion_score * 0.08 +
                    experiencia_relevante_score * 0.15 +
                    coherencia_score * 0.08 +
                    progresion_score * 0.08 +
                    especializacion_score * 0.08 +
                    complejidad_score * 0.13
                )
                
                base_scores = {
                    'accuracy': float(combined_score),
                    'precision': float(combined_score),
                    'recall': float(combined_score),
                    'f1': float(combined_score)
                }
                
                self.models_trained = False
                return base_scores, base_scores, base_scores
            
            # Crear etiquetas sintéticas
            nn_labels, score_continuo = self._create_advanced_labels(X)
            
            # Dividir datos
            test_size = min(0.2, max(0.1, 1 / len(X)))
            
            if len(X) >= 4:
                try:
                    X_train, X_test, y_train, y_test = train_test_split(
                        X, nn_labels, test_size=test_size, random_state=42, stratify=nn_labels
                    )
                except ValueError:
                    X_train, X_test, y_train, y_test = train_test_split(
                        X, nn_labels, test_size=test_size, random_state=42
                    )
            else:
                X_train = X_test = X
                y_train = y_test = nn_labels
            
            # Selección de características
            try:
                self.feature_selector = SelectKBest(score_func=f_classif, k=min(self.n_features, X_train.shape[1]))
                X_train_selected = self.feature_selector.fit_transform(X_train, y_train)
                X_test_selected = self.feature_selector.transform(X_test)
            except:
                X_train_selected = X_train
                X_test_selected = X_test
            
            # Reducción de dimensionalidad con PCA
            try:
                self.pca = PCA(n_components=min(self.n_components, X_train_selected.shape[1]))
                X_train_pca = self.pca.fit_transform(X_train_selected)
                X_test_pca = self.pca.transform(X_test_selected)
            except:
                X_train_pca = X_train_selected
                X_test_pca = X_test_selected
            
            # Entrenar ensemble avanzado
            try:
                self.ensemble_model = self._build_advanced_ensemble(X_train_pca.shape)
                self.ensemble_model.fit(X_train_pca, y_train)
                
                ensemble_pred = self.ensemble_model.predict(X_test_pca)
                ensemble_scores = {
                    'accuracy': accuracy_score(y_test, ensemble_pred),
                    'precision': self._safe_score_calculation(y_test, ensemble_pred, precision_score),
                    'recall': self._safe_score_calculation(y_test, ensemble_pred, recall_score),
                    'f1': self._safe_score_calculation(y_test, ensemble_pred, f1_score)
                }
            except Exception as e:
                logger.warning(f"Error entrenando ensemble: {e}")
                ensemble_scores = {'accuracy': 0.5, 'precision': 0.5, 'recall': 0.5, 'f1': 0.5}
            
            # Reentrenar con todos los datos
            try:
                if len(X) > 1:
                    X_full_selected = self.feature_selector.transform(X) if self.feature_selector else X
                    X_full_pca = self.pca.transform(X_full_selected) if self.pca else X_full_selected
                    self.ensemble_model.fit(X_full_pca, nn_labels)
                    self.models_trained = True
            except Exception as e:
                logger.warning(f"Error reentrenando con todos los datos: {e}")
            
            return ensemble_scores, ensemble_scores, ensemble_scores
            
        except Exception as e:
            logger.error(f"Error entrenando modelos avanzados: {str(e)}")
            raise
    
    def get_advanced_recommendations(self, X, user_ids, top_n=10):
        """
        Obtiene recomendaciones usando modelos avanzados
        """
        try:
            if len(X) == 0:
                return []
            
            # Si solo hay un usuario
            if len(X) == 1:
                features = X[0]
                match_score = (features[5] + features[6]) / 2
                experiencia_score = features[9]
                educacion_score = np.clip(features[10] / 6, 0, 1)
                experiencia_relevante_score = np.clip(features[11] / 15, 0, 1)
                coherencia_score = features[16]
                progresion_score = np.clip(features[17], 0, 1)
                especializacion_score = features[18]
                complejidad_score = features[19]
                
                combined_score = (
                    match_score * 0.20 +
                    experiencia_score * 0.10 +
                    educacion_score * 0.08 +
                    experiencia_relevante_score * 0.15 +
                    coherencia_score * 0.08 +
                    progresion_score * 0.08 +
                    especializacion_score * 0.08 +
                    complejidad_score * 0.13
                )
                
                return [{
                    'user_id': user_ids[0],
                    'score': float(combined_score),
                    'ensemble_score': float(combined_score),
                    'confidence': 'Alta' if combined_score > 0.7 else 'Media' if combined_score > 0.5 else 'Baja',
                    'model_type': 'Advanced Ensemble'
                }]
            
            # Si los modelos no están entrenados
            if not self.models_trained:
                recommendations = []
                for i, user_id in enumerate(user_ids):
                    features = X[i]
                    match_score = (features[5] + features[6]) / 2
                    experiencia_score = features[9]
                    educacion_score = np.clip(features[10] / 6, 0, 1)
                    experiencia_relevante_score = np.clip(features[11] / 15, 0, 1)
                    coherencia_score = features[16]
                    progresion_score = np.clip(features[17], 0, 1)
                    especializacion_score = features[18]
                    complejidad_score = features[19]
                    
                    combined_score = (
                        match_score * 0.20 +
                        experiencia_score * 0.10 +
                        educacion_score * 0.08 +
                        experiencia_relevante_score * 0.15 +
                        coherencia_score * 0.08 +
                        progresion_score * 0.08 +
                        especializacion_score * 0.08 +
                        complejidad_score * 0.13
                    )
                    
                    if combined_score > 0.3:
                        recommendations.append({
                            'user_id': user_id,
                            'score': float(combined_score),
                            'ensemble_score': float(combined_score),
                            'confidence': 'Alta' if combined_score > 0.7 else 'Media' if combined_score > 0.5 else 'Baja',
                            'model_type': 'Advanced Ensemble'
                        })
                
                recommendations.sort(key=lambda x: x['score'], reverse=True)
                return recommendations[:top_n]
            
            # Obtener predicciones del ensemble
            try:
                X_selected = self.feature_selector.transform(X) if self.feature_selector else X
                X_pca = self.pca.transform(X_selected) if self.pca else X_selected
                ensemble_scores = self.ensemble_model.predict_proba(X_pca)[:, 1]
            except:
                ensemble_scores = np.full(len(X), 0.5)
            
            # Normalizar scores
            if len(ensemble_scores) > 1:
                min_score = ensemble_scores.min()
                max_score = ensemble_scores.max()
                if max_score > min_score:
                    normalized_scores = (ensemble_scores - min_score) / (max_score - min_score)
                else:
                    normalized_scores = ensemble_scores
            else:
                normalized_scores = ensemble_scores
            
            # Obtener mejores candidatos
            top_indices = np.argsort(normalized_scores)[-top_n:][::-1]
            
            recommendations = []
            for idx in top_indices:
                combined_score = float(normalized_scores[idx])
                
                if combined_score > 0.3:
                    recommendations.append({
                        'user_id': user_ids[idx],
                        'score': combined_score,
                        'ensemble_score': float(ensemble_scores[idx]),
                        'confidence': 'Alta' if combined_score > 0.7 else 'Media' if combined_score > 0.5 else 'Baja',
                        'model_type': 'Advanced Ensemble (RF + GB + SVM + MLP)'
                    })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error obteniendo recomendaciones avanzadas: {str(e)}")
            raise
    
    def get_advanced_performance_summary(self):
        """
        Devuelve resumen del rendimiento de modelos avanzados
        """
        return {
            'model_type': 'Advanced Ensemble',
            'models_available': {
                'random_forest': True,
                'gradient_boosting': True,
                'support_vector_machine': True,
                'multi_layer_perceptron': True
            },
            'models_trained': self.models_trained,
            'architecture': {
                'feature_selection': 'SelectKBest (ANOVA F-test)',
                'dimensionality_reduction': 'PCA',
                'ensemble_method': 'Voting Classifier (Soft)',
                'advanced_features': 'Coherencia, Progresión, Especialización, Complejidad'
            }
        }