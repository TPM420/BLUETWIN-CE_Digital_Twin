import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


def prepare_layer_matrix(layer_scores_dict):
    """
    layer_scores_dict:
        {
            region1: {'L1':..., 'L2':...},
            region2: {...}
        }
    """

    regions = list(layer_scores_dict.keys())
    layers = list(next(iter(layer_scores_dict.values())).keys())

    X = np.array([
        [layer_scores_dict[r][l] for l in layers]
        for r in regions
    ])

    return regions, layers, X


def run_kmeans(X, k=3):
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = KMeans(n_clusters=k, random_state=42)
    labels = model.fit_predict(X_scaled)

    return labels


def analyze_clusters(regions, labels, bz_scores):
    clusters = {}

    for r, c in zip(regions, labels):
        if c not in clusters:
            clusters[c] = {
                "regions": [],
                "bz": []
            }

        clusters[c]["regions"].append(r)
        clusters[c]["bz"].append(bz_scores[r])

    # print summary
    for c, data in clusters.items():
        avg_bz = np.mean(data["bz"])
        print(f"\nCluster {c}")
        print(f"Regions: {len(data['regions'])}")
        print(f"Average BZ: {avg_bz:.3f}")
        print(f"Members: {data['regions']}")

    return clusters