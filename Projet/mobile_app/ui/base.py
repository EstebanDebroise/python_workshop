"""Classes de base abstraites pour les composants de l'interface utilisateur.

Définit les deux interfaces fondamentales de l'application :
- :class:`Buildable` pour tout composant capable de se construire en contrôle Flet.
- :class:`WeatherSection` pour les sections du dashboard réactives aux mesures météo.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import flet as ft

from models import Weather


class Buildable(ABC):
    """Interface de base pour tout composant capable de produire un contrôle Flet.

    Toutes les vues et sections de l'application héritent de cette classe
    afin de garantir un contrat uniforme d'affichage. Aucune logique n'est
    fournie ici : chaque sous-classe est responsable de sa propre construction.
    """

    @abstractmethod
    def build(self) -> ft.Control:
        """Construit et retourne l'arbre de contrôles Flet du composant.

        Cette méthode doit être appelée une seule fois au moment où le composant
        est ajouté à la page ou à son parent. Les mises à jour ultérieures se font
        via des modifications en place sur les contrôles internes.

        Args:
            Aucun.

        Returns:
            ft.Control: Le contrôle Flet racine du composant, prêt à être inséré
                dans la hiérarchie de la page.
        """


class WeatherSection(Buildable):
    """Interface des sections du dashboard réactives aux mesures météo.

    Étend :class:`Buildable` en ajoutant la méthode :meth:`update` qui permet
    à chaque section de se rafraîchir à la réception d'une nouvelle mesure
    météo provenant du consommateur Kafka.

    Les sections concrètes (:class:`CurrentWeatherSection`, :class:`ThiSection`,
    :class:`PastureSection`, :class:`TreatmentSection`) héritent de cette classe.
    """

    @abstractmethod
    def update(self, w: Weather) -> None:
        """Met à jour l'affichage de la section avec une nouvelle mesure météo.

        Les contrôles Flet internes sont modifiés en place ; la méthode ne
        reconstruit pas l'arbre. L'appelant est responsable d'appeler
        ``page.update()`` pour propager les changements à l'écran.

        Args:
            w (Weather): La nouvelle mesure météo reçue depuis Kafka, contenant
                température, humidité, vent et tous les autres indicateurs.

        Returns:
            None
        """

    @abstractmethod
    def reset(self) -> None:
        """Réinitialise la section à son état d'attente (avant toute mesure).

        Vide les données accumulées (historique, alertes…) et remet les contrôles
        Flet aux valeurs par défaut affichées au démarrage. Utilisé lors d'un
        changement de lieu pour ne pas mélanger les données de deux localisations.
        Les contrôles sont modifiés en place ; l'appelant déclenche ``page.update()``.

        Returns:
            None
        """
