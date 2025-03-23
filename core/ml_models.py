import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import logging

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
        
        self.scaler = StandardScaler()
        
        # Pesos iniciales para la combinación de modelos
        self.rf_weight = 0.6
        self.knn_weight = 0.4
        
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
                roles_habilidades.update(set(rol.habilidades.lower().split(',')))
                roles_conocimientos.update(set(rol.conocimientos.lower().split(',')))
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
                # Obtener habilidades, conocimientos y experiencia
                habilidades = list(usuario.habilidades.all())
                conocimientos = list(usuario.conocimientos.all())
                experiencias = list(usuario.experiencias.all())
                estudios = list(usuario.estudios.all())
                
                # Calcular match de habilidades con peso
                habilidades_usuario = {h.habilidad.lower() for h in habilidades}
                match_habilidades = len(habilidades_usuario.intersection(roles_habilidades)) / len(roles_habilidades) if roles_habilidades else 0
                
                # Calcular match de conocimientos con peso
                conocimientos_usuario = {c.conocimiento.lower() for c in conocimientos}
                match_conocimientos = len(conocimientos_usuario.intersection(roles_conocimientos)) / len(roles_conocimientos) if roles_conocimientos else 0
                
                # Calcular nivel promedio de conocimientos relevantes
                niveles_conocimientos = []
                for c in conocimientos:
                    if c.conocimiento.lower() in roles_conocimientos:
                        niveles_conocimientos.append(c.nivel)
                
                promedio_nivel_conocimientos = np.mean(niveles_conocimientos) if niveles_conocimientos else 0
                
                # Calcular años máximos de experiencia relevante
                max_tiempo_experiencia = max([e.tiempo for e in experiencias]) if experiencias else 0
                cumple_experiencia = 1 if max_tiempo_experiencia >= roles_experiencia_min else 0
                
                # Calcular nivel educativo máximo
                nivel_educativo = max([e.nivel for e in estudios]) if estudios else 0
                
                # Calcular relevancia de experiencia
                experiencia_relevante = 0
                for exp in experiencias:
                    if any(h in exp.descripcion.lower() for h in roles_habilidades) or \
                       any(c in exp.descripcion.lower() for c in roles_conocimientos):
                        experiencia_relevante += exp.tiempo
                
                # Crear vector de características
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
                    'experiencia_relevante': experiencia_relevante
                }
                
                usuarios_features.append(feature_vector)
            
            # Convertir a DataFrame
            df_usuarios = pd.DataFrame(usuarios_features)
            
            # Normalizar características
            features = ['num_habilidades', 'num_conocimientos', 'num_experiencias', 'num_estudios',
                       'match_habilidades', 'match_conocimientos', 'promedio_nivel_conocimientos',
                       'max_tiempo_experiencia', 'cumple_experiencia', 'nivel_educativo',
                       'experiencia_relevante']
            
            # Separar características que ya están normalizadas
            normalized_features = ['match_habilidades', 'match_conocimientos', 'cumple_experiencia']
            scaling_features = [f for f in features if f not in normalized_features]
            
            # Normalizar solo las características que necesitan escalado
            if scaling_features:
                X_scaled = self.scaler.fit_transform(df_usuarios[scaling_features])
                X_scaled = pd.DataFrame(X_scaled, columns=scaling_features)
                
                # Combinar con características normalizadas
                X = pd.concat([X_scaled, df_usuarios[normalized_features]], axis=1)
            else:
                X = df_usuarios[features]
            
            return X.values, df_usuarios['user_id'].values
            
        except Exception as e:
            logger.error(f"Error preparando datos: {str(e)}")
            raise
    
    def train_models(self, X, y):
        """
        Entrena los modelos de Random Forest y KNN
        """
        try:
            # Si solo hay un usuario, calcular scores directamente sin entrenar modelos
            if len(X) == 1:
                features = X[0]
                match_score = (features[5] + features[6]) / 2  # Promedio de match_habilidades y match_conocimientos
                experiencia_score = features[8]  # cumple_experiencia
                educacion_score = features[9] / 5  # nivel_educativo
                experiencia_relevante_score = features[10] / 10  # experiencia_relevante
                
                # Calcular score combinado con pesos ajustados
                combined_score = (
                    match_score * 0.4 +
                    experiencia_score * 0.2 +
                    educacion_score * 0.1 +
                    experiencia_relevante_score * 0.3
                )
                
                return {
                    'accuracy': combined_score,
                    'precision': combined_score,
                    'recall': combined_score,
                    'f1': combined_score
                }, {
                    'accuracy': combined_score,
                    'precision': combined_score,
                    'recall': combined_score,
                    'f1': combined_score
                }
            
            # Dividir datos
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Entrenar Random Forest
            self.rf_model.fit(X_train, y_train)
            rf_pred = self.rf_model.predict(X_test)
            rf_scores = {
                'accuracy': accuracy_score(y_test, rf_pred),
                'precision': precision_score(y_test, rf_pred, average='weighted'),
                'recall': recall_score(y_test, rf_pred, average='weighted'),
                'f1': f1_score(y_test, rf_pred, average='weighted')
            }
            
            # Entrenar KNN
            self.knn_model.fit(X_train, y_train)
            knn_pred = self.knn_model.predict(X_test)
            knn_scores = {
                'accuracy': accuracy_score(y_test, knn_pred),
                'precision': precision_score(y_test, knn_pred, average='weighted'),
                'recall': recall_score(y_test, knn_pred, average='weighted'),
                'f1': f1_score(y_test, knn_pred, average='weighted')
            }
            
            # Ajustar pesos basados en el rendimiento
            rf_performance = np.mean([rf_scores['accuracy'], rf_scores['f1']])
            knn_performance = np.mean([knn_scores['accuracy'], knn_scores['f1']])
            total_performance = rf_performance + knn_performance
            
            if total_performance > 0:
                self.rf_weight = rf_performance / total_performance
                self.knn_weight = knn_performance / total_performance
            
            return rf_scores, knn_scores
            
        except Exception as e:
            logger.error(f"Error entrenando modelos: {str(e)}")
            raise
    
    def get_recommendations(self, X, user_ids, top_n=5):
        """
        Obtiene recomendaciones combinando resultados de ambos modelos
        """
        try:
            # Si solo hay un usuario, calcular score directamente
            if len(X) == 1:
                features = X[0]
                match_score = (features[5] + features[6]) / 2  # Promedio de match_habilidades y match_conocimientos
                experiencia_score = features[8]  # cumple_experiencia
                educacion_score = features[9] / 5  # nivel_educativo
                experiencia_relevante_score = features[10] / 10  # experiencia_relevante
                
                # Calcular score combinado con pesos ajustados
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
                    'confidence': 'Alta' if combined_score > 0.7 else 'Media' if combined_score > 0.5 else 'Baja'
                }]
            
            # Obtener probabilidades de cada modelo
            rf_probs = self.rf_model.predict_proba(X)
            knn_probs = self.knn_model.predict_proba(X)
            
            # Combinar probabilidades con pesos ajustados
            combined_probs = (self.rf_weight * rf_probs + self.knn_weight * knn_probs)
            
            # Calcular scores normalizados
            scores = combined_probs.max(axis=1)
            normalized_scores = (scores - scores.min()) / (scores.max() - scores.min())
            
            # Obtener índices de los mejores candidatos
            top_indices = np.argsort(normalized_scores)[-top_n:][::-1]
            
            # Obtener IDs de usuarios y sus scores
            recommendations = []
            for idx in top_indices:
                # Calcular confianza del modelo
                rf_confidence = rf_probs[idx].max()
                knn_confidence = knn_probs[idx].max()
                combined_score = normalized_scores[idx]
                
                # Solo incluir recomendaciones con score combinado superior a 0.5
                if combined_score > 0.5:
                    recommendations.append({
                        'user_id': user_ids[idx],
                        'score': float(combined_score),
                        'rf_score': float(rf_confidence),
                        'knn_score': float(knn_confidence),
                        'confidence': 'Alta' if combined_score > 0.7 else 'Media' if combined_score > 0.5 else 'Baja'
                    })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error obteniendo recomendaciones: {str(e)}")
            raise 