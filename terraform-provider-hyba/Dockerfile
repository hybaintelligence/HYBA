# Build stage
FROM golang:1.21 as builder

WORKDIR /workspace

# Copy go mod files
COPY go.mod go.mod
COPY go.sum go.sum

# Download dependencies
RUN go mod download

# Copy source code
COPY main.go main.go
COPY internal/ internal/

# Build the provider
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build \
    -a -ldflags="-w -s -X main.version=1.0.0" \
    -o terraform-provider-hyba_v1.0.0 main.go

# Runtime stage for provider binary
FROM alpine:3.18
RUN apk add --no-cache ca-certificates

COPY --from=builder /workspace/terraform-provider-hyba_v1.0.0 /usr/local/bin/

ENTRYPOINT ["/usr/local/bin/terraform-provider-hyba_v1.0.0"]
