Testy integracyjne i jednostkowe

- tests/test_service_a.py - testuje endpointy Service A (uruchamia FastAPI TestClient)
- tests/test_service_b.py - testuje integracyjnie Service B
- tests/test_integration_flow.py - integracyjny test przepływu requires docker-compose up (Rabbit + serwisy)

Uruchomienie:
- Aby uruchomić testy jednostkowe: `pytest tests/test_service_a.py tests/test_service_b.py`

- Integracyjny: upewnij się, że docker compose up --build działa, potem uruchom `pytest tests/test_integration_flow.py`
