#!/usr/bin/env python3
"""Run the weather collector with the current Jona shooting-plan locations and times."""

from __future__ import annotations

import importlib.util
from pathlib import Path


COLLECTOR_PATH = Path(__file__).with_name("update_weather.py")
SPEC = importlib.util.spec_from_file_location("jona_weather_collector", COLLECTOR_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"No se pudo cargar el recolector: {COLLECTOR_PATH}")

collector = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(collector)

collector.LOCATIONS = {
    "ciudad_costa": {
        "name": "Ciudad de la Costa",
        "latitude": -34.8167,
        "longitude": -55.9500,
    },
    "la_paz": {
        "name": "La Paz",
        "latitude": -34.7603,
        "longitude": -56.2259,
    },
    "las_piedras": {
        "name": "Las Piedras",
        "latitude": -34.7264,
        "longitude": -56.2200,
    },
    "parque_del_plata": {
        "name": "Parque del Plata",
        "latitude": -34.7574,
        "longitude": -55.6961,
    },
}

collector.SHOOT_DAYS = [
    {
        "id": "day-1",
        "number": 1,
        "date": "2026-07-25",
        "label": "Sábado 25 de julio",
        "weekend": "first",
        "locations": "Taller · Ciudad de la Costa · Casa Negro · La Paz",
        "blocks": [
            {
                "id": "day-1-workshop",
                "time": "08:00–13:00",
                "start": "08:00",
                "end": "13:00",
                "location_id": "ciudad_costa",
                "location": "Taller · Ciudad de la Costa",
                "type": "Interior y exterior día",
                "sensitivity": ["lluvia", "viento", "niebla", "continuidad de luz"],
            },
            {
                "id": "day-1-la-paz",
                "time": "19:00–20:30",
                "start": "19:00",
                "end": "20:30",
                "location_id": "la_paz",
                "location": "Casa Negro · La Paz",
                "type": "Exterior tardecita / noche",
                "sensitivity": ["lluvia", "viento", "luz de atardecer"],
            },
        ],
    },
    {
        "id": "day-2",
        "number": 2,
        "date": "2026-07-26",
        "label": "Domingo 26 de julio",
        "weekend": "first",
        "locations": "Auto y Casa Jona · La Paz · Colina · Las Piedras",
        "blocks": [
            {
                "id": "day-2-la-paz",
                "time": "14:00–15:30",
                "start": "14:00",
                "end": "15:30",
                "location_id": "la_paz",
                "location": "Auto y Casa Jona · La Paz",
                "type": "Exteriores día",
                "sensitivity": ["lluvia", "viento", "continuidad de cielo"],
            },
            {
                "id": "day-2-colina",
                "time": "18:00–20:30",
                "start": "18:00",
                "end": "20:30",
                "location_id": "las_piedras",
                "location": "Colina · Las Piedras",
                "type": "Exterior noche",
                "sensitivity": ["pasto mojado", "viento para la vela", "lluvia", "frío"],
            },
        ],
    },
    {
        "id": "day-3",
        "number": 3,
        "date": "2026-08-01",
        "label": "Sábado 1.º de agosto",
        "weekend": "second",
        "locations": "Colina · La Paz · Casa · Parque del Plata",
        "blocks": [
            {
                "id": "day-3-colina",
                "time": "07:30–08:30",
                "start": "07:30",
                "end": "08:30",
                "location_id": "la_paz",
                "location": "Colina · La Paz",
                "type": "Exterior mañana",
                "sensitivity": ["rocío", "pasto mojado", "lluvia", "viento", "frío"],
            },
            {
                "id": "day-3-interiors",
                "time": "10:00–18:30",
                "start": "10:00",
                "end": "18:30",
                "location_id": "parque_del_plata",
                "location": "Casa · Parque del Plata",
                "type": "Interiores con necesidad de luz solar",
                "sensitivity": ["nubosidad", "sol directo", "ruido de lluvia", "viento / sonido"],
            },
            {
                "id": "day-3-night",
                "time": "18:30–23:00",
                "start": "18:30",
                "end": "23:00",
                "location_id": "parque_del_plata",
                "location": "Casa · Parque del Plata",
                "type": "Exteriores tardecita / noche",
                "sensitivity": ["lluvia", "viento", "frío", "humedad"],
            },
        ],
    },
    {
        "id": "day-4",
        "number": 4,
        "date": "2026-08-02",
        "label": "Domingo 2 de agosto",
        "weekend": "second",
        "locations": "Casa · Parque del Plata",
        "blocks": [
            {
                "id": "day-4-exterior",
                "time": "10:00–12:30",
                "start": "10:00",
                "end": "12:30",
                "location_id": "parque_del_plata",
                "location": "Casa · Parque del Plata",
                "type": "Exterior día",
                "sensitivity": ["lluvia", "continuidad de sol", "viento"],
            },
            {
                "id": "day-4-interiors",
                "time": "12:30–17:30",
                "start": "12:30",
                "end": "17:30",
                "location_id": "parque_del_plata",
                "location": "Casa · Parque del Plata",
                "type": "Interiores",
                "sensitivity": ["ruido de lluvia", "llegadas", "temperatura"],
            },
        ],
    },
]

collector.WEEKENDS = [
    {
        "id": "first",
        "label": "Primer fin de semana",
        "dates": "25–26 de julio",
        "description": "Ciudad de la Costa · La Paz · Las Piedras",
    },
    {
        "id": "second",
        "label": "Segundo fin de semana",
        "dates": "1–2 de agosto",
        "description": "La Paz · Parque del Plata",
    },
]


if __name__ == "__main__":
    raise SystemExit(collector.main())
