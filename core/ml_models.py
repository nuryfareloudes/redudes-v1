import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import logging
import warnings

# Suprimir advertencias específicas de métricas
warnings.filterwarnings('ignore', category=UserWarning, message='.*Precision is ill-defined.*')
warnings.filterwarnings('ignore', category=UserWarning, message='.*F-score is ill-defined.*')
warnings.filterwarnings('ignore', category=UserWarning, message='.*Recall is ill-defined.*')

logger = logging.getLogger(__name__)


class RecommendationSystem:
    def __init__(self):
        # Configurar Random Forest con más parámetros
        self.rf_model = RandomForestClassifier(
            n_estimators=200,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42
        )

        # Configurar KNN con más parámetros
        self.knn_model = KNeighborsClassifier(
            n_neighbors=5,
            weights='distance',
            metric='euclidean'
        )

        # Configurar Red Neuronal con MLPClassifier
        self.nn_model = MLPClassifier(
            hidden_layer_sizes=(64, 32, 16),
            activation='relu',
            solver='adam',
            alpha=0.001,
            learning_rate='adaptive',
            max_iter=500,
            early_stopping=True,
            validation_fraction=0.2,
            n_iter_no_change=10,
            random_state=42
        )

        self.scaler = StandardScaler()

        # Pesos iniciales para la combinación de modelos (ahora para 3 modelos)
        self.rf_weight = 0.33
        self.knn_weight = 0.33
        self.nn_weight = 0.34

        # Flags para rastrear si los modelos están entrenados
        self.models_trained = False

    def prepare_data(self, usuarios, roles_proyecto):
        """
        Prepara los datos para el entrenamiento del modelo.
        """
        try:
            # Crear features para usuarios
            usuarios_features = []

            # Obtener todas las habilidades y conocimientos requeridos por los roles
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
                # Obtener habilidades, conocimientos y experiencia con manejo de errores
                try:
                    habilidades = list(usuario.habilidades.all()) if hasattr(usuario, 'habilidades') else []
                    conocimientos = list(usuario.conocimientos.all()) if hasattr(usuario, 'conocimientos') else []
                    experiencias = list(usuario.experiencias.all()) if hasattr(usuario, 'experiencias') else []
                    estudios = list(usuario.estudios.all()) if hasattr(usuario, 'estudios') else []
                except:
                    habilidades = conocimientos = experiencias = estudios = []

                # Calcular match de habilidades con peso
                habilidades_usuario = set()
                if habilidades:
                    for h in habilidades:
                        if hasattr(h, 'habilidad'):
                            habilidades_usuario.add(h.habilidad.lower())

                match_habilidades = len(habilidades_usuario.intersection(roles_habilidades)) / len(
                    roles_habilidades) if roles_habilidades else 0

                # Calcular match de conocimientos con peso
                conocimientos_usuario = set()
                if conocimientos:
                    for c in conocimientos:
                        if hasattr(c, 'conocimiento'):
                            conocimientos_usuario.add(c.conocimiento.lower())

                match_conocimientos = len(conocimientos_usuario.intersection(roles_conocimientos)) / len(
                    roles_conocimientos) if roles_conocimientos else 0

                # Calcular nivel promedio de conocimientos relevantes
                niveles_conocimientos = []
                for c in conocimientos:
                    if hasattr(c, 'conocimiento') and hasattr(c, 'nivel'):
                        if c.conocimiento.lower() in roles_conocimientos:
                            niveles_conocimientos.append(c.nivel)

                promedio_nivel_conocimientos = np.mean(niveles_conocimientos) if niveles_conocimientos else 0

                # Calcular años máximos de experiencia relevante
                max_tiempo_experiencia = 0
                if experiencias:
                    for e in experiencias:
                        if hasattr(e, 'tiempo'):
                            max_tiempo_experiencia = max(max_tiempo_experiencia, e.tiempo)

                cumple_experiencia = 1 if max_tiempo_experiencia >= roles_experiencia_min else 0

                # Calcular nivel educativo máximo
                nivel_educativo = 0
                if estudios:
                    for e in estudios:
                        if hasattr(e, 'nivel'):
                            nivel_educativo = max(nivel_educativo, e.nivel)

                # Calcular relevancia de experiencia
                experiencia_relevante = 0
                for exp in experiencias:
                    if hasattr(exp, 'actividades') and hasattr(exp, 'tiempo'):
                        actividades_lower = exp.actividades.lower()
                        if any(h in actividades_lower for h in roles_habilidades) or \
                                any(c in actividades_lower for c in roles_conocimientos):
                            experiencia_relevante += exp.tiempo

                # Nuevas características mejoradas
                diversidad_habilidades = len(
                    set(getattr(h, 'categoria', 'general') for h in habilidades)) if habilidades else 0
                tiempos_experiencia = [e.tiempo for e in experiencias if hasattr(e, 'tiempo')]
                consistencia_experiencia = np.std(tiempos_experiencia) if len(tiempos_experiencia) > 1 else 0

                niveles_habilidades = [getattr(h, 'nivel', 3) for h in habilidades if hasattr(h, 'nivel')]
                promedio_nivel_habilidades = np.mean(niveles_habilidades) if niveles_habilidades else 0

                # Crear vector de características expandido
                feature_vector = {
                    'user_id': usuario.id,
                    'num_habilidades': len(habilidades),
                    'num_conocimientos': len(conocimientos),
                    'num_experiencias': len(experiencias),
                    'num_estudios': len(estudios),
                    'match_habilidades': match_habilidades,
                    'match_conocimientos': match_conocimientos,
                    'promedio_nivel_conocimientos': promedio_nivel_conocimientos,
                    'max_tiempo_experiencia': max_tiempo_experiencia,
                    'cumple_experiencia': cumple_experiencia,
                    'nivel_educativo': nivel_educativo,
                    'experiencia_relevante': experiencia_relevante,
                    'diversidad_habilidades': diversidad_habilidades,
                    'consistencia_experiencia': consistencia_experiencia,
                    'promedio_nivel_habilidades': promedio_nivel_habilidades
                }

                usuarios_features.append(feature_vector)

            # Convertir a DataFrame
            df_usuarios = pd.DataFrame(usuarios_features)

            # Normalizar características
            features = ['num_habilidades', 'num_conocimientos', 'num_experiencias', 'num_estudios',
                        'match_habilidades', 'match_conocimientos', 'promedio_nivel_conocimientos',
                        'max_tiempo_experiencia', 'cumple_experiencia', 'nivel_educativo',
                        'experiencia_relevante', 'diversidad_habilidades', 'consistencia_experiencia',
                        'promedio_nivel_habilidades']

            # Separar características que ya están normalizadas
            normalized_features = ['match_habilidades', 'match_conocimientos', 'cumple_experiencia']
            scaling_features = [f for f in features if f not in normalized_features]

            # Normalizar solo las características que necesitan escalado
            if scaling_features and len(df_usuarios) > 0:
                X_scaled = self.scaler.fit_transform(df_usuarios[scaling_features])
                X_scaled = pd.DataFrame(X_scaled, columns=scaling_features, index=df_usuarios.index)

                # Combinar con características normalizadas
                X = pd.concat([X_scaled, df_usuarios[normalized_features]], axis=1)
            else:
                X = df_usuarios[features]

            return X.values, df_usuarios['user_id'].values

        except Exception as e:
            logger.error(f"Error preparando datos: {str(e)}")
            raise

    def _create_synthetic_labels(self, X):
        """
        Crea etiquetas sintéticas basadas en las características del usuario
        """
        if len(X) == 0:
            return np.array([]), np.array([])

        # Combinar características clave para crear un score objetivo
        match_score = (X[:, 5] + X[:, 6]) / 2  # match_habilidades + match_conocimientos
        experiencia_score = X[:, 8]  # cumple_experiencia
        educacion_score = np.clip(X[:, 9] / 5, 0, 1)  # nivel_educativo normalizado
        experiencia_relevante_score = np.clip(X[:, 10] / 10, 0, 1)  # experiencia_relevante

        # Calcular score combinado
        combined_score = (
                match_score * 0.4 +
                experiencia_score * 0.2 +
                educacion_score * 0.1 +
                experiencia_relevante_score * 0.3
        )

        # Convertir a etiquetas binarias (1 si es un buen candidato, 0 si no)
        if len(combined_score) > 1:
            threshold = np.percentile(combined_score, 60)  # Top 40% como buenos candidatos
        else:
            threshold = 0.5  # Umbral fijo para un solo usuario

        labels = (combined_score >= threshold).astype(int)

        # Asegurar que tengamos al menos una muestra de cada clase si es posible
        if len(np.unique(labels)) == 1 and len(labels) > 1:
            # Si todas las etiquetas son iguales, hacer la mitad de cada clase
            half_point = len(labels) // 2
            labels[:half_point] = 0
            labels[half_point:] = 1

        return labels, combined_score

    def _safe_score_calculation(self, y_true, y_pred, metric_func):
        """
        Calcula métricas de manera segura, manejando casos edge
        """
        try:
            if len(np.unique(y_true)) == 1 or len(np.unique(y_pred)) == 1:
                # Si solo hay una clase, usar accuracy como proxy
                return accuracy_score(y_true, y_pred)
            else:
                return metric_func(y_true, y_pred, average='weighted', zero_division=0)
        except:
            return 0.0

    def train_models(self, X, y):
        """
        Entrena los tres modelos: Random Forest, KNN y Red Neuronal (MLP)
        """
        try:
            # Validar entrada
            if len(X) == 0:
                raise ValueError("No hay datos para entrenar")

            # Si solo hay un usuario, calcular scores directamente sin entrenar modelos
            if len(X) == 1:
                features = X[0]
                match_score = (features[5] + features[6]) / 2
                experiencia_score = features[8]
                educacion_score = np.clip(features[9] / 5, 0, 1)
                experiencia_relevante_score = np.clip(features[10] / 10, 0, 1)

                combined_score = (
                        match_score * 0.4 +
                        experiencia_score * 0.2 +
                        educacion_score * 0.1 +
                        experiencia_relevante_score * 0.3
                )

                base_scores = {
                    'accuracy': float(combined_score),
                    'precision': float(combined_score),
                    'recall': float(combined_score),
                    'f1': float(combined_score)
                }

                self.models_trained = False  # No se pueden entrenar con un solo usuario
                return base_scores, base_scores, base_scores

            # Crear etiquetas sintéticas para la red neuronal
            nn_labels, score_continuo = self._create_synthetic_labels(X)

            # Validar que tenemos suficientes datos para dividir
            test_size = min(0.2, max(0.1, 1 / len(X)))  # Ajustar test_size dinámicamente

            # Dividir datos solo si tenemos suficientes muestras
            if len(X) >= 4:  # Mínimo 4 muestras para hacer split
                try:
                    X_train, X_test, y_train, y_test = train_test_split(
                        X, y, test_size=test_size, random_state=42, stratify=y
                    )
                    nn_train, nn_test, nn_y_train, nn_y_test = train_test_split(
                        X, nn_labels, test_size=test_size, random_state=42, stratify=nn_labels
                    )
                except ValueError:  # Si stratify falla, intentar sin stratify
                    X_train, X_test, y_train, y_test = train_test_split(
                        X, y, test_size=test_size, random_state=42
                    )
                    nn_train, nn_test, nn_y_train, nn_y_test = train_test_split(
                        X, nn_labels, test_size=test_size, random_state=42
                    )
            else:
                # Con pocos datos, usar todos para entrenamiento y evaluación
                X_train = X_test = X
                y_train = y_test = y
                nn_train = nn_test = X
                nn_y_train = nn_y_test = nn_labels

            # Inicializar scores por defecto
            rf_scores = knn_scores = nn_scores = {
                'accuracy': 0.5,
                'precision': 0.5,
                'recall': 0.5,
                'f1': 0.5
            }

            # Entrenar Random Forest
            try:
                self.rf_model.fit(X_train, y_train)
                rf_pred = self.rf_model.predict(X_test)
                rf_scores = {
                    'accuracy': accuracy_score(y_test, rf_pred),
                    'precision': self._safe_score_calculation(y_test, rf_pred, precision_score),
                    'recall': self._safe_score_calculation(y_test, rf_pred, recall_score),
                    'f1': self._safe_score_calculation(y_test, rf_pred, f1_score)
                }
            except Exception as e:
                logger.warning(f"Error entrenando Random Forest: {e}")

            # Entrenar KNN
            try:
                # Ajustar n_neighbors si tenemos pocos datos
                n_neighbors = min(self.knn_model.n_neighbors, len(X_train))
                if n_neighbors != self.knn_model.n_neighbors:
                    self.knn_model.set_params(n_neighbors=n_neighbors)

                self.knn_model.fit(X_train, y_train)
                knn_pred = self.knn_model.predict(X_test)
                knn_scores = {
                    'accuracy': accuracy_score(y_test, knn_pred),
                    'precision': self._safe_score_calculation(y_test, knn_pred, precision_score),
                    'recall': self._safe_score_calculation(y_test, knn_pred, recall_score),
                    'f1': self._safe_score_calculation(y_test, knn_pred, f1_score)
                }
            except Exception as e:
                logger.warning(f"Error entrenando KNN: {e}")

            # Entrenar Red Neuronal (MLP)
            try:
                self.nn_model.fit(nn_train, nn_y_train)
                nn_pred = self.nn_model.predict(nn_test)
                nn_scores = {
                    'accuracy': accuracy_score(nn_y_test, nn_pred),
                    'precision': self._safe_score_calculation(nn_y_test, nn_pred, precision_score),
                    'recall': self._safe_score_calculation(nn_y_test, nn_pred, recall_score),
                    'f1': self._safe_score_calculation(nn_y_test, nn_pred, f1_score)
                }
            except Exception as e:
                logger.warning(f"Error entrenando Red Neuronal: {e}")

            # Ajustar pesos basados en el rendimiento de los tres modelos
            rf_performance = np.mean([rf_scores['accuracy'], rf_scores['f1']])
            knn_performance = np.mean([knn_scores['accuracy'], knn_scores['f1']])
            nn_performance = np.mean([nn_scores['accuracy'], nn_scores['f1']])

            total_performance = rf_performance + knn_performance + nn_performance

            #if total_performance > 0:
            #    self.rf_weight = rf_performance / total_performance
            #    self.knn_weight = knn_performance / total_performance
            #    self.nn_weight = nn_performance / total_performance
            #else:
                # Pesos por defecto si no se puede calcular performance
            self.rf_weight = 0.33
            self.knn_weight = 0.33
            self.nn_weight = 0.34

            logger.info(
                f"Pesos ajustados - RF: {self.rf_weight:.3f}, KNN: {self.knn_weight:.3f}, NN: {self.nn_weight:.3f}")

            # Reentrenar con todos los datos si es posible
            try:
                if len(X) > 1:
                    self.rf_model.fit(X, y)
                    self.knn_model.fit(X, y)
                    self.nn_model.fit(X, nn_labels)
                    self.models_trained = True
            except Exception as e:
                logger.warning(f"Error reentrenando con todos los datos: {e}")

            return rf_scores, knn_scores, nn_scores

        except Exception as e:
            logger.error(f"Error entrenando modelos: {str(e)}")
            raise

    def get_recommendations(self, X, user_ids, top_n=5):
        """
        Obtiene recomendaciones combinando resultados de los tres modelos
        """
        try:
            if len(X) == 0:
                return []

            # Si solo hay un usuario, calcular score directamente
            if len(X) == 1:
                features = X[0]
                match_score = (features[5] + features[6]) / 2
                experiencia_score = features[8]
                educacion_score = np.clip(features[9] / 5, 0, 1)
                experiencia_relevante_score = np.clip(features[10] / 10, 0, 1)

                combined_score = (
                        match_score * 0.4 +
                        experiencia_score * 0.2 +
                        educacion_score * 0.1 +
                        experiencia_relevante_score * 0.3
                )

                return [{
                    'user_id': user_ids[0],
                    'score': float(combined_score),
                    'rf_score': float(combined_score),
                    'knn_score': float(combined_score),
                    'nn_score': float(combined_score),
                    'confidence': 'Alta' if combined_score > 0.7 else 'Media' if combined_score > 0.5 else 'Baja',
                    'model_weights': {
                        'rf': self.rf_weight,
                        'knn': self.knn_weight,
                        'nn': self.nn_weight
                    }
                }]

            # Si los modelos no están entrenados, usar scoring directo
            if not self.models_trained:
                recommendations = []
                for i, user_id in enumerate(user_ids):
                    features = X[i]
                    match_score = (features[5] + features[6]) / 2
                    experiencia_score = features[8]
                    educacion_score = np.clip(features[9] / 5, 0, 1)
                    experiencia_relevante_score = np.clip(features[10] / 10, 0, 1)

                    combined_score = (
                            match_score * 0.4 +
                            experiencia_score * 0.2 +
                            educacion_score * 0.1 +
                            experiencia_relevante_score * 0.3
                    )

                    if combined_score > 0.3:  # Solo incluir candidatos con score mínimo
                        recommendations.append({
                            'user_id': user_id,
                            'score': float(combined_score),
                            'rf_score': float(combined_score),
                            'knn_score': float(combined_score),
                            'nn_score': float(combined_score),
                            'confidence': 'Alta' if combined_score > 0.7 else 'Media' if combined_score > 0.5 else 'Baja',
                            'model_weights': {
                                'rf': self.rf_weight,
                                'knn': self.knn_weight,
                                'nn': self.nn_weight
                            }
                        })

                # Ordenar por score y tomar los mejores
                recommendations.sort(key=lambda x: x['score'], reverse=True)
                return recommendations[:top_n]

            # Obtener probabilidades de cada modelo
            try:
                rf_probs = self.rf_model.predict_proba(X)
                rf_scores = rf_probs[:, 1] if rf_probs.shape[1] > 1 else rf_probs[:, 0]
            except:
                rf_scores = np.full(len(X), 0.5)

            try:
                knn_probs = self.knn_model.predict_proba(X)
                knn_scores = knn_probs[:, 1] if knn_probs.shape[1] > 1 else knn_probs[:, 0]
            except:
                knn_scores = np.full(len(X), 0.5)

            try:
                nn_probs = self.nn_model.predict_proba(X)
                nn_scores = nn_probs[:, 1] if nn_probs.shape[1] > 1 else nn_probs[:, 0]
            except:
                nn_scores = np.full(len(X), 0.5)

            # Combinar probabilidades con pesos ajustados
            combined_scores = (
                    self.rf_weight * rf_scores +
                    self.knn_weight * knn_scores +
                    self.nn_weight * nn_scores
            )

            # Normalizar scores combinados
            if len(combined_scores) > 1:
                min_score = combined_scores.min()
                max_score = combined_scores.max()
                if max_score > min_score:
                    normalized_scores = (combined_scores - min_score) / (max_score - min_score)
                else:
                    normalized_scores = combined_scores
            else:
                normalized_scores = combined_scores

            # Obtener índices de los mejores candidatos
            top_indices = np.argsort(normalized_scores)[-top_n:][::-1]

            # Obtener IDs de usuarios y sus scores
            recommendations = []
            for idx in top_indices:
                combined_score = float(normalized_scores[idx])

                # Solo incluir recomendaciones con score combinado superior a 0.3
                if combined_score > 0.3:
                    recommendations.append({
                        'user_id': user_ids[idx],
                        'score': combined_score,
                        'rf_score': float(rf_scores[idx]),
                        'knn_score': float(knn_scores[idx]),
                        'nn_score': float(nn_scores[idx]),
                        'confidence': 'Alta' if combined_score > 0.7 else 'Media' if combined_score > 0.5 else 'Baja',
                        'model_weights': {
                            'rf': float(self.rf_weight),
                            'knn': float(self.knn_weight),
                            'nn': float(self.nn_weight)
                        }
                    })

            return recommendations

        except Exception as e:
            logger.error(f"Error obteniendo recomendaciones: {str(e)}")
            raise

    def get_model_performance_summary(self):
        """
        Devuelve un resumen del rendimiento y pesos de los modelos
        """
        return {
            'model_weights': {
                'random_forest': float(self.rf_weight),
                'knn': float(self.knn_weight),
                'neural_network': float(self.nn_weight)
            },
            'models_trained': {
                'random_forest': self.models_trained and self.rf_model is not None,
                'knn': self.models_trained and self.knn_model is not None,
                'neural_network': self.models_trained and self.nn_model is not None
            },
            'overall_trained': self.models_trained
        }