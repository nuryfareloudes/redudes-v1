import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.ensemble import RandomForestRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
import sqlite3
import warnings

warnings.filterwarnings('ignore')


class ProfessionalProjectMatcher:
    def __init__(self, db_path):
        """
        Inicializa el sistema de matching profesional-proyecto

        Args:
            db_path (str): Ruta a la base de datos SQLite
        """
        self.db_path = db_path
        self.professionals_data = None
        self.projects_data = None
        self.tfidf_vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.scaler = StandardScaler()
        self.label_encoders = {}

    def load_data(self):
        """Carga los datos de la base de datos"""
        conn = sqlite3.connect(self.db_path)

        # Cargar datos de profesionales con sus habilidades, conocimientos, estudios y experiencia
        professionals_query = """
        SELECT 
            u.id,
            u.nombres,
            u.apellidos,
            u.email,
            u.puesto_actual,
            u.dependencia,
            u.fecha_ingreso,
            GROUP_CONCAT(DISTINCT uh.habilidad) as habilidades,
            GROUP_CONCAT(DISTINCT uh.experiencia) as experiencia_habilidades,
            GROUP_CONCAT(DISTINCT uc.conocimiento || ':' || uc.nivel) as conocimientos,
            GROUP_CONCAT(DISTINCT ue.estudio || ':' || ue.nivel) as estudios,
            GROUP_CONCAT(DISTINCT uex.rol || ':' || uex.tiempo) as experiencia_laboral,
            GROUP_CONCAT(DISTINCT uex.actividades) as actividades
        FROM usuario u
        LEFT JOIN usuario_habilidades uh ON u.id = uh.user_id
        LEFT JOIN usuario_conocimiento uc ON u.id = uc.user_id
        LEFT JOIN usuario_estudios ue ON u.id = ue.user_id
        LEFT JOIN usuario_experiencia uex ON u.id = uex.user_id
        GROUP BY u.id
        """

        # Cargar datos de proyectos con roles requeridos
        projects_query = """
        SELECT 
            p.id,
            p.nombre,
            p.convocatoria,
            p.tipo_proyecto,
            p.tipo_convocatoria,
            p.alcance,
            p.objetivo,
            p.presupuesto,
            p.fecha,
            GROUP_CONCAT(DISTINCT pr.rol) as roles_requeridos,
            GROUP_CONCAT(DISTINCT pr.habilidades) as habilidades_requeridas,
            GROUP_CONCAT(DISTINCT pr.experiencia) as experiencia_requerida,
            GROUP_CONCAT(DISTINCT pr.conocimientos) as conocimientos_requeridos
        FROM proyecto p
        LEFT JOIN proyecto_roles pr ON p.id = pr.project_id
        GROUP BY p.id
        """

        self.professionals_data = pd.read_sql_query(professionals_query, conn)
        self.projects_data = pd.read_sql_query(projects_query, conn)

        conn.close()

        # Limpiar datos nulos
        self.professionals_data = self.professionals_data.fillna('')
        self.projects_data = self.projects_data.fillna('')

        print(f"Cargados {len(self.professionals_data)} profesionales y {len(self.projects_data)} proyectos")

    def preprocess_data(self):
        """Preprocesa los datos para los algoritmos de ML"""
        # Crear texto combinado para profesionales
        self.professionals_data['texto_completo'] = (
                self.professionals_data['puesto_actual'] + ' ' +
                self.professionals_data['habilidades'] + ' ' +
                self.professionals_data['conocimientos'] + ' ' +
                self.professionals_data['estudios'] + ' ' +
                self.professionals_data['experiencia_laboral'] + ' ' +
                self.professionals_data['actividades']
        )

        # Crear texto combinado para proyectos
        self.projects_data['texto_completo'] = (
                self.projects_data['tipo_proyecto'] + ' ' +
                self.projects_data['alcance'] + ' ' +
                self.projects_data['objetivo'] + ' ' +
                self.projects_data['roles_requeridos'] + ' ' +
                self.projects_data['habilidades_requeridas'] + ' ' +
                self.projects_data['experiencia_requerida'] + ' ' +
                self.projects_data['conocimientos_requeridos']
        )

        # Crear características numéricas para profesionales
        self.professionals_data['años_experiencia'] = self._extract_experience_years()
        self.professionals_data['nivel_educacion'] = self._extract_education_level()
        self.professionals_data['diversidad_habilidades'] = self.professionals_data['habilidades'].apply(
            lambda x: len(x.split(',')) if x else 0
        )

        # Crear características numéricas para proyectos
        self.projects_data['complejidad_proyecto'] = self._calculate_project_complexity()
        self.projects_data['num_roles_requeridos'] = self.projects_data['roles_requeridos'].apply(
            lambda x: len(x.split(',')) if x else 0
        )

    def _extract_experience_years(self):
        """Extrae años de experiencia de los datos"""
        experience_years = []
        for exp in self.professionals_data['experiencia_laboral']:
            if exp:
                years = 0
                for item in exp.split(','):
                    if ':' in item:
                        try:
                            years += int(item.split(':')[1])
                        except:
                            pass
                experience_years.append(years)
            else:
                experience_years.append(0)
        return experience_years

    def _extract_education_level(self):
        """Extrae nivel de educación"""
        education_levels = []
        for edu in self.professionals_data['estudios']:
            if edu:
                max_level = 0
                for item in edu.split(','):
                    if ':' in item:
                        try:
                            level = int(item.split(':')[1])
                            max_level = max(max_level, level)
                        except:
                            pass
                education_levels.append(max_level)
            else:
                education_levels.append(0)
        return education_levels

    def _calculate_project_complexity(self):
        """Calcula complejidad del proyecto basada en presupuesto y texto"""
        complexity = []
        for idx, row in self.projects_data.iterrows():
            score = 0
            if row['presupuesto']:
                score += min(row['presupuesto'] / 1000000, 10)  # Normalizar presupuesto
            score += len(row['texto_completo'].split()) / 100  # Complejidad textual
            complexity.append(score)
        return complexity

    def algorithm_1_tfidf_cosine(self, project_id):
        """
        Algoritmo 1: TF-IDF + Similitud Coseno
        Calcula similitud textual entre profesionales y proyecto
        """
        project_text = self.projects_data[self.projects_data['id'] == project_id]['texto_completo'].iloc[0]
        all_texts = list(self.professionals_data['texto_completo']) + [project_text]

        # Vectorizar textos
        tfidf_matrix = self.tfidf_vectorizer.fit_transform(all_texts)

        # Calcular similitud coseno
        project_vector = tfidf_matrix[-1]
        professional_vectors = tfidf_matrix[:-1]

        similarities = cosine_similarity(professional_vectors, project_vector).flatten()

        results = pd.DataFrame({
            'professional_id': self.professionals_data['id'],
            'similarity_score': similarities,
            'algorithm': 'TF-IDF Coseno'
        })

        return results.sort_values('similarity_score', ascending=False)

    def algorithm_2_random_forest(self, project_id):
        """
        Algoritmo 2: Random Forest
        Predice compatibilidad basada en características numéricas
        """
        # Preparar características de profesionales
        prof_features = self.professionals_data[[
            'años_experiencia', 'nivel_educacion', 'diversidad_habilidades'
        ]].copy()

        # Obtener características del proyecto
        project_row = self.projects_data[self.projects_data['id'] == project_id].iloc[0]
        project_complexity = project_row['complejidad_proyecto']
        num_roles = project_row['num_roles_requeridos']

        # Crear targets sintéticos basados en compatibilidad esperada
        # (En un caso real, esto vendría de datos históricos de éxito)
        synthetic_targets = []
        for idx, prof in prof_features.iterrows():
            score = 0
            # Mayor experiencia = mejor match
            score += min(prof['años_experiencia'] / 10, 1) * 0.4
            # Educación apropiada
            score += min(prof['nivel_educacion'] / 5, 1) * 0.3
            # Diversidad de habilidades
            score += min(prof['diversidad_habilidades'] / 10, 1) * 0.3
            # Ajustar por complejidad del proyecto
            score *= min(project_complexity / 5, 1)
            synthetic_targets.append(score)

        prof_features['target'] = synthetic_targets

        # Entrenar Random Forest
        X = prof_features[['años_experiencia', 'nivel_educacion', 'diversidad_habilidades']]
        y = prof_features['target']

        rf = RandomForestRegressor(n_estimators=100, random_state=42)
        rf.fit(X, y)

        # Predecir compatibilidad
        predictions = rf.predict(X)

        results = pd.DataFrame({
            'professional_id': self.professionals_data['id'],
            'compatibility_score': predictions,
            'algorithm': 'Random Forest'
        })

        return results.sort_values('compatibility_score', ascending=False)

    def algorithm_3_neural_network(self, project_id):
        """
        Algoritmo 3: Red Neuronal (MLP)
        Combina características textuales y numéricas
        """
        # Preparar características textuales (reducidas)
        project_text = self.projects_data[self.projects_data['id'] == project_id]['texto_completo'].iloc[0]
        all_texts = list(self.professionals_data['texto_completo']) + [project_text]

        # TF-IDF con menos características para la red neuronal
        tfidf_vectorizer_small = TfidfVectorizer(max_features=50, stop_words='english')
        tfidf_matrix = tfidf_vectorizer_small.fit_transform(all_texts)

        # Características textuales de profesionales
        text_features = tfidf_matrix[:-1].toarray()

        # Características numéricas
        numeric_features = self.professionals_data[[
            'años_experiencia', 'nivel_educacion', 'diversidad_habilidades'
        ]].values

        # Combinar características
        combined_features = np.hstack([text_features, numeric_features])

        # Normalizar
        combined_features_scaled = self.scaler.fit_transform(combined_features)

        # Crear targets sintéticos más sofisticados
        project_vector = tfidf_matrix[-1].toarray().flatten()
        synthetic_targets = []

        for i, prof_vector in enumerate(text_features):
            # Similitud textual
            text_similarity = cosine_similarity([prof_vector], [project_vector])[0][0]

            # Características numéricas normalizadas
            prof_numeric = numeric_features[i]
            numeric_score = (
                    min(prof_numeric[0] / 15, 1) * 0.4 +  # experiencia
                    min(prof_numeric[1] / 5, 1) * 0.3 +  # educación
                    min(prof_numeric[2] / 8, 1) * 0.3  # habilidades
            )

            # Combinar puntuaciones
            final_score = text_similarity * 0.6 + numeric_score * 0.4
            synthetic_targets.append(final_score)

        # Entrenar MLP
        mlp = MLPRegressor(hidden_layer_sizes=(100, 50), max_iter=500, random_state=42)
        mlp.fit(combined_features_scaled, synthetic_targets)

        # Predecir
        predictions = mlp.predict(combined_features_scaled)

        results = pd.DataFrame({
            'professional_id': self.professionals_data['id'],
            'neural_score': predictions,
            'algorithm': 'Red Neuronal'
        })

        return results.sort_values('neural_score', ascending=False)

    def generate_recommendations(self, project_id, top_n=10):
        """
        Genera recomendaciones combinando los tres algoritmos
        """
        print(f"\nGenerando recomendaciones para el proyecto ID: {project_id}")
        print("=" * 60)

        # Obtener información del proyecto
        project_info = self.projects_data[self.projects_data['id'] == project_id].iloc[0]
        print(f"Proyecto: {project_info['nombre']}")
        print(f"Tipo: {project_info['tipo_proyecto']}")
        print(f"Presupuesto: ${project_info['presupuesto']:,}" if project_info['presupuesto'] else "No especificado")
        print("\n" + "=" * 60)

        # Ejecutar algoritmos
        results_1 = self.algorithm_1_tfidf_cosine(project_id)
        results_2 = self.algorithm_2_random_forest(project_id)
        results_3 = self.algorithm_3_neural_network(project_id)

        # Combinar resultados
        combined_results = pd.merge(
            results_1[['professional_id', 'similarity_score']],
            results_2[['professional_id', 'compatibility_score']],
            on='professional_id'
        )
        combined_results = pd.merge(
            combined_results,
            results_3[['professional_id', 'neural_score']],
            on='professional_id'
        )

        # Normalizar puntuaciones (0-1)
        combined_results['similarity_score_norm'] = (
                combined_results['similarity_score'] / combined_results['similarity_score'].max()
        )
        combined_results['compatibility_score_norm'] = (
                combined_results['compatibility_score'] / combined_results['compatibility_score'].max()
        )
        combined_results['neural_score_norm'] = (
                combined_results['neural_score'] / combined_results['neural_score'].max()
        )

        # Calcular puntuación final combinada
        combined_results['final_score'] = (
                combined_results['similarity_score_norm'] * 0.35 +
                combined_results['compatibility_score_norm'] * 0.35 +
                combined_results['neural_score_norm'] * 0.30
        )

        # Ordenar por puntuación final
        combined_results = combined_results.sort_values('final_score', ascending=False)

        # Agregar información de profesionales
        detailed_results = pd.merge(
            combined_results,
            self.professionals_data[['id', 'nombres', 'apellidos', 'email', 'puesto_actual',
                                     'dependencia', 'años_experiencia', 'nivel_educacion']],
            left_on='professional_id',
            right_on='id'
        )

        return detailed_results.head(top_n)

    def print_detailed_report(self, recommendations, project_id):
        """Imprime un reporte detallado de las recomendaciones"""
        project_info = self.projects_data[self.projects_data['id'] == project_id].iloc[0]

        print(f"\n{'=' * 80}")
        print(f"REPORTE DETALLADO DE RECOMENDACIONES")
        print(f"{'=' * 80}")
        print(f"Proyecto: {project_info['nombre']}")
        print(f"Objetivo: {project_info['objetivo'][:200]}...")
        print(f"Roles requeridos: {project_info['roles_requeridos']}")
        print(f"Habilidades requeridas: {project_info['habilidades_requeridas']}")
        print(f"\n{'=' * 80}")
        print(f"TOP {len(recommendations)} CANDIDATOS RECOMENDADOS:")
        print(f"{'=' * 80}")

        for idx, row in recommendations.iterrows():
            print(f"\n#{recommendations.index.get_loc(idx) + 1}. {row['nombres']} {row['apellidos']}")
            print(f"   Email: {row['email']}")
            print(f"   Puesto actual: {row['puesto_actual']}")
            print(f"   Dependencia: {row['dependencia']}")
            print(f"   Años de experiencia: {row['años_experiencia']}")
            print(f"   Nivel educativo: {row['nivel_educacion']}")
            print(f"   PUNTUACIONES:")
            print(f"     • Similitud TF-IDF: {row['similarity_score']:.3f}")
            print(f"     • Random Forest: {row['compatibility_score']:.3f}")
            print(f"     • Red Neuronal: {row['neural_score']:.3f}")
            print(f"     • PUNTUACIÓN FINAL: {row['final_score']:.3f}")
            print(f"   {'-' * 50}")

        print(f"\n{'=' * 80}")
        print("RESUMEN DE ALGORITMOS UTILIZADOS:")
        print(f"{'=' * 80}")
        print("1. TF-IDF + Similitud Coseno:")
        print("   - Analiza similitud textual entre perfil profesional y proyecto")
        print("   - Considera habilidades, experiencia, conocimientos y estudios")

        print("\n2. Random Forest:")
        print("   - Evalúa compatibilidad basada en características numéricas")
        print("   - Considera años de experiencia, nivel educativo y diversidad de habilidades")

        print("\n3. Red Neuronal (MLP):")
        print("   - Combina análisis textual y numérico")
        print("   - Aprende patrones complejos entre características")

        print(f"\n4. Puntuación Final:")
        print("   - Combinación ponderada: TF-IDF (35%) + Random Forest (35%) + Red Neuronal (30%)")


# Función principal de demostración
def main():
    """Función principal para demostrar el sistema"""
    # Nota: Ajusta la ruta de tu base de datos
    DB_PATH = "redudes.db"  # Cambia esto por la ruta real de tu base de datos

    try:
        # Inicializar el sistema
        matcher = ProfessionalProjectMatcher(DB_PATH)

        # Cargar y preprocesar datos
        print("Cargando datos de la base de datos...")
        matcher.load_data()

        print("Preprocesando datos...")
        matcher.preprocess_data()

        # Mostrar proyectos disponibles
        print("\nProyectos disponibles:")
        for idx, row in matcher.projects_data.iterrows():
            print(f"ID: {row['id']} - {row['nombre']}")

        # Ejemplo: generar recomendaciones para el primer proyecto
        if len(matcher.projects_data) > 0:
            project_id = matcher.projects_data.iloc[0]['id']
            recommendations = matcher.generate_recommendations(project_id, top_n=5)
            matcher.print_detailed_report(recommendations, project_id)
        else:
            print("No se encontraron proyectos en la base de datos.")

    except Exception as e:
        print(f"Error: {str(e)}")
        print("Asegúrate de que:")
        print("1. La base de datos existe en la ruta especificada")
        print("2. Las tablas tienen datos")
        print("3. Tienes instaladas las librerías necesarias:")
        print("   pip install pandas scikit-learn numpy sqlite3")


if __name__ == "__main__":
    main()