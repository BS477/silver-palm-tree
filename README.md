# Person detection

Cel: rozdzielenie na 2 serwisy i kolejkę RabbitMQ, skalowalny konsumer i odporne wysyłanie wyników.

Szybkie uruchomienie (lokalnie, Docker Compose):

1) Zbuduj i uruchom całość:
   docker compose up --build

2) Panel RabbitMQ: http://localhost:15672 (guest/guest)

3) Service A (results API): http://localhost:8000
   - POST /results  (akceptuje JSON z image_url i count) — zapisuje do SQLite
   - GET /results

4) Service B (enqueue): http://localhost:8001
   - POST /count { "image_url": "http://..." } — kolejuje analizę do RabbitMQ

Skalowanie konsumerów:
- W docker swarm: ustaw ENV CONSUMER_REPLICAS, np.
  CONSUMER_REPLICAS=3 docker compose up --build
- Alternatywnie: docker compose up --scale consumer=3

Testy:
- Testy z kontenera docker o nazwie unittests
	docker exec unittests pytest

Uwaga o retry:
- Konsumer używa manualnego ack/nack; przy niepowodzeniu wysyłki do Serwisu A wiadomość jest ponownie publikowana z nagłówkiem `x-attempts`.
- Po przekroczeniu MAX_RETRIES wiadomość trafia do kolejki `person_count_failed` (DLQ).