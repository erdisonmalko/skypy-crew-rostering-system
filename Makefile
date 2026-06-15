PHONY: build, run, delete

build:
	docker build -t skypy-crew-rostering .
run:
	docker run -d --name skypy-crew-rostering -p 5000:5000 skypy-crew-rostering
delete:
	docker stop skypy-crew-rostering
	docker rm skypy-crew-rostering