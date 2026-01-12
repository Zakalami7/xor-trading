# Stage 1: Build
FROM rust:1.75-alpine AS builder

RUN apk add --no-cache musl-dev openssl-dev pkgconfig

WORKDIR /app
COPY . .

RUN cargo build --release

# Stage 2: Runtime
FROM alpine:3.19

RUN apk add --no-cache libgcc openssl ca-certificates

RUN adduser -D -u 1000 appuser

WORKDIR /app
COPY --from=builder /app/target/release/xor-execution-engine .

RUN chown -R appuser:appuser /app
USER appuser

CMD ["./xor-execution-engine"]
