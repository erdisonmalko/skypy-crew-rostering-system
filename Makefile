.PHONY: build run stop delete test generate

IMAGE=skypy-crew-rostering
CONTAINER=skypy-crew-rostering

build:
	docker build -t $(IMAGE) .

run:
	docker run -d --name $(CONTAINER) -p 5000:5000 $(IMAGE)

stop:
	-docker stop $(CONTAINER)

delete:
	-docker rm -f $(CONTAINER)

test:
	python3 -m pytest -q

generate:
	python3 scripts/generate_roster.py