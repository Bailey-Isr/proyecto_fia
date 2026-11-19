"""KNN implementado desde cero. Uso: puntaje de RAREZA (sin etiquetas).

Aprende lo normal del servidor (ventanas del periodo base). Para una ventana nueva
mide la distancia promedio a sus k vecinos mas cercanos y la compara con las
distancias que tienen entre si las ventanas normales. Salida entre 0 y 1:
cerca de 1 = mas rara que casi todo lo visto en el periodo base.
Temas del curso: KNN, hiperparametro k, efecto del escalamiento."""
import numpy as np


class DetectorRareza:
    def __init__(self, k=5, escalar=True, max_base=3000, semilla=0):
        self.k = k
        self.escalar = escalar
        self.max_base = max_base
        self.rng = np.random.default_rng(semilla)

    @staticmethod
    def _distancias(A, B):
        a2 = (A ** 2).sum(1)[:, None]
        b2 = (B ** 2).sum(1)[None, :]
        return np.sqrt(np.maximum(a2 + b2 - 2 * A @ B.T, 0.0))

    def _kdist(self, D):
        k = min(self.k, D.shape[1])
        return np.partition(D, k - 1, axis=1)[:, :k].mean(axis=1)

    def ajustar(self, X):
        X = np.asarray(X, dtype=float)
        if len(X) > self.max_base:                      # muestra para no saturar memoria
            X = X[self.rng.choice(len(X), self.max_base, replace=False)]
        if self.escalar:                                # estandarizacion (z-score)
            self.media = X.mean(axis=0)
            self.desv = X.std(axis=0)
            self.desv[self.desv == 0] = 1.0
        else:
            self.media = np.zeros(X.shape[1])
            self.desv = np.ones(X.shape[1])
        self.base = (X - self.media) / self.desv
        D = self._distancias(self.base, self.base)
        np.fill_diagonal(D, np.inf)                     # no contarse a si mismo
        self.dist_base = np.sort(self._kdist(D))
        return self

    def puntajes(self, X, bloque=500):
        X = (np.asarray(X, dtype=float) - self.media) / self.desv
        salida = []
        for i in range(0, len(X), bloque):
            d = self._kdist(self._distancias(X[i:i + bloque], self.base))
            salida.append(np.searchsorted(self.dist_base, d, side="left") / len(self.dist_base))
        return np.concatenate(salida) if salida else np.array([])
