"""Actualizacion Bayesiana secuencial (Naive Bayes con evidencia definida por experto).

Cada ventana de actividad de una entidad (IP) es una nueva evidencia. Se trabaja en
log-odds, asi multiplicar razones de verosimilitud equivale a sumar.
    odds_nuevo = odds_previo * prod( P(senal|ataque) / P(senal|normal) )
Si una senal NO aparece se usa (1-P(s|ataque)) / (1-P(s|normal)), lo que hace que
la probabilidad tambien pueda bajar cuando la actividad se normaliza.
Temas del curso: regla de Bayes, actualizacion Bayesiana, clasificador Bayesiano."""
import math


def _logit(p):
    return math.log(p / (1 - p))


def _prob(l):
    return 1.0 / (1.0 + math.exp(-l))


class SeguimientoBayes:
    def __init__(self, prior, evidencia, limites):
        self.l0 = _logit(prior)
        self.lmin, self.lmax = _logit(limites[0]), _logit(limites[1])
        self.evidencia = evidencia
        self.estado = {}                      # entidad -> log-odds actual

    def actualizar(self, entidad, senales):
        l = self.estado.get(entidad, self.l0)
        for nombre, (p_ataque, p_normal) in self.evidencia.items():
            if nombre not in senales:
                continue
            if senales[nombre]:
                l += math.log(p_ataque / p_normal)
            else:
                l += math.log((1 - p_ataque) / (1 - p_normal))
        l = min(max(l, self.lmin), self.lmax)
        self.estado[entidad] = l
        return _prob(l)
