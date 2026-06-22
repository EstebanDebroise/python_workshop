"""Abstract base classes for UI components.

Defines the two fundamental interfaces of the application:
- :class:`Buildable` for any component capable of building itself into a Flet control.
- :class:`WeatherSection` for dashboard sections reactive to weather measurements.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import flet as ft

from models import Weather


class Buildable(ABC):
    """Base interface for any component capable of producing a Flet control.

    All views and sections of the application inherit from this class to ensure
    a uniform display contract. No logic is provided here: each subclass is
    responsible for its own construction.
    """

    @abstractmethod
    def build(self) -> ft.Control:
        """Build and return the Flet control tree for the component.

        This method should be called only once when the component is added to
        the page or its parent. Later updates are done via in-place modifications
        of the internal controls.

        Args:
            None.

        Returns:
            ft.Control: The root Flet control of the component, ready to be
                inserted into the page hierarchy.
        """


class WeatherSection(Buildable):
    """Interface for dashboard sections reactive to weather measurements.

    Extends :class:`Buildable` by adding the :meth:`update` method that allows
    each section to refresh when a new weather measurement from the Kafka
    consumer is received.

    Concrete sections (:class:`CurrentWeatherSection`, :class:`ThiSection`,
    :class:`PastureSection`, :class:`TreatmentSection`) inherit from this class.
    """

    @abstractmethod
    def update(self, w: Weather) -> None:
        """Update the section display with a new weather measurement.

        Internal Flet controls are modified in-place; the method does not
        rebuild the tree. The caller is responsible for calling ``page.update()``
        to propagate the changes to the screen.

        Args:
            w (Weather): The new weather measurement received from Kafka, containing
                temperature, humidity, wind, and all other indicators.

        Returns:
            None
        """

    @abstractmethod
    def reset(self) -> None:
        """Reset the section to its waiting state (before any measurement).

        Clear accumulated data (history, alerts, etc.) and reset Flet controls
        to default values displayed at startup. Used when changing location to
        avoid mixing data from two locations. Controls are modified in-place;
        the caller triggers ``page.update()``.

        Returns:
            None
        """
