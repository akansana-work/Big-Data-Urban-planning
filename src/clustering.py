"""
Clustering Module for Pune Urban Planning Analysis
Implements K-Means clustering with PCA for ward categorization and analysis.
"""

import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score, calinski_harabasz_score
import matplotlib.pyplot as plt
import seaborn as sns
import os
import json
import warnings
warnings.filterwarnings('ignore')

class UrbanClusteringAnalyzer:
    """Perform clustering analysis on urban planning data."""
    
    def __init__(self, data_dir: str = "data", output_dir: str = "outputs"):
        self.data_dir = data_dir
        self.processed_dir = os.path.join(data_dir, "processed")
        self.output_dir = output_dir
        self.charts_dir = os.path.join(output_dir, "charts")
        self.reports_dir = os.path.join(output_dir, "reports")
        
        # Ensure output directories exist
        os.makedirs(self.charts_dir, exist_ok=True)
        os.makedirs(self.reports_dir, exist_ok=True)
        
        # Clustering parameters
        self.n_clusters = 3
        self.random_state = 42
        
    def load_processed_data(self) -> dict:
        """Load processed datasets."""
        print("Loading processed data for clustering...")
        
        try:
            clustering_df = pd.read_csv(os.path.join(self.processed_dir, "processed_clustering.csv"))
            main_df = pd.read_csv(os.path.join(self.processed_dir, "processed_main.csv"))
            
            print(f"✅ Loaded clustering data: {len(clustering_df)} wards")
            return {
                'clustering': clustering_df,
                'main': main_df
            }
        except Exception as e:
            print(f"❌ Error loading processed data: {e}")
            return {}
    
    def determine_optimal_clusters(self, X: np.ndarray, max_k: int = 8) -> dict:
        """Determine optimal number of clusters using multiple methods."""
        print("Determining optimal number of clusters...")
        
        k_range = range(2, max_k + 1)
        inertias = []
        silhouette_scores = []
        calinski_scores = []
        
        for k in k_range:
            kmeans = KMeans(n_clusters=k, random_state=self.random_state, n_init=10)
            cluster_labels = kmeans.fit_predict(X)
            
            inertias.append(kmeans.inertia_)
            silhouette_scores.append(silhouette_score(X, cluster_labels))
            calinski_scores.append(calinski_harabasz_score(X, cluster_labels))
        
        # Create elbow plot
        fig, axes = plt.subplots(1, 3, figsize=(18, 5))
        
        # Elbow method
        axes[0].plot(k_range, inertias, 'bo-')
        axes[0].set_xlabel('Number of Clusters (k)')
        axes[0].set_ylabel('Within-cluster Sum of Squares')
        axes[0].set_title('Elbow Method for Optimal k')
        axes[0].grid(True, alpha=0.3)
        
        # Silhouette score
        axes[1].plot(k_range, silhouette_scores, 'ro-')
        axes[1].set_xlabel('Number of Clusters (k)')
        axes[1].set_ylabel('Silhouette Score')
        axes[1].set_title('Silhouette Score vs Number of Clusters')
        axes[1].grid(True, alpha=0.3)
        
        # Calinski-Harabasz score
        axes[2].plot(k_range, calinski_scores, 'go-')
        axes[2].set_xlabel('Number of Clusters (k)')
        axes[2].set_ylabel('Calinski-Harabasz Score')
        axes[2].set_title('Calinski-Harabasz Score vs Number of Clusters')
        axes[2].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.charts_dir, 'cluster_optimization.png'), dpi=300, bbox_inches='tight')
        plt.close()
        
        # Find optimal k (max silhouette score)
        optimal_k_silhouette = k_range[np.argmax(silhouette_scores)]
        optimal_k_calinski = k_range[np.argmax(calinski_scores)]
        
        results = {
            'k_range': list(k_range),
            'inertias': inertias,
            'silhouette_scores': silhouette_scores,
            'calinski_scores': calinski_scores,
            'optimal_k_silhouette': optimal_k_silhouette,
            'optimal_k_calinski': optimal_k_calinski,
            'recommended_k': 3  # As per requirements
        }
        
        print(f"✅ Optimal k analysis completed")
        print(f"   • Best k (Silhouette): {optimal_k_silhouette}")
        print(f"   • Best k (Calinski-Harabasz): {optimal_k_calinski}")
        print(f"   • Using k=3 as per requirements")
        
        return results
    
    def apply_pca(self, X: np.ndarray, n_components: int = None) -> dict:
        """Apply PCA for dimensionality reduction."""
        print("Applying PCA for dimensionality reduction...")
        
        # Determine number of components if not specified
        if n_components is None:
            # Use components that explain 90% of variance
            pca_full = PCA()
            pca_full.fit(X)
            cumsum_variance = np.cumsum(pca_full.explained_variance_ratio_)
            n_components = np.argmax(cumsum_variance >= 0.90) + 1
        
        # Apply PCA
        pca = PCA(n_components=n_components, random_state=self.random_state)
        X_pca = pca.fit_transform(X)
        
        # Create PCA analysis plots
        fig, axes = plt.subplots(1, 2, figsize=(15, 6))
        
        # Explained variance
        axes[0].bar(range(1, len(pca.explained_variance_ratio_) + 1), 
                   pca.explained_variance_ratio_, alpha=0.7)
        axes[0].plot(range(1, len(pca.explained_variance_ratio_) + 1), 
                    np.cumsum(pca.explained_variance_ratio_), 'ro-')
        axes[0].set_xlabel('Principal Component')
        axes[0].set_ylabel('Explained Variance Ratio')
        axes[0].set_title('PCA Explained Variance')
        axes[0].grid(True, alpha=0.3)
        axes[0].legend(['Cumulative', 'Individual'])
        
        # PCA scatter (first two components)
        if X_pca.shape[1] >= 2:
            axes[1].scatter(X_pca[:, 0], X_pca[:, 1], alpha=0.7)
            axes[1].set_xlabel(f'PC1 ({pca.explained_variance_ratio_[0]:.2%} variance)')
            axes[1].set_ylabel(f'PC2 ({pca.explained_variance_ratio_[1]:.2%} variance)')
            axes[1].set_title('PCA: First Two Principal Components')
            axes[1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.charts_dir, 'pca_analysis.png'), dpi=300, bbox_inches='tight')
        plt.close()
        
        results = {
            'pca_model': pca,
            'X_transformed': X_pca,
            'explained_variance_ratio': pca.explained_variance_ratio_,
            'cumulative_variance': np.cumsum(pca.explained_variance_ratio_),
            'n_components': n_components,
            'total_variance_explained': np.sum(pca.explained_variance_ratio_)
        }
        
        print(f"✅ PCA completed:")
        print(f"   • Components: {n_components}")
        print(f"   • Variance explained: {results['total_variance_explained']:.2%}")
        
        return results
    
    def perform_kmeans_clustering(self, X: np.ndarray, k: int = 3) -> dict:
        """Perform K-Means clustering."""
        print(f"Performing K-Means clustering with k={k}...")
        
        # Fit K-Means
        kmeans = KMeans(n_clusters=k, random_state=self.random_state, n_init=10)
        cluster_labels = kmeans.fit_predict(X)
        
        # Calculate clustering metrics
        silhouette_avg = silhouette_score(X, cluster_labels)
        calinski_score = calinski_harabasz_score(X, cluster_labels)
        
        # Cluster centers
        cluster_centers = kmeans.cluster_centers_
        
        results = {
            'model': kmeans,
            'labels': cluster_labels,
            'centers': cluster_centers,
            'silhouette_score': silhouette_avg,
            'calinski_score': calinski_score,
            'inertia': kmeans.inertia_,
            'n_clusters': k
        }
        
        print(f"✅ K-Means clustering completed:")
        print(f"   • Silhouette Score: {silhouette_avg:.3f}")
        print(f"   • Calinski-Harabasz Score: {calinski_score:.2f}")
        print(f"   • Inertia: {kmeans.inertia_:.2f}")
        
        return results
    
    def interpret_clusters(self, clustering_df: pd.DataFrame, main_df: pd.DataFrame, 
                          cluster_labels: np.ndarray, feature_names: list) -> dict:
        """Interpret and characterize clusters."""
        print("Interpreting cluster characteristics...")
        
        # Add cluster labels to dataframes
        result_df = main_df.copy()
        result_df['Cluster'] = cluster_labels
        
        clustering_with_labels = clustering_df.copy()
        clustering_with_labels['Cluster'] = cluster_labels
        
        # Calculate cluster statistics
        cluster_stats = {}
        cluster_interpretations = {}
        
        for cluster_id in range(len(np.unique(cluster_labels))):
            cluster_mask = result_df['Cluster'] == cluster_id
            cluster_data = result_df[cluster_mask]
            
            # Basic statistics
            stats = {
                'count': len(cluster_data),
                'percentage': len(cluster_data) / len(result_df) * 100,
                'wards': cluster_data['Ward_Name'].tolist()
            }
            
            # Feature means for interpretation
            feature_means = {}
            key_features = [
                'Population_Density_Calc', 'Pollution_Load_Index_Calc', 'Infrastructure_Density_Calc',
                'Traffic_Stress_Index', 'Environmental_Quality_Score', 'Green_Cover_Percentage',
                'AQI', 'Congestion_Index', 'Average_Income', 'Quality_of_Life_Index'
            ]
            
            for feature in key_features:
                if feature in cluster_data.columns:
                    feature_means[feature] = cluster_data[feature].mean()
            
            stats['feature_means'] = feature_means
            cluster_stats[f'Cluster_{cluster_id}'] = stats
            
            # Interpret cluster based on characteristics
            interpretation = self._interpret_cluster_type(feature_means)
            cluster_interpretations[f'Cluster_{cluster_id}'] = interpretation
        
        # Create cluster visualization
        self._visualize_clusters(result_df, cluster_interpretations)
        
        # Generate cluster profiles
        self._create_cluster_profiles(result_df, key_features)
        
        results = {
            'cluster_stats': cluster_stats,
            'interpretations': cluster_interpretations,
            'result_dataframe': result_df,
            'cluster_centers_interpretation': self._interpret_cluster_centers(cluster_stats)
        }
        
        print("✅ Cluster interpretation completed")
        return results
    
    def _interpret_cluster_type(self, feature_means: dict) -> dict:
        """Interpret cluster type based on feature means."""
        interpretation = {
            'type': 'Unknown',
            'characteristics': [],
            'description': ''
        }
        
        # Get normalized values (assuming 0-1 scale from preprocessing)
        pop_density = feature_means.get('Population_Density_Calc', 0)
        pollution = feature_means.get('Pollution_Load_Index_Calc', 0)
        infrastructure = feature_means.get('Infrastructure_Density_Calc', 0)
        traffic_stress = feature_means.get('Traffic_Stress_Index', 0)
        env_quality = feature_means.get('Environmental_Quality_Score', 0)
        green_cover = feature_means.get('Green_Cover_Percentage', 0)
        income = feature_means.get('Average_Income', 0)
        
        # Define thresholds (based on normalized 0-1 scale)
        high_threshold = 0.6
        medium_threshold = 0.4
        
        # Cluster interpretation logic
        if (pollution > high_threshold and traffic_stress > high_threshold and 
            infrastructure > medium_threshold):
            interpretation['type'] = 'High-Development Commercial/IT Hub'
            interpretation['characteristics'] = [
                'High traffic congestion', 'Elevated pollution levels', 
                'Dense infrastructure', 'Commercial activity'
            ]
            interpretation['description'] = 'Urban areas with intense commercial activity, high traffic, and pollution. Require traffic management and pollution control measures.'
            
        elif (green_cover > medium_threshold and env_quality > medium_threshold and 
              pollution < medium_threshold):
            interpretation['type'] = 'Planned Residential/Green Zone'
            interpretation['characteristics'] = [
                'Good green cover', 'Better air quality', 
                'Planned development', 'Residential focus'
            ]
            interpretation['description'] = 'Well-planned residential areas with good environmental quality and green spaces. Model for sustainable urban development.'
            
        else:
            interpretation['type'] = 'Mixed Residential Zone'
            interpretation['characteristics'] = [
                'Moderate development', 'Mixed land use', 
                'Balanced characteristics', 'Residential with commercial'
            ]
            interpretation['description'] = 'Areas with mixed residential and commercial development, showing moderate levels across all parameters.'
        
        return interpretation
    
    def _visualize_clusters(self, result_df: pd.DataFrame, interpretations: dict):
        """Create cluster visualization plots."""
        
        # Set up the plotting style
        plt.style.use('default')
        sns.set_palette("husl")
        
        # Create cluster distribution plot
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        
        # 1. Cluster distribution
        cluster_counts = result_df['Cluster'].value_counts().sort_index()
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
        
        wedges, texts, autotexts = axes[0,0].pie(cluster_counts.values, 
                                                labels=[f'Cluster {i}' for i in cluster_counts.index],
                                                autopct='%1.1f%%', startangle=90, colors=colors)
        axes[0,0].set_title('Ward Distribution by Cluster', fontsize=14, fontweight='bold')
        
        # 2. Population vs Infrastructure scatter
        scatter = axes[0,1].scatter(result_df['Population_Density_Calc'], 
                                   result_df['Infrastructure_Density_Calc'],
                                   c=result_df['Cluster'], cmap='viridis', alpha=0.7, s=60)
        axes[0,1].set_xlabel('Population Density')
        axes[0,1].set_ylabel('Infrastructure Density')
        axes[0,1].set_title('Population vs Infrastructure Density by Cluster')
        plt.colorbar(scatter, ax=axes[0,1])
        
        # 3. Traffic vs Pollution scatter
        scatter2 = axes[1,0].scatter(result_df['Traffic_Stress_Index'], 
                                    result_df['Pollution_Load_Index_Calc'],
                                    c=result_df['Cluster'], cmap='viridis', alpha=0.7, s=60)
        axes[1,0].set_xlabel('Traffic Stress Index')
        axes[1,0].set_ylabel('Pollution Load Index')
        axes[1,0].set_title('Traffic vs Pollution by Cluster')
        plt.colorbar(scatter2, ax=axes[1,0])
        
        # 4. Environmental Quality vs Green Cover
        scatter3 = axes[1,1].scatter(result_df['Environmental_Quality_Score'], 
                                    result_df['Green_Cover_Percentage'],
                                    c=result_df['Cluster'], cmap='viridis', alpha=0.7, s=60)
        axes[1,1].set_xlabel('Environmental Quality Score')
        axes[1,1].set_ylabel('Green Cover Percentage')
        axes[1,1].set_title('Environmental Quality vs Green Cover by Cluster')
        plt.colorbar(scatter3, ax=axes[1,1])
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.charts_dir, 'cluster_analysis.png'), dpi=300, bbox_inches='tight')
        plt.close()
    
    def _create_cluster_profiles(self, result_df: pd.DataFrame, key_features: list):
        """Create radar charts for cluster profiles."""
        
        # Calculate mean values for each cluster
        cluster_means = result_df.groupby('Cluster')[key_features].mean()
        
        # Create radar chart
        angles = np.linspace(0, 2 * np.pi, len(key_features), endpoint=False).tolist()
        angles += angles[:1]  # Complete the circle
        
        fig, ax = plt.subplots(figsize=(12, 12), subplot_kw=dict(projection='polar'))
        
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
        
        for i, cluster in enumerate(cluster_means.index):
            values = cluster_means.iloc[i].tolist()
            values += values[:1]  # Complete the circle
            
            ax.plot(angles, values, 'o-', linewidth=2, 
                   label=f'Cluster {cluster}', color=colors[i % len(colors)])
            ax.fill(angles, values, alpha=0.25, color=colors[i % len(colors)])
        
        # Customize the radar chart
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels([f.replace('_', ' ').title() for f in key_features], fontsize=10)
        ax.set_ylim(0, 1)
        ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
        ax.set_yticklabels(['0.2', '0.4', '0.6', '0.8', '1.0'])
        ax.grid(True)
        
        plt.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))
        plt.title('Cluster Profiles - Key Urban Planning Features', 
                 size=16, fontweight='bold', pad=20)
        
        plt.savefig(os.path.join(self.charts_dir, 'cluster_radar_profiles.png'), 
                   dpi=300, bbox_inches='tight')
        plt.close()
    
    def _interpret_cluster_centers(self, cluster_stats: dict) -> dict:
        """Provide detailed interpretation of cluster centers."""
        interpretations = {}
        
        for cluster_id, stats in cluster_stats.items():
            features = stats['feature_means']
            wards = stats['wards']
            
            # Identify high-profile wards in each cluster
            notable_wards = []
            if 'Shivajinagar' in wards:
                notable_wards.append('Shivajinagar (Commercial Hub)')
            if 'Kothrud' in wards:
                notable_wards.append('Kothrud (Planned Residential)')
            if 'Hinjewadi' in wards:
                notable_wards.append('Hinjewadi (IT Hub)')
            
            interpretation = {
                'ward_count': stats['count'],
                'percentage': round(stats['percentage'], 1),
                'notable_wards': notable_wards,
                'key_characteristics': self._get_key_characteristics(features),
                'planning_recommendations': self._get_planning_recommendations(features)
            }
            
            interpretations[cluster_id] = interpretation
        
        return interpretations
    
    def _get_key_characteristics(self, features: dict) -> list:
        """Extract key characteristics from feature means."""
        characteristics = []
        
        # Define thresholds
        high = 0.6
        medium = 0.4
        
        if features.get('Pollution_Load_Index_Calc', 0) > high:
            characteristics.append('High pollution levels')
        if features.get('Traffic_Stress_Index', 0) > high:
            characteristics.append('Heavy traffic congestion')
        if features.get('Infrastructure_Density_Calc', 0) > high:
            characteristics.append('Dense infrastructure')
        if features.get('Green_Cover_Percentage', 0) > medium:
            characteristics.append('Good green cover')
        if features.get('Environmental_Quality_Score', 0) > medium:
            characteristics.append('Better environmental quality')
        
        return characteristics
    
    def _get_planning_recommendations(self, features: dict) -> list:
        """Generate planning recommendations based on cluster characteristics."""
        recommendations = []
        
        high = 0.6
        medium = 0.4
        
        if features.get('Pollution_Load_Index_Calc', 0) > high:
            recommendations.append('Implement pollution control measures')
            recommendations.append('Promote electric vehicles and public transport')
        
        if features.get('Traffic_Stress_Index', 0) > high:
            recommendations.append('Improve traffic management systems')
            recommendations.append('Develop alternative transportation routes')
        
        if features.get('Green_Cover_Percentage', 0) < medium:
            recommendations.append('Increase green spaces and tree plantation')
            recommendations.append('Create parks and recreational areas')
        
        if features.get('Infrastructure_Density_Calc', 0) < medium:
            recommendations.append('Develop basic infrastructure and amenities')
            recommendations.append('Improve healthcare and education facilities')
        
        return recommendations
    
    def save_clustering_results(self, results: dict):
        """Save clustering results and analysis."""
        print("Saving clustering results...")
        
        # Save cluster assignments
        if 'result_dataframe' in results:
            results['result_dataframe'].to_csv(
                os.path.join(self.processed_dir, 'clustered_wards.csv'), index=False)
        
        # Save interpretation results
        interpretation_results = {
            'cluster_statistics': results.get('cluster_stats', {}),
            'cluster_interpretations': results.get('interpretations', {}),
            'cluster_centers_analysis': results.get('cluster_centers_interpretation', {}),
            'analysis_summary': {
                'total_wards': len(results.get('result_dataframe', [])),
                'n_clusters': len(results.get('cluster_stats', {})),
                'clustering_metrics': {
                    'silhouette_score': results.get('silhouette_score'),
                    'calinski_score': results.get('calinski_score')
                }
            }
        }
        
        with open(os.path.join(self.reports_dir, 'clustering_analysis.json'), 'w') as f:
            json.dump(interpretation_results, f, indent=2, default=str)
        
        print("✅ Clustering results saved")
    
    def run_clustering_pipeline(self) -> dict:
        """Run the complete clustering analysis pipeline."""
        print("🔄 Starting clustering analysis pipeline...")
        print("=" * 50)
        
        # 1. Load processed data
        data = self.load_processed_data()
        if not data:
            return {}
        
        clustering_df = data['clustering']
        main_df = data['main']
        
        # 2. Prepare feature matrix
        feature_columns = [col for col in clustering_df.columns 
                          if col not in ['Ward_ID', 'Ward_Name']]
        X = clustering_df[feature_columns].values
        
        print(f"Using {len(feature_columns)} features for clustering")
        
        # 3. Determine optimal clusters
        optimization_results = self.determine_optimal_clusters(X)
        
        # 4. Apply PCA (optional dimensionality reduction)
        pca_results = self.apply_pca(X)
        
        # 5. Perform K-Means clustering on original features
        clustering_results = self.perform_kmeans_clustering(X, k=self.n_clusters)
        
        # 6. Interpret clusters
        interpretation_results = self.interpret_clusters(
            clustering_df, main_df, clustering_results['labels'], feature_columns)
        
        # 7. Combine all results
        final_results = {
            **optimization_results,
            **pca_results,
            **clustering_results,
            **interpretation_results,
            'feature_names': feature_columns
        }
        
        # 8. Save results
        self.save_clustering_results(final_results)
        
        print("=" * 50)
        print("✅ Clustering analysis pipeline completed!")
        self._print_clustering_summary(final_results)
        
        return final_results
    
    def _print_clustering_summary(self, results: dict):
        """Print a summary of clustering results."""
        print("\n📊 Clustering Analysis Summary:")
        print(f"   • Number of clusters: {results.get('n_clusters', 'N/A')}")
        print(f"   • Silhouette score: {results.get('silhouette_score', 0):.3f}")
        print(f"   • Calinski-Harabasz score: {results.get('calinski_score', 0):.2f}")
        
        print("\n🏘️  Cluster Interpretations:")
        interpretations = results.get('interpretations', {})
        for cluster_id, interpretation in interpretations.items():
            print(f"   • {cluster_id}: {interpretation['type']}")
            print(f"     Characteristics: {', '.join(interpretation['characteristics'])}")
        
        print(f"\n📈 PCA: {results.get('n_components', 'N/A')} components explain " +
              f"{results.get('total_variance_explained', 0):.1%} of variance")

if __name__ == "__main__":
    analyzer = UrbanClusteringAnalyzer()
    results = analyzer.run_clustering_pipeline()
    
    if results:
        print("\n🎯 Key Findings:")
        cluster_stats = results.get('cluster_stats', {})
        for cluster_id, stats in cluster_stats.items():
            print(f"   • {cluster_id}: {stats['count']} wards ({stats['percentage']:.1f}%)")
            if stats.get('wards'):
                notable = [w for w in stats['wards'] if w in ['Shivajinagar', 'Kothrud', 'Hinjewadi']]
                if notable:
                    print(f"     Notable wards: {', '.join(notable)}")
