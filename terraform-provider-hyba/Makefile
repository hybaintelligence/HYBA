default: install

.PHONY: build
build:
	go build -o terraform-provider-hyba_v1.0.0

.PHONY: install
install: build
	mkdir -p ~/.terraform.d/plugins/registry.terraform.io/hyba-ai/hyba/1.0.0/darwin_arm64
	cp terraform-provider-hyba_v1.0.0 ~/.terraform.d/plugins/registry.terraform.io/hyba-ai/hyba/1.0.0/darwin_arm64/
	chmod +x ~/.terraform.d/plugins/registry.terraform.io/hyba-ai/hyba/1.0.0/darwin_arm64/terraform-provider-hyba_v1.0.0

.PHONY: test
test:
	go test -v -cover -timeout=2m ./...

.PHONY: fmt
fmt:
	gofmt -s -w -e .

.PHONY: lint
lint:
	golangci-lint run ./...

.PHONY: clean
clean:
	rm -f terraform-provider-hyba_v1.0.0
	go clean

.PHONY: docs
docs:
	go generate ./...

.PHONY: docker-build
docker-build:
	docker build -t hyba-terraform-provider:latest .

.PHONY: docker-push
docker-push:
	docker tag hyba-terraform-provider:latest registry.hyba.ai/hyba-terraform-provider:latest
	docker push registry.hyba.ai/hyba-terraform-provider:latest

.PHONY: help
help:
	@echo "HYBA Terraform Provider"
	@echo ""
	@echo "Commands:"
	@echo "  make build          Build the provider"
	@echo "  make install        Build and install locally"
	@echo "  make test           Run tests"
	@echo "  make fmt            Format code"
	@echo "  make lint           Run linter"
	@echo "  make docs           Generate documentation"
	@echo "  make clean          Clean build artifacts"
	@echo "  make docker-build   Build Docker image"
	@echo "  make docker-push    Push Docker image"
	@echo "  make help           Show this help message"
